from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from .forms import (
    ContactForm,
    QuoteStep1Form, QuoteStep2Form, QuoteStep3Form,
    QuoteStep4Form, QuoteStep5Form,
)
from .models import ContactSubmission, QuoteRequest

QUOTE_STEPS = [
    ('about',   'About You',            QuoteStep1Form),
    ('order',   'The Order',            QuoteStep2Form),
    ('custom',  'Customisation',        QuoteStep3Form),
    ('country', 'Production Country',   QuoteStep4Form),
    ('extras',  'Special Requirements', QuoteStep5Form),
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
    }
    return render(request, 'homepage/index.html', context)


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Thanks! We'll be in touch within 48 hours."))
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'homepage/contact.html', {'form': form})


def quote(request, step=1):
    total_steps = len(QUOTE_STEPS)
    step = max(1, min(step, total_steps))
    step_index = step - 1
    step_slug, step_title, FormClass = QUOTE_STEPS[step_index]

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
        {'number': i + 1, 'title': s[1], 'active': i + 1 == step, 'done': i + 1 < step}
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

        _send_internal_notification(quote_obj)
        _send_customer_confirmation(quote_obj)

        return redirect('quote_success')
    except Exception as e:
        messages.error(request, "Something went wrong saving your request. Please try again. (" + str(e) + ")")
        return redirect('quote_step', step=1)


def quote_success(request):
    return render(request, 'homepage/quote_success.html')


def legal_page(request, page):
    from .models import LegalPage
    try:
        legal = LegalPage.objects.get(page=page)
    except LegalPage.DoesNotExist:
        from django.http import Http404
        raise Http404
    return render(request, 'homepage/legal.html', {'legal': legal})


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
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'production@gtwog.ch', 'changeme123')
        return HttpResponse('Superuser created - delete this view now!')
    return HttpResponse('Already exists')