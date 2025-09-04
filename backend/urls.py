from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from despesas.views import (
    PublicCategoriaViewSet, CasalViewSet, MembroCasalViewSet,
    DespesaModeloViewSet, RegraRateioPadraoViewSet,
    LancamentoViewSet, RateioLancamentoViewSet
)

router = DefaultRouter()
router.register(r"categorias", PublicCategoriaViewSet, basename="categoria")
router.register(r"casais", CasalViewSet, basename="casal")
router.register(r"membros", MembroCasalViewSet, basename="membro-casal")
router.register(r"despesas-modelo", DespesaModeloViewSet, basename="despesa-modelo")
router.register(r"rateios-padrao", RegraRateioPadraoViewSet, basename="rateio-padrao")
router.register(r"lancamentos", LancamentoViewSet, basename="lancamento")
router.register(r"rateios", RateioLancamentoViewSet, basename="rateio-lancamento")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),

    # JWT
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # Schema e Docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
