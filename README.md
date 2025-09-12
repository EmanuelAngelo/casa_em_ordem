# 💳 Gastos a Dois

Aplicação para **gestão de finanças compartilhadas entre casais**, permitindo organizar despesas, criar categorias, controlar cartões de crédito, acompanhar lançamentos e visualizar estatísticas em dashboards.

---

## 🚀 Tecnologias

### Backend
- [Django 5](https://www.djangoproject.com/) + [Django REST Framework](https://www.django-rest-framework.org/)
- [SimpleJWT](https://django-rest-framework-simplejwt.readthedocs.io/) (autenticação JWT)
- SQLite (dev) / PostgreSQL (produção)
- `django-filter` para filtros dinâmicos
- `django-cors-headers` para integração com frontend

### Frontend
- [Vue 3](https://vuejs.org/)
- [Vuetify 3](https://next.vuetifyjs.com/en/)
- Axios para comunicação com a API
- Vue Router

---

## ⚙️ Funcionalidades

- 👥 **Cadastro de Casais**  
  Cada usuário cria ou participa de um casal.  
  O casal é o contexto para todas as despesas e lançamentos.

- 🧾 **Lançamentos**  
  - Cadastro de despesas pessoais ou compartilhadas  
  - Associação com categorias e subcategorias  
  - Controle de status: **Pendente, Pago, Cancelado**  
  - Inclusão de despesas parceladas (cartão de crédito)

- 📂 **Categorias e Subcategorias**  
  - Estrutura hierárquica para organizar os lançamentos  
  - CRUD completo com associação a casais

- 💳 **Cartões de Crédito**  
  - Cadastro de cartões (nome, bandeira, limite, dia de fechamento e vencimento)  
  - Lançamentos vinculados ao cartão  
  - Controle automático de parcelas

- 📊 **Dashboard (em construção)**  
  - Resumo mensal de gastos  
  - Comparação por categorias  
  - Indicadores por pessoa (no casal)

---

## 🔑 Autenticação

- Login e registro de usuários via **JWT**  
- Criação automática de um casal no registro  
- Cada endpoint da API respeita o escopo do casal

---

## 🛠️ Instalação

### Backend

```bash
# entrar no diretório backend
cd backend

# criar virtualenv
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

# instalar dependências
pip install -r requirements.txt

# rodar migrações
python manage.py migrate

# rodar seed inicial (categorias e subcategorias)
python manage.py seed_categorias

# iniciar servidor
python manage.py runserver

