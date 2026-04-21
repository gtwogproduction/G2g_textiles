from decimal import Decimal

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import Http404, JsonResponse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _l
from .forms import (
    ContactForm,
    QuoteStep1Form, QuoteStep2Form, QuoteStep3Form,
    QuoteStep4Form, QuoteStep5Form,
    StatusUpdateForm, FactoryAssignForm, LinkCustomerForm,
    QuoteHeaderForm, QuoteLineItemFormSet,
)
from .models import ContactSubmission, QuoteRequest, OrderStatusUpdate, Quote, QuoteLineItem, QuoteSignature, DesignFile

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


STATUS_ORDER = [
    'quote_received', 'in_review', 'quote_sent', 'sampling',
    'sample_approved', 'in_production', 'quality_check', 'shipped', 'delivered',
]


def _next_update_status(quote):
    """Return the next status key that hasn't been used in a normal 'update', or None if all done."""
    used = set(quote.status_updates.filter(update_type='update').values_list('status', flat=True))
    for s in STATUS_ORDER:
        if s not in used:
            return s
    return None


def _latest_update_status(quote):
    """Return the most recent status key posted as a normal 'update', or None."""
    last = quote.status_updates.filter(update_type='update').order_by('created_at').last()
    return last.status if last else None


def _is_customer(user):
    return not user.groups.exists()


_QTY_MIDPOINTS = {
    '50-100':    75,
    '100-250':   175,
    '250-500':   375,
    '500-1000':  750,
    '1000-5000': 3000,
    '5000+':     5000,
}


def _midpoint_of_qty_band(band):
    return _QTY_MIDPOINTS.get(band, 100)


_STATUS_BADGE_COLOURS = {
    'quote_received':  ('rgba(0,0,0,0.06)',      '#6b6760'),
    'in_review':       ('rgba(180,130,0,0.12)',   '#6b4e00'),
    'quote_sent':      ('rgba(180,130,0,0.12)',   '#6b4e00'),
    'sampling':        ('rgba(0,80,180,0.10)',    '#003580'),
    'sample_approved': ('rgba(40,120,80,0.12)',   '#1e5c3a'),
    'in_production':   ('rgba(0,80,180,0.10)',    '#003580'),
    'quality_check':   ('rgba(180,130,0,0.12)',   '#6b4e00'),
    'shipped':         ('rgba(40,120,80,0.12)',   '#1e5c3a'),
    'delivered':       ('rgba(40,120,80,0.18)',   '#174d30'),
}


def _build_status_notification_html(first_name, order_name, status_label, status_key,
                                     date_str, note, portal_url,
                                     update_type='update', tracking_number='', tracking_url=''):
    bg, fg = _STATUS_BADGE_COLOURS.get(status_key, ('rgba(0,0,0,0.06)', '#6b6760'))

    is_issue = (update_type == 'issue')
    header_colour = '#b87a00' if is_issue else '#1a1a1a'
    intro_text = (
        'There is an issue or delay on your order for'
        if is_issue else
        'There is a new update on your order for'
    )
    note_label = 'What happened' if is_issue else 'Note from production'

    note_block = ""
    if note:
        border_colour = '#b87a00' if is_issue else '#1a1a1a'
        note_block = f"""
        <tr><td style="padding:0 40px 24px">
          <div style="background:#f5f2ee;border-left:3px solid {border_colour};padding:14px 18px;
                      border-radius:0 4px 4px 0;font-size:14px;line-height:1.6;color:#1a1a1a">
            <div style="font-size:11px;font-weight:600;letter-spacing:0.08em;
                        text-transform:uppercase;color:#6b6760;margin-bottom:6px">
              {note_label}
            </div>
            {note}
          </div>
        </td></tr>"""

    tracking_block = ""
    if tracking_url:
        tn_text = f'<div style="margin-top:8px;font-size:12px;color:#6b6760">Tracking number: {tracking_number}</div>' if tracking_number else ''
        tracking_block = f"""
      <tr><td style="padding:0 40px 24px">
        <div style="background:#f0f7f2;border-left:3px solid #1e5c3a;padding:14px 18px;
                    border-radius:0 4px 4px 0">
          <div style="font-size:11px;font-weight:600;letter-spacing:0.08em;
                      text-transform:uppercase;color:#6b6760;margin-bottom:8px">
            Shipment tracking
          </div>
          <a href="{tracking_url}"
             style="display:inline-block;background:#1e5c3a;color:#ffffff;
                    font-size:13px;font-weight:600;letter-spacing:0.04em;
                    text-decoration:none;padding:10px 20px;border-radius:4px">
            Track your shipment &rarr;
          </a>
          {tn_text}
        </div>
      </td></tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Order Update</title>
</head>
<body style="margin:0;padding:0;background:#edeae4;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif">

<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#edeae4;padding:40px 20px">
<tr><td align="center">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:580px">

  <!-- Logo header -->
  <tr><td style="background:{header_colour};padding:24px 40px;border-radius:4px 4px 0 0">
    <span style="font-family:Arial,sans-serif;font-size:20px;font-weight:900;
                 letter-spacing:0.18em;text-transform:uppercase;color:#f5f2ee;
                 text-decoration:none">
      G2G <span style="opacity:0.55">TEXTILES</span>
    </span>
  </td></tr>

  <!-- Body card -->
  <tr><td style="background:#ffffff;border-radius:0 0 4px 4px;overflow:hidden">
    <table width="100%" cellpadding="0" cellspacing="0" border="0">

      <!-- Greeting -->
      <tr><td style="padding:36px 40px 8px">
        <p style="margin:0;font-size:22px;font-weight:600;color:#1a1a1a;line-height:1.2">
          Hi {first_name},
        </p>
      </td></tr>

      <!-- Intro -->
      <tr><td style="padding:12px 40px 24px">
        <p style="margin:0;font-size:15px;color:#6b6760;line-height:1.6">
          {intro_text}
          <strong style="color:#1a1a1a">{order_name}</strong>.
        </p>
      </td></tr>

      <!-- Status + date row -->
      <tr><td style="padding:0 40px 28px">
        <table cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td style="padding-right:20px">
              <div style="font-size:11px;font-weight:600;letter-spacing:0.08em;
                          text-transform:uppercase;color:#6b6760;margin-bottom:6px">Status</div>
              <span style="display:inline-block;background:{bg};color:{fg};
                           font-size:11px;font-weight:700;letter-spacing:0.06em;
                           text-transform:uppercase;padding:4px 10px;border-radius:2px">
                {status_label}
              </span>
            </td>
            <td>
              <div style="font-size:11px;font-weight:600;letter-spacing:0.08em;
                          text-transform:uppercase;color:#6b6760;margin-bottom:6px">Date</div>
              <span style="font-size:14px;color:#1a1a1a">{date_str}</span>
            </td>
          </tr>
        </table>
      </td></tr>

      <!-- Optional note -->
      {note_block}

      <!-- Optional tracking -->
      {tracking_block}

      <!-- Divider -->
      <tr><td style="padding:0 40px">
        <div style="border-top:1px solid rgba(0,0,0,0.08)"></div>
      </td></tr>

      <!-- CTA -->
      <tr><td style="padding:28px 40px 36px">
        <p style="margin:0 0 18px;font-size:14px;color:#6b6760;line-height:1.6">
          Log in to your portal to view the full timeline for this order.
        </p>
        <a href="{portal_url}"
           style="display:inline-block;background:#1a1a1a;color:#ffffff;
                  font-size:13px;font-weight:600;letter-spacing:0.04em;
                  text-decoration:none;padding:12px 24px;border-radius:4px">
          View Order Status &rarr;
        </a>
      </td></tr>

    </table>
  </td></tr>

  <!-- Footer -->
  <tr><td style="padding:24px 0 0;text-align:center">
    <p style="margin:0;font-size:12px;color:#6b6760;line-height:1.8">
      G2G Textiles &nbsp;&middot;&nbsp; production@gtwog.ch
    </p>
  </td></tr>

</table>
</td></tr>
</table>

</body>
</html>"""


def _send_status_notification(quote, update):
    if not quote.customer or not quote.customer.email:
        return
    if not quote.notify_on_updates:
        return
    from django.core.mail import send_mail
    from django.conf import settings as django_settings

    first_name = (
        quote.customer.first_name
        or (quote.contact_name.split()[0] if quote.contact_name else 'there')
    )
    order_name = quote.company_name or quote.contact_name
    portal_url = "https://gtwog.ch/en/portal/customer/" + str(quote.pk) + "/"
    status_label = update.get_status_display()
    date_str = update.created_at.strftime('%d %b %Y')
    is_issue = (update.update_type == 'issue')
    subject = (
        f"\u26a0 Delay on your order \u2014 G2G Textiles"
        if is_issue else
        f"Order Update: {status_label} \u2014 G2G Textiles"
    )

    note_label = "What happened" if is_issue else "Note from production"
    intro_text = (
        "There is an issue or delay on your order for"
        if is_issue else
        "There is a new update on your order for"
    )

    plain = (
        f"Hi {first_name},\n\n"
        f"{intro_text} {order_name}.\n\n"
        f"Status: {status_label}\n"
        f"Date:   {date_str}\n"
        + (f"\n{note_label}:\n{update.note}\n" if update.note else "")
        + (f"\nTrack your shipment: {update.tracking_url}\n" if update.tracking_url else "")
        + f"\nView your order: {portal_url}\n\n"
        f"Best regards,\nThe G2G Textiles Team\nproduction@gtwog.ch"
    )

    html = _build_status_notification_html(
        first_name=first_name,
        order_name=order_name,
        status_label=status_label,
        status_key=update.status,
        date_str=date_str,
        note=update.note,
        portal_url=portal_url,
        update_type=update.update_type,
        tracking_number=update.tracking_number,
        tracking_url=update.tracking_url,
    )

    try:
        send_mail(
            subject=subject,
            message=plain,
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[quote.customer.email],
            html_message=html,
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send status notification: {e}")


def _build_quote_notification_html(first_name, order_name, quote_number,
                                    line_items, total, currency,
                                    valid_until_str, notes_customer, portal_url,
                                    email_body='', tech_pack_url=''):
    rows = ""
    for item in line_items:
        disc = f" (–{item.discount_pct}%)" if item.discount_pct else ""
        rows += f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #edeae4;font-size:13px;color:#1a1a1a">{item.description}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #edeae4;font-size:13px;color:#6b6760;text-align:center">{item.quantity}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #edeae4;font-size:13px;color:#6b6760;text-align:right">{currency} {item.unit_price}{disc}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #edeae4;font-size:13px;font-weight:500;color:#1a1a1a;text-align:right">{currency} {item.subtotal}</td>
        </tr>"""

    notes_block = ""
    if notes_customer:
        notes_block = f"""
      <tr><td style="padding:0 40px 24px">
        <div style="background:#f5f2ee;border-left:3px solid #1a1a1a;padding:14px 18px;
                    border-radius:0 4px 4px 0;font-size:14px;line-height:1.6;color:#1a1a1a">
          <div style="font-size:11px;font-weight:600;letter-spacing:0.08em;
                      text-transform:uppercase;color:#6b6760;margin-bottom:6px">Note</div>
          {notes_customer}
        </div>
      </td></tr>"""

    valid_block = f'<span style="font-size:13px;color:#6b6760">Valid until: <strong style="color:#1a1a1a">{valid_until_str}</strong></span>' if valid_until_str else ""

    import html as _html
    email_body_html = "<br>".join(
        f'<span style="display:block;margin-bottom:8px">{_html.escape(para)}</span>'
        for para in (email_body or '').strip().split('\n\n')
        if para.strip()
    ) or 'Please find your proforma invoice below.'

    tech_pack_block = ""
    if tech_pack_url:
        tech_pack_block = f"""
      <tr><td style="padding:0 40px 24px">
        <div style="background:#f5f2ee;border-left:3px solid #1a1a1a;padding:14px 18px;
                    border-radius:0 4px 4px 0">
          <div style="font-size:11px;font-weight:600;letter-spacing:0.08em;
                      text-transform:uppercase;color:#6b6760;margin-bottom:8px">
            Tech Pack Template
          </div>
          <p style="margin:0 0 10px;font-size:13px;color:#6b6760;line-height:1.5">
            Please fill in the template below for each style and send it back with your order confirmation.
          </p>
          <a href="{tech_pack_url}"
             style="display:inline-block;background:#1a1a1a;color:#ffffff;
                    font-size:13px;font-weight:600;letter-spacing:0.04em;
                    text-decoration:none;padding:10px 20px;border-radius:4px">
            Download Tech Pack Template &darr;
          </a>
        </div>
      </td></tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Proforma Invoice</title>
</head>
<body style="margin:0;padding:0;background:#edeae4;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#edeae4;padding:40px 20px">
<tr><td align="center">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:600px">
  <tr><td style="background:#1a1a1a;padding:24px 40px;border-radius:4px 4px 0 0">
    <span style="font-family:Arial,sans-serif;font-size:20px;font-weight:900;
                 letter-spacing:0.18em;text-transform:uppercase;color:#f5f2ee">
      G2G <span style="opacity:0.55">TEXTILES</span>
    </span>
  </td></tr>
  <tr><td style="background:#ffffff;border-radius:0 0 4px 4px;overflow:hidden">
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
      <tr><td style="padding:36px 40px 8px">
        <p style="margin:0;font-size:22px;font-weight:600;color:#1a1a1a">Hi {first_name},</p>
      </td></tr>
      <tr><td style="padding:12px 40px 4px">
        <p style="margin:0;font-size:15px;color:#6b6760;line-height:1.6">
          {email_body_html}
        </p>
      </td></tr>
      <tr><td style="padding:8px 40px 4px">
        <p style="margin:0;font-size:13px;color:#6b6760;line-height:1.5">
          Proforma Invoice for <strong style="color:#1a1a1a">{order_name}</strong> &mdash; Ref: <strong style="color:#1a1a1a">{quote_number}</strong>
        </p>
      </td></tr>
      <tr><td style="padding:8px 40px 28px">
        <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #edeae4;border-radius:4px;overflow:hidden">
          <thead>
            <tr style="background:#f5f2ee">
              <th style="padding:8px 12px;font-size:11px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:#6b6760;text-align:left">Item</th>
              <th style="padding:8px 12px;font-size:11px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:#6b6760;text-align:center">Qty</th>
              <th style="padding:8px 12px;font-size:11px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:#6b6760;text-align:right">Unit Price</th>
              <th style="padding:8px 12px;font-size:11px;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;color:#6b6760;text-align:right">Subtotal</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
          <tfoot>
            <tr style="background:#f5f2ee">
              <td colspan="3" style="padding:10px 12px;font-size:13px;font-weight:600;color:#1a1a1a;text-align:right">Total</td>
              <td style="padding:10px 12px;font-size:14px;font-weight:700;color:#1a1a1a;text-align:right">{currency} {total}</td>
            </tr>
          </tfoot>
        </table>
      </td></tr>
      {notes_block}
      {tech_pack_block}
      <tr><td style="padding:0 40px">
        <div style="border-top:1px solid rgba(0,0,0,0.08)"></div>
      </td></tr>
      <tr><td style="padding:28px 40px 8px">{valid_block}</td></tr>
      <tr><td style="padding:12px 40px 36px">
        <p style="margin:0 0 18px;font-size:14px;color:#6b6760;line-height:1.6">
          Log in to your portal to view the full invoice details.
        </p>
        <a href="{portal_url}"
           style="display:inline-block;background:#1a1a1a;color:#ffffff;
                  font-size:13px;font-weight:600;letter-spacing:0.04em;
                  text-decoration:none;padding:12px 24px;border-radius:4px">
          View Proforma Invoice &rarr;
        </a>
      </td></tr>
    </table>
  </td></tr>
  <tr><td style="padding:24px 0 0;text-align:center">
    <p style="margin:0;font-size:12px;color:#6b6760;line-height:1.8">
      G2G Textiles &nbsp;&middot;&nbsp; production@gtwog.ch
    </p>
  </td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


DEFAULT_PROFORMA_EMAIL_BODY = (
    "Dear {first_name},\n\n"
    "Thank you for your interest in G2G Textiles. Please find your proforma invoice below — "
    "this outlines an estimate of what your order will cost based on the details you provided.\n\n"
    "If you are happy with this quote and would like to proceed, please get in touch with us at "
    "production@gtwog.ch referencing your invoice number. To move into production we will need "
    "a completed tech pack for each style. Please find our standard tech pack template attached — "
    "fill it in and send it back along with your confirmation.\n\n"
    "If you have any questions or would like to adjust anything, don't hesitate to reach out. "
    "We look forward to working with you.\n\n"
    "Kind regards,\nThe G2G Textiles Team\nproduction@gtwog.ch"
)


def _send_quote_notification(quote, email_body=''):
    if not quote.quote_request.customer or not quote.quote_request.customer.email:
        return
    from django.core.mail import send_mail
    from django.conf import settings as django_settings

    qr = quote.quote_request
    first_name = (
        qr.customer.first_name
        or (qr.contact_name.split()[0] if qr.contact_name else 'there')
    )
    if not email_body:
        email_body = DEFAULT_PROFORMA_EMAIL_BODY.format(first_name=first_name)
    order_name = qr.company_name or qr.contact_name
    portal_url = f"https://gtwog.ch/en/portal/customer/{qr.pk}/quote/"
    line_items = list(quote.line_items.all())
    valid_str = quote.valid_until.strftime('%d %b %Y') if quote.valid_until else ''

    from .models import SiteSettings
    try:
        tech_pack_url = SiteSettings.objects.first().tech_pack_template.url if SiteSettings.objects.exists() and SiteSettings.objects.first().tech_pack_template else ''
    except Exception:
        tech_pack_url = ''

    subject = f"Proforma Invoice {quote.quote_number} — G2G Textiles"
    plain = (
        f"Hi {first_name},\n\n"
        f"{email_body}\n\n"
        f"Proforma Invoice {quote.quote_number} for {order_name}:\n\n"
        + "\n".join(
            f"- {item.description}: {item.quantity} × {quote.currency} {item.unit_price} = {quote.currency} {item.subtotal}"
            for item in line_items
        )
        + f"\n\nTotal: {quote.currency} {quote.total}"
        + (f"\nValid until: {valid_str}" if valid_str else "")
        + (f"\n\n{quote.notes_customer}" if quote.notes_customer else "")
        + (f"\n\nDownload tech pack template: {tech_pack_url}" if tech_pack_url else "")
        + f"\n\nView invoice: {portal_url}\n\nBest regards,\nThe G2G Textiles Team\nproduction@gtwog.ch"
    )
    html = _build_quote_notification_html(
        first_name=first_name,
        order_name=order_name,
        quote_number=quote.quote_number,
        line_items=line_items,
        total=quote.total,
        currency=quote.currency,
        valid_until_str=valid_str,
        notes_customer=quote.notes_customer,
        portal_url=portal_url,
        email_body=email_body,
        tech_pack_url=tech_pack_url,
    )
    try:
        send_mail(
            subject=subject,
            message=plain,
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[qr.customer.email],
            html_message=html,
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send quote notification: {e}")


def _send_quote_accepted_notification(quote):
    from django.core.mail import send_mail
    from django.conf import settings as django_settings

    qr = quote.quote_request
    customer_name = (
        (qr.customer.get_full_name() or qr.customer.username)
        if qr.customer else (qr.contact_name or 'Unknown')
    )
    admin_url = f"/en/admin/homepage/quote/{quote.pk}/change/"
    subject = f"Quote {quote.quote_number} accepted — {qr.company_name}"
    plain = (
        f"Quote {quote.quote_number} has been accepted by the customer.\n\n"
        f"Company:  {qr.company_name}\n"
        f"Customer: {customer_name}\n\n"
        f"View in admin: https://gtwog.ch{admin_url}"
    )
    try:
        send_mail(
            subject=subject,
            message=plain,
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            recipient_list=[django_settings.QUOTE_NOTIFICATION_EMAIL],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Failed to send quote accepted notification: {e}")


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
def customer_order_notifications(request, pk):
    if _is_g2g_staff(request.user) or _is_factory_user(request.user):
        return redirect('portal_home')
    if request.method != 'POST':
        return redirect('customer_order', pk=pk)
    try:
        quote = QuoteRequest.objects.get(pk=pk, customer=request.user)
    except QuoteRequest.DoesNotExist:
        raise Http404
    quote.notify_on_updates = not quote.notify_on_updates
    quote.save(update_fields=['notify_on_updates'])
    if quote.notify_on_updates:
        messages.success(request, _('Email notifications turned on.'))
    else:
        messages.success(request, _('Email notifications turned off.'))
    return redirect('customer_order', pk=pk)


@login_required
def customer_upload_design_file(request, pk):
    if not _is_customer(request.user):
        return redirect('portal_home')
    if request.method != 'POST':
        return redirect('customer_order', pk=pk)
    try:
        qr = QuoteRequest.objects.get(pk=pk, customer=request.user)
    except QuoteRequest.DoesNotExist:
        raise Http404
    f = request.FILES.get('design_file')
    if not f:
        messages.error(request, _('Please select a file to upload.'))
        return redirect('customer_order', pk=pk)
    DesignFile.objects.create(
        quote_request=qr,
        file=f,
        original_name=f.name,
        uploaded_by=request.user,
    )
    messages.success(request, _('Design file uploaded successfully.'))
    return redirect('customer_order', pk=pk)


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

    _status_labels = dict(OrderStatusUpdate.STATUS_CHOICES)
    next_status_key = _next_update_status(quote)
    current_status_key = _latest_update_status(quote) or STATUS_ORDER[0]
    pipeline_complete = next_status_key is None

    update_form = StatusUpdateForm()
    assign_form = FactoryAssignForm(initial={'factory': quote.assigned_factory})
    link_customer_form = LinkCustomerForm(initial={'customer': quote.customer})

    if request.method == 'POST':
        if 'post_update' in request.POST:
            update_form = StatusUpdateForm(request.POST, request.FILES)
            if update_form.is_valid():
                utype = update_form.cleaned_data['update_type']
                if utype == 'update':
                    if pipeline_complete:
                        messages.error(request, _('All status stages have been posted.'))
                        return redirect('staff_order', pk=pk)
                    enforced_status = next_status_key
                else:
                    enforced_status = current_status_key
                # Tracking only allowed for shipped updates
                tracking_number = update_form.cleaned_data.get('tracking_number', '')
                tracking_url = update_form.cleaned_data.get('tracking_url', '')
                if enforced_status != 'shipped' or utype != 'update':
                    tracking_number = ''
                    tracking_url = ''
                upd = OrderStatusUpdate.objects.create(
                    quote_request=quote,
                    status=enforced_status,
                    update_type=utype,
                    note=update_form.cleaned_data['note'],
                    attachment=update_form.cleaned_data.get('attachment'),
                    tracking_number=tracking_number,
                    tracking_url=tracking_url,
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
        elif 'toggle_payment' in request.POST:
            quote.payment_confirmed = not quote.payment_confirmed
            quote.save(update_fields=['payment_confirmed'])
            if quote.payment_confirmed:
                messages.success(request, _('Payment confirmed. Factory can now see this order.'))
            else:
                messages.success(request, _('Payment confirmation removed.'))
            return redirect('staff_order', pk=pk)
        elif request.POST.get('action') == 'link_customer':
            link_customer_form = LinkCustomerForm(request.POST)
            if link_customer_form.is_valid():
                quote.customer = link_customer_form.cleaned_data['customer']
                quote.save(update_fields=['customer'])
                if quote.customer:
                    messages.success(request, _('Customer account linked.'))
                else:
                    messages.success(request, _('Customer account removed.'))
                return redirect('staff_order', pk=pk)
            else:
                messages.error(request, _('Could not link customer — please try again.'))
                return redirect('staff_order', pk=pk)

    updates = quote.status_updates.all()
    return render(request, 'homepage/portal/staff_order.html', {
        'quote': quote,
        'updates': updates,
        'update_form': update_form,
        'assign_form': assign_form,
        'link_customer_form': link_customer_form,
        'next_status_key': next_status_key or '',
        'next_status_label': _status_labels.get(next_status_key, '') if next_status_key else '',
        'current_status_key': current_status_key,
        'current_status_label': _status_labels.get(current_status_key, ''),
        'pipeline_complete': pipeline_complete,
        'quote_obj': getattr(quote, 'quote', None),
    })


@login_required
def factory_dashboard(request):
    if not _is_factory_user(request.user):
        return redirect('portal_home')
    quotes = QuoteRequest.objects.filter(assigned_factory=request.user, payment_confirmed=True).order_by('-submitted_at')
    return render(request, 'homepage/portal/factory_dashboard.html', {'quotes': quotes})


@login_required
def factory_order(request, pk):
    if not _is_factory_user(request.user):
        return redirect('portal_home')
    try:
        quote = QuoteRequest.objects.get(pk=pk, assigned_factory=request.user, payment_confirmed=True)
    except QuoteRequest.DoesNotExist:
        raise Http404

    _status_labels = dict(OrderStatusUpdate.STATUS_CHOICES)
    next_status_key = _next_update_status(quote)
    current_status_key = _latest_update_status(quote) or STATUS_ORDER[0]
    pipeline_complete = next_status_key is None

    update_form = StatusUpdateForm()

    if request.method == 'POST':
        update_form = StatusUpdateForm(request.POST, request.FILES)
        if update_form.is_valid():
            utype = update_form.cleaned_data['update_type']
            if utype == 'update':
                if pipeline_complete:
                    messages.error(request, _('All status stages have been posted.'))
                    return redirect('factory_order', pk=pk)
                enforced_status = next_status_key
            else:
                enforced_status = current_status_key
            tracking_number = update_form.cleaned_data.get('tracking_number', '')
            tracking_url = update_form.cleaned_data.get('tracking_url', '')
            if enforced_status != 'shipped' or utype != 'update':
                tracking_number = ''
                tracking_url = ''
            upd = OrderStatusUpdate.objects.create(
                quote_request=quote,
                status=enforced_status,
                update_type=utype,
                note=update_form.cleaned_data['note'],
                attachment=update_form.cleaned_data.get('attachment'),
                tracking_number=tracking_number,
                tracking_url=tracking_url,
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
        'next_status_key': next_status_key or '',
        'next_status_label': _status_labels.get(next_status_key, '') if next_status_key else '',
        'current_status_key': current_status_key,
        'current_status_label': _status_labels.get(current_status_key, ''),
        'pipeline_complete': pipeline_complete,
    })


@login_required
def staff_create_quote(request, pk):
    if not _is_g2g_staff(request.user):
        return redirect('portal_home')
    try:
        quote_request = QuoteRequest.objects.get(pk=pk)
    except QuoteRequest.DoesNotExist:
        raise Http404

    # Redirect if quote already exists
    if hasattr(quote_request, 'quote'):
        return redirect('staff_quote_edit', quote_pk=quote_request.quote.pk)

    if request.method == 'POST':
        header_form = QuoteHeaderForm(request.POST)
        formset = QuoteLineItemFormSet(request.POST)
        # Build an unsaved Quote so formset has a parent
        if header_form.is_valid() and formset.is_valid():
            quote = header_form.save(commit=False)
            quote.quote_request = quote_request
            quote.created_by = request.user
            quote.save()
            formset.instance = quote
            formset.save()
            messages.success(request, _('Quote created.'))
            return redirect('staff_quote_edit', quote_pk=quote.pk)
    else:
        header_form = QuoteHeaderForm()
        # Seed suggested line items
        suggested = []
        for i in range(quote_request.num_styles):
            suggested.append({
                'description': f"{quote_request.product_types} — Style {i + 1}",
                'quantity': _midpoint_of_qty_band(quote_request.quantity_per_style),
                'unit_price': '0.00',
                'discount_pct': '0',
                'note': '',
                'order': i,
                'DELETE': False,
            })
        from django.forms import formset_factory
        initial = suggested if suggested else [{}]
        formset = QuoteLineItemFormSet(initial=initial)

    from .models import SiteSettings
    settings_obj = SiteSettings.objects.first()
    tech_pack_url = settings_obj.tech_pack_template.url if settings_obj and settings_obj.tech_pack_template else ''
    customer_name = (quote_request.contact_name or '').split()[0] or 'there'
    return render(request, 'homepage/portal/staff_quote_edit.html', {
        'quote_request': quote_request,
        'header_form': header_form,
        'formset': formset,
        'quote_obj': None,
        'is_create': True,
        'default_email_body': DEFAULT_PROFORMA_EMAIL_BODY.format(first_name=customer_name),
        'tech_pack_url': tech_pack_url,
    })


@login_required
def staff_quote_edit(request, quote_pk):
    if not _is_g2g_staff(request.user):
        return redirect('portal_home')
    try:
        quote = Quote.objects.get(pk=quote_pk)
    except Quote.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        header_form = QuoteHeaderForm(request.POST, instance=quote)
        formset = QuoteLineItemFormSet(request.POST, instance=quote)
        if header_form.is_valid() and formset.is_valid():
            header_form.save()
            formset.save()
            messages.success(request, _('Quote saved.'))
            return redirect('staff_quote_edit', quote_pk=quote.pk)
    else:
        header_form = QuoteHeaderForm(instance=quote)
        formset = QuoteLineItemFormSet(instance=quote)

    from .models import SiteSettings
    settings_obj = SiteSettings.objects.first()
    tech_pack_url = settings_obj.tech_pack_template.url if settings_obj and settings_obj.tech_pack_template else ''
    qr = quote.quote_request
    customer_name = (qr.contact_name or '').split()[0] or 'there'
    return render(request, 'homepage/portal/staff_quote_edit.html', {
        'quote_request': qr,
        'header_form': header_form,
        'formset': formset,
        'quote_obj': quote,
        'is_create': False,
        'default_email_body': DEFAULT_PROFORMA_EMAIL_BODY.format(first_name=customer_name),
        'tech_pack_url': tech_pack_url,
        'signatures': quote.signatures.all(),
    })


@login_required
def staff_quote_send(request, quote_pk):
    if not _is_g2g_staff(request.user):
        return redirect('portal_home')
    if request.method != 'POST':
        return redirect('staff_quote_edit', quote_pk=quote_pk)
    try:
        quote = Quote.objects.get(pk=quote_pk)
    except Quote.DoesNotExist:
        raise Http404
    email_body = request.POST.get('email_body', '').strip()
    quote.status = 'sent'
    quote.save(update_fields=['status', 'updated_at'])
    _send_quote_notification(quote, email_body=email_body)
    messages.success(request, _('Quote sent to customer.'))
    return redirect('staff_quote_edit', quote_pk=quote_pk)


@login_required
def staff_quote_print(request, quote_pk):
    if not _is_g2g_staff(request.user):
        return redirect('portal_home')
    try:
        quote = Quote.objects.get(pk=quote_pk)
    except Quote.DoesNotExist:
        raise Http404
    line_items = quote.line_items.all()
    return render(request, 'homepage/portal/staff_quote_print.html', {
        'quote': quote,
        'line_items': line_items,
        'signatures': quote.signatures.all(),
    })


@login_required
def customer_quote_view(request, pk):
    if not _is_customer(request.user):
        return redirect('portal_home')
    try:
        quote_request = QuoteRequest.objects.get(pk=pk, customer=request.user)
        quote = quote_request.quote
    except (QuoteRequest.DoesNotExist, Quote.DoesNotExist, AttributeError):
        raise Http404
    if quote.status == 'draft':
        raise Http404
    line_items = quote.line_items.all()
    signatures = quote.signatures.all()
    can_sign = not signatures.filter(signer_role=QuoteSignature.ROLE_CUSTOMER).exists()
    return render(request, 'homepage/portal/customer_quote.html', {
        'quote': quote,
        'quote_request': quote_request,
        'line_items': line_items,
        'signatures': signatures,
        'can_sign': can_sign,
    })


@login_required
def customer_quote_print(request, pk):
    if not _is_customer(request.user):
        return redirect('portal_home')
    try:
        quote_request = QuoteRequest.objects.get(pk=pk, customer=request.user)
        quote = quote_request.quote
    except (QuoteRequest.DoesNotExist, AttributeError):
        raise Http404
    if quote.status == 'draft':
        raise Http404
    line_items = quote.line_items.all()
    signatures = quote.signatures.filter(signer_role=QuoteSignature.ROLE_CUSTOMER)
    return render(request, 'homepage/portal/customer_quote_print.html', {
        'quote': quote,
        'quote_request': quote_request,
        'line_items': line_items,
        'signatures': signatures,
    })


@login_required
def quote_sign(request, quote_pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        quote = Quote.objects.get(pk=quote_pk)
    except Quote.DoesNotExist:
        raise Http404

    if quote.status == 'draft':
        raise Http404

    # Determine role and check access
    if _is_g2g_staff(request.user):
        role = QuoteSignature.ROLE_STAFF
    elif _is_customer(request.user):
        # Customer may only sign their own quote
        if not QuoteRequest.objects.filter(pk=quote.quote_request_id, customer=request.user).exists():
            return JsonResponse({'error': 'Forbidden'}, status=403)
        role = QuoteSignature.ROLE_CUSTOMER
    else:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if QuoteSignature.objects.filter(quote=quote, signer_role=role).exists():
        return JsonResponse({'error': 'Already signed'}, status=409)

    sig_image = request.POST.get('signature_image', '').strip()
    if not sig_image or not sig_image.startswith('data:image/png;base64,'):
        return JsonResponse({'error': 'Invalid signature format'}, status=400)

    signer_name = request.user.get_full_name() or request.user.username
    QuoteSignature.objects.create(
        quote=quote,
        signer=request.user,
        signer_name=signer_name,
        signer_role=role,
        signature_image=sig_image,
        ip_address=request.META.get('REMOTE_ADDR'),
    )

    if role == QuoteSignature.ROLE_CUSTOMER:
        quote.status = 'accepted'
        quote.save(update_fields=['status', 'updated_at'])
        _send_quote_accepted_notification(quote)
        return redirect('customer_quote_view', pk=quote.quote_request_id)
    return redirect('staff_quote_edit', quote_pk=quote.pk)


@login_required
def staff_delete_update(request, update_pk):
    if not _is_g2g_staff(request.user):
        return redirect('portal_home')
    if request.method != 'POST':
        return redirect('staff_dashboard')
    try:
        update = OrderStatusUpdate.objects.get(pk=update_pk)
    except OrderStatusUpdate.DoesNotExist:
        raise Http404
    order_pk = update.quote_request_id
    update.delete()
    messages.success(request, _('Status update deleted.'))
    return redirect('staff_order', pk=order_pk)