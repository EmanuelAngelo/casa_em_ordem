from datetime import date
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from .models import (
    Casal, MembroCasal, DespesaModelo, Lancamento, RateioLancamento,
    EscopoDespesa, RegraRateio, StatusLancamento, RegraRateioPadrao
)

User = get_user_model()


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
        # distribui arredondamento no último
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
    """
    Gera lançamentos da competência (1º dia do mês) para todas as DespesaModelo ativas do casal.
    Não duplica se já existir lançamento idêntico (despesa + competência).
    """
    if competencia.day != 1:
        competencia = competencia.replace(day=1)

    criados = []
    despesas = (
        DespesaModelo.objects
        .filter(casal=casal, ativo=True)
        .select_related("categoria")
    )

    for dm in despesas:
        # verifica duplicidade
        ja_existe = Lancamento.objects.filter(
            casal=casal, despesa_modelo=dm, competencia=competencia
        ).exists()
        if ja_existe:
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
            pagador=criado_por,      # default: quem gerou (pode editar depois)
            criado_por=criado_por,
        )

        # cria rateios
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
