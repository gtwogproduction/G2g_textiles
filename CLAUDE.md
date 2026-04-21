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

No linting is configured. No build tools are needed — CSS/JS are served as-is via WhiteNoise/Django.

```bash
# Run portal integration tests
python manage.py test homepage.tests.test_portal --verbosity=2
```

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

### Portal

A customer/production portal lives under `/en/portal/` (and `/de/portal/`). It is role-gated using Django Groups.

| URL | View | Who can access |
|-----|------|----------------|
| `portal/login/` | `portal_login` | Public |
| `portal/logout/` | `portal_logout` | Authenticated |
| `portal/` | `portal_home` | Authenticated — redirects by role |
| `portal/customer/` | `customer_dashboard` | Customer (no group) |
| `portal/customer/<pk>/` | `customer_order` | Customer (own orders only) |
| `portal/staff/` | `staff_dashboard` | `g2g_staff` group |
| `portal/staff/<pk>/` | `staff_order` | `g2g_staff` group |
| `portal/factory/` | `factory_dashboard` | `factory` group |
| `portal/factory/<pk>/` | `factory_order` | `factory` group |
| `portal/staff/<pk>/quote/create/` | `staff_create_quote` | `g2g_staff` group |
| `portal/staff/quote/<quote_pk>/` | `staff_quote_edit` | `g2g_staff` group |
| `portal/staff/quote/<quote_pk>/send/` | `staff_quote_send` | `g2g_staff` group |
| `portal/staff/quote/<quote_pk>/print/` | `staff_quote_print` | `g2g_staff` group |
| `portal/customer/<pk>/quote/` | `customer_quote_view` | Customer (own orders only) |

**User roles (Django Groups)**

| Group | Access |
|-------|--------|
| `g2g_staff` | All orders; can post status updates and assign factories |
| `factory` | Only orders where `assigned_factory` matches their account; can post updates |
| *(no group)* | Customer — only orders where `customer` matches their account |

**Creating portal users (step by step)**

1. Go to `/en/admin/auth/user/add/` → set username + password → Save.
2. **G2G staff account** — open the user, scroll to Groups, add `g2g_staff`. They can now log in at `/en/portal/` and see all orders.
3. **Factory account** — same as above but add `factory` group. They see only orders assigned to them.
4. **Customer account** — leave Groups empty. Then open the relevant `QuoteRequest` in `/en/admin/homepage/quoterequest/`, scroll to the **Portal** fieldset, set the `Customer` field to the user, and Save. The customer can now log in and see their order timeline.
5. **Django admin access** — tick **Staff status** on the user for admin panel access; tick **Superuser status** for full unrestricted access.

Portal login URL to share: `https://gtwog.ch/en/portal/login/`

**Settings** (already in `settings.py`):
```python
LOGIN_URL = '/en/portal/login/'
LOGIN_REDIRECT_URL = '/en/portal/'
LOGOUT_REDIRECT_URL = '/en/'
```

**New/updated models**

- **OrderStatusUpdate** — tracks progress on a `QuoteRequest`. Fields: `quote_request` (FK), `status` (9 choices: quote_received → delivered), `update_type` ('update' / 'issue'), `note`, `attachment` (Cloudinary FileField), `tracking_number`, `tracking_url`, `created_by` (FK→User), `created_at`.
- **QuoteRequest** — two new nullable FK fields: `customer` (FK→User) and `assigned_factory` (FK→User).
- **Quote** — formal pricing document linked to a `QuoteRequest` (OneToOne). Auto-generates `quote_number` in `Q-YYYY-NNNN` format. Fields: `status` (draft/sent/accepted/rejected/expired), `currency`, `valid_until`, `estimated_delivery`, `notes_internal` (staff only), `notes_customer` (shown to customer), `created_by` (FK→User).
- **QuoteLineItem** — individual priced rows on a `Quote`. Fields: `description`, `quantity`, `unit_price`, `discount_pct`, `note`, `order`. Computed `subtotal` property applies discount.

**Quote Builder workflow (staff)**

1. Open any order in the staff portal → click **Create Quote** in the right column.
2. The editor pre-populates one line item per style from the QuoteRequest. Set prices, add/remove rows — the CHF total updates live in the browser.
3. Fill in currency, validity date, estimated delivery, and optional customer notes → **Save Draft**.
4. When ready: **Send to Customer** — sets status to `sent` and emails the customer an HTML quote with line items and total.
5. **Print / Save as PDF** opens a standalone A4 print view (`window.print()`).
6. Customers see their quote under *My Orders → View Quote* (draft returns 404).

**Status pipeline (sequential)**

Status updates follow a fixed 9-stage pipeline: `quote_received → in_review → sourcing → sampling → in_production → quality_check → shipped → customs → delivered`. Each stage can only be posted once. The next stage is enforced server-side — staff and factory users see a read-only "Next stage" display rather than a dropdown. Issues/delays can be flagged at any point without advancing the pipeline. Tracking number and link are only available when posting the `shipped` stage.

**New files**
- `homepage/static/homepage/css/portal.css`
- `homepage/templates/homepage/portal/` — `base.html`, `login.html`, `customer_dashboard.html`, `customer_order.html`, `staff_dashboard.html`, `staff_order.html`, `factory_dashboard.html`, `factory_order.html`, `staff_quote_edit.html`, `staff_quote_print.html`, `customer_quote.html`

### Quote Wizard

The quote wizard spans 5 steps (About You → Order Details → Customisation → Production Country → Special Requirements). State is accumulated in Django's session across steps and a `QuoteRequest` model instance is created and progressively updated. On final submission, two emails are sent via Resend (SMTP at smtp.resend.com:465): an internal notification to production@gtwog.ch and a confirmation to the customer.

### Models

- **QuoteRequest** — 50+ fields for the full quote wizard submission; also holds `customer` and `assigned_factory` FK fields for the portal
- **OrderStatusUpdate** — per-order status timeline entries with sequential pipeline enforcement (see Portal section)
- **Quote** — formal pricing document linked to a QuoteRequest (see Quote Builder workflow above)
- **QuoteLineItem** — individual priced rows on a Quote
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
- Five CSS files: `style.css` (global), `quote.css` (wizard), `contact.css`, `blog.css`, `portal.css` (portal)
- Google Fonts: Bebas Neue, DM Sans

---

## Blog Writer Tool (`tools/blog-writer/`)

A dev-only, standalone tool for generating bilingual (EN + DE) blog articles using a 4-phase Claude AI pipeline. Runs locally at `http://localhost:3001` and writes draft `BlogPost` records directly to the **live Render PostgreSQL database**.

### How to Run

```bash
# From project root, with project venv active
cd tools/blog-writer
pip install -r requirements.txt   # first time only
pip install psycopg2-binary        # PostgreSQL driver
cp .env.example .env              # then fill in keys
uvicorn server:app --port 3001 --reload
# Open http://localhost:3001
```

### Environment (`.env`)

```
ANTHROPIC_API_KEY=sk-ant-...
DJANGO_PROJECT_PATH=/Users/kiram/Desktop/Webdevelopment/G2g_textiles
DJANGO_SETTINGS_MODULE=g2g_textiles.settings
DATABASE_URL=<External Database URL from Render PostgreSQL service page>
SITE_URL=https://gtwog.ch
PORT=3001
```

Cloudinary keys (`CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`) are loaded automatically from the main project's `.env` — no need to duplicate them.

`DATABASE_URL` must be the **External** URL from Render's PostgreSQL service page (not the internal hostname, which is only accessible within the Render network).

### Architecture

FastAPI app (`server.py`) that bootstraps Django ORM via `django.setup()` so it can read/write the live database directly without going through the Django web server.

| File | Purpose |
|------|---------|
| `server.py` | FastAPI app, Django bootstrap, all route handlers |
| `pipeline.py` | 4-phase Claude pipeline with SSE streaming and JSON retry |
| `django_client.py` | ORM helpers: `get_categories`, `get_recent_posts`, `create_draft_post` |
| `cloudinary_client.py` | Async cover image upload to Cloudinary |
| `public/index.html` | SPA — Write tab + Reference tab |
| `public/app.js` | SSE client, phase cards, review/edit panel, save flow |
| `public/style.css` | UI styles |

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Serves `public/index.html` |
| GET | `/api/categories` | All `BlogCategory` objects |
| GET | `/api/posts` | Recent `BlogPost` list for Reference tab |
| POST | `/api/upload-image` | Upload cover image → Cloudinary, return `{public_id, secure_url}` |
| POST | `/api/generate` | **SSE stream** — runs 4-phase pipeline |
| POST | `/api/publish` | Create draft `BlogPost`, return `{id, slug, admin_url}` |
| POST | `/api/scrape-url` | Scrape reference URL → `{title, text}` |

### AI Pipeline (4 phases)

All phases stream tokens to the browser in real time via SSE. Each phase has one auto-retry on JSON parse failure.

1. **SEO Strategist** — produces keyword strategy, heading structure, internal link suggestions, meta framework
2. **Content Writer** — writes full EN article HTML using the SEO brief; injects G2G domain knowledge (fabrics, techniques, MOQ, certifications, production countries)
3. **QA Editor** — checks headings, fixes internal links to absolute `https://gtwog.ch` URLs, enforces excerpt/meta char limits, fixes B2B tone
4. **German Translator** — translates all visible text to Hochdeutsch; preserves all HTML tags, URLs, brand names, and technical acronyms

### UI Flow

**Write tab (3 steps)**
1. Enter topic, post type, category, optional reference URLs, optional cover image → Generate
2. Watch 4 phase cards stream with live progress bar
3. Edit EN + DE content inline (contenteditable) → fill meta fields → Save as Draft

**Reference tab** — table of recent posts with client-side title filter; each row links to the Django admin edit page.

Saved posts appear in Django admin at `/en/admin/homepage/blogpost/` with `is_published=False`.
