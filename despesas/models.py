from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.text import slugify

User = get_user_model()

class CarimboTempo(models.Model):
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Casal(CarimboTempo):
    """
    Agrupa até dois usuários que compartilham as despesas.
    """
    nome = models.CharField("Nome do casal (apelido)", max_length=100, blank=True, default="")

    class Meta:
        verbose_name = "Casal"
        verbose_name_plural = "Casais"

    def __str__(self):
        return self.nome or f"Casal #{self.pk}"

    @property
    def total_membros(self) -> int:
        return self.membros.filter(ativo=True).count()


class MembroCasal(CarimboTempo):
    """
    Liga usuários a um Casal. Regra: no máximo 2 membros ativos por casal.
    Também limita 1 casal ativo por usuário (por simplicidade).
    """
    casal = models.ForeignKey(Casal, related_name="membros", on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, related_name="membros_casal", on_delete=models.CASCADE)
    apelido = models.CharField("Apelido no casal", max_length=50, blank=True, default="")
    ativo = models.BooleanField(default=True)
    salario_mensal =models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Valor do saláraio mensal para base de calculo.")

    class Meta:
        verbose_name = "Membro do casal"
        verbose_name_plural = "Membros do casal"
        unique_together = (("casal", "usuario"),)

    def clean(self):
        # No máximo 2 membros ativos por casal
        if self.ativo:
            ativos = MembroCasal.objects.filter(casal=self.casal, ativo=True)
            if self.pk:
                ativos = ativos.exclude(pk=self.pk)
            if ativos.count() >= 2:
                raise ValidationError("Um casal pode ter no máximo 2 membros ativos.")

        # Um usuário deve pertencer a no máximo 1 casal ativo
        if self.ativo:
            qs = MembroCasal.objects.filter(usuario=self.usuario, ativo=True)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("Um usuário só pode ter 1 vínculo ativo com casal.")

    def __str__(self):
        return f"{self.usuario} em {self.casal} ({'ativo' if self.ativo else 'inativo'})"


class EscopoDespesa(models.TextChoices):
    COMPARTILHADA = "COMP", "Compartilhada"
    PESSOAL = "PESS", "Pessoal"


class Periodicidade(models.TextChoices):
    MENSAL = "MENSAL", "Mensal"
    ANUAL = "ANUAL", "Anual"
    UNICA = "UNICA", "Única"


class RegraRateio(models.TextChoices):
    IGUAL = "IGUAL", "Igual para todos"
    PERCENTUAL = "PERCENTUAL", "Por percentual"
    VALOR_FIXO = "VALOR_FIXO", "Por valor fixo"


class Categoria(CarimboTempo):
    # --- MUDANÇAS AQUI ---
    casal = models.ForeignKey(Casal, related_name="categorias", on_delete=models.CASCADE)
    nome = models.CharField(max_length=100) # unique=True foi removido daqui
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    ativa = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]
        # Garante que o nome da categoria seja único APENAS dentro do mesmo casal
        unique_together = [("casal", "nome")]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome


class Subcategoria(CarimboTempo):
    categoria = models.ForeignKey(Categoria, related_name="subcategorias", on_delete=models.CASCADE)
    nome = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, blank=True)
    ativa = models.BooleanField(default=True)

    class Meta:
        unique_together = [("categoria", "nome")]
        ordering = ["categoria__nome", "nome"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.categoria.nome} / {self.nome}"

class DespesaModelo(CarimboTempo):
    """
    Template de despesa (recorrente ou não). Usado para gerar lançamentos.
    Para PESSOAL, `dono_pessoal` é obrigatório.
    Para COMPARTILHADA, pode ter regra de rateio padrão.
    """
    casal = models.ForeignKey(Casal, related_name="despesas_modelo", on_delete=models.CASCADE)
    nome = models.CharField(max_length=120)
    categoria = models.ForeignKey(Categoria, related_name="despesas_modelo", on_delete=models.PROTECT)
    escopo = models.CharField(max_length=4, choices=EscopoDespesa.choices, default=EscopoDespesa.COMPARTILHADA)

    dono_pessoal = models.ForeignKey(
        User, related_name="despesas_pessoais_modelo", on_delete=models.PROTECT,
        null=True, blank=True, help_text="Obrigatório se escopo = Pessoal"
    )

    valor_previsto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    dia_vencimento = models.PositiveSmallIntegerField(default=1)
    recorrente = models.BooleanField(default=True)
    periodicidade = models.CharField(max_length=10, choices=Periodicidade.choices, default=Periodicidade.MENSAL)

    # Apenas para COMPARTILHADA
    regra_rateio = models.CharField(
        max_length=12,
        choices=RegraRateio.choices,
        default=RegraRateio.IGUAL,
        help_text="Como dividir valores quando gerar lançamentos.",
    )

    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Despesa (modelo)"
        verbose_name_plural = "Despesas (modelo)"
        ordering = ["nome"]

    def clean(self):
        if self.escopo == EscopoDespesa.PESSOAL and not self.dono_pessoal:
            raise ValidationError("Despesas pessoais exigem um dono_pessoal.")
        if self.escopo == EscopoDespesa.COMPARTILHADA and self.dono_pessoal:
            raise ValidationError("Despesas compartilhadas não devem ter dono_pessoal.")
        if self.escopo == EscopoDespesa.PESSOAL and self.regra_rateio != RegraRateio.IGUAL:
            # Rateio não se aplica a pessoal — 100% do dono
            self.regra_rateio = RegraRateio.IGUAL

    def __str__(self):
        return f"{self.nome} ({self.get_escopo_display()})"


class RegraRateioPadrao(CarimboTempo):
    """
    Define rateio padrão para DESPESAS COMPARTILHADAS.
    Use percentual OU valor_fixo por membro (conforme DespesaModelo.regra_rateio).
    """
    despesa_modelo = models.ForeignKey(DespesaModelo, related_name="rateios_padrao", on_delete=models.CASCADE)
    membro = models.ForeignKey(User, related_name="rateios_padrao", on_delete=models.PROTECT)
    percentual = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    valor_fixo = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = "Rateio padrão (modelo)"
        verbose_name_plural = "Rateios padrão (modelo)"
        unique_together = (("despesa_modelo", "membro"),)

    def clean(self):
        if self.despesa_modelo.escopo != EscopoDespesa.COMPARTILHADA:
            raise ValidationError("Rateio padrão só se aplica a despesas compartilhadas.")

        if self.despesa_modelo.regra_rateio == RegraRateio.PERCENTUAL:
            if self.percentual is None:
                raise ValidationError("Percentual é obrigatório quando a regra de rateio é PERCENTUAL.")
            if not (0 <= float(self.percentual) <= 100):
                raise ValidationError("Percentual deve estar entre 0 e 100.")
            if self.valor_fixo is not None:
                raise ValidationError("Não use valor_fixo quando a regra é PERCENTUAL.")
        elif self.despesa_modelo.regra_rateio == RegraRateio.VALOR_FIXO:
            if self.valor_fixo is None:
                raise ValidationError("Valor fixo é obrigatório quando a regra de rateio é VALOR_FIXO.")
            if self.percentual is not None:
                raise ValidationError("Não use percentual quando a regra é VALOR_FIXO.")
        else:
            # IGUAL: nenhum campo necessário (calculado por quantidade de membros)
            if self.percentual is not None or self.valor_fixo is not None:
                raise ValidationError("Para rateio IGUAL não informe percentual/valor_fixo.")

    def __str__(self):
        base = f"{self.despesa_modelo} - {self.membro}"
        if self.percentual is not None:
            return f"{base} ({self.percentual}%)"
        if self.valor_fixo is not None:
            return f"{base} (R$ {self.valor_fixo})"
        return f"{base} (igual)"


class StatusLancamento(models.TextChoices):
    PENDENTE = "PENDENTE", "Pendente"
    PAGO = "PAGO", "Pago"
    CANCELADO = "CANCELADO", "Cancelado"


class BandeiraCartao(models.TextChoices):
    VISA = "VISA", "Visa"
    MASTERCARD = "MASTER", "Mastercard"
    ELO = "ELO", "Elo"
    AMEX = "AMEX", "Amex"
    OUTRO = "OUTRO", "Outro"

class CartaoCredito(CarimboTempo):
    casal = models.ForeignKey(Casal, related_name="cartoes", on_delete=models.CASCADE)
    nome = models.CharField(max_length=80)  # ex: "Cartão Maria - Nubank"
    bandeira = models.CharField(max_length=10, choices=BandeiraCartao.choices, default=BandeiraCartao.OUTRO)
    limite = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    dia_fechamento = models.PositiveSmallIntegerField(default=1)  # 1..28
    dia_vencimento = models.PositiveSmallIntegerField(default=10) # 1..28
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Cartão de crédito"
        verbose_name_plural = "Cartões de crédito"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome}"

class CompraCartao(CarimboTempo):
    """
    Agrupa as parcelas (cada parcela é um Lancamento).
    """
    casal = models.ForeignKey(Casal, related_name="compras_cartao", on_delete=models.CASCADE)
    cartao = models.ForeignKey(CartaoCredito, related_name="compras", on_delete=models.PROTECT)
    descricao = models.CharField(max_length=180, blank=True, default="")
    subcategoria = models.ForeignKey(Subcategoria, related_name="compras_cartao", on_delete=models.PROTECT)
    escopo = models.CharField(max_length=4, choices=EscopoDespesa.choices, default=EscopoDespesa.COMPARTILHADA)
    dono_pessoal = models.ForeignKey(User, related_name="compras_cartao_pessoais", on_delete=models.PROTECT, null=True, blank=True)

    valor_total = models.DecimalField(max_digits=12, decimal_places=2)
    parcelas_total = models.PositiveSmallIntegerField(default=1)
    primeira_competencia = models.DateField(help_text="Competência da 1ª parcela (YYYY-MM-01)")
    primeiro_vencimento = models.DateField(help_text="Vencimento da 1ª parcela")

    pagador = models.ForeignKey(User, related_name="compras_cartao_pagador", on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Compra no cartão"
        verbose_name_plural = "Compras no cartão"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.descricao or 'Compra cartão'} ({self.parcelas_total}x)"

class Lancamento(CarimboTempo):
    """
    Gasto lançado (instância mensal/única).
    """
    casal = models.ForeignKey(Casal, related_name="lancamentos", on_delete=models.CASCADE)
    despesa_modelo = models.ForeignKey(DespesaModelo, related_name="lancamentos", on_delete=models.SET_NULL, null=True, blank=True)
    subcategoria = models.ForeignKey(
        Subcategoria, related_name="lancamentos", on_delete=models.PROTECT
    )
    escopo = models.CharField(max_length=4, choices=EscopoDespesa.choices)
    dono_pessoal = models.ForeignKey(
        User, related_name="lancamentos_pessoais", on_delete=models.PROTECT,
        null=True, blank=True, help_text="Obrigatório se escopo = Pessoal"
    )
    descricao = models.CharField(max_length=180, blank=True, default="")
    competencia = models.DateField(help_text="Use o 1º dia do mês como referência (YYYY-MM-01).")
    data_vencimento = models.DateField()
    valor_total = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=StatusLancamento.choices, default=StatusLancamento.PENDENTE)
    data_pagamento = models.DateField(null=True, blank=True)
    pagador = models.ForeignKey(User, related_name="pagamentos", on_delete=models.PROTECT)
    compra_cartao = models.ForeignKey(CompraCartao, related_name="parcelas", on_delete=models.SET_NULL, null=True, blank=True)
    parcela_numero = models.PositiveSmallIntegerField(null=True, blank=True)
    parcelas_total = models.PositiveSmallIntegerField(null=True, blank=True)
    criado_por = models.ForeignKey(User, related_name="lancamentos_criados", on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Lançamento"
        verbose_name_plural = "Lançamentos"
        ordering = ["-competencia", "data_vencimento", "id"]

    def clean(self):
        if self.escopo == EscopoDespesa.PESSOAL and not self.dono_pessoal:
            raise ValidationError("Lançamentos pessoais exigem dono_pessoal.")
        if self.escopo == EscopoDespesa.COMPARTILHADA and self.dono_pessoal:
            raise ValidationError("Lançamentos compartilhados não devem ter dono_pessoal.")

    def __str__(self):
            cat = self.subcategoria.categoria.nome if self.subcategoria else "Sem categoria"
            sub = self.subcategoria.nome if self.subcategoria else "-"
            return f"{self.descricao or sub} - {cat} - {self.competencia:%Y-%m}"


class RateioLancamento(CarimboTempo):
    """
    Valor devido por membro para um Lançamento.
    Para PESSOAL, haverá 1 linha (100% do dono). Para COMPARTILHADA, 1 por membro.
    """
    lancamento = models.ForeignKey(Lancamento, related_name="rateios", on_delete=models.CASCADE)
    membro = models.ForeignKey(User, related_name="rateios", on_delete=models.PROTECT)
    percentual = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    valor = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Rateio (lançamento)"
        verbose_name_plural = "Rateios (lançamento)"
        unique_together = (("lancamento", "membro"),)

    def __str__(self):
        base = f"{self.lancamento} - {self.membro}"
        if self.percentual is not None:
            return f"{base} ({self.percentual}% = R$ {self.valor})"
        return f"{base} (R$ {self.valor})"
