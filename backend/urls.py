# backend/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from despesas.views import (
    # Auth / User
    RegisterView, ChangePasswordView, CurrentUserView,
    # Grupo e moradores
    CasalViewSet, MembroCasalViewSet, CasalExtrasViewSet,
    # Cadastros
    CategoriaViewSet, SubcategoriaViewSet, DespesaModeloViewSet, RegraRateioPadraoViewSet,
    # Financeiro
    LancamentoViewSet, CartaoCreditoViewSet, CompraCartaoViewSet,
    # Relatórios / Resumos
    ResumoLancamentosView, RelatorioFinanceiroView,
)

router = DefaultRouter()

# Núcleo
router.register(r"categorias", CategoriaViewSet, basename="categorias")
router.register(r"subcategorias", SubcategoriaViewSet, basename="subcategororias")
router.register(r"lancamentos", LancamentoViewSet, basename="lancamentos")

# Padrão NOVO (grupo/morador)
router.register(r"grupos", CasalViewSet, basename="grupos")
router.register(r"moradores", MembroCasalViewSet, basename="moradores")
router.register(r"grupos-extras", CasalExtrasViewSet, basename="grupos-extras")

# Demais recursos
router.register(r"despesas-modelo", DespesaModeloViewSet, basename="despesas-modelo")
router.register(r"rateios-padrao", RegraRateioPadraoViewSet, basename="rateios-padrao")
router.register(r"cartoes", CartaoCreditoViewSet, basename="cartoes")
router.register(r"compras-cartao", CompraCartaoViewSet, basename="compras-cartao")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),

    # Endpoints extras (não-ViewSet)
    path("api/lancamentos-resumo/", ResumoLancamentosView.as_view(), name="lancamentos-resumo"),
    path("api/relatorio-financeiro/", RelatorioFinanceiroView.as_view(), name="relatorio-financeiro"),

    # Auth
    path("api/auth/register/", RegisterView.as_view(), name="auth-register"),
    path("api/auth/change-password/", ChangePasswordView.as_view(), name="auth-change-password"),
    path("api/users/me/", CurrentUserView.as_view(), name="users-me"),

    # JWT
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # OpenAPI / Swagger
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
