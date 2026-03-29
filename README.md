# G2G Textiles — Homepage

A Django homepage + quote wizard for G2G Textiles B2B clothing service.

## Quick Start

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations
python manage.py migrate

# 4. Create a superuser (to view submissions in admin)
python manage.py createsuperuser

# 5. Run the development server
python manage.py runserver
```

- Homepage: http://127.0.0.1:8000
- Quote Wizard: http://127.0.0.1:8000/quote/
- Admin: http://127.0.0.1:8000/admin

## Project Structure

```
g2g_textiles/
├── g2g_textiles/          # Project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── homepage/              # Main app
│   ├── templates/homepage/
│   │   ├── index.html         # Homepage
│   │   ├── quote.html         # Quote wizard (6 steps)
│   │   └── quote_success.html # Confirmation page
│   ├── static/homepage/
│   │   ├── css/style.css      # Global styles
│   │   ├── css/quote.css      # Quote wizard styles
│   │   ├── js/main.js         # Homepage JS
│   │   └── js/quote.js        # Wizard JS (conditional fields, animations)
│   ├── models.py      # ContactSubmission + QuoteRequest
│   ├── forms.py       # ContactForm + 6x QuoteStep forms
│   ├── views.py       # homepage, contact, quote wizard, success
│   ├── urls.py
│   └── admin.py       # Full admin with fieldsets + status management
├── manage.py
└── requirements.txt
```

## Quote Wizard — 6 Steps

| Step | Title | Key Fields |
|------|-------|------------|
| 1 | About You | Company, industry, contact, role, email |
| 2 | The Order | Products, quantity, styles, sizing |
| 3 | Customisation | Colours, print method, positions, design files |
| 4 | Timeline & Delivery | Deadline, samples, delivery location |
| 5 | Budget | Budget range (CHF) |
| 6 | Special Requirements | Sustainability, certifications, notes |

All quote submissions are saved to the database and visible in Django Admin with status management (New → Reviewing → Quoted → Won/Lost).
