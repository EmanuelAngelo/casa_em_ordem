from django.core.management.base import BaseCommand
from django.db import transaction
from despesas.models import Casal
from despesas.services import criar_categorias_padrao_para_casal # Importa a função central

class Command(BaseCommand):
    help = "Cria categorias e subcategorias padrão para um casal específico que ainda não as tenha."

    def add_arguments(self, parser):
        parser.add_argument('casal_id', type=int, help='O ID do Casal para popular com categorias padrão.')

    @transaction.atomic
    def handle(self, *args, **options):
        casal_id = options['casal_id']
        try:
            casal = Casal.objects.get(pk=casal_id)
        except Casal.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Casal com ID {casal_id} não encontrado."))
            return

        # Verifica se o casal já tem categorias para não duplicar
        if casal.categorias.exists():
            self.stdout.write(self.style.WARNING(f"O casal '{casal.nome}' (ID: {casal_id}) já possui categorias. Nenhuma ação foi tomada."))
            return
            
        self.stdout.write(f"Criando categorias padrão para o casal '{casal.nome}' (ID: {casal_id})...")
        
        criar_categorias_padrao_para_casal(casal)

        self.stdout.write(self.style.SUCCESS(
            f"Categorias padrão criadas com sucesso para o casal ID {casal_id}."
        ))
