"""
All the database tables for ResearchDoc.

Each Python class is one SQL table. Each class attribute is one column.
The links between tables (ForeignKey, OneToOneField) describe how rows
in one table point at rows in another.

The chain of ownership looks like:
    User -> UserDetail
         -> Subscription
         -> ResearchProject -> Resource
                            -> ResearchSummary -> Citation -> Resource
                            -> ComparisonTable -> Column / Row / Cell

Everything cascades on delete from the top down. So if you delete a User
their projects vanish, and with each project goes its resources,
summaries, citations and comparison tables.
"""
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class UserDetail(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    firstname = models.CharField(max_length=100, blank=True)
    surname = models.CharField(max_length=100, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.firstname or self.surname:
            return f"{self.firstname} {self.surname}".strip()
        return self.user.username


class Subscription(models.Model):
    """The user's current plan: free / plus / pro.

    The interesting bits the price, the project cap, which AI features
    are unlocked live in PLAN_DEFINITIONS below the class. This row
    just records *which* plan a user is on. The admin manages these
    with paging + archive (no real delete) because that's how real
    SaaS billing systems work.
    """
    FREE = 'free'
    PLUS = 'plus'
    PRO = 'pro'
    PLAN_CHOICES = [
        (FREE, 'Free'),
        (PLUS, 'Plus'),
        (PRO, 'Pro'),
    ]

    name = models.CharField(max_length=200)
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES, default=FREE)
    is_active = models.BooleanField(default=True, help_text='False means archived')
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='subscriptions', null=True, blank=True,
    )
    # When the user "upgraded" to this plan (renewal date for billing UI)
    renewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_plan_type_display()})"

    # --- Convenience accessors used by views and templates ---

    @property
    def plan(self):
        return PLAN_DEFINITIONS.get(self.plan_type, PLAN_DEFINITIONS[self.FREE])

    @property
    def max_projects(self):
        return self.plan['max_projects']

    @property
    def max_papers_per_project(self):
        return self.plan['max_papers_per_project']

    def feature_enabled(self, feature_key):
        """True if the current plan unlocks the named feature."""
        return feature_key in self.plan['features']


# Single source of truth for what each plan includes. The pricing
# page, dashboard widgets, and limit checks all read from here.
PLAN_DEFINITIONS = {
    Subscription.FREE: {
        'name': 'Free',
        'price': 0,
        'price_label': '$0',
        'tagline': 'Get started with the basics.',
        'max_projects': 2,
        'max_papers_per_project': 5,
        'max_summaries_per_project': 2,
        'features': {
            'basic_search',
            'manual_citations',
        },
        'feature_list': [
            ('Up to 2 research projects', True),
            ('5 papers per project', True),
            ('Manual citation entry', True),
            ('Basic full-text search', True),
            ('APA citation style only', True),
            ('AI paper summarisation', False),
            ('AI project synthesis', False),
            ('AI citation suggestions', False),
            ('AI summary refinement', False),
            ('IEEE / MLA / Chicago / Harvard styles', False),
            ('Visual comparison tables', False),
        ],
    },
    Subscription.PLUS: {
        'name': 'Plus',
        'price': 9,
        'price_label': '$9',
        'tagline': 'For active researchers and PhD students.',
        'max_projects': 10,
        'max_papers_per_project': 50,
        'max_summaries_per_project': 20,
        'features': {
            'basic_search',
            'manual_citations',
            'all_citation_styles',
            'ai_paper_summary',
            'ai_suggest_citations',
            'comparison_tables',
        },
        'feature_list': [
            ('Up to 10 research projects', True),
            ('50 papers per project', True),
            ('All 5 citation styles (APA, IEEE, MLA, Chicago, Harvard)', True),
            ('AI paper summarisation', True),
            ('AI citation suggestions', True),
            ('Visual comparison tables', True),
            ('Full-text search across all papers', True),
            ('AI project synthesis', False),
            ('AI summary refinement', False),
            ('Priority email support', False),
        ],
    },
    Subscription.PRO: {
        'name': 'Pro',
        'price': 29,
        'price_label': '$29',
        'tagline': 'Everything unlocked for research labs and power users.',
        'max_projects': 9999,
        'max_papers_per_project': 999,
        'max_summaries_per_project': 999,
        'features': {
            'basic_search',
            'manual_citations',
            'all_citation_styles',
            'ai_paper_summary',
            'ai_suggest_citations',
            'ai_project_summary',
            'ai_refine_summary',
            'comparison_tables',
            'priority_support',
        },
        'feature_list': [
            ('Unlimited research projects', True),
            ('Unlimited papers per project', True),
            ('All 5 citation styles', True),
            ('AI paper summarisation', True),
            ('AI citation suggestions', True),
            ('AI project synthesis (full-corpus)', True),
            ('AI summary refinement', True),
            ('Visual comparison tables', True),
            ('Priority email support', True),
        ],
    },
}


def get_active_subscription(user):
    """Return the user's active subscription, falling back to a Free record."""
    sub = Subscription.objects.filter(owner=user, is_active=True).order_by('-created_at').first()
    if sub:
        return sub
    return Subscription.objects.create(
        owner=user, name=f"{user.username}'s workspace",
        plan_type=Subscription.FREE, is_active=True,
    )


class ResearchProject(models.Model):
    """One research project the main workspace concept of the app.

    A project is just a labelled container for resources, summaries and
    comparison tables. The owner ForeignKey is what enforces
    "everyone sees their own projects only".
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    subscription = models.ForeignKey(
        Subscription, on_delete=models.SET_NULL,
        related_name='projects', null=True, blank=True,
    )
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('project_detail', args=[self.pk])

