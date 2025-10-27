# despesas/utils.py
from typing import Optional, TYPE_CHECKING

from django.contrib.auth import get_user_model
from .models import MembroCasal, Casal, PreferenciasUsuario

# Para tipagem somente em tempo de checagem (Pylance/Mypy), sem impactar o runtime.
if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser as DjangoUser  # ou AbstractUser

User = get_user_model()


def _get_or_create_prefs(user: "DjangoUser") -> PreferenciasUsuario:
    prefs, _ = PreferenciasUsuario.objects.get_or_create(usuario=user)
    return prefs


def get_casal_ativo_do_usuario(user: "DjangoUser") -> Optional[Casal]:
    """
    1) Se houver grupo_atual nas preferências e o usuário ainda pertence a ele, usa esse.
    2) Senão, pega o primeiro grupo em que o usuário é membro ativo e sincroniza nas preferências.
    3) Se não houver nenhum, retorna None.
    """
    prefs = (
        PreferenciasUsuario.objects.filter(usuario=user)
        .select_related("grupo_atual")
        .first()
    )
    if prefs and prefs.grupo_atual_id:
        if MembroCasal.objects.filter(
            usuario=user, casal_id=prefs.grupo_atual_id, ativo=True
        ).exists():
            return prefs.grupo_atual

    membro = (
        MembroCasal.objects.filter(usuario=user, ativo=True)
        .select_related("casal")
        .first()
    )
    if membro:
        prefs = prefs or _get_or_create_prefs(user)
        if prefs.grupo_atual_id != membro.casal_id:
            prefs.grupo_atual = membro.casal
            prefs.save(update_fields=["grupo_atual"])
        return membro.casal

    return None


def assert_user_pertence_ao_casal(user: "DjangoUser", casal: Casal) -> None:
    if not MembroCasal.objects.filter(usuario=user, casal=casal, ativo=True).exists():
        from django.core.exceptions import ValidationError

        raise ValidationError("Usuário não pertence ao grupo informado.")
