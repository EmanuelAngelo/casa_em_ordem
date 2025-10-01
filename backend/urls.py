from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from despesas.views import (
    CartaoCreditoViewSet, CategoriaViewSet, CompraCartaoViewSet, RelatorioFinanceiroView,
    SubcategoriaViewSet, LancamentoViewSet, CasalViewSet, MembroCasalViewSet,
    DespesaModeloViewSet, RegraRateioPadraoViewSet, RateioLancamentoViewSet,
    RegisterView, CasalExtrasViewSet, ResumoLancamentosView, ChangePasswordView, CurrentUserView
)

router = DefaultRouter()

# Núcleo
router.register(r"categorias", CategoriaViewSet, basename="categoria")
router.register(r"subcategorias", SubcategoriaViewSet, basename="subcategoria")
router.register(r"lancamentos", LancamentoViewSet, basename="lancamento")

# Padrão NOVO (apenas estes):
router.register(r"grupos", CasalViewSet, basename="grupo")
router.register(r"moradores", MembroCasalViewSet, basename="morador")

# Demais recursos
router.register(r"despesas-modelo", DespesaModeloViewSet, basename="despesa-modelo")
router.register(r"rateios-padrao", RegraRateioPadraoViewSet, basename="rateio-padrao")
router.register(r"rateios", RateioLancamentoViewSet, basename="rateio-lancamento")
router.register(r"grupos-extras", CasalExtrasViewSet, basename="grupo-extras")
router.register(r"cartoes", CartaoCreditoViewSet, basename="cartao-credito")
router.register(r"compras-cartao", CompraCartaoViewSet, basename="compra-cartao")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),

    path("api/lancamentos-resumo/", ResumoLancamentosView.as_view(), name="lancamentos-resumo"),
    path("api/relatorio-financeiro/", RelatorioFinanceiroView.as_view(), name="relatorio-financeiro"),

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
