"""
The REST API endpoints.

A `ModelViewSet` is DRF's shortcut for "give me list / retrieve / create
/ update / partial-update / delete on this model" in a single class.
Combined with the DefaultRouter over in urls.py, each one expands into
six URL patterns automatically. So this file looks small but it's doing
a lot.

Important security bit: every viewset overrides get_queryset() to scope
results to the request user. Even though DRF requires authentication
globally, that on its own would let user A query user B's projects by
guessing IDs. The owner filter is what stops that.
"""
from rest_framework import viewsets, permissions
from rest_framework.response import Response

from .models import (
    ResearchProject, Resource, ResearchSummary, Citation,
    ComparisonTable, Subscription,
)
from .serializers import (
    ResearchProjectSerializer, ResourceSerializer,
    ResearchSummarySerializer, CitationSerializer,
    ComparisonTableSerializer, SubscriptionSerializer,
)


class OwnedResourceMixin:
    permission_classes = [permissions.IsAuthenticated]

    def get_owner_filter(self):
        return {}

    def get_queryset(self):  # type: ignore[override]
        return self.queryset.filter(**self.get_owner_filter())


class ResearchProjectViewSet(OwnedResourceMixin, viewsets.ModelViewSet):
    """CRUD on projects. The owner is set from the logged-in user on create."""
    queryset = ResearchProject.objects.all()
    serializer_class = ResearchProjectSerializer

    def get_owner_filter(self):
        return {'owner': self.request.user}

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ResourceViewSet(OwnedResourceMixin, viewsets.ModelViewSet):
    """CRUD on resources. Supports `?project=<id>` to filter by one project."""
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer

    def get_owner_filter(self):
        return {'project__owner': self.request.user}

    def get_queryset(self):
        qs = super().get_queryset()
        project_id = self.request.query_params.get('project')
        if project_id and project_id.isdigit():
            qs = qs.filter(project_id=int(project_id))
        return qs
