from django.contrib import admin
from django.utils.html import format_html
from .models import (
    FAQComment, TrainingPackage, Weapon, 
    Instructor, Booking, Testimonial, RangeLocation
)

@admin.register(FAQComment)
class FAQCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'short_content', 'parent_link', 'created_at', 'is_active', 'is_reply')
    list_filter = ('created_at', 'is_active', 'parent')
    search_fields = ('content', 'user__username')
    list_editable = ('is_active',)
    list_per_page = 20
    date_hierarchy = 'created_at'
    actions = ['approve_comments', 'disapprove_comments']

    fieldsets = (
        (None, {
            'fields': ('user', 'content', 'parent')
        }),
        ('Moderation', {
            'fields': ('is_active',)
        }),
    )

    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Content'

    def parent_link(self, obj):
        if obj.parent:
            return format_html('<a href="{}">{}</a>', 
                             f'/admin/lessons/faqcomment/{obj.parent.id}/change/',
                             obj.parent.short_content())
        return "-"
    parent_link.short_description = 'Parent Comment'

    def is_reply(self, obj):
        return obj.parent is not None
    is_reply.boolean = True
    is_reply.short_description = 'Is Reply?'

    def approve_comments(self, request, queryset):
        queryset.update(is_active=True)
    approve_comments.short_description = "Approve selected comments"

    def disapprove_comments(self, request, queryset):
        queryset.update(is_active=False)
    disapprove_comments.short_description = "Disapprove selected comments"


@admin.register(TrainingPackage)
class TrainingPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'formatted_price', 'duration', 'is_active', 'created_at')
    list_filter = ('is_active', 'duration')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    
    def formatted_price(self, obj):
        return f"${obj.price}"
    formatted_price.short_description = 'Price'


@admin.register(Weapon)
class WeaponAdmin(admin.ModelAdmin):
    list_display = ('name', 'caliber', 'type', 'is_active', 'image_preview')
    list_filter = ('type', 'is_active')
    search_fields = ('name', 'caliber')
    list_editable = ('is_active',)
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px;"/>', obj.image.url)
        return "-"
    image_preview.short_description = 'Preview'


@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ('user', 'years_experience', 'certifications_short', 'is_active')
    list_filter = ('is_active', 'years_experience')
    search_fields = ('user__username', 'certifications')
    list_editable = ('is_active',)
    raw_id_fields = ('user',)
    
    def certifications_short(self, obj):
        return obj.certifications[:50] + '...' if len(obj.certifications) > 50 else obj.certifications
    certifications_short.short_description = 'Certifications'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'package', 'formatted_date', 
        'formatted_time', 'payment_status', 'payment_method'
    )
    list_filter = ('payment_status', 'payment_method', 'date')
    search_fields = ('user__username', 'package__name', 'transaction_id')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'
    list_select_related = ('user', 'package', 'weapon', 'instructor')
    
    fieldsets = (
        ('Booking Details', {
            'fields': ('user', 'package', 'weapon', 'instructor', 'date', 'time', 'duration')
        }),
        ('Customer Information', {
            'fields': ('full_name', 'email', 'phone', 'notes')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_status', 'transaction_id', 'amount_paid')
        }),
        ('System Information', {
            'fields': ('is_confirmed', 'created_at', 'updated_at')
        }),
    )

    def formatted_date(self, obj):
        return obj.date.strftime('%b %d, %Y')
    formatted_date.short_description = 'Date'
    formatted_date.admin_order_field = 'date'

    def formatted_time(self, obj):
        return obj.time.strftime('%I:%M %p')
    formatted_time.short_description = 'Time'
    formatted_time.admin_order_field = 'time'


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'rating_stars', 'short_content', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'rating')
    search_fields = ('name', 'content')
    list_editable = ('is_approved',)
    actions = ['approve_testimonials', 'disapprove_testimonials']
    
    def rating_stars(self, obj):
        return '★' * obj.rating + '☆' * (5 - obj.rating)
    rating_stars.short_description = 'Rating'

    def short_content(self, obj):
        return obj.content[:75] + '...' if len(obj.content) > 75 else obj.content
    short_content.short_description = 'Content'

    def approve_testimonials(self, request, queryset):
        queryset.update(is_approved=True)
    approve_testimonials.short_description = "Approve selected testimonials"

    def disapprove_testimonials(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove_testimonials.short_description = "Disapprove selected testimonials"


@admin.register(RangeLocation)
class RangeLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_address', 'phone', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'address')
    list_editable = ('is_active',)
    
    def short_address(self, obj):
        return obj.address[:50] + '...' if len(obj.address) > 50 else obj.address
    short_address.short_description = 'Address'


# Admin site customization
admin.site.site_header = "Ready Aim Learn Administration"
admin.site.site_title = "Ready Aim Learn Admin Portal"
admin.site.index_title = "Welcome to Ready Aim Learn Admin"