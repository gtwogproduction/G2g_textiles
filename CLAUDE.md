# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

G2G Textiles is a B2B Django website for a custom clothing manufacturer. It serves as a marketing homepage and a 6-step quote request wizard. The production site runs at https://gtwog.ch and is hosted on Render.com.

## Development Commands

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser

# Run locally
python manage.py runserver
# → Homepage:   http://127.0.0.1:8000
# → Quote:      http://127.0.0.1:8000/quote/
# → Admin:      http://127.0.0.1:8000/admin

# i18n — compile translations after editing .po files
python manage.py compilemessages
```

No test suite or linting is configured. No build tools are needed — CSS/JS are served as-is via WhiteNoise/Django.

## Deployment (Render.com)

Configured via `render.yaml`. On every deploy Render runs:
```
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
gunicorn g2g_textiles.wsgi:application
```

SQLite is used locally; PostgreSQL is used in production (configured via `DATABASE_URL` env var). Static files are served by WhiteNoise. Media files (images, videos) are stored on Cloudinary.

## Architecture

The entire site lives in a single Django app: `homepage/`.

### URL → View → Template mapping

| URL | View | Template |
|-----|------|----------|
| `/` | `homepage()` | `index.html` |
| `/contact/` | `contact()` | `contact.html` |
| `/quote/` → `/quote/5/` | `quote()` | `quote.html` |
| `/quote/success/` | `quote_success()` | `quote_success.html` |
| `/blog/` | `blog_list()` | `blog_list.html` |
| `/blog/<slug>/` | `blog_detail()` | `blog_detail.html` |
| `/impressum/`, `/agb/` | `legal_page()` | `legal.html` |

### Quote Wizard

The quote wizard spans 5 steps (About You → Order Details → Customisation → Production Country → Special Requirements). State is accumulated in Django's session across steps and a `QuoteRequest` model instance is created and progressively updated. On final submission, two emails are sent via Resend (SMTP at smtp.resend.com:465): an internal notification to production@gtwog.ch and a confirmation to the customer.

### Models

- **QuoteRequest** — 50+ fields for the full quote wizard submission
- **ContactSubmission** — Quick contact form
- **SiteSettings** — Singleton controlling homepage hero, CTA, footer, and SEO meta
- **Service**, **HowItWorksStep**, **ClientLogo** — Editable homepage section content
- **BlogPost**, **BlogCategory**, **BlogPostImage** — Editorial/case study content
- **LegalPage** — Impressum & AGB content

### Internationalisation (i18n)

The site supports English and German. Key patterns:
- URL prefixes: `/en/…` and `/de/…` via `i18n_patterns` in `urls.py`
- Language auto-detection uses Accept-Language header → CloudFlare IP geolocation → defaults to English
- All translatable model fields have a `_de` suffix (e.g. `title` / `title_de`)
- Views determine language with `is_de = current_lang.startswith('de')`
- Templates use `{% load i18n %}` and `{% trans "…" %}`
- Translation strings live in `locale/en/` and `locale/de/`; edit `.po` files then run `compilemessages`

### Frontend

- No JS framework — vanilla JS only (`main.js` for nav/scroll animations, `quote.js` for conditional field visibility in the wizard)
- Four CSS files: `style.css` (global), `quote.css` (wizard), `contact.css`, `blog.css`
- Google Fonts: Bebas Neue, DM Sans
