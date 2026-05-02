from django.urls import path

from . import views
from .views import (
    ProjectListView, ProjectCreateView, ProjectUpdateView, ProjectDeleteView,
    ManageSubscribersView, SubscriberCreateView,
    SubscriberUpdateView, SubscriberDeleteView,
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

    path('summary/', views.summary_view, name='summary_blank'),
    path('projects/<int:project_pk>/summary/', views.summary_view, name='summary_view'),
    path('citations/<int:summary_pk>/add/', views.citation_add, name='citation_add'),
    path('citations/<int:pk>/delete/', views.citation_delete, name='citation_delete'),
    path('citations/<int:pk>/restyle/', views.citation_restyle, name='citation_restyle'),

    path('projects/<int:project_pk>/comparison/add/', views.comparison_create, name='comparison_create'),
    path('comparison/<int:pk>/edit/', views.comparison_edit, name='comparison_edit'),
    path('comparison/<int:pk>/save/', views.comparison_save, name='comparison_save'),
    path('comparison/<int:pk>/delete/', views.comparison_delete, name='comparison_delete'),

    path('insight/', views.insight_search, name='insight'),

    path('settings/', views.settings_view, name='settings'),
    path('pricing/', views.pricing, name='pricing'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('oauth-check/<str:provider>/', views.oauth_check, name='oauth_check'),

    path('manage/', ManageSubscribersView.as_view(), name='manage_subscribers'),
    path('manage/add/', SubscriberCreateView.as_view(), name='subscriber_add'),
    path('manage/edit/<int:pk>/', SubscriberUpdateView.as_view(), name='subscriber_edit'),
    path('manage/delete/<int:pk>/', SubscriberDeleteView.as_view(), name='subscriber_delete'),
]
