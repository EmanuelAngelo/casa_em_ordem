# despesas/management/commands/seed_categorias.py
from django.core.management.base import BaseCommand
from despesas.models import Categoria, Subcategoria

CATEGORIAS = {
    "Condomínio / Moradia": [
        "Taxa de condomínio",
        "Energia",
        "Água",
        "Internet",
        "Gás",
        "Feira do mês",
        "Streaming",
        "Aluguel",
    ],
    "Transporte": [
        "Combustível",
        "Uber/99",
        "Manutenção do carro",
        "Transporte público",
    ],
    "Alimentação": [
        "Supermercado",
        "Restaurante/Lanchonete",
        "Delivery",
    ],
    "Lazer e Assinaturas": [
        "Netflix/Prime/Disney+",
        "Academia",
        "Viagens",
        "Jogos/Apps",
    ],
    "Saúde": [
        "Plano de saúde",
        "Farmácia",
        "Consultas/Exames",
    ],
    "Educação": [
        "Cursos",
        "Livros/Material",
        "Mensalidades escolares/faculdade",
    ],
    "Finanças": [
        "Cartão de crédito",
        "Empréstimos",
        "Investimentos",
        "Seguros",
    ],
}

class Command(BaseCommand):
    help = "Cria Categorias e Subcategorias padrão"

    def handle(self, *args, **options):
        total_cats = 0
        total_subs = 0

        for cat_nome, subs in CATEGORIAS.items():
            cat, created = Categoria.objects.get_or_create(nome=cat_nome, defaults={"ativa": True})
            if created:
                total_cats += 1

            for sub in subs:
                _, s_created = Subcategoria.objects.get_or_create(
                    categoria=cat, nome=sub, defaults={"ativa": True}
                )
                if s_created:
                    total_subs += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seed concluído. Categorias criadas: {total_cats}, Subcategorias criadas: {total_subs}"
        ))
