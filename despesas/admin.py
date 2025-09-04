from django.contrib import admin
from .models import (
    Casal, MembroCasal, Categoria, DespesaModelo, RegraRateioPadrao,
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
    list_display = ("id", "nome", "escopo_sugerido", "icone")
    list_filter = ("escopo_sugerido",)
    search_fields = ("nome",)

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

@admin.register(Lancamento)
class LancamentoAdmin(admin.ModelAdmin):
    list_display = ("id", "casal", "escopo", "categoria", "descricao", "competencia", "data_vencimento", "valor_total", "status", "pagador")
    list_filter = ("escopo", "status", "casal", "categoria", "competencia")
    search_fields = ("descricao",)
    inlines = [RateioLancamentoInline]
