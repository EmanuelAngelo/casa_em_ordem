from django.shortcuts import render
from datetime import date
from rest_framework import viewsets, status, mixins, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend

from .models import Casal, Categoria, MembroCasal, Subcategoria, Lancamento, DespesaModelo, RegraRateioPadrao, RateioLancamento
from .serializers import (
    CategoriaSerializer, SubcategoriaSerializer, LancamentoSerializer,
    DespesaModeloSerializer, RegraRateioPadraoSerializer, RateioLancamentoSerializer,
    MembroCasalSerializer, CasalSerializer
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
    filterset_fields = []


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

class RateioLancamentoViewSet(CasalScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = RateioLancamento.objects.select_related("lancamento", "membro").all()
    serializer_class = RateioLancamentoSerializer
    permission_classes = [IsAuthenticated, IsAutenticadoNoSeuCasal, SomenteDoMeuCasal]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["lancamento", "membro"]

    def get_casal_filter_kwargs(self):
        return {"lancamento__casal": self.get_casal_usuario()}
    
    
class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all().order_by("nome")
    serializer_class = CategoriaSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["nome"]

class SubcategoriaViewSet(viewsets.ModelViewSet):
    queryset = Subcategoria.objects.select_related("categoria").all().order_by("categoria__nome", "nome")
    serializer_class = SubcategoriaSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["nome", "categoria__nome"]

    def get_queryset(self):
        qs = super().get_queryset()
        categoria_id = self.request.query_params.get("categoria")
        if categoria_id:
            qs = qs.filter(categoria_id=categoria_id)
        return qs

class LancamentoViewSet(viewsets.ModelViewSet):
    queryset = Lancamento.objects.select_related("subcategoria", "subcategoria__categoria").all()
    serializer_class = LancamentoSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["descricao", "subcategoria__nome", "subcategoria__categoria__nome"]

    def get_queryset(self):
        qs = super().get_queryset()
        # filtros já usados no seu front:
        status = self.request.query_params.get("status")
        escopo = self.request.query_params.get("escopo")
        categoria = self.request.query_params.get("categoria")       # id de Categoria (pai)
        subcategoria = self.request.query_params.get("subcategoria") # id de Subcategoria
        competencia = self.request.query_params.get("competencia")   # yyyy-mm-01

        if status:
            qs = qs.filter(status=status)
        if escopo:
            qs = qs.filter(escopo=escopo)
        if categoria:
            qs = qs.filter(subcategoria__categoria_id=categoria)
        if subcategoria:
            qs = qs.filter(subcategoria_id=subcategoria)
        if competencia:
            qs = qs.filter(competencia=competencia)

        return qs
