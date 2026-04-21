from datetime import date as _date

from django.db import models
from django.conf import settings
from cloudinary_storage.storage import VideoMediaCloudinaryStorage


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

    name = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    preferred_contact = models.CharField(max_length=20, choices=CONTACT_METHOD_CHOICES, default='any')
    product_type = models.CharField(max_length=30, choices=PRODUCT_CHOICES, default='other')
    order_size = models.CharField(max_length=20, choices=ORDER_SIZE_CHOICES, default='unsure')
    timeline = models.CharField(max_length=20, choices=TIMELINE_CHOICES, default='flexible')
    design_help = models.CharField(max_length=20, choices=DESIGN_HELP_CHOICES, default='have_files')
    experience = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='first_time')
    message = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} — {self.company} ({self.submitted_at.strftime('%d %b %Y')})"

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

    company_name = models.CharField(max_length=150)
    industry = models.CharField(max_length=30, choices=INDUSTRY_CHOICES)
    industry_other = models.CharField(max_length=100, blank=True)
    contact_name = models.CharField(max_length=100)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    product_types = models.CharField(max_length=200)
    product_other = models.CharField(max_length=100, blank=True)
    num_styles = models.PositiveIntegerField(default=1)
    quantity_per_style = models.CharField(max_length=20, choices=QUANTITY_CHOICES)
    gender_sizing = models.CharField(max_length=30, choices=GENDER_CHOICES)
    size_range = models.CharField(max_length=100, blank=True)
    brand_colours = models.CharField(max_length=200, blank=True)
    print_method = models.CharField(max_length=30, choices=PRINT_METHOD_CHOICES)
    print_positions = models.CharField(max_length=10, choices=PRINT_POSITIONS_CHOICES)
    has_logo = models.BooleanField(default=True)
    design_files_status = models.CharField(max_length=30, choices=FILES_READY_CHOICES)
    pantone_matching = models.BooleanField(default=False)
    customisation_notes = models.TextField(blank=True)
    desired_delivery = models.CharField(max_length=20, choices=TIMELINE_CHOICES)
    hard_deadline = models.DateField(null=True, blank=True)
    sample_required = models.CharField(max_length=20, choices=SAMPLE_CHOICES)
    delivery_country = models.CharField(max_length=100, default='Switzerland')
    delivery_city = models.CharField(max_length=100, blank=True)
    split_delivery = models.BooleanField(default=False)
    budget_range = models.CharField(max_length=20, choices=BUDGET_CHOICES)
    budget_notes = models.CharField(max_length=200, blank=True)
    sustainability = models.CharField(max_length=20, choices=SUSTAINABILITY_CHOICES, default='not_priority')
    certifications_needed = models.CharField(max_length=200, blank=True)
    existing_supplier = models.BooleanField(default=False)
    existing_supplier_notes = models.CharField(max_length=200, blank=True)
    heard_about_us = models.CharField(max_length=100, blank=True)
    additional_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='quote_requests'
    )
    assigned_factory = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='assigned_orders'
    )
    notify_on_updates = models.BooleanField(
        default=True,
        help_text='Send the customer an email when a new status update is posted.'
    )
    payment_confirmed = models.BooleanField(
        default=False,
        help_text='Mark once the customer has paid. The factory only sees this order after payment is confirmed.'
    )

    def __str__(self):
        return f"{self.company_name} — {self.contact_name} ({self.submitted_at.strftime('%d %b %Y')})"

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Quote Request'
        verbose_name_plural = 'Quote Requests'


class OrderStatusUpdate(models.Model):
    STATUS_CHOICES = [
        ('quote_received', 'Quote Received'),
        ('in_review', 'In Review'),
        ('quote_sent', 'Quote Sent'),
        ('sampling', 'Sampling'),
        ('sample_approved', 'Sample Approved'),
        ('in_production', 'In Production'),
        ('quality_check', 'Quality Check'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ]
    UPDATE_TYPE_CHOICES = [
        ('update', 'Status Update'),
        ('issue',  'Delay / Issue'),
    ]

    quote_request = models.ForeignKey(QuoteRequest, on_delete=models.CASCADE, related_name='status_updates')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)
    update_type = models.CharField(max_length=10, choices=UPDATE_TYPE_CHOICES, default='update')
    note = models.TextField(blank=True)
    attachment = models.FileField(upload_to='status_updates/', blank=True, null=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    tracking_url = models.URLField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='status_updates_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_status_display()} — {self.quote_request}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order Status Update'
        verbose_name_plural = 'Order Status Updates'


class Quote(models.Model):
    STATUS_CHOICES = [
        ('draft',    'Draft'),
        ('sent',     'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired',  'Expired'),
    ]
    quote_request     = models.OneToOneField(
        QuoteRequest, on_delete=models.CASCADE, related_name='quote'
    )
    quote_number      = models.CharField(max_length=20, unique=True, blank=True)
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    currency          = models.CharField(max_length=5, default='CHF')
    valid_until       = models.DateField(null=True, blank=True)
    estimated_delivery = models.DateField(null=True, blank=True)
    notes_internal    = models.TextField(blank=True,
                            help_text='Visible to staff only — not shown to the customer.')
    notes_customer    = models.TextField(blank=True,
                            help_text='Shown on the customer-facing quote.')
    created_by        = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='quotes_created'
    )
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.quote_number:
            year = _date.today().year
            last = Quote.objects.filter(
                quote_number__startswith=f'Q-{year}-'
            ).order_by('quote_number').last()
            num = int(last.quote_number.split('-')[2]) + 1 if last else 1
            self.quote_number = f'Q-{year}-{num:04d}'
        super().save(*args, **kwargs)

    @property
    def subtotal(self):
        from decimal import Decimal
        return sum((item.subtotal for item in self.line_items.all()), Decimal('0.00'))

    @property
    def total(self):
        return self.subtotal

    def __str__(self):
        return f"{self.quote_number} — {self.quote_request}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Quote'
        verbose_name_plural = 'Quotes'


class QuoteLineItem(models.Model):
    quote        = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='line_items')
    description  = models.CharField(max_length=255)
    quantity     = models.PositiveIntegerField(default=1)
    unit_price   = models.DecimalField(max_digits=10, decimal_places=2)
    discount_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        help_text='Discount percentage (0–100)'
    )
    note         = models.CharField(max_length=200, blank=True)
    order        = models.PositiveIntegerField(default=0)

    @property
    def subtotal(self):
        from decimal import Decimal
        factor = 1 - (self.discount_pct / Decimal('100'))
        return (self.unit_price * self.quantity * factor).quantize(Decimal('0.01'))

    def __str__(self):
        return f"{self.description} × {self.quantity}"

    class Meta:
        ordering = ['order', 'pk']
        verbose_name = 'Quote Line Item'
        verbose_name_plural = 'Quote Line Items'


class QuoteSignature(models.Model):
    ROLE_CUSTOMER = 'customer'
    ROLE_STAFF = 'g2g_staff'
    ROLE_CHOICES = [(ROLE_CUSTOMER, 'Customer'), (ROLE_STAFF, 'G2G Staff')]

    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name='signatures')
    signer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='quote_signatures'
    )
    signer_name = models.CharField(max_length=200)
    signer_role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    signature_image = models.TextField()
    signed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['signed_at']
        unique_together = [('quote', 'signer_role')]
        verbose_name = 'Quote Signature'
        verbose_name_plural = 'Quote Signatures'

    def __str__(self):
        return f"{self.signer_name} ({self.get_signer_role_display()}) — {self.quote.quote_number}"


class SiteSettings(models.Model):
    hero_video = models.FileField(
    upload_to='hero/',
    blank=True,
    null=True,
    storage=VideoMediaCloudinaryStorage(),
    help_text='MP4 or WebM video for hero background'
)
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

    # German translations
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

    # SEO & Meta
    meta_title_en = models.CharField(max_length=60, blank=True, default='G2G Textiles — B2B Custom Clothing')
    meta_title_de = models.CharField(max_length=60, blank=True, default='G2G Textiles — B2B Textilien')
    meta_description_en = models.TextField(max_length=160, blank=True, default='Premium custom clothing for businesses, sports clubs and brands. From 50 units. Free consulting included.')
    meta_description_de = models.TextField(max_length=160, blank=True, default='Hochwertige Individualkleidung für Unternehmen, Vereine und Marken. Ab 50 Stück. Kostenlose Beratung inklusive.')
    meta_og_image = models.ImageField(upload_to='meta/', blank=True, null=True)
    favicon = models.ImageField(upload_to='meta/', blank=True, null=True)
    tech_pack_template = models.FileField(
        upload_to='documents/',
        blank=True,
        null=True,
        help_text='Standard tech pack template PDF sent with proforma invoices. Same file used for all orders.'
    )

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return 'Site Settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        return cls.objects.get(pk=1)


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

class ClientLogo(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='clients/')
    url = models.URLField(blank=True)
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


class BlogCategory(models.Model):
    name = models.CharField(max_length=60)
    name_de = models.CharField(max_length=60, blank=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Blog Category'
        verbose_name_plural = 'Blog Categories'
        ordering = ['name']


class BlogPost(models.Model):
    POST_TYPE_CHOICES = [
        ('article', 'Article / Guide'),
        ('case_study', 'Case Study'),
        ('video', 'Video Post'),
    ]
    meta_title = models.CharField(max_length=60, blank=True, help_text='SEO title (max 60 chars). Falls back to post title if empty.')
    meta_description = models.TextField(max_length=160, blank=True, help_text='SEO description (max 160 chars). Falls back to excerpt if empty.')
    title = models.CharField(max_length=200)
    title_de = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(unique=True, max_length=200)
    post_type = models.CharField(max_length=20, choices=POST_TYPE_CHOICES, default='article')
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    excerpt = models.TextField(max_length=300, blank=True, help_text='Short summary shown on listing page')
    excerpt_de = models.TextField(max_length=300, blank=True)
    body = models.TextField(help_text='HTML content — use &lt;h2&gt;, &lt;p&gt;, &lt;ul&gt;, &lt;strong&gt;, &lt;a&gt; etc.')
    body_de = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='blog/', blank=True, null=True)
    video_url = models.URLField(blank=True, help_text='YouTube or Vimeo embed URL e.g. https://www.youtube.com/embed/xxxxx')
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'


class BlogPostImage(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='blog/images/')
    caption = models.CharField(max_length=200, blank=True)
    caption_de = models.CharField(max_length=200, blank=True, verbose_name='Caption (DE)')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Image'
        verbose_name_plural = 'Images'

    def __str__(self):
        return f"Image {self.order} — {self.post.title}"