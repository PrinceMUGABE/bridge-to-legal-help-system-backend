
# articles/urls.py
from django.urls import path
from . import views


urlpatterns = [
    # Public endpoints (no authentication required)
    path('', views.get_all_articles, name='get-all-articles'),
    path('<int:article_id>/', views.get_article, name='get-article'),
    path('featured/', views.get_featured_articles, name='get-featured-articles'),
    path('categories/', views.get_categories, name='get-categories'),
    path('search/', views.search_articles, name='search-articles'),
    
    # Admin only endpoints (authentication required)
    path('create/', views.create_article, name='create-article'),
    path('<int:article_id>/update/', views.update_article, name='update-article'),
    path('<int:article_id>/delete/', views.delete_article, name='delete-article'),
]