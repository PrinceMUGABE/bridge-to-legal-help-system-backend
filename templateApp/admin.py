# templates/admin.py
from django.contrib import admin
from .models import Template


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = [
        'title', 
        'category', 
        'format', 
        'price', 
        'downloads', 
        'rating', 
        'author',
        'is_active',
        'created_at'
    ]
    
    list_filter = [
        'category', 
        'format', 
        'price', 
        'is_active', 
        'created_at',
        'rating'
    ]
    
    search_fields = [
        'title', 
        'description', 
        'author'
    ]
    
    list_editable = [
        'is_active', 
        'rating',
        'price'
    ]
    
    readonly_fields = [
        'downloads', 
        'created_at', 
        'updated_at'
    ]
    
    fieldsets = (
        ('Template Information', {
            'fields': (
                'title',
                'category',
                'format',
                'description',
                'author'
            )
        }),
        ('Settings', {
            'fields': (
                'price',
                'preview',
                'is_active',
                'rating'
            )
        }),
        ('File', {
            'fields': ('template_file',)
        }),
        ('Statistics', {
            'fields': (
                'downloads',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'make_active',
        'make_inactive',
        'make_free',
        'make_premium'
    ]
    
    def make_active(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} templates marked as active.")
    make_active.short_description = "Mark selected templates as active"
    
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} templates marked as inactive.")
    make_inactive.short_description = "Mark selected templates as inactive"
    
    def make_free(self, request, queryset):
        queryset.update(price='Free')
        self.message_user(request, f"{queryset.count()} templates marked as free.")
    make_free.short_description = "Mark selected templates as free"
    
    def make_premium(self, request, queryset):
        queryset.update(price='Premium')
        self.message_user(request, f"{queryset.count()} templates marked as premium.")
    make_premium.short_description = "Mark selected templates as premium"