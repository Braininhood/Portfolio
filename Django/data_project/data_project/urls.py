from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('upload/', views.upload_file, name='upload_file'),
    path('connect-database/', views.connect_database, name='connect_database'),
    path('file/<int:file_id>/', views.file_detail, name='file_detail'),
    path('file/<int:file_id>/visualization/create/', views.create_visualization, name='create_visualization'),
    path('file/<int:file_id>/visualization/preview/', views.preview_visualization, name='preview_visualization'),
    path('file/<int:file_id>/clean/', views.clean_data, name='clean_data'),
    path('file/<int:file_id>/batch-clean/', views.batch_clean, name='batch_clean'),
    path('file/<int:file_id>/delete/', views.delete_file, name='delete_file'),
    path('visualization/<int:viz_id>/delete/', views.delete_visualization, name='delete_visualization'),
    path('index/', views.index, name='index'),
    # Advanced visualization routes
    path('file/<int:file_id>/advanced-visualization/', views.advanced_visualization, name='advanced_visualization'),
    path('file/<int:file_id>/visualization/custom-preview/', views.custom_visualization_preview, name='custom_visualization_preview'),
] 