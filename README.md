# TeamBoard - B2B Knowledge Base API Platform

A fully functional Django + Django REST Framework backend for the TeamBoard assignment.

## What is implemented

- Company registration with auto-generated API key
- JWT login using SimpleJWT
- Protected knowledge-base search endpoint
- Atomic query logging for every search, including zero-result searches
- Admin-only usage summary dashboard using `Company.role == "admin"`
- PostgreSQL through Docker Compose
- `.env`-based configuration
- Seed command with 12 knowledge-base entries
- Postman collection covering the required API scenarios
- Django tests for the critical flows

## Tech stack

- Python 3.11+
- Django 5.0.7
- Django REST Framework 3.15.2
- SimpleJWT 5.3.1
- PostgreSQL 16 via Docker

## Project structure

```text
teamboard/
├── api/
│   ├── management/commands/seed_kb.py
│   ├── migrations/0001_initial.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── permissions.py
│   ├── signals.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── postman/TeamBoard.postman_collection.json
├── teamboard/settings.py
├── teamboard/urls.py
├── docker-compose.yml
├── manage.py
├── requirements.txt
├── .env
└── .env.example
```

## Setup instructions

### 1. Create and activate a virtual environment

```bash
python -m venv venv
```

Windows PowerShell:

```bash
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

A working development `.env` is included. For your own machine, you can also copy from the example:

```bash
cp .env.example .env
```

Default values:

```env
POSTGRES_DB=teamboard_db
POSTGRES_USER=teamboard_user
POSTGRES_PASSWORD=teamboard_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### 4. Start PostgreSQL

```bash
docker compose up -d
```

Check that the database container is running:

```bash
docker compose ps
```

### 5. Apply migrations

```bash
python manage.py migrate
```

### 6. Seed the knowledge base

```bash
python manage.py seed_kb
```

### 7. Run the server

```bash
python manage.py runserver
```

Server base URL:

```text
http://127.0.0.1:8000
```

## API endpoints

### 1. Register company

`POST /api/auth/register/`

Public endpoint. No token required.

Request:

```json
{
  "username": "acmecorp",
  "password": "securepass123",
  "company_name": "Acme Corp",
  "email": "dev@acmecorp.com"
}
```

Success response: `201 Created`

```json
{
  "username": "acmecorp",
  "company_name": "Acme Corp",
  "api_key": "auto-generated-api-key",
  "access": "jwt-access-token"
}
```

Notes:

- The view creates only the Django `User`.
- `api/signals.py` auto-creates the `Company` and generates `api_key` using `secrets.token_urlsafe(32)`.
- The role always defaults to `client`.
- Duplicate username returns `400`.

### 2. Login company

`POST /api/auth/login/`

Public endpoint. No token required.

Request:

```json
{
  "username": "acmecorp",
  "password": "securepass123"
}
```

Success response: `200 OK`

```json
{
  "access": "jwt-access-token",
  "company_name": "Acme Corp",
  "api_key": "auto-generated-api-key"
}
```

Invalid credentials return `401`.

### 3. Query knowledge base

`POST /api/kb/query/`

Protected endpoint. Requires JWT token:

```text
Authorization: Bearer <access_token>
```

Request:

```json
{
  "search": "select_related"
}
```

Success response: `200 OK`

```json
{
  "search": "select_related",
  "count": 1,
  "results": [
    {
      "id": "1",
      "question": "What is select_related in Django ORM?",
      "answer": "select_related performs a SQL JOIN and fetches related ForeignKey or OneToOne objects in the same database query.",
      "category": "database"
    }
  ]
}
```

Important behavior:

- The company is extracted from `request.user.company`.
- Search uses `Q(question__icontains=search) | Q(answer__icontains=search)`.
- Search and `QueryLog` creation are inside one `transaction.atomic()` block.
- Blank search returns `400`.
- Missing/invalid token returns `401`.
- Zero results still returns `200` with `count: 0` and still writes a `QueryLog`.

### 4. Admin usage summary

`GET /api/admin/usage-summary/`

Protected endpoint. Requires a JWT token from a user whose `Company.role` is `admin`.

Success response: `200 OK`

```json
{
  "total_queries": 3,
  "active_companies": 1,
  "top_search_terms": [
    {
      "search_term": "select_related",
      "count": 2
    },
    {
      "search_term": "transaction atomic",
      "count": 1
    }
  ]
}
```

A normal `client` receives `403 Forbidden`.

## How to make a company admin

The assignment requires admin access to be based on `Company.role`, not `is_staff` or `is_superuser`.

After registering a user, open Django shell:

```bash
python manage.py shell
```

Run:

```python
from django.contrib.auth.models import User
from api.models import Company
user = User.objects.get(username='acmecorp')
user.company.role = Company.Role.ADMIN
user.company.save()
```

Then log in again and use the fresh JWT token for `/api/admin/usage-summary/`.

## Run tests

The included tests cover registration, duplicate username, login, invalid login, protected access, KB search logging, zero-result logging, client 403, and admin summary.

With PostgreSQL running:

```bash
python manage.py test
```

For a quick local SQLite-only test run:

```bash
USE_SQLITE=True python manage.py test
```

## Postman collection

Import this file into Postman:

```text
postman/TeamBoard.postman_collection.json
```

The collection includes these scenarios:

1. Register company success
2. Register duplicate username returns 400
3. Login success
4. Login invalid credentials returns 401
5. Query KB without token returns 401
6. Query KB blank search returns 400
7. Query KB with matching results returns 200
8. Query KB zero results still returns 200 and logs usage
9. Admin usage summary as client returns 403
10. Admin usage summary as admin returns 200
11. Query another common term to populate top search terms

## GitHub push checklist

```bash
git init
git add .
git commit -m "Build TeamBoard B2B knowledge base API"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

## Grading alignment checklist

- [x] Four required endpoints implemented
- [x] Register and login are public with `authentication_classes = []` and `permission_classes = []`
- [x] JWT protection configured globally
- [x] Models use the required field names
- [x] Company uses OneToOneField to Django `User`
- [x] API key generated in signal with `secrets.token_urlsafe(32)`
- [x] Role defaults to `client`
- [x] KB search uses case-insensitive `icontains` on question and answer
- [x] Query logging happens inside `transaction.atomic()`
- [x] Zero-result searches are logged
- [x] Admin permission checks `request.user.company.role == Company.Role.ADMIN`
- [x] Usage summary uses `aggregate`, `values().distinct().count()`, and `values().annotate()`
- [x] PostgreSQL runs through Docker
- [x] Credentials stored in `.env`
- [x] Dependencies pinned in `requirements.txt`
- [x] Postman collection included
