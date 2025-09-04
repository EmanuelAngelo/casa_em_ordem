from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import MembroCasal, Casal

User = get_user_model()

def get_casal_ativo_do_usuario(user: User) -> Casal | None: # pyright: ignore[reportInvalidTypeForm]
    membro = MembroCasal.objects.filter(usuario=user, ativo=True).select_related("casal").first()
    return membro.casal if membro else None

def assert_user_pertence_ao_casal(user: User, casal: Casal): # type: ignore
    if not MembroCasal.objects.filter(usuario=user, casal=casal, ativo=True).exists():
        raise ValidationError("Usuário não pertence ao casal informado.")
