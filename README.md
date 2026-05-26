
# ResearchDoc
A research management SaaS platform built with Django and Bootstrap 5 for INFS3202/7202 Web Information Systems at UQ.

**Student:** Aditya Raj Singh (48979519)

This project follows the patterns and conventions taught in Applied Classes.

# Credentials (ADMIN AND USER DETAILS)

These accounts are created by the `seed_sample_data` command (see setup below).

## Regular User

```text
email: aditya6283@gmail.com
Password: Uq@62833
```

## Admin User

```text
Username: admin
Password: admin123
```
# Project Structure

```text
researchdoc_app/
│
├── manage.py
├── requirements.txt
├── README.md
├── .env
├── .gitignore
│
├── media/
│
├── templates/
│   ├── account/
│   │   ├── login.html
│   │   ├── signup.html
│   │   ├── password_change.html
│   │   ├── password_reset.html
│   │   ├── password_reset_done.html
│   │   ├── password_reset_from_key.html
│   │   ├── password_reset_from_key_done.html
│   │   └── email.html
│   │
│   └── socialaccount/
│       └── authentication_error.html
│
├── researchapp/
│   ├── migrations/
│   ├── static/
│   ├── templatetags/
│   ├── admin.py
│   ├── api_views.py
│   ├── apps.py
│   ├── citations.py
│   ├── forms.py
│   ├── models.py
│   ├── serializers.py
│   ├── signals.py
│   ├── urls.py
│   └── views.py
│
├── researchdoc/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
└── venv/
```

---

# How the Project Works

## Django Project vs App

The main Django project is:

```text
researchdoc/
```

This contains:
- settings
- project-level URLs
- WSGI configuration
- ASGI configuration

The actual application logic is inside:

```text
researchapp/
```

This contains:
- models
- forms
- views
- API endpoints
- templates
- business logic

---

# Request Flow

When a user visits:

```text
https://infs3202-3dfe6012.uqcloud.net/researchdoc/
```

the request flows through:

```text
Browser
→ Nginx
→ Gunicorn
→ Django WSGI
→ urls.py
→ views.py
→ models.py
→ templates
→ response back to browser
```

---

# URL Routing

The deployed application is served under:

```text
/researchdoc/
```

Nginx forwards requests from `/researchdoc/` to the Gunicorn service.

Inside Django:
- `researchdoc/urls.py` uses:

```python
path('', include('researchapp.urls'))
```

Templates use Django URL reversing:

```html
{% url 'dashboard' %}
```

instead of hardcoded links.

---

# MVC Pattern Used

| Layer | File | Purpose |
|---|---|---|
| Model | `models.py` | Database tables |
| Form | `forms.py` | Form handling |
| View | `views.py` | Business logic |
| URL | `urls.py` | Route mapping |
| Template | `templates/*.html` | Frontend rendering |

---

# Authentication

Authentication is implemented using:
- Django Authentication
- django-allauth
- Google OAuth
- GitHub OAuth

Features include:
- login
- signup
- logout
- password reset
- social login

Custom templates are stored in:

```text
templates/account/
```

and:

```text
templates/socialaccount/
```

---

# CRUD Features

The system supports CRUD operations for:
- research projects
- research resources
- citations
- summaries

Django class-based views are used including:
- ListView
- CreateView
- UpdateView
- DeleteView

---

# AI Features

ResearchDoc includes AI-assisted features such as:
- AI paper summarisation
- citation suggestions
- AI research assistant chatbot
- summary generation
- research insight extraction

LangChain components used include:
- PromptTemplate
- ChatOpenAI
- JsonOutputParser

---

# Static Files

Static files are stored in:

```text
researchapp/static/
```

Templates load them using:

```html
{% load static %}
```

Production static files are collected into:

```text
/var/www/htdocs/researchdoc_static/
```

---

# Media Files

Uploaded files and profile images are stored in:

```text
media/
```

and served through:

```text
/researchdoc_media/
```

using Nginx.

---

# Deployment on UQCloud

The application is deployed using:
- Gunicorn
- Nginx reverse proxy
- MySQL
- systemd service

---

# Deployment Structure

| Component | Location |
|---|---|
| Project root | `/var/www/djangoapps/researchdoc_app/` |
| Django root | `/var/www/djangoapps/researchdoc_app/researchdoc/` |
| Virtual environment | `/var/www/djangoapps/researchdoc_app/venv/` |
| Gunicorn port | `127.0.0.1:8002` |
| Static files | `/var/www/htdocs/researchdoc_static/` |
| Media files | `/var/www/djangoapps/researchdoc_app/media/` |

---

# Local Development Setup

## 1. Create virtual environment

```bash
python3 -m venv venv
```

## 2. Activate virtual environment

```bash
source venv/bin/activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure environment variables

Copy the example file and adjust as needed:

```bash
cp .env.example .env
```

Every variable has a sensible default, so the app runs with an empty `.env`.
Leave `MYSQL_PASSWORD` blank to use **SQLite locally** (zero setup); set it to
switch to MySQL like the deployment. Leave `OPENAI_API_KEY` blank to run the AI
features in deterministic offline-fallback mode.

---

# Database Setup

The app uses **SQLite by default** for local development, so no database setup
is required. When `MYSQL_PASSWORD` is set in the environment it switches to
**MySQL**, which is what the UQCloud deployment uses.

```python
# researchdoc/settings.py selects the backend from the environment:
if os.getenv('MYSQL_PASSWORD'):
    DATABASES = {'default': {'ENGINE': 'django.db.backends.mysql', ...}}
else:
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', ...}}
```

---

# Run Migrations

```bash
python manage.py migrate
```

---

# Create Superuser

```bash
python manage.py createsuperuser
```

---

# Seed Sample Data (optional)

Populates demo projects, papers, citations and the demo/admin accounts above:

```bash
python manage.py seed_sample_data
```

---

# Run Tests

```bash
python manage.py test researchapp
```

---

# Run Development Server

```bash
python manage.py runserver
```

Visit:

```text
http://127.0.0.1:8000/researchdoc/
```

---



---

# Key Features

- Research project management
- Research resource management (papers + links) with favourites and reading status
- Citation generation in APA, IEEE, MLA, Chicago and Harvard
- Citation export to BibTeX / plain text
- AI-powered paper and project summaries
- Research assistant chatbot
- Full-text search across papers and summaries
- Social authentication
- User profiles
- Dashboard analytics (citation-style chart)
- Responsive Bootstrap 5 UI with light/dark themes
- SaaS-style architecture

---

# Technologies Used

- Django
- Bootstrap 5
- MySQL
- Gunicorn
- Nginx
- LangChain
- OpenAI API
- django-allauth
- HTML/CSS/JavaScript

---

# Rubric Mapping

| Rubric Area | Feature |
|---|---|
| Deployment | UQCloud deployment |
| Authentication | Social login + user accounts |
| CRUD | Projects/resources/citations |
| UI/UX | Responsive Bootstrap UI |
| Database | MySQL integration |
| AI Integration | Research assistant + summaries |
| SaaS Features | Subscription/admin management |

---

# Use of Generative AI

Generative AI tools were used in a limited supporting role during development.

AI assistance included:
- debugging deployment issues on UQCloud
- understanding Gunicorn and Nginx configuration
- understanding URL routing and deployment prefixes
- reviewing Bootstrap frontend layout ideas
- helping understand some concepts from Applied Classes
- reviewing environment variable configuration
- assisting with a few frontend refinements and helper functions

AI was mainly used as a reference and debugging assistant rather than for core logic or architecture.

The overall system design, workflows, feature implementation, database design, and application logic were independently designed and implemented following the Applied Classes and course requirements.

---

# Submission

The submission includes:
- source code
- deployment configuration
- README
- demo credentials
- database migrations
- templates
- static files
- deployment guide