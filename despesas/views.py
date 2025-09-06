from datetime import date

from django.contrib.auth import get_user_model
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets, mixins, filters
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Casal,
    Categoria,
    MembroCasal,
    Subcategoria,
    Lancamento,
    DespesaModelo,
    RegraRateioPadrao,
    RateioLancamento,
)
from .permissions import (
    IsAutenticadoNoSeuCasal,
    SomenteDoMeuCasal,
    CasalScopedQuerysetMixin,
)
from .serializers import (
    RegisterSerializer,
    CategoriaSerializer,
    SubcategoriaSerializer,
    LancamentoSerializer,
    DespesaModeloSerializer,
    RegraRateioPadraoSerializer,
    RateioLancamentoSerializer,
    MembroCasalSerializer,
    CasalSerializer,
)
from .services import gerar_lancamentos_competencia, quitar_lancamento
from .utils import get_casal_ativo_do_usuario, assert_user_pertence_ao_casal

User = get_user_model()


# ----------------------------
# Registro (público)
# ----------------------------
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        payload = ser.save()
        return Response(payload, status=status.HTTP_201_CREATED)


# ----------------------------
# Extras do casal (convite)
# ----------------------------
class CasalExtrasViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="convidar")
    def convidar(self, request):
        """
        Body: { "username_or_email": "alguem" }
        Adiciona a pessoa ao casal do usuário (se tiver vaga e se existir).
        """
        username_or_email = request.data.get("username_or_email", "").strip()
        if not username_or_email:
            return Response({"detail": "Informe username_or_email."}, status=400)

        casal = get_casal_ativo_do_usuario(request.user)
        if not casal:
            return Response({"detail": "Usuário não possui casal ativo."}, status=400)

        # Regra: no máximo 2 membros
        if casal.membros.filter(ativo=True).count() >= 2:
            return Response({"detail": "Este casal já possui 2 membros ativos."}, status=409)

        try:
            user = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
        except User.DoesNotExist:
            return Response({"detail": "Usuário não encontrado."}, status=404)

        # Verifica se o user já tem vínculo ativo
        if MembroCasal.objects.filter(usuario=user, ativo=True).exists():
            return Response({"detail": "Este usuário já está vinculado a um casal ativo."}, status=409)

        MembroCasal.objects.create(
            casal=casal,
            usuario=user,
            apelido=user.first_name or user.username,
            ativo=True,
        )
        return Response({"detail": "Convite concluído. Usuário adicionado ao casal."}, status=201)


# ----------------------------
# Casal / Membros
# ----------------------------
class CasalViewSet(viewsets.ModelViewSet):
    """
    Criar e gerenciar seu casal.
    - POST cria o casal e já vincula o usuário como membro ativo.
    - GET retorna apenas o casal ao qual o usuário pertence.
    """
    queryset = Casal.objects.all()
    serializer_class = CasalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        casal = get_casal_ativo_do_usuario(self.request.user)
        return self.queryset.filter(id=casal.id) if casal else self.queryset.none()

    def perform_create(self, serializer):
        casal = serializer.save()
        MembroCasal.objects.create(
            casal=casal,
            usuario=self.request.user,
            apelido=self.request.user.first_name or "",
            ativo=True,
        )

    @action(detail=False, methods=["get"], url_path="meu")
    def meu(self, request):
        casal = get_casal_ativo_do_usuario(request.user)
        if not casal:
            return Response({"detail": "Você ainda não está vinculado a um casal."}, status=404)
        data = self.get_serializer(casal).data
        return Response(data)


class MembroCasalViewSet(CasalScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = MembroCasal.objects.select_related("casal", "usuario").all()
    serializer_class = MembroCasalSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["ativo", "usuario"]

    def perform_create(self, serializer):
        casal = self.get_casal_usuario()
        serializer.save(casal=casal)


# ----------------------------
# Categorias / Subcategorias
# ----------------------------
class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all().order_by("nome")
    serializer_class = CategoriaSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["nome"]


class SubcategoriaViewSet(viewsets.ModelViewSet):
    queryset = Subcategoria.objects.select_related("categoria").all().order_by("categoria__nome", "nome")
    serializer_class = SubcategoriaSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["nome", "categoria__nome"]
    filterset_fields = ["categoria"]

    def get_queryset(self):
        qs = super().get_queryset()
        categoria_id = self.request.query_params.get("categoria")
        if categoria_id:
            qs = qs.filter(categoria_id=categoria_id)
        return qs


# ----------------------------
# Despesas Modelo / Rateios padrão
# ----------------------------
class DespesaModeloViewSet(CasalScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = DespesaModelo.objects.select_related("casal", "categoria", "dono_pessoal").all()
    serializer_class = DespesaModeloSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["escopo", "categoria", "recorrente", "periodicidade", "ativo"]
    search_fields = ["nome"]

    def get_queryset(self):
        casal = self.get_casal_usuario()
        return super().get_queryset().filter(casal=casal)

    def perform_create(self, serializer):
        casal = self.get_casal_usuario()
        serializer.save(casal=casal)


class RegraRateioPadraoViewSet(CasalScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = RegraRateioPadrao.objects.select_related("despesa_modelo", "membro").all()
    serializer_class = RegraRateioPadraoSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["despesa_modelo"]

    def get_queryset(self):
        casal = self.get_casal_usuario()
        return super().get_queryset().filter(despesa_modelo__casal=casal)


# ----------------------------
# Lançamentos / Rateios
# ----------------------------
class LancamentoViewSet(CasalScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = (
        Lancamento.objects
        .select_related("subcategoria", "subcategoria__categoria", "pagador", "dono_pessoal", "criado_por")
        .all()
    )
    serializer_class = LancamentoSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["descricao", "subcategoria__nome", "subcategoria__categoria__nome"]
    filterset_fields = ["status", "escopo", "subcategoria", "subcategoria__categoria", "competencia"]

    def get_queryset(self):
        casal = self.get_casal_usuario()
        return super().get_queryset().filter(casal=casal)

    def perform_create(self, serializer):
        casal = self.get_casal_usuario()
        serializer.save(casal=casal, criado_por=self.request.user)

    def perform_update(self, serializer):
        # casal não está no payload (read_only), então não muda
        serializer.save()

    # POST /api/lancamentos/{id}/quitar/
    @action(detail=True, methods=["post"], url_path="quitar")
    def quitar(self, request, pk=None):
        lanc = self.get_object()
        try:
            quitar_lancamento(lanc, request.user)
            return Response({"detail": "Lançamento quitado com sucesso."})
        except Exception as e:
            return Response({"detail": str(e)}, status=400)

    # POST /api/lancamentos/gerar/?competencia=YYYY-MM-01
    @action(detail=False, methods=["post"], url_path="gerar")
    def gerar(self, request):
        competencia = request.query_params.get("competencia")
        if not competencia:
            return Response({"detail": "Informe ?competencia=YYYY-MM-01"}, status=400)
        casal = self.get_casal_usuario()
        try:
            total = gerar_lancamentos_competencia(casal, competencia)
            return Response({"detail": f"{total} lançamentos gerados para {competencia}."})
        except Exception as e:
            return Response({"detail": str(e)}, status=400)


class RateioLancamentoViewSet(CasalScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = RateioLancamento.objects.select_related("lancamento", "membro").all()
    serializer_class = RateioLancamentoSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["lancamento", "membro"]

    def get_casal_filter_kwargs(self):
        # filtra via lancamento.casal
        return {"lancamento__casal": self.get_casal_usuario()}
