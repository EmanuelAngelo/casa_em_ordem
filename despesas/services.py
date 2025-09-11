from datetime import date
from dateutil.relativedelta import relativedelta
from decimal import Decimal, ROUND_DOWN
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from .models import (
    Casal, CompraCartao, MembroCasal, DespesaModelo, Lancamento, RateioLancamento,
    EscopoDespesa, RegraRateio, StatusLancamento, RegraRateioPadrao, Categoria, Subcategoria
)

User = get_user_model()

# --- NOVA FUNÇÃO PARA CRIAR CATEGORIAS PADRÃO ---

CATEGORIAS_PADRAO = {
    "Moradia": ["Aluguel", "Condomínio", "Energia", "Água", "Internet", "Gás", "Manutenção"],
    "Alimentação": ["Supermercado", "Restaurante/Lanchonete", "Delivery"],
    "Transporte": ["Combustível", "Uber/99", "Manutenção do carro", "Transporte público"],
    "Saúde": ["Plano de saúde", "Farmácia", "Consultas/Exames"],
    "Lazer e Assinaturas": ["Streaming (Netflix, etc)", "Academia", "Viagens", "Passeios"],
    "Educação": ["Cursos", "Livros/Material", "Mensalidades"],
    "Finanças": ["Fatura do Cartão", "Empréstimos", "Investimentos", "Seguros"],
    "Compras Pessoais": ["Roupas e Acessórios", "Cosméticos", "Eletrônicos", "Presentes"],
}

def criar_categorias_padrao_para_casal(casal: Casal):
    """
    Cria um conjunto de categorias e subcategorias padrão para um novo casal.
    Esta função é chamada durante o registro de um casal.
    """
    for cat_nome, sub_nomes in CATEGORIAS_PADRAO.items():
        # Cria a categoria principal associada ao casal
        categoria = Categoria.objects.create(
            casal=casal,
            nome=cat_nome,
            ativa=True
        )
        # Cria as subcategorias vinculadas
        for sub_nome in sub_nomes:
            Subcategoria.objects.create(
                categoria=categoria,
                nome=sub_nome,
                ativa=True
            )
    return True


def _membros_ativos_ids(casal: Casal) -> list[int]:
    return list(
        MembroCasal.objects.filter(casal=casal, ativo=True).values_list("usuario_id", flat=True)
    )


def _ratear_valor(valor_total: Decimal, regra: str, casal: Casal, despesa: DespesaModelo):
    """
    Retorna lista de tuplas (user_id, percentual, valor).
    - IGUAL: divide igualmente entre membros ativos.
    - PERCENTUAL: usa RegraRateioPadrao.percentual (soma deve ~100).
    - VALOR_FIXO: usa RegraRateioPadrao.valor_fixo (soma deve ~valor_total).
    Para escopo PESSOAL, retorna 100% dono_pessoal.
    """
    if despesa.escopo == EscopoDespesa.PESSOAL:
        return [(despesa.dono_pessoal_id, Decimal("100.00"), valor_total)]

    membros = _membros_ativos_ids(casal)
    if not membros:
        raise ValidationError("Casal sem membros ativos para rateio.")

    if regra == RegraRateio.IGUAL:
        parte = (valor_total / Decimal(len(membros))).quantize(Decimal("0.01"))
        valores = []
        acumulado = Decimal("0.00")
        for i, uid in enumerate(membros, start=1):
            if i < len(membros):
                valores.append((uid, None, parte))
                acumulado += parte
            else:
                valores.append((uid, None, valor_total - acumulado))
        return valores

    if regra == RegraRateio.PERCENTUAL:
        linhas = list(RegraRateioPadrao.objects.filter(despesa_modelo=despesa))
        if not linhas:
            raise ValidationError("Defina rateio percentual padrão para a despesa.")
        soma = sum((l.percentual or 0) for l in linhas)
        if abs(float(soma) - 100.0) > 0.01:
            raise ValidationError("Soma dos percentuais do rateio padrão deve ser 100%.")
        out = []
        acumulado = Decimal("0.00")
        for i, l in enumerate(linhas, start=1):
            if i < len(linhas):
                v = (valor_total * (l.percentual / Decimal("100"))).quantize(Decimal("0.01"))
                out.append((l.membro_id, l.percentual, v))
                acumulado += v
            else:
                out.append((l.membro_id, l.percentual, valor_total - acumulado))
        return out

    if regra == RegraRateio.VALOR_FIXO:
        linhas = list(RegraRateioPadrao.objects.filter(despesa_modelo=despesa))
        if not linhas:
            raise ValidationError("Defina rateio por valor fixo padrão para a despesa.")
        soma = sum((l.valor_fixo or 0) for l in linhas)
        if abs(float(soma - valor_total)) > 0.01:
            raise ValidationError("Soma dos valores fixos deve ser igual ao valor_total.")
        return [(l.membro_id, None, l.valor_fixo) for l in linhas]

    raise ValidationError("Regra de rateio inválida.")


@transaction.atomic
def gerar_lancamentos_competencia(casal: Casal, competencia: date, criado_por: User) -> list[Lancamento]:
    if competencia.day != 1:
        competencia = competencia.replace(day=1)

    criados = []
    despesas = (
        DespesaModelo.objects
        .filter(casal=casal, ativo=True)
        .select_related("categoria")
    )

    for dm in despesas:
        if Lancamento.objects.filter(casal=casal, despesa_modelo=dm, competencia=competencia).exists():
            continue

        venc = competencia.replace(day=dm.dia_vencimento)
        valor = Decimal(dm.valor_previsto)

        lanc = Lancamento.objects.create(
            casal=casal,
            despesa_modelo=dm,
            categoria=dm.categoria,
            escopo=dm.escopo,
            dono_pessoal=dm.dono_pessoal if dm.escopo == dm.EscopoDespesa.PESSOAL else None,
            descricao=dm.nome,
            competencia=competencia,
            data_vencimento=venc,
            valor_total=valor,
            status=StatusLancamento.PENDENTE,
            pagador=criado_por,
            criado_por=criado_por,
        )

        for uid, perc, v in _ratear_valor(valor, dm.regra_rateio, casal, dm):
            RateioLancamento.objects.create(
                lancamento=lanc, membro_id=uid, percentual=perc, valor=v
            )
        criados.append(lanc)
    return criados


@transaction.atomic
def quitar_lancamento(lancamento: Lancamento, data_pagamento=None, pagador: User | None = None) -> Lancamento:
    if lancamento.status == StatusLancamento.PAGO:
        return lancamento
    lancamento.status = StatusLancamento.PAGO
    if data_pagamento:
        lancamento.data_pagamento = data_pagamento
    else:
        from django.utils import timezone
        lancamento.data_pagamento = timezone.localdate()
    if pagador:
        lancamento.pagador = pagador
    lancamento.save(update_fields=["status", "data_pagamento", "pagador", "atualizado_em"])
    return lancamento


# --- NOVA FUNÇÃO ADICIONADA ---
@transaction.atomic
def criar_rateios_para_lancamento(lancamento: Lancamento):
    """
    Cria os registros de RateioLancamento para um Lancamento.
    - PESSOAL: 100% para o dono_pessoal.
    - COMPARTILHADA: Divide igualmente entre os membros ativos do casal.
    """
    lancamento.rateios.all().delete()  # Garante que não haja rateios duplicados em caso de atualização

    casal = lancamento.casal
    valor_total = lancamento.valor_total

    if lancamento.escopo == EscopoDespesa.PESSOAL:
        if not lancamento.dono_pessoal:
            raise ValidationError("Lançamento pessoal precisa de um dono.")
        RateioLancamento.objects.create(
            lancamento=lancamento,
            membro=lancamento.dono_pessoal,
            valor=valor_total
        )
        return

    if lancamento.escopo == EscopoDespesa.COMPARTILHADA:
        membros_ids = _membros_ativos_ids(casal)
        if not membros_ids:
            raise ValidationError("Casal sem membros ativos para rateio.")
        
        num_membros = len(membros_ids)
        valor_base = (valor_total / num_membros).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
        
        valores_rateio = [valor_base] * num_membros
        soma_arredondada = sum(valores_rateio)
        diferenca = valor_total - soma_arredondada
        
        if diferenca > 0:
            valores_rateio[-1] += diferenca

        for i, membro_id in enumerate(membros_ids):
            RateioLancamento.objects.create(
                lancamento=lancamento,
                membro_id=membro_id,
                valor=valores_rateio[i]
            )

# --- FUNÇÃO ATUALIZADA ---
@transaction.atomic
def gerar_lancamentos_da_compra(compra: "CompraCartao", criado_por):
    """
    Cria N Lancamentos (parcelas) a partir de CompraCartao e os rateios para cada um.
    """
    valor_total_compra = compra.valor_total
    total_parcelas = compra.parcelas_total
    
    valor_parcela_padrao = (valor_total_compra / total_parcelas).quantize(
        Decimal("0.01"), rounding=ROUND_DOWN
    )
    valores_parcelas = [valor_parcela_padrao] * total_parcelas
    diferenca = valor_total_compra - sum(valores_parcelas)
    
    if diferenca > 0:
        valores_parcelas[-1] += diferenca

    competencia = compra.primeira_competencia
    venc = compra.primeiro_vencimento

    for i in range(total_parcelas):
        lanc = Lancamento.objects.create(
            casal=compra.casal,
            despesa_modelo=None,
            subcategoria=compra.subcategoria,
            escopo=compra.escopo,
            dono_pessoal=compra.dono_pessoal,
            descricao=f"{compra.descricao or 'Compra no cartão'} ({i + 1}/{total_parcelas})",
            competencia=competencia,
            data_vencimento=venc,
            valor_total=valores_parcelas[i],
            status=StatusLancamento.PENDENTE,
            data_pagamento=None,
            pagador=compra.pagador,
            criado_por=criado_por,
            compra_cartao=compra,
            parcela_numero=i + 1,
            parcelas_total=total_parcelas,
        )
        # Chama a nova função para criar os rateios da parcela
        criar_rateios_para_lancamento(lanc)

        competencia = (competencia + relativedelta(months=+1)).replace(day=1)
        venc = venc + relativedelta(months=+1)

