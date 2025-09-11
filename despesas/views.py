from datetime import date
from decimal import Decimal
from itertools import chain # Import para combinar listas
from django.db.models import Sum
from operator import attrgetter # Import para ordenar objetos

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
    CartaoCredito,
    Casal,
    Categoria,
    CompraCartao,
    MembroCasal,
    StatusLancamento,
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
    CartaoCreditoSerializer,
    CompraCartaoSerializer,
    RegisterSerializer,
    CategoriaSerializer,
    ResumoLancamentoSerializer,
    SubcategoriaSerializer,
    LancamentoSerializer,
    DespesaModeloSerializer,
    RegraRateioPadraoSerializer,
    RateioLancamentoSerializer,
    MembroCasalSerializer,
    CasalSerializer,
    ChangePasswordSerializer,
)
from .services import criar_rateios_para_lancamento, gerar_lancamentos_competencia, gerar_lancamentos_da_compra, quitar_lancamento
from .utils import get_casal_ativo_do_usuario, assert_user_pertence_ao_casal
from despesas import serializers

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

        if casal.membros.filter(ativo=True).count() >= 2:
            return Response({"detail": "Este casal já possui 2 membros ativos."}, status=409)

        try:
            user = User.objects.get(Q(username=username_or_email) | Q(email=username_or_email))
        except User.DoesNotExist:
            return Response({"detail": "Usuário não encontrado."}, status=404)

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
class CategoriaViewSet(CasalScopedQuerysetMixin, viewsets.ModelViewSet):
    # Adicionamos o CasalScopedQuerysetMixin
    queryset = Categoria.objects.all().order_by("nome")
    serializer_class = CategoriaSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal] # Permissões mais restritas
    filter_backends = [filters.SearchFilter]
    search_fields = ["nome"]
    # O perform_create já é herdado do mixin, associando o casal automaticamente

class SubcategoriaViewSet(CasalScopedQuerysetMixin, viewsets.ModelViewSet):
    # Adicionamos o CasalScopedQuerysetMixin
    queryset = Subcategoria.objects.select_related("categoria").all().order_by("categoria__nome", "nome")
    serializer_class = SubcategoriaSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal] # Permissões mais restritas
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["nome", "categoria__nome"]
    filterset_fields = ["categoria"]

    # O mixin já filtra as subcategorias baseado na categoria, que por sua vez já é do casal
    def get_casal_filter_kwargs(self):
        return {"categoria__casal": self.get_casal_usuario()}


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
    filterset_fields = ["status", "escopo", "subcategoria", "subcategoria__categoria", "competencia", "compra_cartao"]

    def get_queryset(self):
        casal = self.get_casal_usuario()
        return super().get_queryset().filter(casal=casal)

    def perform_create(self, serializer):
        casal = self.get_casal_usuario()
        lancamento = serializer.save(casal=casal, criado_por=self.request.user)
        # Chama o serviço para criar os rateios
        criar_rateios_para_lancamento(lancamento)

    def perform_update(self, serializer):
        lancamento = serializer.save()
        # Também atualiza os rateios ao editar um lançamento
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
        # filtra via lancamento.casal
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
    """
    Retorna uma lista combinada e ordenada de:
    1. Compras de Cartão (agrupadas como um único item)
    2. Lançamentos únicos (que não são parte de uma compra de cartão)
    """
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal]

    def get(self, request, *args, **kwargs):
        casal = get_casal_ativo_do_usuario(request.user)
        if not casal:
            return Response([], status=status.HTTP_200_OK)

        # 1. Pega todas as compras de cartão
        compras = CompraCartao.objects.filter(casal=casal).select_related("subcategoria", "subcategoria__categoria")

        # 2. Pega todos os lançamentos que NÃO estão associados a uma compra
        lancamentos_unicos = Lancamento.objects.filter(
            casal=casal,
            compra_cartao__isnull=True
        ).select_related("subcategoria", "subcategoria__categoria")

        # 3. Combina as duas listas e ordena pela data de competência (ou primeira competência)
        # O 'key' usa o primeiro atributo que encontrar no objeto para ordenar
        combined_list = sorted(
            chain(compras, lancamentos_unicos),
            key=lambda x: x.competencia if isinstance(x, Lancamento) else x.primeira_competencia,
            reverse=True
        )
        
        # 4. Serializa a lista combinada usando o novo serializer
        serializer = ResumoLancamentoSerializer(combined_list, many=True)
        return Response(serializer.data)


class RelatorioFinanceiroView(APIView):
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal]

    def get(self, request, *args, **kwargs):
        casal = get_casal_ativo_do_usuario(request.user)
        if not casal:
            return Response({"detail": "Casal não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        try:
            competencia_str = request.query_params.get("competencia") # Espera "YYYY-MM"
            membro_id_str = request.query_params.get("membro_id") # "geral" ou um ID de usuário

            ano, mes = map(int, competencia_str.split('-'))
        except (ValueError, TypeError):
            return Response(
                {"detail": "Parâmetro 'competencia' (YYYY-MM) é obrigatório e deve ser válido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Filtra os rateios (a fonte da verdade sobre quem pagou o quê)
        rateios_qs = RateioLancamento.objects.filter(
            lancamento__casal=casal,
            lancamento__competencia__year=ano,
            lancamento__competencia__month=mes,
            lancamento__status__in=[StatusLancamento.PAGO, StatusLancamento.PENDENTE] # Considera pagos e pendentes
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
        else: # "geral"
             salario_total = membros_do_casal.aggregate(total=Sum('salario_mensal'))['total'] or Decimal("0.00")


        # Agrega os gastos por categoria
        gastos_por_categoria = rateios_qs.values(
            'lancamento__subcategoria__categoria__nome'
        ).annotate(
            valor_total=Sum('valor')
        ).order_by('-valor_total')

        total_gasto = rateios_qs.aggregate(total=Sum('valor'))['total'] or Decimal("0.00")

        return Response({
            "salario_declarado": salario_total,
            "total_gasto": total_gasto,
            "gastos_por_categoria": list(gastos_por_categoria)
        })
    
# --- NOVA VIEW PARA TROCA DE SENHA ---
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['nova_senha'])
        user.save()

        return Response({"detail": "Senha alterada com sucesso."}, status=status.HTTP_200_OK)


# class ConviteViewSet(CasalScopedQuerysetMixin, viewsets.ModelViewSet):
#     """
#     ViewSet para criar, listar e aceitar convites.
#     """
#     serializer_class = ConviteCreateSerializer
#     permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal]

#     def get_queryset(self):
#         # Mostra apenas os convites pendentes do casal do usuário
#         casal = self.get_casal_usuario()
#         return Convite.objects.filter(casal_origem=casal, status=StatusConvite.PENDENTE)

#     def perform_create(self, serializer):
#         casal = self.get_casal_usuario()
#         remetente = self.request.user
#         email_convidado = serializer.validated_data['email_convidado']

#         # Regras de negócio
#         if casal.membros.filter(ativo=True).count() >= 2:
#             raise serializers.ValidationError("Este casal já possui 2 membros ativos.")
#         if MembroCasal.objects.filter(usuario__email=email_convidado, ativo=True).exists():
#             raise serializers.ValidationError("Este e-mail já pertence a um casal ativo.")

#         # Cria o convite
#         convite = serializer.save(
#             casal_origem=casal,
#             remetente=remetente,
#             email_convidado=email_convidado
#         )

#         # Envia o e-mail
#         url_aceite = f"http://localhost:3000/aceitar-convite?token={convite.token}" # Mude o host se necessário
#         send_mail(
#             subject=f"Você foi convidado para o casal '{casal.nome}'",
#             message=(
#                 f"Olá!\n\n"
#                 f"{remetente.get_full_name() or remetente.username} convidou você para se juntar ao casal '{casal.nome}' no app Gastos a Dois.\n\n"
#                 f"Para aceitar, clique no link abaixo:\n"
#                 f"{url_aceite}\n\n"
#                 f"Se você não esperava este convite, por favor, ignore este e-mail."
#             ),
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             recipient_list=[email_convidado],
#             fail_silently=False,
#         )

#     # Endpoint público para buscar detalhes do convite pelo token
#     @action(detail=False, methods=['get'], permission_classes=[AllowAny], url_path='info/(?P<token>[^/.]+)')
#     def info(self, request, token=None):
#         try:
#             convite = Convite.objects.get(token=token, status=StatusConvite.PENDENTE)
#             return Response(ConvitePublicSerializer(convite).data)
#         except Convite.DoesNotExist:
#             return Response({"detail": "Convite inválido ou expirado."}, status=status.HTTP_404_NOT_FOUND)

#     # Endpoint para o usuário logado aceitar o convite
#     @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='aceitar')
#     def aceitar(self, request):
#         serializer = AceitarConviteSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         token = serializer.validated_data['token']
#         usuario_aceitando = request.user

#         try:
#             convite = Convite.objects.get(token=token, status=StatusConvite.PENDENTE)
#         except Convite.DoesNotExist:
#             raise serializers.ValidationError("Convite inválido ou expirado.")

#         casal_destino = convite.casal_origem

#         # Validações finais
#         if MembroCasal.objects.filter(usuario=usuario_aceitando, ativo=True).exists():
#             raise serializers.ValidationError("Você já faz parte de um casal ativo.")
#         if casal_destino.membros.filter(ativo=True).count() >= 2:
#             raise serializers.ValidationError("O casal de destino já está cheio.")

#         # Tudo certo, adiciona o membro
#         MembroCasal.objects.create(
#             casal=casal_destino,
#             usuario=usuario_aceitando,
#             apelido=usuario_aceitando.first_name or usuario_aceitando.username,
#             ativo=True
#         )
#         convite.status = StatusConvite.ACEITO
#         convite.save()
#         return Response({"detail": "Bem-vindo(a) ao casal!"})