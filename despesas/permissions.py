from rest_framework.permissions import BasePermission, SAFE_METHODS
from .utils import get_casal_ativo_do_usuario

class IsAutenticadoNoSeuCasal(BasePermission):
    """
    Garante que o usuário está autenticado e tem casal ativo.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return get_casal_ativo_do_usuario(request.user) is not None


class SomenteDoMeuCasal(BasePermission):
    """
    Verificação em nível de objeto: o objeto deve pertencer ao casal do usuário.
    Para modelos que têm 'casal' direto ou via relação conhecida.
    """
    def has_object_permission(self, request, view, obj):
        casal_user = get_casal_ativo_do_usuario(request.user)
        if casal_user is None:
            return False
        # Tenta resolver atributo 'casal' direto:
        objeto_casal = getattr(obj, "casal", None)
        if objeto_casal:
            return objeto_casal_id(objeto_casal) == casal_user.id

        # Casos especiais:
        from .models import DespesaModelo, RegraRateioPadrao
        if isinstance(obj, DespesaModelo):
            return obj.casal_id == casal_user.id
        if isinstance(obj, RegraRateioPadrao):
            return obj.despesa_modelo.casal_id == casal_user.id

        # Categoria é global — liberar leitura (e escrita apenas se quiser global admin)
        from .models import Categoria
        if isinstance(obj, Categoria):
            return True

        return False


def objeto_casal_id(casal) -> int | None:
    try:
        return casal.id
    except Exception:
        return None


class CasalScopedQuerysetMixin:
    """
    Mixin para filtrar automaticamente por casal do usuário e setar casal no create.
    Requer que o queryset do ViewSet seja do modelo que tenha campo 'casal' OU
    seja possível filtrar por relação (override get_casal_filter_kwargs se necessário).
    """
    def get_casal_filter_kwargs(self):
        return {"casal": self.get_casal_usuario()}

    def get_casal_usuario(self):
        from .utils import get_casal_ativo_do_usuario
        casal = get_casal_ativo_do_usuario(self.request.user)
        return casal

    def get_queryset(self):
        qs = super().get_queryset()
        casal = self.get_casal_usuario()
        if casal is None:
            return qs.none()
        try:
            return qs.filter(**self.get_casal_filter_kwargs())
        except Exception:
            # Para modelos sem 'casal' (ex.: Categoria), não filtra
            return qs

    def perform_create(self, serializer):
        casal = self.get_casal_usuario()
        extra = {}
        if "criado_por" in [f.name for f in serializer.Meta.model._meta.get_fields()]:
            extra["criado_por"] = self.request.user
        serializer.save(casal=casal, **extra)
