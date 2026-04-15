from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _l
from .forms import (
    ContactForm,
    QuoteStep1Form, QuoteStep2Form, QuoteStep3Form,
    QuoteStep4Form, QuoteStep5Form,
)
from .models import ContactSubmission, QuoteRequest

QUOTE_STEPS = [
    ('about',   _l('About You'),            QuoteStep1Form),
    ('order',   _l('The Order'),            QuoteStep2Form),
    ('custom',  _l('Customisation'),        QuoteStep3Form),
    ('country', _l('Production Country'),   QuoteStep4Form),
    ('extras',  _l('Special Requirements'), QuoteStep5Form),
]

SESSION_KEY = 'quote_data'
GERMAN_COUNTRIES = {'DE', 'AT', 'CH', 'LI', 'LU'}


def detect_preferred_language(request):
    if request.session.get('_language'):
        return request.session['_language']
    accept = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    if accept:
        primary = accept.split(',')[0].split(';')[0].strip().lower()
        if primary.startswith('de'):
            return 'de'
        if primary.startswith('en'):
            return 'en'
    country = request.META.get('HTTP_CF_IPCOUNTRY', '').upper()
    if country in GERMAN_COUNTRIES:
        return 'de'
    return 'en'


class LocalisedSettings:
    def __init__(self, obj, is_de):
        self._obj = obj
        self._is_de = is_de

    def __getattr__(self, name):
        if self._is_de:
            de_val = getattr(self._obj, f'{name}_de', None)
            if de_val:
                return de_val
        return getattr(self._obj, name)


def homepage(request):
    from .models import SiteSettings, Service, HowItWorksStep, ClientLogo

    current_lang = getattr(request, 'LANGUAGE_CODE', 'en')
    if 'lang_redirected' not in request.session:
        request.session['lang_redirected'] = True
        preferred = detect_preferred_language(request)
        if preferred != current_lang:
            from django.utils.translation import activate
            activate(preferred)
            request.session['_language'] = preferred
            return redirect(f'/{preferred}/')

    is_de = current_lang.startswith('de')

    site_settings = SiteSettings.get()
    localised_settings = LocalisedSettings(site_settings, is_de)

    services_qs = Service.objects.filter(is_active=True)
    steps_qs = HowItWorksStep.objects.filter(is_active=True)
    clients_qs = ClientLogo.objects.filter(is_active=True)

    services = [
        {
            'img': s.image.url if s.image else None,
            'title': (s.title_de or s.title) if is_de else s.title,
            'description': (s.description_de or s.description) if is_de else s.description,
        }
        for s in services_qs
    ]

    steps = [
        {
            'number': s.number,
            'title': (s.title_de or s.title) if is_de else s.title,
            'description': (s.description_de or s.description) if is_de else s.description,
        }
        for s in steps_qs
    ]

    clients = [{'img': c.logo.url, 'name': c.name, 'url': c.url} for c in clients_qs]

    context = {
        'site_settings': localised_settings,
        'services': services,
        'steps': steps,
        'clients': clients,
        'is_de': is_de,
    }
    return render(request, 'homepage/index.html', context)


def contact(request):
    from .models import SiteSettings
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            try:
                form.save()
            except Exception as e:
                print("Contact form save failed: " + str(e))
            messages.success(request, _("Thanks! We'll be in touch within 48 hours."))
            return redirect('contact')
    else:
        form = ContactForm()
    site_settings = SiteSettings.get()
    return render(request, 'homepage/contact.html', {'form': form, 'site_settings': site_settings})


def legal_page(request, page):
    from .models import LegalPage, SiteSettings
    try:
        legal = LegalPage.objects.get(page=page)
    except LegalPage.DoesNotExist:
        from django.http import Http404
        raise Http404
    site_settings = SiteSettings.get()
    return render(request, 'homepage/legal.html', {'legal': legal, 'site_settings': site_settings})


def quote(request, step=1):
    total_steps = len(QUOTE_STEPS)
    step = max(1, min(step, total_steps))
    step_index = step - 1
    step_slug, step_title, FormClass = QUOTE_STEPS[step_index]

    step_title = str(step_title)

    current_lang = getattr(request, 'LANGUAGE_CODE', 'en')
    is_de = current_lang.startswith('de')

    if SESSION_KEY not in request.session:
        request.session[SESSION_KEY] = {}

    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            data = request.session[SESSION_KEY]
            data.update(form.cleaned_data)
            if 'product_types' in data and isinstance(data['product_types'], list):
                data['product_types'] = ','.join(data['product_types'])
            if 'production_countries' in data and isinstance(data['production_countries'], list):
                data['production_countries'] = ','.join(data['production_countries'])
            request.session[SESSION_KEY] = data
            request.session.modified = True

            if step < total_steps:
                return redirect('quote_step', step=step + 1)
            else:
                return _submit_quote(request)
    else:
        initial = request.session.get(SESSION_KEY, {})
        if 'product_types' in initial and isinstance(initial['product_types'], str):
            initial = dict(initial)
            initial['product_types'] = initial['product_types'].split(',')
        if 'production_countries' in initial and isinstance(initial['production_countries'], str):
            initial = dict(initial)
            initial['production_countries'] = initial['production_countries'].split(',')
        form = FormClass(initial=initial)

    steps_meta = [
        {
            'number': i + 1,
            'title': str(s[1]),
            'active': i + 1 == step,
            'done': i + 1 < step,
        }
        for i, s in enumerate(QUOTE_STEPS)
    ]

    return render(request, 'homepage/quote.html', {
        'form': form,
        'step': step,
        'total_steps': total_steps,
        'step_title': step_title,
        'step_slug': step_slug,
        'steps_meta': steps_meta,
        'progress': round((step / total_steps) * 100),
        'is_de': is_de,
    })


def _send_internal_notification(quote):
    from django.core.mail import send_mail
    from django.conf import settings as django_settings

    subject = "New Quote Request - " + (quote.company_name or quote.contact_name)

    lines = [
        "New quote request received via the G2G Textiles website.",
        "",
        "CONTACT DETAILS",
        "Name:        " + quote.contact_name,
        "Company:     " + (quote.company_name or "-"),
        "Role:        " + (quote.get_role_display() if quote.role else "-"),
        "Industry:    " + (quote.get_industry_display() if quote.industry else "-"),
        "Email:       " + quote.email,
        "Phone:       " + (quote.phone or "-"),
        "Website:     " + (quote.website or "-"),
        "",
        "THE ORDER",
        "Products:        " + quote.product_types,
        "Styles:          " + str(quote.num_styles),
        "Quantity/Style:  " + quote.get_quantity_per_style_display(),
        "",
        "CUSTOMISATION",
        "Brand Colours:   " + (quote.brand_colours or "-"),
        "Print Method:    " + quote.get_print_method_display(),
        "Print Positions: " + quote.get_print_positions_display(),
        "Has Logo:        " + ("Yes" if quote.has_logo else "No"),
        "Design Files:    " + quote.get_design_files_status_display(),
        "Pantone Match:   " + ("Yes" if quote.pantone_matching else "No"),
        "Notes:           " + (quote.customisation_notes or "-"),
        "",
        "SPECIAL REQUIREMENTS",
        "Sustainability:    " + quote.get_sustainability_display(),
        "Certifications:    " + (quote.certifications_needed or "-"),
        "Existing Supplier: " + ("Yes" if quote.existing_supplier else "No"),
        "Supplier Notes:    " + (quote.existing_supplier_notes or "-"),
        "Heard About Us:    " + (quote.heard_about_us or "-"),
        "Additional Notes:  " + (quote.additional_notes or "-"),
        "",
        "Submitted: " + quote.submitted_at.strftime("%d %b %Y at %H:%M") + " UTC",
    ]
    body = "\n".join(lines)

    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[django_settings.QUOTE_NOTIFICATION_EMAIL],
            fail_silently=False,
        )
    except Exception as e:
        print("Failed to send internal notification: " + str(e))


def _send_customer_confirmation(quote):
    from django.core.mail import send_mail
    from django.conf import settings as django_settings

    first_name = quote.contact_name.split()[0] if quote.contact_name else "there"
    subject = "Your Quote Request - G2G Textiles"

    lines = [
        "Hi " + first_name + ",",
        "",
        "Thank you for reaching out to G2G Textiles. We have received your quote request and will get back to you within 48 hours with a tailored proposal.",
        "",
        "Here is a summary of what you submitted:",
        "",
        "Products:  " + quote.product_types,
        "Quantity:  " + quote.get_quantity_per_style_display() + " per style (" + str(quote.num_styles) + " style" + ("s" if quote.num_styles > 1 else "") + ")",
        "",
        "If you have any questions in the meantime, feel free to reply to this email or reach us at production@gtwog.ch.",
        "",
        "We look forward to working with you.",
        "",
        "Best regards,",
        "The G2G Textiles Team",
        "",
        "---",
        "G2G Textiles | production@gtwog.ch",
    ]
    body = "\n".join(lines)

    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[quote.email],
            fail_silently=False,
        )
    except Exception as e:
        print("Failed to send customer confirmation: " + str(e))


def _submit_quote(request):
    data = request.session.get(SESSION_KEY, {})
    try:
        for bool_field in ['has_logo', 'pantone_matching', 'existing_supplier']:
            data[bool_field] = bool(data.get(bool_field, False))

        allowed = {f.name for f in QuoteRequest._meta.get_fields()}
        clean = {k: v for k, v in data.items() if k in allowed}
        quote_obj = QuoteRequest.objects.create(**clean)
        del request.session[SESSION_KEY]

        try:
            _send_internal_notification(quote_obj)
        except Exception as e:
            print("Internal notification failed: " + str(e))

        try:
            _send_customer_confirmation(quote_obj)
        except Exception as e:
            print("Customer confirmation failed: " + str(e))

        return redirect('quote_success')
    except Exception as e:
        messages.error(request, "Something went wrong saving your request. Please try again. (" + str(e) + ")")
        return redirect('quote_step', step=1)


def quote_success(request):
    return render(request, 'homepage/quote_success.html')


def translation_test(request):
    from django.http import HttpResponse
    from django.utils.translation import gettext as _
    import os
    locale_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'locale', 'de', 'LC_MESSAGES')
    files = os.listdir(locale_path) if os.path.exists(locale_path) else ['NOT FOUND']
    result = f"Files: {files} | Services in DE: {_('Services')} | LANG: {request.LANGUAGE_CODE}"
    return HttpResponse(result)


def create_super(request):
    from django.http import HttpResponse
    from django.contrib.auth.models import User
    import os
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
    if not password:
        return HttpResponse('No password set in environment variables')
    if User.objects.filter(username=username).exists():
        u = User.objects.get(username=username)
        u.set_password(password)
        u.is_superuser = True
        u.is_staff = True
        u.save()
        return HttpResponse('Password reset successfully')
    User.objects.create_superuser(username, email, password)
    return HttpResponse('Superuser created successfully')


def migration_status(request):
    from django.http import HttpResponse
    from django.db import connection
    from homepage.models import SiteSettings
    cursor = connection.cursor()
    cursor.execute("SELECT app, name FROM django_migrations WHERE app='homepage' ORDER BY name")
    rows = cursor.fetchall()
    migrations = "\n".join([f"{r[0]} - {r[1]}" for r in rows])
    all_fields = [f.name for f in SiteSettings._meta.get_fields()]
    de_fields = [f for f in all_fields if '_de' in f]
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='homepage_sitesettings' AND column_name LIKE '%_de%'")
    db_columns = [r[0] for r in cursor.fetchall()]
    result = f"MIGRATIONS:\n{migrations}\n\nMODEL DE FIELDS:\n{chr(10).join(de_fields) or 'NONE'}\n\nDB COLUMNS:\n{chr(10).join(db_columns) or 'NONE'}"
    return HttpResponse(result, content_type='text/plain')


def blog_list(request):
    from .models import BlogPost, BlogCategory
    category_slug = request.GET.get('category', '')
    categories = BlogCategory.objects.all()
    posts = BlogPost.objects.filter(is_published=True)
    if category_slug:
        posts = posts.filter(category__slug=category_slug)
    return render(request, 'homepage/blog_list.html', {
        'posts': posts,
        'categories': categories,
        'active_category': category_slug,
    })


def blog_detail(request, slug):
    from .models import BlogPost
    from django.http import Http404
    try:
        post = BlogPost.objects.get(slug=slug, is_published=True)
    except BlogPost.DoesNotExist:
        raise Http404
    is_de = getattr(request, 'LANGUAGE_CODE', 'en').startswith('de')
    return render(request, 'homepage/blog_detail.html', {
        'post': post,
        'is_de': is_de,
    })

def test_email(request):
    from django.http import HttpResponse
    from django.core.mail import send_mail
    from django.conf import settings as django_settings
    try:
        send_mail(
            subject='G2G Test Email',
            message='This is a test email from G2G Textiles.',
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[django_settings.QUOTE_NOTIFICATION_EMAIL],
            fail_silently=False,
        )
        return HttpResponse('Email sent successfully!')
    except Exception as e:
        return HttpResponse('Email failed: ' + str(e))