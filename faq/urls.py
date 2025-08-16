
# faq/urls.py
from django.urls import path
from . import views


urlpatterns = [
    # Public endpoints (no authentication required)
    path('', views.get_all_faqs, name='get-all-faqs'),
    path('<int:faq_id>/', views.get_faq, name='get-faq'),
    path('popular/', views.get_popular_faqs, name='get-popular-faqs'),
    path('categories/', views.get_categories, name='get-categories'),
    path('search/', views.search_faqs, name='search-faqs'),
    
    # Admin only endpoints (authentication required)
    path('create/', views.create_faq, name='create-faq'),
    path('<int:faq_id>/update/', views.update_faq, name='update-faq'),
    path('<int:faq_id>/delete/', views.delete_faq, name='delete-faq'),
]