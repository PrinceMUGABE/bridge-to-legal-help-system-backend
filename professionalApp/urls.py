from django.urls import path
from . import views

app_name = 'lawyerApp'

urlpatterns = [
    # Create a new lawyer
    path('create/', views.create_lawyer, name='create_lawyer'),
    
    # Get, update, and delete a lawyer by ID
    path('<int:lawyer_id>/', views.get_lawyer_by_id, name='get_lawyer_by_id'),
    path('update/<int:lawyer_id>/', views.update_lawyer, name='update_lawyer'),
    path('delete/<int:lawyer_id>/', views.delete_lawyer, name='delete_lawyer'),
    
    # Get all lawyers with filtering options
    path('lawyers/', views.get_all_lawyers, name='get_all_lawyers'),
    
    # Get lawyers by specific criteria
    path('created-by-me/', views.get_lawyers_created_by_user, name='get_lawyers_created_by_user'),
    path('redidence/', views.get_lawyers_by_residence, name='get_lawyers_by_residence'),
    
    # Get lawyer info for the logged-in user
    path('user/', views.get_logged_in_lawyer_info, name='get_logged_in_lawyer_info'),
]