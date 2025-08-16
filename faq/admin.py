# faq/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import FAQ


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = [
        'question_preview',
        'category', 
        'popular',
        'get_status_badge',
        'is_active',
        'created_at'
    ]
    list_filter = ['category', 'popular', 'is_active', 'created_at']
    search_fields = ['question', 'answer']
    list_editable = ['popular', 'is_active']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('FAQ Content', {
            'fields': ('question', 'answer')
        }),
        ('Classification', {
            'fields': ('category', 'popular', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def question_preview(self, obj):
        """Show truncated question for better display"""
        if len(obj.question) > 60:
            return obj.question[:60] + '...'
        return obj.question
    question_preview.short_description = 'Question'
    
    def get_status_badge(self, obj):
        if obj.popular and obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Popular</span>'
            )
        elif obj.is_active:
            return format_html(
                '<span style="background-color: #17a2b8; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Active</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #6c757d; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Inactive</span>'
            )
    get_status_badge.short_description = 'Status'
    
    actions = ['make_popular', 'remove_popular', 'activate_faqs', 'deactivate_faqs']
    
    def make_popular(self, request, queryset):
        updated = queryset.update(popular=True)
        self.message_user(request, f'{updated} FAQs were marked as popular.')
    make_popular.short_description = "Mark selected FAQs as popular"
    
    def remove_popular(self, request, queryset):
        updated = queryset.update(popular=False)
        self.message_user(request, f'{updated} FAQs were removed from popular.')
    remove_popular.short_description = "Remove popular status from selected FAQs"
    
    def activate_faqs(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} FAQs were activated.')
    activate_faqs.short_description = "Activate selected FAQs"
    
    def deactivate_faqs(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} FAQs were deactivated.')
    deactivate_faqs.short_description = "Deactivate selected FAQs"