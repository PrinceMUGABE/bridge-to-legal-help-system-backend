# templates/urls.py
from django.urls import path
from . import views

app_name = 'templates'

urlpatterns = [
    # Template CRUD operations
    path('', views.get_all_templates, name='get_all_templates'),
    path('create/', views.create_template, name='create_template'),
    path('<int:template_id>/', views.get_template_detail, name='get_template_detail'),
    path('<int:template_id>/update/', views.update_template, name='update_template'),
    path('<int:template_id>/delete/', views.delete_template, name='delete_template'),
    
    # Template actions
    path('<int:template_id>/download/', views.download_template, name='download_template'),
    
    # Template metadata
    path('categories/', views.get_template_categories, name='get_template_categories'),
    path('statistics/', views.get_template_statistics, name='get_template_statistics'),
    path('popular/', views.get_popular_templates, name='get_popular_templates'),
]