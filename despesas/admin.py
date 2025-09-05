from django.contrib import admin
from .models import (
    Casal, MembroCasal, Categoria, Subcategoria, Lancamento, DespesaModelo, RegraRateioPadrao,
    Lancamento, RateioLancamento
)

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

@admin.register(Lancamento)
class LancamentoAdmin(admin.ModelAdmin):
    list_display = ("descricao", "subcategoria", "valor_total", "competencia", "status")
    search_fields = ("descricao", "subcategoria__nome", "subcategoria__categoria__nome")
    list_filter = ("status", "subcategoria__categoria", "subcategoria")

class RegraRateioPadraoInline(admin.TabularInline):
    model = RegraRateioPadrao
    extra = 0

@admin.register(DespesaModelo)
class DespesaModeloAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "casal", "escopo", "categoria", "valor_previsto", "dia_vencimento", "recorrente", "periodicidade", "ativo")
    list_filter = ("escopo", "recorrente", "periodicidade", "ativo", "casal", "categoria")
    search_fields = ("nome",)
    inlines = [RegraRateioPadraoInline]

class RateioLancamentoInline(admin.TabularInline):
    model = RateioLancamento
    extra = 0

