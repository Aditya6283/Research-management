from django.urls import path

from . import views
from .views import (
    ProjectListView, ProjectCreateView, ProjectUpdateView, ProjectDeleteView,
)

urlpatterns = [
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('projects/', ProjectListView.as_view(), name='project_list'),
    path('projects/add/', ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/', ProjectUpdateView.as_view(), name='project_edit'),
    path('projects/<int:pk>/delete/', ProjectDeleteView.as_view(), name='project_delete'),

    path('resources/upload/', views.resource_upload, name='resource_upload'),
    path('projects/<int:project_pk>/upload/', views.resource_upload, name='resource_upload_for_project'),
    path('resources/<int:pk>/delete/', views.resource_delete, name='resource_delete'),
]
