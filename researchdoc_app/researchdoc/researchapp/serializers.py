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


class ComparisonColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComparisonColumn
        fields = ['id', 'name', 'order']
        read_only_fields = ['id']


class ComparisonRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComparisonRow
        fields = ['id', 'label', 'order']
        read_only_fields = ['id']


class ComparisonCellSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComparisonCell
        fields = ['id', 'row', 'column', 'value']
        read_only_fields = ['id']


class ComparisonTableSerializer(serializers.ModelSerializer):
    """A whole comparison spreadsheet in one JSON object.

    Rebuilding the table from its parts (columns, rows, cells) on the
    frontend means we hand it over as one nested document rather than
    making the client do four separate fetches.
    """
    columns = ComparisonColumnSerializer(many=True, read_only=True)
    rows = ComparisonRowSerializer(many=True, read_only=True)
    cells = ComparisonCellSerializer(many=True, read_only=True)

    class Meta:
        model = ComparisonTable
        fields = [
            'id', 'project', 'title',
            'columns', 'rows', 'cells',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at',
                            'columns', 'rows', 'cells']


class ResearchProjectSerializer(serializers.ModelSerializer):
    """Project metadata plus counts (resources / summaries / comparisons).

    We deliberately *don't* nest the full child lists here for a user
    with 50 projects that would mean a huge payload. The client asks
    for `/api/resources/?project=<id>` separately when it actually
    needs the children.
    """
    resource_count = serializers.IntegerField(
        source='resources.count', read_only=True,
    )
    summary_count = serializers.IntegerField(
        source='summaries.count', read_only=True,
    )
    comparison_count = serializers.IntegerField(
        source='comparisons.count', read_only=True,
    )
    owner_username = serializers.CharField(
        source='owner.username', read_only=True,
    )

    class Meta:
        model = ResearchProject
        fields = [
            'id', 'title', 'description', 'owner', 'owner_username',
            'subscription', 'is_archived',
            'resource_count', 'summary_count', 'comparison_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'owner', 'owner_username',
                            'resource_count', 'summary_count',
                            'comparison_count', 'created_at', 'updated_at']


class SubscriptionSerializer(serializers.ModelSerializer):
    """SaaS subscription (read-only for the API user)."""
    plan_display = serializers.CharField(
        source='get_plan_type_display', read_only=True,
    )

    class Meta:
        model = Subscription
        fields = [
            'id', 'name', 'plan_type', 'plan_display',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = '__all__'.split()  # entire serializer is read-only
