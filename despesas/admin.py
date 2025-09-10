from django.contrib import admin
from .models import (
    CartaoCredito, Casal, MembroCasal, Categoria, Subcategoria, Lancamento, DespesaModelo, RegraRateioPadrao,
    RateioLancamento, CompraCartao  # Adicionar CompraCartao
)

# ... (CasalAdmin, MembroCasalAdmin, CategoriaAdmin, SubcategoriaAdmin não mudam) ...

@admin.register(Casal)
class CasalAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "criado_em")
    search_fields = ("nome",)

@admin.register(MembroCasal)
class MembroCasalAdmin(admin.ModelAdmin):
    list_display = ("id", "casal", "usuario", "apelido", "ativo", "criado_em")
    list_filter = ("ativo", "casal")

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativa", "criado_em")
    search_fields = ("nome",)
    list_filter = ("ativa",)

@admin.register(Subcategoria)
class SubcategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "categoria", "ativa", "criado_em")
    search_fields = ("nome", "categoria__nome")
    list_filter = ("categoria", "ativa")

# --- MUDANÇAS AQUI ---

class RateioLancamentoInline(admin.TabularInline):
    model = RateioLancamento
    extra = 0

@admin.register(Lancamento)
class LancamentoAdmin(admin.ModelAdmin):
    # Adicionamos 'compra_cartao' para visualização e o tornamos readonly
    list_display = ("descricao", "subcategoria", "valor_total", "competencia", "status", "compra_cartao")
    search_fields = ("descricao", "subcategoria__nome", "subcategoria__categoria__nome")
    list_filter = ("status", "subcategoria__categoria", "subcategoria")
    readonly_fields = ("compra_cartao",) # Impede edição manual, pois é gerenciado pelo sistema

# ... (DespesaModeloAdmin e CartaoCreditoAdmin não mudam) ...
class RegraRateioPadraoInline(admin.TabularInline):
    model = RegraRateioPadrao
    extra = 0

@admin.register(DespesaModelo)
class DespesaModeloAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "casal", "escopo", "categoria", "valor_previsto", "dia_vencimento", "recorrente", "periodicidade", "ativo")
    list_filter = ("escopo", "recorrente", "periodicidade", "ativo", "casal", "categoria")
    search_fields = ("nome",)
    inlines = [RegraRateioPadraoInline]
    
@admin.register(CartaoCredito)
class CartaoCreditoAdmin(admin.ModelAdmin):
    list_display = ("nome", "bandeira", "limite", "dia_fechamento", "dia_vencimento", "ativo")
    search_fields = ("nome",)
    list_filter = ("bandeira", "ativo")


# --- NOVOS REGISTROS E INLINES ---

class LancamentoInline(admin.TabularInline):
    """ Para visualizar as parcelas geradas a partir da compra """
    model = Lancamento
    extra = 0
    readonly_fields = ("casal", "despesa_modelo", "subcategoria", "escopo", "dono_pessoal", "descricao", "competencia", "data_vencimento", "valor_total", "status", "data_pagamento", "pagador", "compra_cartao", "parcela_numero", "parcelas_total", "criado_por")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(CompraCartao)
class CompraCartaoAdmin(admin.ModelAdmin):
    """
    Este é o local correto para criar uma compra parcelada.
    O sistema irá gerar os Lançamentos (parcelas) automaticamente.
    """
    list_display = ("descricao", "cartao", "valor_total", "parcelas_total", "primeira_competencia")
    list_filter = ("cartao", "escopo")
    search_fields = ("descricao",)
    inlines = [LancamentoInline]