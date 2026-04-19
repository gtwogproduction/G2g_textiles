from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import Http404
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _l
from .forms import (
    ContactForm,
    QuoteStep1Form, QuoteStep2Form, QuoteStep3Form,
    QuoteStep4Form, QuoteStep5Form,
    StatusUpdateForm, FactoryAssignForm,
)
from .models import ContactSubmission, QuoteRequest, OrderStatusUpdate

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
    try:
        post = BlogPost.objects.get(slug=slug, is_published=True)
    except BlogPost.DoesNotExist:
        raise Http404
    is_de = getattr(request, 'LANGUAGE_CODE', 'en').startswith('de')
    return render(request, 'homepage/blog_detail.html', {
        'post': post,
        'is_de': is_de,
    })


# ---------------------------------------------------------------------------
# Portal helpers
# ---------------------------------------------------------------------------

def _is_g2g_staff(user):
    return user.groups.filter(name='g2g_staff').exists()


def _is_factory_user(user):
    return user.groups.filter(name='factory').exists()


def _send_status_notification(quote, update):
    if not quote.customer or not quote.customer.email:
        return
    from django.core.mail import send_mail
    from django.conf import settings as django_settings

    first_name = (
        quote.customer.first_name
        or (quote.contact_name.split()[0] if quote.contact_name else 'there')
    )
    subject = f"Order Update: {update.get_status_display()} — G2G Textiles"
    lines = [
        f"Hi {first_name},",
        "",
        f"There is a new update on your order for {quote.company_name or quote.contact_name}.",
        "",
        f"Status: {update.get_status_display()}",
        f"Date:   {update.created_at.strftime('%d %b %Y')}",
    ]
    if update.note:
        lines += ["", "Note from production:", update.note]
    lines += [
        "",
        "Log in to your portal to view your full order history:",
        "https://gtwog.ch/en/portal/customer/" + str(quote.pk) + "/",
        "",
        "Best regards,",
        "The G2G Textiles Team",
        "production@gtwog.ch",
    ]
    try:
        send_mail(
            subject=subject,
            message="\n".join(lines),
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[quote.customer.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send status notification: {e}")


# ---------------------------------------------------------------------------
# Portal views
# ---------------------------------------------------------------------------

def portal_login(request):
    if request.user.is_authenticated:
        return redirect('portal_home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            return redirect(request.GET.get('next', '') or 'portal_home')
    else:
        form = AuthenticationForm()
    return render(request, 'homepage/portal/login.html', {'form': form})


def portal_logout(request):
    auth_logout(request)
    return redirect('portal_login')


@login_required
def portal_home(request):
    if _is_g2g_staff(request.user):
        return redirect('staff_dashboard')
    if _is_factory_user(request.user):
        return redirect('factory_dashboard')
    return redirect('customer_dashboard')


@login_required
def customer_dashboard(request):
    if _is_g2g_staff(request.user) or _is_factory_user(request.user):
        return redirect('portal_home')
    quotes = QuoteRequest.objects.filter(customer=request.user)
    return render(request, 'homepage/portal/customer_dashboard.html', {'quotes': quotes})


@login_required
def customer_order(request, pk):
    if _is_g2g_staff(request.user) or _is_factory_user(request.user):
        return redirect('portal_home')
    try:
        quote = QuoteRequest.objects.get(pk=pk, customer=request.user)
    except QuoteRequest.DoesNotExist:
        raise Http404
    updates = quote.status_updates.all()
    return render(request, 'homepage/portal/customer_order.html', {
        'quote': quote,
        'updates': updates,
    })


@login_required
def staff_dashboard(request):
    if not _is_g2g_staff(request.user):
        return redirect('portal_home')
    quotes = QuoteRequest.objects.all().order_by('-submitted_at')
    return render(request, 'homepage/portal/staff_dashboard.html', {'quotes': quotes})


@login_required
def staff_order(request, pk):
    if not _is_g2g_staff(request.user):
        return redirect('portal_home')
    try:
        quote = QuoteRequest.objects.get(pk=pk)
    except QuoteRequest.DoesNotExist:
        raise Http404

    update_form = StatusUpdateForm()
    assign_form = FactoryAssignForm(initial={'factory': quote.assigned_factory})

    if request.method == 'POST':
        if 'post_update' in request.POST:
            update_form = StatusUpdateForm(request.POST, request.FILES)
            if update_form.is_valid():
                upd = OrderStatusUpdate.objects.create(
                    quote_request=quote,
                    status=update_form.cleaned_data['status'],
                    note=update_form.cleaned_data['note'],
                    attachment=update_form.cleaned_data.get('attachment'),
                    created_by=request.user,
                )
                _send_status_notification(quote, upd)
                messages.success(request, _('Status update posted.'))
                return redirect('staff_order', pk=pk)
        elif 'assign_factory' in request.POST:
            assign_form = FactoryAssignForm(request.POST)
            if assign_form.is_valid():
                quote.assigned_factory = assign_form.cleaned_data['factory']
                quote.save(update_fields=['assigned_factory'])
                messages.success(request, _('Factory assigned.'))
                return redirect('staff_order', pk=pk)

    updates = quote.status_updates.all()
    return render(request, 'homepage/portal/staff_order.html', {
        'quote': quote,
        'updates': updates,
        'update_form': update_form,
        'assign_form': assign_form,
    })


@login_required
def factory_dashboard(request):
    if not _is_factory_user(request.user):
        return redirect('portal_home')
    quotes = QuoteRequest.objects.filter(assigned_factory=request.user).order_by('-submitted_at')
    return render(request, 'homepage/portal/factory_dashboard.html', {'quotes': quotes})


@login_required
def factory_order(request, pk):
    if not _is_factory_user(request.user):
        return redirect('portal_home')
    try:
        quote = QuoteRequest.objects.get(pk=pk, assigned_factory=request.user)
    except QuoteRequest.DoesNotExist:
        raise Http404

    update_form = StatusUpdateForm()

    if request.method == 'POST':
        update_form = StatusUpdateForm(request.POST, request.FILES)
        if update_form.is_valid():
            upd = OrderStatusUpdate.objects.create(
                quote_request=quote,
                status=update_form.cleaned_data['status'],
                note=update_form.cleaned_data['note'],
                attachment=update_form.cleaned_data.get('attachment'),
                created_by=request.user,
            )
            _send_status_notification(quote, upd)
            messages.success(request, _('Status update posted.'))
            return redirect('factory_order', pk=pk)

    updates = quote.status_updates.all()
    return render(request, 'homepage/portal/factory_order.html', {
        'quote': quote,
        'updates': updates,
        'update_form': update_form,
    })