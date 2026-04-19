from django import forms
from django.contrib.auth.models import User
from django.forms import inlineformset_factory
from .models import ContactSubmission, QuoteRequest, OrderStatusUpdate, Quote, QuoteLineItem

PRODUCT_CHOICES = [
    ('tshirts', 'T-Shirts'),
    ('polos', 'Polo Shirts'),
    ('hoodies', 'Hoodies / Sweatshirts'),
    ('jackets', 'Jackets / Outerwear'),
    ('sports_kits', 'Sports Kits'),
    ('workwear', 'Workwear / Uniforms'),
    ('trainingsanzug', 'Trainingsanzug'),
    ('denim', 'Denim'),
    ('socks', 'Socks'),
    ('caps', 'Caps / Headwear'),
    ('bags', 'Bags / Accessories'),
    ('mixed', 'Mixed / Multiple'),
    ('other', 'Other'),
]

COUNTRY_CHOICES = [
    ('china', 'China'),
    ('portugal', 'Portugal'),
    ('italy', 'Italy'),
    ('no_preference', 'No preference — recommend what suits best'),
]


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactSubmission
        fields = [
            'name', 'company', 'email', 'phone', 'preferred_contact',
            'product_type', 'order_size', 'timeline',
            'design_help', 'experience', 'message',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your full name'}),
            'company': forms.TextInput(attrs={'placeholder': 'Company, club or organisation'}),
            'email': forms.EmailInput(attrs={'placeholder': 'your@email.com'}),
            'phone': forms.TextInput(attrs={'placeholder': '+41 79 000 00 00 (optional)'}),
            'preferred_contact': forms.RadioSelect(),
            'product_type': forms.Select(),
            'order_size': forms.RadioSelect(),
            'timeline': forms.RadioSelect(),
            'design_help': forms.RadioSelect(),
            'experience': forms.RadioSelect(),
            'message': forms.Textarea(attrs={
                'placeholder': 'Anything else we should know?',
                'rows': 3,
            }),
        }


class QuoteStep1Form(forms.Form):
    """About You"""
    CLIENT_TYPE_CHOICES = [
        ('business', 'Business / Organisation'),
        ('private', 'Private Individual'),
    ]
    client_type = forms.ChoiceField(
        choices=CLIENT_TYPE_CHOICES,
        widget=forms.RadioSelect,
        initial='business',
    )
    company_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. FC Zürich, Zalando CH'})
    )
    industry = forms.ChoiceField(choices=QuoteRequest.INDUSTRY_CHOICES, required=False)
    industry_other = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'placeholder': 'Please specify'}))
    contact_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Your full name'}))
    role = forms.ChoiceField(choices=QuoteRequest.ROLE_CHOICES, required=False)
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'your@email.com'}))
    phone = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'placeholder': '+41 79 000 00 00'}))
    website = forms.URLField(required=False, widget=forms.URLInput(attrs={'placeholder': 'https://yourcompany.com'}))


class QuoteStep2Form(forms.Form):
    """The Order"""
    product_types = forms.MultipleChoiceField(
        choices=PRODUCT_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    product_other = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'placeholder': 'Describe other product'}))
    num_styles = forms.IntegerField(min_value=1, max_value=100, initial=1, widget=forms.NumberInput(attrs={'placeholder': '1'}))
    quantity_per_style = forms.ChoiceField(choices=QuoteRequest.QUANTITY_CHOICES)


class QuoteStep3Form(forms.Form):
    """Customisation"""
    brand_colours = forms.CharField(
        max_length=200, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Navy #1B3A6B, White #FFFFFF'})
    )
    print_method = forms.ChoiceField(choices=QuoteRequest.PRINT_METHOD_CHOICES, widget=forms.RadioSelect)
    print_positions = forms.ChoiceField(choices=QuoteRequest.PRINT_POSITIONS_CHOICES, widget=forms.RadioSelect)
    has_logo = forms.BooleanField(required=False, initial=True, label='We have an existing logo')
    design_files_status = forms.ChoiceField(choices=QuoteRequest.FILES_READY_CHOICES, widget=forms.RadioSelect)
    pantone_matching = forms.BooleanField(required=False, label='Pantone / exact colour matching required')
    customisation_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Special labels, packaging, finishing, etc.'})
    )


class QuoteStep4Form(forms.Form):
    """Production Country"""
    production_countries = forms.MultipleChoiceField(
        choices=COUNTRY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        label='Production country preference',
        help_text='Select all that apply. We will recommend the best option based on your brief.'
    )
    production_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Any specific requirements or priorities regarding production location?'
        })
    )


class QuoteStep5Form(forms.Form):
    """Special Requirements"""
    sustainability = forms.ChoiceField(choices=QuoteRequest.SUSTAINABILITY_CHOICES, widget=forms.RadioSelect)
    certifications_needed = forms.CharField(
        max_length=200, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. OEKO-TEX, GOTS, Fair Trade'})
    )
    existing_supplier = forms.BooleanField(required=False, label='We currently work with another supplier')
    existing_supplier_notes = forms.CharField(
        max_length=200, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'What are you looking to improve?'})
    )
    heard_about_us = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Google, referral, Instagram'})
    )
    additional_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Anything else we should know?'})
    )


class StatusUpdateForm(forms.Form):
    update_type = forms.ChoiceField(
        choices=OrderStatusUpdate.UPDATE_TYPE_CHOICES,
        widget=forms.RadioSelect,
        initial='update',
    )
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe the update or explain the delay'})
    )
    attachment = forms.FileField(required=False)
    tracking_number = forms.CharField(required=False, max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. 1Z999AA10123456784'}))
    tracking_url = forms.URLField(required=False,
        widget=forms.URLInput(attrs={'placeholder': 'https://track.carrier.com/...'}))



class FactoryAssignForm(forms.Form):
    factory = forms.ModelChoiceField(
        queryset=User.objects.filter(groups__name='factory'),
        required=False,
        empty_label='— No factory assigned —',
        label='Assign to factory',
    )


class QuoteHeaderForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ['currency', 'valid_until', 'estimated_delivery',
                  'notes_internal', 'notes_customer']
        widgets = {
            'valid_until':         forms.DateInput(attrs={'type': 'date'}),
            'estimated_delivery':  forms.DateInput(attrs={'type': 'date'}),
            'notes_internal':      forms.Textarea(attrs={'rows': 3,
                                       'placeholder': 'Internal notes (not shown to customer)'}),
            'notes_customer':      forms.Textarea(attrs={'rows': 3,
                                       'placeholder': 'Notes shown on the customer quote'}),
        }


QuoteLineItemFormSet = inlineformset_factory(
    Quote,
    QuoteLineItem,
    fields=['description', 'quantity', 'unit_price', 'discount_pct', 'note', 'order'],
    extra=1,
    can_delete=True,
    widgets={
        'description': forms.TextInput(attrs={
            'placeholder': 'e.g. FC Zürich Home Jersey — Navy/White',
            'class': 'li-description',
        }),
        'quantity':    forms.NumberInput(attrs={'class': 'li-qty', 'min': '1'}),
        'unit_price':  forms.NumberInput(attrs={'class': 'li-price', 'step': '0.01', 'min': '0'}),
        'discount_pct': forms.NumberInput(attrs={'class': 'li-discount', 'step': '0.01',
                                                  'min': '0', 'max': '100'}),
        'note':        forms.TextInput(attrs={'placeholder': 'Optional line note',
                                              'class': 'li-note'}),
        'order':       forms.HiddenInput(),
    }
)