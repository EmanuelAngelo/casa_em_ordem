from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models import Sum, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Casal,
    MembroCasal,
    Categoria,
    Subcategoria,
    DespesaModelo,
    RegraRateioPadrao,
    Lancamento,
    CartaoCredito,
    CompraCartao,
)
from .permissions import (
    IsAutenticadoNoSeuCasal,
    SomenteDoMeuCasal,
    CasalScopedQuerysetMixin,
)
from .serializers import (
    # auth / user
    RegisterSerializer,
    ChangePasswordSerializer,
    UsuarioSlimSerializer,
    # grupo/morador
    CasalSerializer,
    MembroCasalSerializer,
    # cadastros
    CategoriaSerializer,
    SubcategoriaSerializer,
    DespesaModeloSerializer,
    RegraRateioPadraoSerializer,
    # financeiro
    LancamentoSerializer,
    CartaoCreditoSerializer,
    CompraCartaoSerializer,
    ResumoLancamentoSerializer,
)
from .services import criar_categorias_padrao_para_casal
from .utils import get_casal_ativo_do_usuario

User = get_user_model()

# ---------------------------
# Auth / Usuário
# ---------------------------

class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        payload = ser.save()
        return Response(payload, status=status.HTTP_201_CREATED)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["nova_senha"])
        user.save()
        return Response({"detail": "Senha alterada com sucesso."}, status=status.HTTP_200_OK)

class CurrentUserView(APIView):
    """
    GET  /api/users/me/
    POST /api/users/me/ { "grupo_id": <id> } -> define grupo atual se for membro
    """
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        serializer = UsuarioSlimSerializer(request.user)
        return Response(serializer.data)
    def post(self, request, *args, **kwargs):
        from .models import PreferenciasUsuario
        grupo_id = request.data.get("grupo_id")
        if not grupo_id:
            return Response({"detail": "Informe grupo_id."}, status=400)
        try:
            grupo = Casal.objects.get(id=grupo_id)
        except Casal.DoesNotExist:
            return Response({"detail": "Grupo não encontrado."}, status=404)
        if not MembroCasal.objects.filter(casal=grupo, usuario=request.user, ativo=True).exists():
            return Response({"detail": "Você não pertence a este grupo."}, status=403)
        prefs, _ = PreferenciasUsuario.objects.get_or_create(usuario=request.user)
        prefs.grupo_atual = grupo
        prefs.save(update_fields=["grupo_atual"])
        return Response({"detail": "Grupo atual definido com sucesso.", "grupo_id": grupo.id})

# ---------------------------
# Extras do Grupo (convite)
# ---------------------------

class CasalExtrasViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="convidar")
    def convidar(self, request):
        username_or_email = request.data.get("username_or_email", "").strip()
        if not username_or_email:
            return Response({"detail": "Informe username_or_email."}, status=400)

        casal = get_casal_ativo_do_usuario(request.user)
        if not casal:
            return Response({"detail": "Defina/crie um grupo atual para convidar pessoas."}, status=400)

        try:
            user = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
        except User.DoesNotExist:
            return Response({"detail": "Usuário não encontrado."}, status=404)

        if MembroCasal.objects.filter(casal=casal, usuario=user).exists():
            return Response({"detail": "Usuário já está neste grupo."}, status=409)

        MembroCasal.objects.create(
            casal=casal,
            usuario=user,
            apelido=user.first_name or user.username,
            ativo=True,
        )
        return Response({"detail": "Usuário adicionado ao grupo."}, status=201)

# ---------------------------
# Grupo (Casal) e Moradores
# ---------------------------

class CasalViewSet(viewsets.ModelViewSet):
    queryset = Casal.objects.all()
    serializer_class = CasalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        casal = get_casal_ativo_do_usuario(self.request.user)
        return self.queryset.filter(id=casal.id) if casal else self.queryset.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        casal = serializer.save()
        # vincula o criador
        MembroCasal.objects.create(
            casal=casal,
            usuario=request.user,
            apelido=request.user.first_name or request.user.username,
            ativo=True,
        )
        # popula categorias padrão
        criar_categorias_padrao_para_casal(casal)
        # define como grupo atual nas preferências
        from .models import PreferenciasUsuario
        prefs, _ = PreferenciasUsuario.objects.get_or_create(usuario=request.user)
        prefs.grupo_atual = casal
        prefs.save(update_fields=["grupo_atual"])
        return Response(self.get_serializer(casal).data, status=201)

    @action(detail=False, methods=["get"], url_path="meu")
    def meu(self, request):
        casal = get_casal_ativo_do_usuario(request.user)
        if not casal:
            # 200 com null: modo solo não quebra frontend
            return Response(None, status=200)
        data = self.get_serializer(casal).data
        return Response(data)

class MembroCasalViewSet(CasalScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = MembroCasal.objects.select_related("casal", "usuario").all()
    serializer_class = MembroCasalSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["ativo", "usuario"]

    def get_queryset(self):
        return self.filter_queryset_por_casal(super().get_queryset())

    def create(self, request, *args, **kwargs):
        casal = self.get_casal_usuario()
        if not casal:
            return Response({"detail": "Crie/seleciona um grupo para adicionar moradores."}, status=400)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(casal=self.get_casal_usuario())

# ---------------------------
# Cadastros
# ---------------------------

class CategoriaViewSet(CasalScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]

    def get_queryset(self):
        return self.filter_queryset_por_casal(super().get_queryset())

    def create(self, request, *args, **kwargs):
        if not self.get_casal_usuario():
            return Response({"detail": "Crie/seleciona um grupo para cadastrar categorias."}, status=400)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(casal=self.get_casal_usuario())

class SubcategoriaViewSet(viewsets.ModelViewSet):
    """
    Não tem 'casal' direto; filtra por categoria__casal.
    """
    queryset = Subcategoria.objects.select_related("categoria", "categoria__casal").all()
    serializer_class = SubcategoriaSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["categoria", "ativa"]

    def get_queryset(self):
        casal = get_casal_ativo_do_usuario(self.request.user)
        if not casal:
            return self.queryset.none()
        return self.queryset.filter(categoria__casal=casal)

    def create(self, request, *args, **kwargs):
        casal = get_casal_ativo_do_usuario(request.user)
        if not casal:
            return Response({"detail": "Crie/seleciona um grupo para cadastrar subcategorias."}, status=400)
        return super().create(request, *args, **kwargs)

class DespesaModeloViewSet(viewsets.ModelViewSet):
    """
    Também filtra por categoria__casal.
    """
    queryset = DespesaModelo.objects.select_related("categoria", "categoria__casal").all()
    serializer_class = DespesaModeloSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["ativo", "escopo", "categoria"]

    def get_queryset(self):
        casal = get_casal_ativo_do_usuario(self.request.user)
        if not casal:
            return self.queryset.none()
        return self.queryset.filter(categoria__casal=casal)

    def create(self, request, *args, **kwargs):
        casal = get_casal_ativo_do_usuario(request.user)
        if not casal:
            return Response({"detail": "Crie/seleciona um grupo para cadastrar despesas modelo."}, status=400)
        return super().create(request, *args, **kwargs)

class RegraRateioPadraoViewSet(viewsets.ModelViewSet):
    queryset = RegraRateioPadrao.objects.select_related(
        "despesa_modelo", "despesa_modelo__categoria", "despesa_modelo__categoria__casal"
    ).all()
    serializer_class = RegraRateioPadraoSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]

    def get_queryset(self):
        casal = get_casal_ativo_do_usuario(self.request.user)
        if not casal:
            return self.queryset.none()
        return self.queryset.filter(despesa_modelo__categoria__casal=casal)

# ---------------------------
# Financeiro
# ---------------------------

class LancamentoViewSet(CasalScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Lancamento.objects.select_related(
        "subcategoria",
        "subcategoria__categoria",
        "compra_cartao",
    ).all()
    serializer_class = LancamentoSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ["competencia", "data_vencimento", "id"]
    filterset_fields = ["status", "escopo", "subcategoria", "pagador"]

    def get_queryset(self):
        return self.filter_queryset_por_casal(super().get_queryset())

    def create(self, request, *args, **kwargs):
        casal = self.get_casal_usuario()
        if not casal:
            return Response({"detail": "Crie/seleciona um grupo para lançar despesas/receitas."}, status=400)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(casal=self.get_casal_usuario(), criado_por=self.request.user)

    @action(detail=True, methods=["post"], url_path="quitar")
    def quitar(self, request, pk=None):
        lancamento = self.get_object()
        if lancamento.status != "PAGO":
            lancamento.status = "PAGO"
            lancamento.save(update_fields=["status"])
        return Response({"detail": "Quitado com sucesso."})

class CartaoCreditoViewSet(CasalScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = CartaoCredito.objects.all()
    serializer_class = CartaoCreditoSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]

    def get_queryset(self):
        return self.filter_queryset_por_casal(super().get_queryset())

    def create(self, request, *args, **kwargs):
        if not self.get_casal_usuario():
            return Response({"detail": "Crie/seleciona um grupo para cadastrar cartões."}, status=400)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(casal=self.get_casal_usuario())

class CompraCartaoViewSet(CasalScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = CompraCartao.objects.select_related("cartao", "subcategoria", "subcategoria__categoria").all()
    serializer_class = CompraCartaoSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]

    def get_queryset(self):
        return self.filter_queryset_por_casal(super().get_queryset())

    def create(self, request, *args, **kwargs):
        if not self.get_casal_usuario():
            return Response({"detail": "Crie/seleciona um grupo para lançar compras no cartão."}, status=400)
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(casal=self.get_casal_usuario())

# ---------------------------
# Resumo / Relatório
# ---------------------------

class ResumoLancamentosView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        casal = get_casal_ativo_do_usuario(request.user)
        if not casal:
            return Response([], status=200)
        qs = (
            Lancamento.objects.filter(casal=casal)
            .values("id", "descricao", "valor_total", "status", "competencia", "data_vencimento")
            .order_by("-competencia", "-data_vencimento", "-id")[:200]
        )
        return Response(list(qs), status=200)

class RelatorioFinanceiroView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        casal = get_casal_ativo_do_usuario(request.user)
        if not casal:
            return Response(
                {"salario_declarado": 0, "total_gasto": 0, "gastos_por_categoria": []},
                status=200,
            )
        competencia = request.query_params.get("competencia")
        membro_id = request.query_params.get("membro_id")

        qs = Lancamento.objects.filter(casal=casal)
        if competencia:
            qs = qs.filter(competencia__startswith=competencia)  # "YYYY-MM"
        if membro_id and membro_id != "geral":
            qs = qs.filter(Q(pagador_id=membro_id) | Q(dono_pessoal_id=membro_id))

        total = qs.aggregate(total=Sum("valor_total"))["total"] or 0
        salario = (
            MembroCasal.objects.filter(casal=casal, ativo=True).aggregate(total=Sum("salario_mensal"))["total"] or 0
        )
        por_cat = (
            qs.values("subcategoria__categoria__nome")
            .annotate(valor_total=Sum("valor_total"))
            .order_by("-valor_total")
        )
        data = {
            "salario_declarado": float(salario),
            "total_gasto": float(total),
            "gastos_por_categoria": [
                {
                    "lancamento__subcategoria__categoria__nome": row["subcategoria__categoria__nome"],
                    "valor_total": float(row["valor_total"]),
                }
                for row in por_cat
            ],
        }
        return Response(data, status=200)
