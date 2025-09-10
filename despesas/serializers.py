from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Casal,
    MembroCasal,
    Categoria,
    Subcategoria,
    Lancamento,
    DespesaModelo,
    RegraRateioPadrao,
    RateioLancamento,
    EscopoDespesa,
    RegraRateio,
    CartaoCredito, 
    CompraCartao,
)

User = get_user_model()


# -----------------------------
# Auth / Registro
# -----------------------------
class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6)
    nome_casal = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate_username(self, v):
        if User.objects.filter(username=v).exists():
            raise serializers.ValidationError("Usuário já existe.")
        return v

    def create(self, validated):
        first_name = validated.get("first_name", "")
        username = validated["username"]
        email = validated.get("email", "")
        password = validated["password"]
        nome_casal = validated.get("nome_casal") or (first_name or username)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
        )

        casal = Casal.objects.create(nome=nome_casal or "")
        MembroCasal.objects.create(
            casal=casal,
            usuario=user,
            apelido=first_name or username,
            ativo=True,
        )

        # Gera tokens JWT
        refresh = RefreshToken.for_user(user)
        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "email": user.email,
            },
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


# -----------------------------
# Usuário / Casal
# -----------------------------
class UsuarioSlimSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "email")


class MembroCasalSerializer(serializers.ModelSerializer):
    usuario = UsuarioSlimSerializer(read_only=True)
    usuario_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source="usuario", required=True
    )

    class Meta:
        model = MembroCasal
        fields = (
            "id",
            "casal",
            "usuario",
            "usuario_id",
            "apelido",
            "ativo",
            "criado_em",
            "atualizado_em",
        )
        read_only_fields = ("casal", "criado_em", "atualizado_em")


class CasalSerializer(serializers.ModelSerializer):
    membros = MembroCasalSerializer(many=True, read_only=True)

    class Meta:
        model = Casal
        fields = ("id", "nome", "membros", "criado_em", "atualizado_em")


# -----------------------------
# Categorias
# -----------------------------
class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = ["id", "nome", "slug", "ativa"]


class SubcategoriaSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(read_only=True)
    categoria_id = serializers.PrimaryKeyRelatedField(
        source="categoria", queryset=Categoria.objects.all(), write_only=True
    )

    class Meta:
        model = Subcategoria
        fields = ["id", "nome", "slug", "ativa", "categoria", "categoria_id"]


# -----------------------------
# Lançamentos
# -----------------------------
class RateioLancamentoSerializer(serializers.ModelSerializer):
    membro = UsuarioSlimSerializer(read_only=True)
    membro_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source="membro"
    )

    class Meta:
        model = RateioLancamento
        fields = (
            "id",
            "lancamento",
            "membro",
            "membro_id",
            "percentual",
            "valor",
            "criado_em",
            "atualizado_em",
        )
        read_only_fields = ("criado_em", "atualizado_em")


class CartaoCreditoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartaoCredito
        fields = ["id", "nome", "bandeira", "limite", "dia_fechamento", "dia_vencimento", "ativo"]

class CompraCartaoSerializer(serializers.ModelSerializer):
    cartao = CartaoCreditoSerializer(read_only=True)
    cartao_id = serializers.PrimaryKeyRelatedField(source="cartao", queryset=CartaoCredito.objects.all(), write_only=True)

    subcategoria = SubcategoriaSerializer(read_only=True)
    subcategoria_id = serializers.PrimaryKeyRelatedField(source="subcategoria", queryset=Subcategoria.objects.all(), write_only=True)

    pagador = UsuarioSlimSerializer(read_only=True)
    pagador_id = serializers.PrimaryKeyRelatedField(source="pagador", queryset=User.objects.all(), write_only=True)

    dono_pessoal = UsuarioSlimSerializer(read_only=True)
    dono_pessoal_id = serializers.PrimaryKeyRelatedField(source="dono_pessoal", queryset=User.objects.all(), write_only=True, allow_null=True, required=False)

    class Meta:
        model = CompraCartao
        # CORREÇÃO: Removidos os campos "compra_cartao", "parcela_numero" e o "parcelas_total" duplicado.
        fields = [
            "id", "casal", "cartao", "cartao_id", "descricao",
            "subcategoria", "subcategoria_id", "escopo", "dono_pessoal", "dono_pessoal_id",
            "valor_total", "parcelas_total", "primeira_competencia", "primeiro_vencimento",
            "pagador", "pagador_id", "criado_em", "atualizado_em"
        ]
        read_only_fields = ("casal", "criado_em", "atualizado_em")

    def validate(self, data):
        escopo = data.get("escopo", getattr(self.instance, "escopo", None))
        dono = data.get("dono_pessoal", getattr(self.instance, "dono_pessoal", None))
        if escopo == EscopoDespesa.PESSOAL and not dono:
            raise serializers.ValidationError("Compras pessoais exigem dono_pessoal.")
        if escopo == EscopoDespesa.COMPARTILHADA and dono:
            raise serializers.ValidationError("Compras compartilhadas não devem ter dono_pessoal.")
        if data.get("parcelas_total", 1) < 1:
            raise serializers.ValidationError("parcelas_total deve ser >= 1.")
        return data

class LancamentoSerializer(serializers.ModelSerializer):
    # write-only
    subcategoria_id = serializers.PrimaryKeyRelatedField(
        source="subcategoria", queryset=Subcategoria.objects.all(), write_only=True
    )
    pagador_id = serializers.PrimaryKeyRelatedField(
        source="pagador", queryset=User.objects.all(), write_only=True
    )
    dono_pessoal_id = serializers.PrimaryKeyRelatedField(
        source="dono_pessoal",
        queryset=User.objects.all(),
        write_only=True,
        allow_null=True,
        required=False,
    )

    # read-only
    subcategoria = SubcategoriaSerializer(read_only=True)
    categoria = CategoriaSerializer(source="subcategoria.categoria", read_only=True)
    pagador = UsuarioSlimSerializer(read_only=True)
    dono_pessoal = UsuarioSlimSerializer(read_only=True)

    # se quiser expor, mas SEM permitir write:
    criado_por = UsuarioSlimSerializer(read_only=True)

    class Meta:
        model = Lancamento
        fields = [
            "id",
            "casal",              # read-only (setado no perform_create)
            "despesa_modelo",     # opcional se você usar templates
            "subcategoria_id",    # write
            "subcategoria",       # read
            "categoria",          # read (pai da subcategoria)
            "escopo",
            "dono_pessoal_id",    # write
            "dono_pessoal",       # read
            "descricao",
            "competencia",
            "data_vencimento",
            "valor_total",
            "status",
            "data_pagamento",
            "pagador_id",         # write
            "pagador",            # read
            "criado_por",         # read
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ("casal", "criado_por", "criado_em", "atualizado_em")

    def validate(self, data):
        escopo = data.get("escopo", getattr(self.instance, "escopo", None))
        dono = data.get("dono_pessoal", getattr(self.instance, "dono_pessoal", None))

        if escopo == EscopoDespesa.PESSOAL and not dono:
            raise serializers.ValidationError("Lançamentos pessoais exigem dono_pessoal.")
        if escopo == EscopoDespesa.COMPARTILHADA and dono:
            raise serializers.ValidationError("Lançamentos compartilhados não devem ter dono_pessoal.")
        return data


# -----------------------------
# Despesa Modelo + Rateios Padrão
# -----------------------------
class RegraRateioPadraoSerializer(serializers.ModelSerializer):
    membro = UsuarioSlimSerializer(read_only=True)
    membro_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source="membro", required=True
    )

    class Meta:
        model = RegraRateioPadrao
        fields = (
            "id",
            "despesa_modelo",
            "membro",
            "membro_id",
            "percentual",
            "valor_fixo",
            "criado_em",
            "atualizado_em",
        )
        read_only_fields = ("criado_em", "atualizado_em")


class DespesaModeloSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(read_only=True)
    categoria_id = serializers.PrimaryKeyRelatedField(
        queryset=Categoria.objects.all(), write_only=True, source="categoria"
    )
    dono_pessoal = UsuarioSlimSerializer(read_only=True)
    dono_pessoal_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source="dono_pessoal",
        allow_null=True,
        required=False,
    )
    rateios_padrao = RegraRateioPadraoSerializer(many=True, read_only=True)

    class Meta:
        model = DespesaModelo
        fields = (
            "id",
            "casal",              # read-only (setado no perform_create no ViewSet)
            "nome",
            "categoria",
            "categoria_id",
            "escopo",
            "dono_pessoal",
            "dono_pessoal_id",
            "valor_previsto",
            "dia_vencimento",
            "recorrente",
            "periodicidade",
            "regra_rateio",
            "ativo",
            "rateios_padrao",
            "criado_em",
            "atualizado_em",
        )
        read_only_fields = ("casal", "criado_em", "atualizado_em")

    def validate(self, data):
        escopo = data.get("escopo", getattr(self.instance, "escopo", None))
        dono = data.get("dono_pessoal", getattr(self.instance, "dono_pessoal", None))
        regra = data.get("regra_rateio", getattr(self.instance, "regra_rateio", RegraRateio.IGUAL))

        if escopo == EscopoDespesa.PESSOAL and not dono:
            raise serializers.ValidationError("Despesas pessoais exigem um dono_pessoal.")
        if escopo == EscopoDespesa.COMPARTILHADA and dono:
            raise serializers.ValidationError("Despesas compartilhadas não devem ter dono_pessoal.")
        if escopo == EscopoDespesa.PESSOAL and regra != RegraRateio.IGUAL:
            data["regra_rateio"] = RegraRateio.IGUAL
        return data


class ResumoLancamentoSerializer(serializers.Serializer):
    """
    Serializer unificado para exibir tanto Lançamentos únicos
    quanto Compras parceladas de forma agregada.
    """
    id = serializers.IntegerField()
    type = serializers.CharField() # 'lancamento' ou 'compra'
    descricao = serializers.CharField()
    subcategoria = SubcategoriaSerializer(read_only=True)
    escopo = serializers.CharField()
    
    # Campos que podem vir de ambos os modelos
    valor_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    competencia = serializers.DateField(required=False) # Usado para ordenação
    data_vencimento = serializers.DateField(required=False)
    
    # Campos específicos
    parcelas_total = serializers.IntegerField(required=False)
    status = serializers.CharField(required=False)

    def to_representation(self, instance):
        if isinstance(instance, Lancamento):
            return {
                'id': instance.id,
                'type': 'lancamento',
                'descricao': instance.descricao,
                'subcategoria': SubcategoriaSerializer(instance.subcategoria).data,
                'escopo': instance.escopo,
                'valor_total': instance.valor_total,
                'parcelas_total': 1,
                'competencia': instance.competencia,
                'data_vencimento': instance.data_vencimento,
                'status': instance.status,
            }
        elif isinstance(instance, CompraCartao):
            # Para compras, usamos a primeira competência/vencimento para fins de ordenação
            return {
                'id': instance.id,
                'type': 'compra',
                'descricao': instance.descricao,
                'subcategoria': SubcategoriaSerializer(instance.subcategoria).data,
                'escopo': instance.escopo,
                'valor_total': instance.valor_total,
                'parcelas_total': instance.parcelas_total,
                'competencia': instance.primeira_competencia,
                'data_vencimento': instance.primeiro_vencimento,
                'status': 'PARCELADA', # Um status customizado para o frontend
            }
        return super().to_representation(instance)