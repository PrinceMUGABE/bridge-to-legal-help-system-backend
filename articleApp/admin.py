# articles/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = [
        'title', 
        'category', 
        'author',
        'featured',  # Added featured to list_display
        'get_status_badge',
        'views', 
        'read_time',
        'date'
    ]
    list_filter = ['category', 'featured', 'date']
    search_fields = ['title', 'excerpt', 'author']
    list_editable = ['featured']
    readonly_fields = ['views', 'created_at', 'updated_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Article Content', {
            'fields': ('title', 'excerpt', 'content', 'image')
        }),
        ('Article Details', {
            'fields': ('category', 'author', 'read_time', 'featured')
        }),
        ('Statistics', {
            'fields': ('views', 'date'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_status_badge(self, obj):
        if obj.featured:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Featured</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #17a2b8; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Regular</span>'
            )
    get_status_badge.short_description = 'Status'