from django.core.management.base import BaseCommand
from django.db import transaction
from despesas.models import Casal
from despesas.services import criar_categorias_padrao_para_casal

class Command(BaseCommand):
    help = "Cria categorias e subcategorias padrão para um GRUPO (casal) específico."

    def add_arguments(self, parser):
        parser.add_argument('casal_id', type=int, help='ID do grupo (casal) a popular com categorias padrão.')

    @transaction.atomic
    def handle(self, *args, **options):
        casal_id = options['casal_id']
        try:
            casal = Casal.objects.get(pk=casal_id)
        except Casal.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Grupo com ID {casal_id} não encontrado."))
            return

        if casal.categorias.exists():
            self.stdout.write(self.style.WARNING(f"O grupo '{casal.nome}' (ID: {casal_id}) já possui categorias."))
            return

        self.stdout.write(f"Criando categorias padrão para o grupo '{casal.nome}' (ID: {casal_id})...")
        criar_categorias_padrao_para_casal(casal)
        self.stdout.write(self.style.SUCCESS("Categorias padrão criadas com sucesso."))
