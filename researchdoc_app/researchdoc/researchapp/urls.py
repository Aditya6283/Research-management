"""
URL routes for the researchapp app.

Every entry maps a URL pattern to a view, and gives it a `name=` so
templates can use {% url 'name' %} instead of hardcoding the path. The
project-level urls.py adds the /researchdoc/ prefix on top of these.

The DRF `router.register(...)` calls near the top auto-generate full
CRUD URL patterns for each viewset (list / retrieve / create / update /
delete) that's the bulk of /researchdoc/api/.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from .views import (
    ProjectListView, ProjectCreateView, ProjectUpdateView, ProjectDeleteView,
    ManageSubscribersView, SubscriberCreateView,
    SubscriberUpdateView, SubscriberDeleteView,
)
from . import api_views


# DRF router. Each register() call creates list + detail URLs for one
# viewset (e.g. /api/projects/ and /api/projects/<id>/). The list is short
# but it covers full CRUD for every resource that's the point of using
# the router rather than spelling out every path by hand.

router = DefaultRouter()
router.register(r'projects', api_views.ResearchProjectViewSet, basename='api-projects')
router.register(r'resources', api_views.ResourceViewSet, basename='api-resources')
router.register(r'summaries', api_views.ResearchSummaryViewSet, basename='api-summaries')
router.register(r'citations', api_views.CitationViewSet, basename='api-citations')
router.register(r'comparison-tables', api_views.ComparisonTableViewSet, basename='api-comparison-tables')
router.register(r'subscriptions', api_views.SubscriptionViewSet, basename='api-subscriptions')

urlpatterns = [
    # Public
    path('', views.index, name='index'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Research project CRUD (class-based views)
    path('projects/', ProjectListView.as_view(), name='project_list'),
    path('projects/add/', ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/', ProjectUpdateView.as_view(), name='project_edit'),
    path('projects/<int:pk>/delete/', ProjectDeleteView.as_view(), name='project_delete'),

    # Papers and links inside a project
    path('resources/upload/', views.resource_upload, name='resource_upload'),
    path('projects/<int:project_pk>/upload/', views.resource_upload, name='resource_upload_for_project'),
    path('resources/<int:pk>/delete/', views.resource_delete, name='resource_delete'),

    # Written summaries and the citations that live inside them
    path('summary/', views.summary_view, name='summary_blank'),
    path('projects/<int:project_pk>/summary/', views.summary_view, name='summary_view'),
    path('citations/<int:summary_pk>/add/', views.citation_add, name='citation_add'),
    path('citations/<int:pk>/delete/', views.citation_delete, name='citation_delete'),
    path('citations/<int:pk>/restyle/', views.citation_restyle, name='citation_restyle'),

    # Comparison tables
    path('projects/<int:project_pk>/comparison/add/', views.comparison_create, name='comparison_create'),
    path('comparison/<int:pk>/edit/', views.comparison_edit, name='comparison_edit'),
    path('comparison/<int:pk>/save/', views.comparison_save, name='comparison_save'),
    path('comparison/<int:pk>/delete/', views.comparison_delete, name='comparison_delete'),

    # Search across all the user's resources + summaries
    path('insight/', views.insight_search, name='insight'),

    # AI endpoints see views.ai_* for what each one does
    path('ai/refine/', views.ai_refine_summary, name='ai_refine'),
    path('ai/suggest/', views.ai_suggest_citations, name='ai_suggest'),
    path('ai/summarize/', views.ai_summarize_paper, name='ai_summarize'),
    path('ai/summarize-project/', views.ai_summarize_project, name='ai_summarize_project'),

    # AI Research Coach chatbot HTMX + session-stored conversation
    path('chat/<int:project_pk>/', views.research_chat_ui, name='research_chat_ui'),
    path('chat/<int:project_pk>/reset/', views.research_chat_reset, name='research_chat_reset'),
    path('chat/init/', views.research_chat_init, name='research_chat_init'),
    path('chat/', views.research_chat, name='research_chat'),

    # User settings (profile + appearance)
    path('settings/', views.settings_view, name='settings'),

    # Subscription / pricing
    path('pricing/', views.pricing, name='pricing'),
    path('subscribe/', views.subscribe, name='subscribe'),

    # Friendly OAuth-not-configured check (intercepts the social buttons)
    path('oauth-check/<str:provider>/', views.oauth_check, name='oauth_check'),

    # REST API DRF's auto-router gives us /api/projects/, /api/resources/ etc.
    # The "api-auth/" line just gives the browsable API a login/logout link.
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),

    # Admin-side subscriber CRUD
    path('manage/', ManageSubscribersView.as_view(), name='manage_subscribers'),
    path('manage/add/', SubscriberCreateView.as_view(), name='subscriber_add'),
    path('manage/edit/<int:pk>/', SubscriberUpdateView.as_view(), name='subscriber_edit'),
    path('manage/delete/<int:pk>/', SubscriberDeleteView.as_view(), name='subscriber_delete'),
]
