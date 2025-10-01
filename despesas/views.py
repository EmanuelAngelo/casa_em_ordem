from datetime import date
from decimal import Decimal
from itertools import chain
from django.db.models import Sum
from operator import attrgetter

from django.contrib.auth import get_user_model
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets, mixins, filters
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.mail import send_mail
from backend import settings

from .models import (
    CartaoCredito, Casal, Categoria, CompraCartao, MembroCasal, StatusLancamento,
    Subcategoria, Lancamento, DespesaModelo, RegraRateioPadrao, RateioLancamento,
)
from .permissions import IsAutenticadoNoSeuCasal, SomenteDoMeuCasal, CasalScopedQuerysetMixin
from .serializers import (
    CartaoCreditoSerializer, CompraCartaoSerializer, RegisterSerializer, CategoriaSerializer,
    ResumoLancamentoSerializer, SubcategoriaSerializer, LancamentoSerializer, DespesaModeloSerializer,
    RegraRateioPadraoSerializer, RateioLancamentoSerializer, MembroCasalSerializer, CasalSerializer,
    ChangePasswordSerializer, UsuarioSlimSerializer,
)
from .services import criar_rateios_para_lancamento, gerar_lancamentos_competencia, gerar_lancamentos_da_compra, quitar_lancamento
from .utils import get_casal_ativo_do_usuario, assert_user_pertence_ao_casal

User = get_user_model()

class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        payload = ser.save()
        return Response(payload, status=status.HTTP_201_CREATED)

class CasalExtrasViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="convidar")
    def convidar(self, request):
        """
        Body: { "username_or_email": "alguem" }
        Adiciona a pessoa ao grupo do usuário (se existir).
        """
        username_or_email = request.data.get("username_or_email", "").strip()
        if not username_or_email:
            return Response({"detail": "Informe username_or_email."}, status=400)

        casal = get_casal_ativo_do_usuario(request.user)
        if not casal:
            return Response({"detail": "Usuário não possui grupo ativo."}, status=400)

        try:
            user = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
        except User.DoesNotExist:
            return Response({"detail": "Usuário não encontrado."}, status=404)

        if MembroCasal.objects.filter(casal=casal, usuario=user).exists():
            return Response({"detail": "Usuário já está neste grupo."}, status=409)

        # (REMOVIDO) antes havia limitação de 2 membros ativos por grupo.
        MembroCasal.objects.create(
            casal=casal,
            usuario=user,
            apelido=user.first_name or user.username,
            ativo=True,
        )
        return Response({"detail": "Convite concluído. Usuário adicionado ao grupo."}, status=201)

class CasalViewSet(viewsets.ModelViewSet):
    """
    Criar e gerenciar seu grupo doméstico.
    - POST cria o grupo e já vincula o usuário como membro ativo.
    - GET retorna apenas o grupo ao qual o usuário pertence (o ativo).
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
            return Response({"detail": "Você ainda não está vinculado a um grupo."}, status=404)
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

class CategoriaViewSet(CasalScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Categoria.objects.all().order_by("nome")
    serializer_class = CategoriaSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]
    filter_backends = [filters.SearchFilter]
    search_fields = ["nome"]

class SubcategoriaViewSet(CasalScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Subcategoria.objects.select_related("categoria").all().order_by("categoria__nome", "nome")
    serializer_class = SubcategoriaSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["nome", "categoria__nome"]
    filterset_fields = ["categoria"]
    def get_casal_filter_kwargs(self):
        return {"categoria__casal": self.get_casal_usuario()}
    def perform_create(self, serializer):
        serializer.save()

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
    def perform_create(self, serializer):
        serializer.save()

class LancamentoViewSet(CasalScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Lancamento.objects.select_related("subcategoria", "subcategoria__categoria", "pagador", "dono_pessoal", "criado_por").all()
    serializer_class = LancamentoSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["descricao", "subcategoria__nome", "subcategoria__categoria__nome"]
    filterset_fields = ["status", "escopo", "subcategoria", "subcategoria__categoria", "competencia", "compra_cartao"]
    def get_queryset(self):
        casal = self.get_casal_usuario()
        return super().get_queryset().filter(casal=casal)
    def perform_create(self, serializer):
        casal = self.get_casal_usuario()
        lancamento = serializer.save(casal=casal, criado_por=self.request.user)
        criar_rateios_para_lancamento(lancamento)
    def perform_update(self, serializer):
        lancamento = serializer.save()
        criar_rateios_para_lancamento(lancamento)
    @action(detail=True, methods=["post"], url_path="quitar")
    def quitar(self, request, pk=None):
        lanc = self.get_object()
        try:
            quitar_lancamento(lancamento=lanc, pagador=request.user)
            return Response({"detail": "Lançamento quitado com sucesso."})
        except Exception as e:
            return Response({"detail": str(e)}, status=400)
    @action(detail=False, methods=["post"], url_path="gerar")
    def gerar(self, request):
        competencia_str = request.query_params.get("competencia")
        if not competencia_str:
            return Response({"detail": "Informe ?competencia=YYYY-MM-01"}, status=400)
        try:
            competencia = date.fromisoformat(competencia_str)
            casal = self.get_casal_usuario()
            lancamentos_criados = gerar_lancamentos_competencia(casal, competencia, request.user)
            total = len(lancamentos_criados)
            return Response({"detail": f"{total} lançamentos gerados para {competencia_str}."})
        except ValueError:
            return Response({"detail": "Formato de data inválido. Use YYYY-MM-DD."}, status=400)
        except Exception as e:
            return Response({"detail": str(e)}, status=400)

class RateioLancamentoViewSet(CasalScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = RateioLancamento.objects.select_related("lancamento", "membro").all()
    serializer_class = RateioLancamentoSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["lancamento", "membro"]
    def get_casal_filter_kwargs(self):
        return {"lancamento__casal": self.get_casal_usuario()}

class CartaoCreditoViewSet(CasalScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = CartaoCredito.objects.select_related("casal").all()
    serializer_class = CartaoCreditoSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]
    def get_queryset(self):
        return super().get_queryset().filter(casal=self.get_casal_usuario())
    def perform_create(self, serializer):
        serializer.save(casal=self.get_casal_usuario())

class CompraCartaoViewSet(CasalScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = CompraCartao.objects.select_related("casal", "cartao", "subcategoria", "pagador", "dono_pessoal").all()
    serializer_class = CompraCartaoSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["cartao", "subcategoria", "escopo"]
    search_fields = ["descricao"]
    def get_queryset(self):
        return super().get_queryset().filter(casal=self.get_casal_usuario())
    def perform_create(self, serializer):
        compra = serializer.save(casal=self.get_casal_usuario())
        gerar_lancamentos_da_compra(compra, criado_por=self.request.user)

class ResumoLancamentosView(APIView):
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal]
    def get(self, request, *args, **kwargs):
        casal = get_casal_ativo_do_usuario(request.user)
        if not casal:
            return Response([], status=status.HTTP_200_OK)
        compras = CompraCartao.objects.filter(casal=casal).select_related("subcategoria", "subcategoria__categoria")
        lancamentos_unicos = Lancamento.objects.filter(casal=casal, compra_cartao__isnull=True).select_related("subcategoria", "subcategoria__categoria")
        combined_list = sorted(chain(compras, lancamentos_unicos), key=lambda x: x.competencia if isinstance(x, Lancamento) else x.primeira_competencia, reverse=True)
        serializer = ResumoLancamentoSerializer(combined_list, many=True)
        return Response(serializer.data)

class RelatorioFinanceiroView(APIView):
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal]
    def get(self, request, *args, **kwargs):
        casal = get_casal_ativo_do_usuario(request.user)
        if not casal:
            return Response({"detail": "Grupo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        try:
            competencia_str = request.query_params.get("competencia")
            membro_id_str = request.query_params.get("membro_id")
            ano, mes = map(int, competencia_str.split('-'))
        except (ValueError, TypeError):
            return Response({"detail": "Parâmetro 'competencia' (YYYY-MM) é obrigatório e deve ser válido."}, status=status.HTTP_400_BAD_REQUEST)
        rateios_qs = RateioLancamento.objects.filter(
            lancamento__casal=casal,
            lancamento__competencia__year=ano,
            lancamento__competencia__month=mes,
            lancamento__status__in=[StatusLancamento.PAGO, StatusLancamento.PENDENTE]
        )
        membros_do_casal = MembroCasal.objects.filter(casal=casal, ativo=True)
        salario_total = Decimal("0.00")
        if membro_id_str and membro_id_str != "geral":
            try:
                membro_id = int(membro_id_str)
                rateios_qs = rateios_qs.filter(membro_id=membro_id)
                salario_total = membros_do_casal.get(usuario_id=membro_id).salario_mensal
            except (ValueError, MembroCasal.DoesNotExist):
                return Response({"detail": "Membro não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        else:
            salario_total = membros_do_casal.aggregate(total=Sum('salario_mensal'))['total'] or Decimal("0.00")
        gastos_por_categoria = rateios_qs.values('lancamento__subcategoria__categoria__nome').annotate(valor_total=Sum('valor')).order_by('-valor_total')
        total_gasto = rateios_qs.aggregate(total=Sum('valor'))['total'] or Decimal("0.00")
        return Response({"salario_declarado": salario_total, "total_gasto": total_gasto, "gastos_por_categoria": list(gastos_por_categoria)})

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['nova_senha'])
        user.save()
        return Response({"detail": "Senha alterada com sucesso."}, status=status.HTTP_200_OK)

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        serializer = UsuarioSlimSerializer(request.user)
        return Response(serializer.data)
