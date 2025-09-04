# Gestão de Caçambas - API

Sistema de controle de saídas de caçambas (Django + Django REST Framework).  
Inclui administração via web e operação via app/API.

---

## 🚀 Tecnologias

- Django 5+
- Django REST Framework
- JWT (SimpleJWT)
- drf-spectacular (documentação OpenAPI/Swagger)
- django-filter
- django-cors-headers
- SQLite (default) ou PostgreSQL

---

## 📦 Instalação

```bash
git clone <repo-url>
cd gestao_cacambas

# criar e ativar ambiente virtual
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate # Linux/Mac

# instalar dependências
pip install -r requirements.txt

# copiar variáveis de ambiente
cp .env.example .env
```

Edite `.env` conforme necessário.

---

## ⚙️ Migrações e superusuário

```bash
python manage.py migrate
python manage.py createsuperuser
```

---

## ▶️ Executar servidor

```bash
python manage.py runserver
```

Acesse:
- Admin: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
- Documentação Swagger: [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)

---

## 🔑 Autenticação

Obtenha tokens JWT:

```http
POST /api/token/
{
  "username": "seu_user",
  "password": "sua_senha"
}
```

Retorna:
```json
{
  "refresh": "...",
  "access": "..."
}
```

Use o token de acesso nos headers:
```
Authorization: Bearer <access_token>
```

---

## 📚 Endpoints Principais

### Produtos
- `GET /api/v1/produtos/`
- `POST /api/v1/produtos/`
- `PATCH /api/v1/produtos/{id}/toggle/`

### Veículos
- `GET /api/v1/veiculos/`
- `POST /api/v1/veiculos/`
- `PATCH /api/v1/veiculos/{id}/toggle/`
- `POST /api/v1/veiculos/import-csv/` (enviar arquivo CSV)

### Movimentações
- `GET /api/v1/movimentacoes/`
- `POST /api/v1/movimentacoes/`
- `GET /api/v1/movimentacoes/hoje/`
- `POST /api/v1/movimentacoes/{id}/solicitar_cancelamento/`
- `POST /api/v1/movimentacoes/{id}/aprovar_cancelamento/`
- `POST /api/v1/movimentacoes/{id}/rejeitar_cancelamento/`

### Relatórios
- `GET /api/v1/relatorios/movimentacoes/?de=...&ate=...`
- `GET /api/v1/relatorios/movimentacoes/?format=csv`

---

## 📂 Importação CSV de Veículos

Exemplo de CSV:

```csv
placa,numero_interno,capacidade,tipo,marca,esta_ativo
ABC1D23,E001,12.00,Truck,VW,true
DEF4G56,E002,10.50,Toco,Mercedes,true
```

---

## 🗂 Fixtures de Produtos

Carregar produtos iniciais (Barro, Areia, Piçarra):

```bash
python manage.py loaddata fixtures_produtos_iniciais.json
```

---

## 📬 Postman

Coleção pronta no arquivo:
`gestao_cacambas_postman_collection.json`

---

## 🐳 Docker (opcional)

Exemplo de `docker-compose.yml` (app + Postgres):

```yaml
version: '3.9'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: gestaocacambas
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"

  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/code
    ports:
      - "8000:8000"
    depends_on:
      - db
```

---

## 👤 Permissões

- **Admin (staff):** CRUD completo + relatórios + aprovar/rejeitar cancelamentos.
- **Operador:** pode criar movimentações e visualizar apenas as próprias.

---

## 📄 Licença

Uso interno / privado.
```

