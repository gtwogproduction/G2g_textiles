from django.contrib import admin
from django.utils.html import format_html
from .models import (
    ContactSubmission, QuoteRequest, OrderStatusUpdate,
    SiteSettings, Service, HowItWorksStep, ClientLogo, LegalPage,
    BlogPost, BlogCategory, BlogPostImage,
)


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'email', 'order_size', 'submitted_at']
    list_filter = ['order_size', 'submitted_at']
    search_fields = ['name', 'company', 'email']
    readonly_fields = ['submitted_at']


class OrderStatusUpdateInline(admin.TabularInline):
    model = OrderStatusUpdate
    extra = 0
    readonly_fields = ['created_by', 'created_at']
    fields = ['status', 'update_type', 'note', 'attachment', 'tracking_number', 'tracking_url', 'created_by', 'created_at']


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'contact_name', 'email', 'industry', 'quantity_per_style', 'status', 'customer', 'assigned_factory', 'submitted_at']
    list_filter = ['status', 'industry', 'submitted_at']
    search_fields = ['company_name', 'contact_name', 'email']
    readonly_fields = ['submitted_at']
    list_editable = ['status']
    inlines = [OrderStatusUpdateInline]
    fieldsets = (
        ('About', {'fields': ('company_name', 'industry', 'industry_other', 'contact_name', 'role', 'email', 'phone', 'website')}),
        ('The Order', {'fields': ('product_types', 'product_other', 'num_styles', 'quantity_per_style')}),
        ('Customisation', {'fields': ('brand_colours', 'print_method', 'print_positions', 'has_logo', 'design_files_status', 'pantone_matching', 'customisation_notes')}),
        ('Special Requirements', {'fields': ('sustainability', 'certifications_needed', 'existing_supplier', 'existing_supplier_notes', 'heard_about_us', 'additional_notes')}),
        ('Portal', {
            'fields': ('customer', 'assigned_factory', 'notify_on_updates'),
            'description': 'Link this quote to a customer account and assign a factory. Create user accounts in the Users section of admin, then add them to the "g2g_staff" or "factory" group as needed.',
        }),
        ('Meta', {'fields': ('status', 'submitted_at')}),
    )


@admin.register(OrderStatusUpdate)
class OrderStatusUpdateAdmin(admin.ModelAdmin):
    list_display = ['quote_request', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['quote_request__company_name', 'note']
    readonly_fields = ['created_at']


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Hero Section — English', {'fields': (
            'hero_eyebrow', 'hero_headline_line1', 'hero_headline_line2', 'hero_headline_line3',
            'hero_subtext', 'hero_cta_primary', 'hero_cta_secondary',
            'hero_badge_year', 'hero_badge_text', 'hero_video',
        )}),
        ('Hero Section — Deutsch', {'fields': (
            'hero_eyebrow_de', 'hero_headline_line1_de', 'hero_headline_line2_de', 'hero_headline_line3_de',
            'hero_subtext_de', 'hero_cta_primary_de', 'hero_cta_secondary_de', 'hero_badge_text_de',
        ), 'classes': ('collapse',)}),
        ('Contact CTA — English', {'fields': (
            'cta_label', 'cta_headline_line1', 'cta_headline_line2',
            'cta_subtext', 'cta_btn_primary', 'cta_btn_secondary',
        )}),
        ('Contact CTA — Deutsch', {'fields': (
            'cta_label_de', 'cta_headline_line1_de', 'cta_headline_line2_de',
            'cta_subtext_de', 'cta_btn_primary_de', 'cta_btn_secondary_de',
        ), 'classes': ('collapse',)}),
        ('Footer', {'fields': (
            'footer_instagram_url', 'footer_instagram_handle', 'footer_copyright',
        )}),
        ('SEO & Meta', {'fields': (
            'meta_title_en', 'meta_title_de',
            'meta_description_en', 'meta_description_de',
            'meta_og_image', 'favicon',
        )}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['order', 'title', 'image_preview', 'is_active']
    list_editable = ['order', 'is_active']
    list_display_links = ['title']
    fieldsets = (
        ('English', {'fields': ('title', 'description', 'image')}),
        ('German', {'fields': ('title_de', 'description_de'), 'classes': ('collapse',)}),
        ('Settings', {'fields': ('order', 'is_active')}),
    )

    @admin.display(description='Preview')
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:40px;border-radius:4px;" />', obj.image.url)
        return '—'


@admin.register(HowItWorksStep)
class HowItWorksStepAdmin(admin.ModelAdmin):
    list_display = ['order', 'number', 'title', 'is_active']
    list_editable = ['order', 'is_active']
    list_display_links = ['title']
    fieldsets = (
        ('English', {'fields': ('number', 'title', 'description')}),
        ('German', {'fields': ('title_de', 'description_de'), 'classes': ('collapse',)}),
        ('Settings', {'fields': ('order', 'is_active')}),
    )


@admin.register(ClientLogo)
class ClientLogoAdmin(admin.ModelAdmin):
    list_display = ['order', 'name', 'logo_preview', 'is_active']
    list_editable = ['order', 'is_active']
    list_display_links = ['name']

    @admin.display(description='Preview')
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="height:32px;" />', obj.logo.url)
        return '—'


@admin.register(LegalPage)
class LegalPageAdmin(admin.ModelAdmin):
    list_display = ['page', 'title', 'last_updated']
    fields = ['page', 'title', 'content']


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_de', 'slug']
    prepopulated_fields = {'slug': ('name',)}


class BlogPostImageInline(admin.TabularInline):
    model = BlogPostImage
    extra = 3
    fields = ['image', 'caption', 'caption_de', 'order', 'image_preview']
    readonly_fields = ['image_preview']

    @admin.display(description='Preview')
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:60px;border-radius:4px;" />'
                '<br><small style="color:#999;font-size:10px;word-break:break-all;">{}</small>',
                obj.image.url, obj.image.url
            )
        return '—'

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'post_type', 'is_published', 'published_at', 'cover_preview']
    list_filter = ['is_published', 'post_type', 'category']
    list_editable = ['is_published']
    search_fields = ['title', 'title_de', 'body']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    inlines = [BlogPostImageInline]

    fieldsets = (
        ('Content — English', {
            'fields': ('title', 'slug', 'post_type', 'category', 'excerpt', 'body', 'cover_image', 'video_url')
        }),
        ('Content — Deutsch', {
            'fields': ('title_de', 'excerpt_de', 'body_de'),
            'classes': ('collapse',),
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
        }),
        ('Publishing', {
            'fields': ('is_published', 'published_at', 'created_at', 'updated_at'),
        }),
    )

    @admin.display(description='Cover')
    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html('<img src="{}" style="height:40px;border-radius:4px;" />', obj.cover_image.url)
        return '—'