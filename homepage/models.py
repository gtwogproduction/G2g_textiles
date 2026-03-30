from django.db import models


class ContactSubmission(models.Model):
    PRODUCT_CHOICES = [
        ('tshirts', 'T-Shirts'),
        ('polos', 'Polo Shirts'),
        ('hoodies', 'Hoodies / Sweatshirts'),
        ('jackets', 'Jackets / Outerwear'),
        ('sports_kits', 'Sports Kits'),
        ('workwear', 'Workwear / Uniforms'),
        ('caps', 'Caps / Headwear'),
        ('bags', 'Bags / Accessories'),
        ('mixed', 'Mixed / Multiple'),
        ('other', 'Other / Not sure yet'),
    ]
    ORDER_SIZE_CHOICES = [
        ('50-100', '50–100 units'),
        ('100-250', '100–250 units'),
        ('250-500', '250–500 units'),
        ('500-1000', '500–1,000 units'),
        ('1000+', '1,000+ units'),
        ('unsure', 'Not sure yet'),
    ]
    CONTACT_METHOD_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Phone call'),
        ('whatsapp', 'WhatsApp'),
        ('any', 'Any — whatever is fastest'),
    ]
    EXPERIENCE_CHOICES = [
        ('first_time', 'First time ordering custom clothing'),
        ('some', 'Done it before, looking for a better supplier'),
        ('experienced', 'Experienced — know exactly what I need'),
    ]
    DESIGN_HELP_CHOICES = [
        ('have_files', 'Yes — I have ready design files'),
        ('need_help', 'No — I need design/concept help too'),
        ('have_concept', 'I have a concept but need it refined'),
    ]
    TIMELINE_CHOICES = [
        ('asap', 'ASAP'),
        ('1month', 'Within 1 month'),
        ('1-3months', '1–3 months'),
        ('flexible', 'Flexible'),
    ]

    # Who
    name = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    preferred_contact = models.CharField(max_length=20, choices=CONTACT_METHOD_CHOICES, default='any')

    # What
    product_type = models.CharField(max_length=30, choices=PRODUCT_CHOICES, default='other')
    order_size = models.CharField(max_length=20, choices=ORDER_SIZE_CHOICES, default='unsure')
    timeline = models.CharField(max_length=20, choices=TIMELINE_CHOICES, default='flexible')
    design_help = models.CharField(max_length=20, choices=DESIGN_HELP_CHOICES, default='have_files')
    experience = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='first_time')
    message = models.TextField(blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} — {self.company} ({self.submitted_at.strftime('%d %b %Y')})"

    # German versions
    hero_eyebrow_de = models.CharField(max_length=100, blank=True)
    hero_headline_line1_de = models.CharField(max_length=100, blank=True)
    hero_headline_line2_de = models.CharField(max_length=100, blank=True)
    hero_headline_line3_de = models.CharField(max_length=100, blank=True)
    hero_subtext_de = models.TextField(blank=True)
    hero_cta_primary_de = models.CharField(max_length=60, blank=True)
    hero_cta_secondary_de = models.CharField(max_length=60, blank=True)
    hero_badge_text_de = models.CharField(max_length=60, blank=True)
    cta_label_de = models.CharField(max_length=60, blank=True)
    cta_headline_line1_de = models.CharField(max_length=100, blank=True)
    cta_headline_line2_de = models.CharField(max_length=100, blank=True)
    cta_subtext_de = models.TextField(blank=True)
    cta_btn_primary_de = models.CharField(max_length=60, blank=True)
    cta_btn_secondary_de = models.CharField(max_length=60, blank=True)
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Contact Submission'
        verbose_name_plural = 'Contact Submissions'


class QuoteRequest(models.Model):
    INDUSTRY_CHOICES = [
        ('sports_club', 'Sports Club / Team'),
        ('retail_fashion', 'Retail & Fashion Brand'),
        ('corporate', 'Corporate / Office'),
        ('hospitality', 'Hospitality / Uniforms'),
        ('events', 'Events / Promotions'),
        ('ngo', 'NGO / Non-profit'),
        ('other', 'Other'),
    ]
    ROLE_CHOICES = [
        ('owner', 'Owner / Founder'),
        ('buyer', 'Buyer / Procurement'),
        ('marketing', 'Marketing / Brand Manager'),
        ('manager', 'Team / Club Manager'),
        ('designer', 'Designer'),
        ('other', 'Other'),
    ]
    QUANTITY_CHOICES = [
        ('50-100', '50–100 units'),
        ('100-250', '100–250 units'),
        ('250-500', '250–500 units'),
        ('500-1000', '500–1,000 units'),
        ('1000-5000', '1,000–5,000 units'),
        ('5000+', '5,000+ units'),
    ]
    GENDER_CHOICES = [
        ('unisex', 'Unisex only'),
        ('mens_womens', "Men's & Women's cuts"),
        ('kids', 'Kids / Youth sizes included'),
        ('all', 'All of the above'),
    ]
    PRINT_METHOD_CHOICES = [
        ('embroidery', 'Embroidery'),
        ('screen_print', 'Screen Print'),
        ('dtf', 'DTF (Direct to Film)'),
        ('dtg', 'DTG (Direct to Garment)'),
        ('sublimation', 'Sublimation'),
        ('heat_transfer', 'Heat Transfer'),
        ('unsure', 'Not sure — advise me'),
    ]
    PRINT_POSITIONS_CHOICES = [
        ('1', '1 position'),
        ('2', '2 positions'),
        ('3-4', '3–4 positions'),
        ('5+', '5+ positions'),
        ('allover', 'All-over print'),
    ]
    FILES_READY_CHOICES = [
        ('yes_vector', 'Yes — vector files ready (AI/EPS/SVG)'),
        ('yes_raster', 'Yes — raster files only (PNG/JPG)'),
        ('no_need_design', 'No — I need design help'),
        ('no_brief_only', 'No — I have a brief/concept only'),
    ]
    TIMELINE_CHOICES = [
        ('asap', 'ASAP — as fast as possible'),
        ('2-4weeks', '2–4 weeks'),
        ('1-2months', '1–2 months'),
        ('2-3months', '2–3 months'),
        ('flexible', 'Flexible — no hard deadline'),
    ]
    SAMPLE_CHOICES = [
        ('yes_required', 'Yes — required before production'),
        ('yes_preferred', 'Yes — preferred but not required'),
        ('no', 'No — proceed straight to production'),
    ]
    BUDGET_CHOICES = [
        ('under_1k', 'Under CHF 1,000'),
        ('1k-5k', 'CHF 1,000–5,000'),
        ('5k-15k', 'CHF 5,000–15,000'),
        ('15k-50k', 'CHF 15,000–50,000'),
        ('50k+', 'CHF 50,000+'),
        ('undisclosed', 'Prefer not to say'),
    ]
    SUSTAINABILITY_CHOICES = [
        ('required', 'Very important — required'),
        ('preferred', 'Preferred if possible'),
        ('not_priority', 'Not a priority'),
    ]
    STATUS_CHOICES = [
        ('new', 'New'),
        ('reviewing', 'Reviewing'),
        ('quoted', 'Quoted'),
        ('won', 'Won'),
        ('lost', 'Lost'),
    ]

    # Block 1
    company_name = models.CharField(max_length=150)
    industry = models.CharField(max_length=30, choices=INDUSTRY_CHOICES)
    industry_other = models.CharField(max_length=100, blank=True)
    contact_name = models.CharField(max_length=100)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)

    # Block 2
    product_types = models.CharField(max_length=200)
    product_other = models.CharField(max_length=100, blank=True)
    num_styles = models.PositiveIntegerField(default=1)
    quantity_per_style = models.CharField(max_length=20, choices=QUANTITY_CHOICES)
    gender_sizing = models.CharField(max_length=30, choices=GENDER_CHOICES)
    size_range = models.CharField(max_length=100, blank=True)

    # Block 3
    brand_colours = models.CharField(max_length=200, blank=True)
    print_method = models.CharField(max_length=30, choices=PRINT_METHOD_CHOICES)
    print_positions = models.CharField(max_length=10, choices=PRINT_POSITIONS_CHOICES)
    has_logo = models.BooleanField(default=True)
    design_files_status = models.CharField(max_length=30, choices=FILES_READY_CHOICES)
    pantone_matching = models.BooleanField(default=False)
    customisation_notes = models.TextField(blank=True)

    # Block 4
    desired_delivery = models.CharField(max_length=20, choices=TIMELINE_CHOICES)
    hard_deadline = models.DateField(null=True, blank=True)
    sample_required = models.CharField(max_length=20, choices=SAMPLE_CHOICES)
    delivery_country = models.CharField(max_length=100, default='Switzerland')
    delivery_city = models.CharField(max_length=100, blank=True)
    split_delivery = models.BooleanField(default=False)

    # Block 5
    budget_range = models.CharField(max_length=20, choices=BUDGET_CHOICES)
    budget_notes = models.CharField(max_length=200, blank=True)

    # Block 6
    sustainability = models.CharField(max_length=20, choices=SUSTAINABILITY_CHOICES, default='not_priority')
    certifications_needed = models.CharField(max_length=200, blank=True)
    existing_supplier = models.BooleanField(default=False)
    existing_supplier_notes = models.CharField(max_length=200, blank=True)
    heard_about_us = models.CharField(max_length=100, blank=True)
    additional_notes = models.TextField(blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')

    def __str__(self):
        return f"{self.company_name} — {self.contact_name} ({self.submitted_at.strftime('%d %b %Y')})"

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Quote Request'
        verbose_name_plural = 'Quote Requests'


# ===== CMS MODELS =====

class SiteSettings(models.Model):
    """Single-row settings for hero and general page text."""
    hero_eyebrow = models.CharField(max_length=100, default='B2B Textile Solutions')
    hero_headline_line1 = models.CharField(max_length=100, default='Clothing')
    hero_headline_line2 = models.CharField(max_length=100, default='Built for')
    hero_headline_line3 = models.CharField(max_length=100, default='Business.')
    hero_subtext = models.TextField(default='From sports kits to retail lines — G2G Textiles delivers premium custom clothing at scale. No compromises, no middlemen.')
    hero_cta_primary = models.CharField(max_length=60, default='Get a Quote')
    hero_cta_secondary = models.CharField(max_length=60, default='See How It Works')
    hero_badge_year = models.CharField(max_length=10, default='2015')
    hero_badge_text = models.CharField(max_length=60, default='Trusted by 300+ brands')

    cta_label = models.CharField(max_length=60, default='Ready to order?')
    cta_headline_line1 = models.CharField(max_length=100, default="Let's build")
    cta_headline_line2 = models.CharField(max_length=100, default='your order.')
    cta_subtext = models.TextField(default='Get in touch directly or use the full quote wizard — it takes 5 minutes and gives us everything we need to send you a precise quote.')
    cta_btn_primary = models.CharField(max_length=60, default='Start Quote Wizard')
    cta_btn_secondary = models.CharField(max_length=60, default='Quick Contact')

    footer_instagram_url = models.URLField(default='https://instagram.com/g2gtextiles', blank=True)
    footer_instagram_handle = models.CharField(max_length=60, default='@g2gtextiles', blank=True)
    footer_copyright = models.CharField(max_length=100, default='© 2025 G2G Textiles.')

    # SEO & Meta
    meta_title_en = models.CharField(max_length=60, blank=True, default='G2G Textiles — B2B Custom Clothing')
    meta_title_de = models.CharField(max_length=60, blank=True, default='G2G Textiles — B2B Textilien')
    meta_description_en = models.TextField(max_length=160, blank=True, default='Premium custom clothing for businesses, sports clubs and brands. From 50 units. Free consulting included.')
    meta_description_de = models.TextField(max_length=160, blank=True, default='Hochwertige Individualkleidung für Unternehmen, Vereine und Marken. Ab 50 Stück. Kostenlose Beratung inklusive.')
    meta_og_image = models.ImageField(upload_to='meta/', blank=True, null=True, help_text='Social share image (1200x630px recommended)')
    favicon = models.ImageField(upload_to='meta/', blank=True, null=True, help_text='.ico or .png, 32x32px recommended')

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return 'Site Settings'

    def save(self, *args, **kwargs):
        # Enforce single row
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Service(models.Model):
    title = models.CharField(max_length=100)
    title_de = models.CharField(max_length=100, blank=True, verbose_name='Title (DE)')
    description = models.TextField()
    description_de = models.TextField(blank=True, verbose_name='Description (DE)')
    image = models.ImageField(upload_to='services/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Service'
        verbose_name_plural = 'Services'

    def __str__(self):
        return self.title


class HowItWorksStep(models.Model):
    number = models.CharField(max_length=4, default='01')
    title = models.CharField(max_length=100)
    title_de = models.CharField(max_length=100, blank=True, verbose_name='Title (DE)')
    description = models.TextField()
    description_de = models.TextField(blank=True, verbose_name='Description (DE)')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'How It Works Step'
        verbose_name_plural = 'How It Works Steps'

    def __str__(self):
        return f"{self.number} — {self.title}"


class PricingTier(models.Model):
    name = models.CharField(max_length=60)
    name_de = models.CharField(max_length=60, blank=True, verbose_name='Name (DE)')
    units = models.CharField(max_length=60)
    units_de = models.CharField(max_length=60, blank=True, verbose_name='Units (DE)')
    description = models.TextField()
    description_de = models.TextField(blank=True, verbose_name='Description (DE)')
    features = models.TextField(help_text='One feature per line')
    features_de = models.TextField(blank=True, help_text='One feature per line (DE)', verbose_name='Features (DE)')
    cta_label = models.CharField(max_length=60, default='Get a Quote')
    is_highlighted = models.BooleanField(default=False, help_text='Show as "Most Popular"')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Pricing Tier'
        verbose_name_plural = 'Pricing Tiers'

    def __str__(self):
        return self.name

    def get_features_list(self):
        return [f.strip() for f in self.features.splitlines() if f.strip()]

    def get_features_list_de(self):
        return [f.strip() for f in self.features_de.splitlines() if f.strip()]


class ClientLogo(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='clients/')
    url = models.URLField(blank=True, help_text='Link to client website (optional)')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Client Logo'
        verbose_name_plural = 'Client Logos'

    def __str__(self):
        return self.name
    

class LegalPage(models.Model):
    PAGE_CHOICES = [
        ('impressum', 'Impressum'),
        ('agb', 'AGB'),
    ]
    page = models.CharField(max_length=20, choices=PAGE_CHOICES, unique=True)
    title = models.CharField(max_length=100)
    content = models.TextField(help_text='Plain text or basic HTML')
    last_updated = models.DateField(auto_now=True)

    def __str__(self):
        return self.get_page_display()

    class Meta:
        verbose_name = 'Legal Page'
        verbose_name_plural = 'Legal Pages'
        