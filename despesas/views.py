from django.shortcuts import render
from datetime import date
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Casal, MembroCasal, Categoria, DespesaModelo,
    RegraRateioPadrao, Lancamento, RateioLancamento, StatusLancamento
)
from .serializers import (
    CasalSerializer, MembroCasalSerializer, CategoriaSerializer,
    DespesaModeloSerializer, RegraRateioPadraoSerializer,
    LancamentoSerializer, RateioLancamentoSerializer
)
from .permissions import IsAutenticadoNoSeuCasal, SomenteDoMeuCasal, CasalScopedQuerysetMixin
from .utils import get_casal_ativo_do_usuario, assert_user_pertence_ao_casal
from .services import gerar_lancamentos_competencia, quitar_lancamento


class PublicCategoriaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Categorias são globais (somente leitura).
    """
    queryset = Categoria.objects.all().order_by("nome")
    serializer_class = CategoriaSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["escopo_sugerido"]


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
        MembroCasal.objects.create(casal=casal, usuario=self.request.user, apelido=self.request.user.first_name or "", ativo=True)

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
        return serializer.save(casal=casal)


class DespesaModeloViewSet(CasalScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = DespesaModelo.objects.select_related("casal", "categoria", "dono_pessoal").all()
    serializer_class = DespesaModeloSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["escopo", "categoria", "recorrente", "periodicidade", "ativo"]
    search_fields = ["nome"]


class RegraRateioPadraoViewSet(viewsets.ModelViewSet):
    queryset = RegraRateioPadrao.objects.select_related("despesa_modelo", "membro").all()
    serializer_class = RegraRateioPadraoSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["despesa_modelo"]

    def get_queryset(self):
        # filtra pelo casal do usuário via despesa_modelo.casal
        casal = get_casal_ativo_do_usuario(self.request.user)
        if not casal:
            return self.queryset.none()
        return self.queryset.filter(despesa_modelo__casal=casal)


class LancamentoViewSet(CasalScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = (
        Lancamento.objects
        .select_related("casal", "despesa_modelo", "categoria", "dono_pessoal", "pagador", "criado_por")
        .prefetch_related("rateios")
        .all()
    )
    serializer_class = LancamentoSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["escopo", "categoria", "status", "competencia", "data_vencimento", "pagador"]
    search_fields = ["descricao"]

    @action(detail=False, methods=["post"], url_path="gerar")
    def gerar(self, request):
        """
        Gera lançamentos da competência (YYYY-MM-01) para o casal do usuário.
        body: {"competencia": "2025-09-01"} (opcional; default = mês atual)
        """
        from django.utils import timezone
        casal = get_casal_ativo_do_usuario(request.user)
        if not casal:
            return Response({"detail": "Vincule-se a um casal antes."}, status=400)

        comp_str = request.data.get("competencia")
        if comp_str:
            try:
                ano, mes, dia = map(int, comp_str.split("-"))
                comp = date(ano, mes, dia)
            except Exception:
                return Response({"detail": "competencia deve ser YYYY-MM-DD."}, status=400)
        else:
            hoje = timezone.localdate()
            comp = hoje.replace(day=1)

        criados = gerar_lancamentos_competencia(casal, comp, request.user)
        data = self.get_serializer(criados, many=True).data
        return Response({"criados": len(criados), "lancamentos": data}, status=201)

    @action(detail=True, methods=["post"], url_path="quitar")
    def quitar(self, request, pk=None):
        """
        Quita um lançamento (status=PAGO). body opcional: {"data_pagamento": "2025-09-04", "pagador_id": <id>}
        """
        lanc = self.get_object()
        dp = request.data.get("data_pagamento")
        pagador_id = request.data.get("pagador_id")
        pagador = None
        if pagador_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            pagador = User.objects.filter(id=pagador_id).first()
        if dp:
            try:
                ano, mes, dia = map(int, dp.split("-"))
                from datetime import date
                dp_date = date(ano, mes, dia)
            except Exception:
                return Response({"detail": "data_pagamento inválida."}, status=400)
        else:
            dp_date = None

        lanc = quitar_lancamento(lanc, dp_date, pagador)
        return Response(self.get_serializer(lanc).data, status=200)


class RateioLancamentoViewSet(CasalScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = RateioLancamento.objects.select_related("lancamento", "membro").all()
    serializer_class = RateioLancamentoSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["lancamento", "membro"]

    def get_casal_filter_kwargs(self):
        # filtra via lancamento.casal
        return {"lancamento__casal": self.get_casal_usuario()}
