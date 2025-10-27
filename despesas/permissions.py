from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.exceptions import PermissionDenied
from .utils import get_casal_ativo_do_usuario

class IsAutenticadoNoSeuCasal(BasePermission):
    """
    Antes: retornava 403 quando não havia grupo atual.
    Agora: para métodos de leitura (GET/HEAD/OPTIONS), permite seguir sem grupo (as views devem devolver queryset vazio).
          Para métodos de escrita, exige grupo atual.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True  # leitura liberada; a view deve filtrar/vaziar
        casal = get_casal_ativo_do_usuario(request.user)
        return casal is not None

class SomenteDoMeuCasal(BasePermission):
    """
    Mantém a checagem de objeto, mas só é chamada quando há objeto.
    Para escrita, continua exigindo pertencer ao grupo; para leitura, já passamos pelo filtro de queryset.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        # objetos principais têm 'casal' (grupo) relacionado
        casal = getattr(obj, "casal", None) or getattr(getattr(obj, "categoria", None), "casal", None)
        if casal is None:
            return False
        from .models import MembroCasal
        return MembroCasal.objects.filter(casal=casal, usuario=request.user, ativo=True).exists()

class CasalScopedQuerysetMixin:
    """
    Fornece utilitário para as ViewSets limitarem o queryset ao grupo atual.
    Se não existir grupo, retorna None; a view deve tratar (lista vazia; escrita bloqueada).
    """
    def get_casal_usuario(self):
        return get_casal_ativo_do_usuario(self.request.user)

    def filter_queryset_por_casal(self, qs):
        casal = self.get_casal_usuario()
        return qs.filter(casal=casal) if casal else qs.none()
