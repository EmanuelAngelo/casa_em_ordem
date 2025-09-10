from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from despesas.views import (
    CartaoCreditoViewSet, CategoriaViewSet, CompraCartaoViewSet, SubcategoriaViewSet, LancamentoViewSet, CasalViewSet, MembroCasalViewSet,
    DespesaModeloViewSet, RegraRateioPadraoViewSet,
    LancamentoViewSet, RateioLancamentoViewSet, RegisterView, CasalExtrasViewSet, ResumoLancamentosView
)

router = DefaultRouter()
router.register(r"categorias", CategoriaViewSet, basename="categoria")
router.register(r"subcategorias", SubcategoriaViewSet, basename="subcategoria")
router.register(r"lancamentos", LancamentoViewSet, basename="lancamento")
router.register(r"casais", CasalViewSet, basename="casal")
router.register(r"membros", MembroCasalViewSet, basename="membro-casal")
router.register(r"despesas-modelo", DespesaModeloViewSet, basename="despesa-modelo")
router.register(r"rateios-padrao", RegraRateioPadraoViewSet, basename="rateio-padrao")
router.register(r"rateios", RateioLancamentoViewSet, basename="rateio-lancamento")
router.register(r"casais-extras", CasalExtrasViewSet, basename="casal-extras")
router.register(r"cartoes", CartaoCreditoViewSet, basename="cartao-credito")
router.register(r"compras-cartao", CompraCartaoViewSet, basename="compra-cartao")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    
    # --- NOVA ROTA PARA A LISTA RESUMIDA ---
    path("api/lancamentos-resumo/", ResumoLancamentosView.as_view(), name="lancamentos-resumo"),

    path("api/auth/register/", RegisterView.as_view(), name="auth-register"),

    # JWT
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Schema e Docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]

