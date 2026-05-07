"""
Serializers translate between Python objects (the model instances we
work with internally) and JSON (what the REST API sends and receives).

`ModelSerializer` is the shortcut form point it at a model, list the
fields you want exposed, and you get validation, JSON output and JSON
input for free. You only have to drop into a regular `Serializer` when
the API shape doesn't match your model.

Two patterns that show up a lot below:
  - "display" fields (`style_display`, `resource_type_display`) that
    return the human-readable label of a choices field. Saves the
    frontend having to know the mapping.
  - nested read-only serializers (Summary embeds its Citations,
    ComparisonTable embeds Columns/Rows/Cells) so the client can render
    a whole sub-tree in one round trip.
"""
from rest_framework import serializers
from .models import (
    ResearchProject, Resource, ResearchSummary, Citation,
    ComparisonTable, ComparisonColumn, ComparisonRow, ComparisonCell,
    Subscription,
)


class ResourceSerializer(serializers.ModelSerializer):
    """The full Resource row title, file/url, and all the bib metadata."""
    resource_type_display = serializers.CharField(
        source='get_resource_type_display', read_only=True,
    )
    file_size_display = serializers.CharField(read_only=True)

    class Meta:
        model = Resource
        fields = [
            'id', 'project', 'title', 'description',
            'resource_type', 'resource_type_display',
            'file', 'url', 'file_size_display',
            'authors', 'year', 'venue', 'volume', 'issue', 'pages', 'doi',
            'uploaded_at',
        ]
        read_only_fields = ['id', 'uploaded_at', 'file_size_display',
                            'resource_type_display']


class CitationSerializer(serializers.ModelSerializer):
    """One Citation row, including the already-formatted text and its style."""
    style_display = serializers.CharField(
        source='get_style_display', read_only=True,
    )

    class Meta:
        model = Citation
        fields = [
            'id', 'summary', 'resource',
            'citation_text', 'style', 'style_display',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'style_display']


class ResearchSummarySerializer(serializers.ModelSerializer):
    """Summary plus the list of citations it contains (citations are nested read-only)."""
    citations = CitationSerializer(many=True, read_only=True)
    citation_count = serializers.IntegerField(
        source='citations.count', read_only=True,
    )

    class Meta:
        model = ResearchSummary
        fields = [
            'id', 'project', 'title', 'content', 'author',
            'citations', 'citation_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at',
                            'citations', 'citation_count']
