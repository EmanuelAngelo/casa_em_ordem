from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Casal, MembroCasal, Categoria, Subcategoria, Lancamento, DespesaModelo, RegraRateioPadrao,
    Lancamento, RateioLancamento, EscopoDespesa, RegraRateio, StatusLancamento
)

User = get_user_model()

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
        fields = ("id", "casal", "usuario", "usuario_id", "apelido", "ativo", "criado_em", "atualizado_em")
        read_only_fields = ("casal", "criado_em", "atualizado_em")


class CasalSerializer(serializers.ModelSerializer):
    membros = MembroCasalSerializer(many=True, read_only=True)

    class Meta:
        model = Casal
        fields = ("id", "nome", "membros", "criado_em", "atualizado_em")


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

class LancamentoSerializer(serializers.ModelSerializer):
    # write
    subcategoria_id = serializers.PrimaryKeyRelatedField(
        source="subcategoria", queryset=Subcategoria.objects.all(), write_only=True
    )
    pagador_id = serializers.PrimaryKeyRelatedField(
        source="pagador", queryset=User.objects.all(), write_only=True
    )
    dono_pessoal_id = serializers.PrimaryKeyRelatedField(
        source="dono_pessoal", queryset=User.objects.all(), write_only=True, allow_null=True, required=False
    )
    # read
    subcategoria = SubcategoriaSerializer(read_only=True)
    categoria = CategoriaSerializer(source="subcategoria.categoria", read_only=True)
    pagador = UsuarioSlimSerializer(read_only=True)
    dono_pessoal = UsuarioSlimSerializer(read_only=True)

    class Meta:
        model = Lancamento
        fields = [
            "id", "casal", "despesa_modelo",
            "subcategoria_id", "subcategoria", "categoria",
            "escopo", "dono_pessoal_id", "dono_pessoal",
            "descricao", "competencia", "data_vencimento",
            "valor_total", "status", "data_pagamento",
            "pagador_id", "pagador",
            "criado_por", "criado_em", "atualizado_em",
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


class RegraRateioPadraoSerializer(serializers.ModelSerializer):
    membro = UsuarioSlimSerializer(read_only=True)
    membro_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source="membro", required=True
    )

    class Meta:
        model = RegraRateioPadrao
        fields = ("id", "despesa_modelo", "membro", "membro_id", "percentual", "valor_fixo", "criado_em", "atualizado_em")
        read_only_fields = ("criado_em", "atualizado_em")


class DespesaModeloSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(read_only=True)
    categoria_id = serializers.PrimaryKeyRelatedField(
        queryset=Categoria.objects.all(), write_only=True, source="categoria"
    )
    dono_pessoal = UsuarioSlimSerializer(read_only=True)
    dono_pessoal_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source="dono_pessoal", allow_null=True, required=False
    )
    rateios_padrao = RegraRateioPadraoSerializer(many=True, read_only=True)

    class Meta:
        model = DespesaModelo
        fields = (
            "id", "casal", "nome", "categoria", "categoria_id", "escopo",
            "dono_pessoal", "dono_pessoal_id", "valor_previsto", "dia_vencimento",
            "recorrente", "periodicidade", "regra_rateio", "ativo", "rateios_padrao",
            "criado_em", "atualizado_em"
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


class RateioLancamentoSerializer(serializers.ModelSerializer):
    membro = UsuarioSlimSerializer(read_only=True)
    membro_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source="membro"
    )

    class Meta:
        model = RateioLancamento
        fields = ("id", "lancamento", "membro", "membro_id", "percentual", "valor", "criado_em", "atualizado_em")
        read_only_fields = ("criado_em", "atualizado_em")
