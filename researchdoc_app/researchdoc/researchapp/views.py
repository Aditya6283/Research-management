"""
All the view functions for the project live here. It's long but it's
broken up into clear sections so it's easy to scroll through.

Two view styles are mixed:
- Plain function views for the simple pages (dashboard, the AI endpoints,
  the settings page). They're easier to read when the view only really
  does one thing.
- Class-based views for the CRUD pages (project list/create/edit/delete,
  manage subscribers). The CBV gives you pagination and form handling
  basically for free.

A few cross-cutting bits to know about:
- @login_required and the LoginRequiredMixin keep anonymous users out.
- Every queryset is scoped by owner=request.user so people only ever
  see their own data.
- The AI views call OpenAI via LangChain but fall back to a deterministic
  algorithm if there's no API key set that way demos still work.
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.core.paginator import Paginator

from .models import (
    UserDetail, Subscription, PLAN_DEFINITIONS, get_active_subscription,
    ResearchProject, Resource, ResearchSummary, Citation,
    ComparisonTable, ComparisonColumn, ComparisonRow, ComparisonCell,
)
from .forms import (
    UserDetailFullForm, ResearchProjectForm, ResourceForm,
    ResearchSummaryForm, ComparisonTableForm,
    UserSettingsForm, PreferencesForm,
)

# The chatbot LLM returns Markdown; we convert it to HTML before rendering
# so bullet lists and **bold** look right. mark_safe tells Django the
# string is already safe HTML (the LLM output is from our own prompts so
# we trust it same call the labs use).
import markdown as _md_lib
from django.utils.safestring import mark_safe
from django.http import HttpResponse


# Build the LangChain LLM instance.
# Used by all four AI endpoints. Keeps the OpenAI vs Anthropic decision in
# one place looks at LLM_MODEL first (gpt-* → OpenAI, claude-* → Anthropic)
# and then at which key is actually configured. Returns None if there's no
# key at all, which makes every AI view drop to its fallback path.

def _build_llm(temperature=0.3, max_tokens=None):
    """Return a ready-to-use LangChain chat model, or None if no key is set."""
    from django.conf import settings
    model = (settings.LLM_MODEL or '').lower()
    has_openai = bool(settings.OPENAI_API_KEY)

    use_openai = (
        model.startswith(('gpt', 'o1', 'o3', 'o4')) and has_openai
        or (has_openai)
    )

    kwargs = {'temperature': temperature}
    if max_tokens:
        kwargs['max_tokens'] = max_tokens

    if use_openai:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.LLM_MODEL or 'gpt-5.4-mini',
            **kwargs,
        )
    return None


# Plan-based feature gating
# Real SaaS sites paywall features behind a plan. This is the same idea:
# the AI endpoints all sit behind this decorator and the plan dict in
# models.PLAN_DEFINITIONS is the single source of truth for what's unlocked.

def _feature_required(feature_key, error_msg=None):
    """Only run the view if the user's plan unlocks `feature_key`.

    For JSON / AJAX endpoints we return HTTP 402 (Payment Required) it's
    the standards-blessed status code for paywalled requests with a JSON
    body the client can show. For normal page views we just redirect to
    the pricing page with a flash message.
    """
    from functools import wraps

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            sub = get_active_subscription(request.user)
            if sub.feature_enabled(feature_key):
                return view_func(request, *args, **kwargs)
            msg = error_msg or "This feature requires a higher plan."
            # AJAX/JSON?
            wants_json = (
                request.headers.get('X-Requested-With') == 'XMLHttpRequest'
                or request.headers.get('Accept', '').startswith('application/json')
                or request.path.startswith('/researchdoc/ai/')
            )
            if wants_json:
                return JsonResponse({
                    'ok': False, 'error': msg,
                    'upgrade_url': reverse_lazy('pricing').__str__(),
                    'required_plan': 'Plus or Pro',
                }, status=402)
            messages.warning(request, msg + ' Upgrade to unlock it.')
            return redirect('pricing')
        return _wrapped
    return decorator


# Public pages

def index(request):
    """The marketing landing page. Anyone can hit this, no login needed."""
    return render(request, 'landingpage.html', {
        'title': 'ResearchDoc The Intelligent Space for Your Research',
    })


# Dashboard

@login_required
def dashboard(request):
    """The page you land on after logging in. Shows your projects + stats."""
    projects = ResearchProject.objects.filter(
        owner=request.user, is_archived=False,
    )
    total_citations = Citation.objects.filter(
        summary__project__owner=request.user,
    ).count()
    total_resources = Resource.objects.filter(
        project__owner=request.user,
    ).count()
    sub = get_active_subscription(request.user)
    return render(request, 'dashboard.html', {
        'projects': projects,
        'total_citations': total_citations,
        'total_resources': total_resources,
        'subscription': sub,
        'plan': sub.plan,
        'project_pct': min(100, int(100 * projects.count() / max(1, sub.max_projects))),
    })


# Research project CRUD
# Standard four-view pattern: list, create, edit, delete. Using Django's
# class-based views here because they handle the boring bits (pagination,
# form rendering, redirect-on-success) by themselves.

class ProjectListView(LoginRequiredMixin, ListView):
    """List the user's projects, paginated, with a search box."""
    model = ResearchProject
    template_name = 'project_list.html'
    context_object_name = 'projects'
    paginate_by = 5

    def get_queryset(self):
        # Only show projects this user owns. This is the authorisation check.
        queryset = ResearchProject.objects.filter(owner=self.request.user)

        # ?search=foo filters across title and description.
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(description__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    """Make a new research project. Also checks the user's plan cap."""
    model = ResearchProject
    form_class = ResearchProjectForm
    template_name = 'project_form.html'
    success_url = reverse_lazy('project_list')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            sub = get_active_subscription(request.user)
            current = ResearchProject.objects.filter(
                owner=request.user, is_archived=False,
            ).count()
            if current >= sub.max_projects:
                messages.warning(
                    request,
                    f"You've reached the {sub.get_plan_type_display()} plan limit of "
                    f"{sub.max_projects} project{'s' if sub.max_projects != 1 else ''}. "
                    f"Upgrade to add more.",
                )
                return redirect('pricing')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Set the owner to the logged-in user before saving
        form.instance.owner = self.request.user
        sub = get_active_subscription(self.request.user)
        form.instance.subscription = sub
        messages.success(self.request, f"Project '{form.instance.title}' created.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'create'
        return context


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    """Edit an existing project."""
    model = ResearchProject
    form_class = ResearchProjectForm
    template_name = 'project_form.html'

    def get_queryset(self):
        return ResearchProject.objects.filter(owner=self.request.user)

    def get_success_url(self):
        return reverse_lazy('project_detail', args=[self.object.pk])

    def form_valid(self, form):
        messages.success(self.request, "Project updated.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode'] = 'edit'
        return context


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a project. Cascades take care of everything inside it.

    Heads up: Django 4+ moved the actual deletion into form_valid(), so
    overriding delete() does nothing on modern Django (took me a while
    to spot that the success message wasn't firing).
    """
    model = ResearchProject
    template_name = 'project_confirm_delete.html'
    success_url = reverse_lazy('dashboard')

    def get_queryset(self):
        return ResearchProject.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        title = self.get_object().title
        response = super().form_valid(form)
        messages.success(self.request, f"Project '{title}' deleted.")
        return response


@login_required
def project_detail(request, pk):
    """Show all resources, summaries, and comparisons in a project."""
    project = get_object_or_404(ResearchProject, pk=pk, owner=request.user)
    return render(request, 'project_detail.html', {
        'project': project,
        'resources': project.resources.all(),
        'summaries': project.summaries.all(),
        'comparisons': project.comparisons.all(),
    })


# Resources papers and links uploaded into a project

@login_required
def resource_upload(request, project_pk=None):
    """Upload a PDF or add a link to a project. Honours the per-plan cap."""
    project = None
    if project_pk:
        project = get_object_or_404(
            ResearchProject, pk=project_pk, owner=request.user,
        )

    user_projects = ResearchProject.objects.filter(
        owner=request.user, is_archived=False,
    )
    sub = get_active_subscription(request.user)

    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        target_project_pk = request.POST.get('project')
        if not project and target_project_pk:
            project = get_object_or_404(
                ResearchProject, pk=target_project_pk, owner=request.user,
            )
        # Enforce per-project upload cap
        if project and project.resources.count() >= sub.max_papers_per_project:
            messages.warning(
                request,
                f"Your {sub.get_plan_type_display()} plan allows "
                f"{sub.max_papers_per_project} papers per project. "
                f"Upgrade for more.",
            )
            return redirect('pricing')
        if form.is_valid() and project:
            resource = form.save(commit=False)
            resource.project = project
            resource.save()  # save first so we have a file on disk

            # Extract text from PDF for full-text search and AI summarization
            extracted = f"{resource.title} {resource.description}"
            if resource.file:
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(resource.file.path)
                    pdf_text = []
                    for page in reader.pages[:30]:  # limit to first 30 pages
                        try:
                            pdf_text.append(page.extract_text() or '')
                        except Exception:
                            continue
                    extracted = (extracted + '\n' + '\n'.join(pdf_text)).strip()
                except Exception as e:
                    messages.warning(
                        request,
                        f"Uploaded, but couldn't extract PDF text: {e}",
                    )

            resource.extracted_text = extracted[:50000]  # cap at 50k chars
            resource.save(update_fields=['extracted_text'])

            messages.success(request, f"'{resource.title}' uploaded.")
            return redirect('project_detail', pk=project.pk)
    else:
        form = ResourceForm()

    recent = Resource.objects.filter(project__owner=request.user)[:10]
    total = Resource.objects.filter(project__owner=request.user).count()
    return render(request, 'upload_paper.html', {
        'form': form, 'project': project,
        'user_projects': user_projects,
        'recent_uploads': recent, 'total_uploads': total,
        'subscription': sub,
    })


@login_required
@require_POST
def resource_delete(request, pk):
    resource = get_object_or_404(Resource, pk=pk, project__owner=request.user)
    project_pk = resource.project.pk
    resource.delete()
    messages.success(request, "Resource deleted.")
    return redirect('project_detail', pk=project_pk)


# ====
# Research summaries with citations
# ====

@login_required
def summary_view(request, project_pk=None):
    """Combined summary editor + citations + comparison shortcuts."""
    project = None
    if project_pk:
        project = get_object_or_404(
            ResearchProject, pk=project_pk, owner=request.user,
        )

    summary = None
    summary_pk = request.GET.get('summary')
    if summary_pk and project:
        summary = ResearchSummary.objects.filter(
            pk=summary_pk, project=project,
        ).first()

    if request.method == 'POST' and project:
        form = ResearchSummaryForm(request.POST, instance=summary)
        if form.is_valid():
            s = form.save(commit=False)
            s.project = project
            s.author = request.user
            s.save()
            messages.success(request, "Summary saved.")
            return redirect('summary_view', project_pk=project.pk)
    else:
        form = ResearchSummaryForm(instance=summary)

    citations = []
    if summary:
        citations = summary.citations.select_related('resource').all()

    available_resources = []
    if project:
        available_resources = project.resources.all()

    return render(request, 'summary.html', {
        'project': project, 'summary': summary, 'form': form,
        'citations': citations,
        'available_resources': available_resources,
        'comparisons': project.comparisons.all() if project else [],
    })


@login_required
@require_POST
def citation_add(request, summary_pk):
    """
    Add a citation in the chosen academic style. If the user supplies
    custom citation text it is used as-is; otherwise the citation is
    auto-formatted from the linked Resource's bibliographic metadata.
    """
    from .citations import format_citation
    summary = get_object_or_404(
        ResearchSummary, pk=summary_pk, project__owner=request.user,
    )
    resource_id = request.POST.get('resource_id')
    resource = get_object_or_404(
        Resource, pk=resource_id, project__owner=request.user,
    )
    style = request.POST.get('style', Citation.APA)
    if style not in dict(Citation.STYLE_CHOICES):
        style = Citation.APA

    # Free plan is APA-only
    sub = get_active_subscription(request.user)
    if style != Citation.APA and not sub.feature_enabled('all_citation_styles'):
        messages.info(
            request,
            "Only APA is available on the Free plan your citation was "
            "saved as APA. Upgrade to Plus or Pro for IEEE, MLA, Chicago, "
            "and Harvard.",
        )
        style = Citation.APA

    citation_text = request.POST.get('citation_text', '').strip()
    if not citation_text:
        citation_text = format_citation(resource, style)
    citation_text = citation_text[:1000]

    Citation.objects.create(
        summary=summary, resource=resource,
        citation_text=citation_text, style=style,
    )
    messages.success(request, f"Citation added in {dict(Citation.STYLE_CHOICES)[style]}.")
    return redirect(request.META.get('HTTP_REFERER', '/researchdoc/dashboard/'))


@login_required
@require_POST
def citation_restyle(request, pk):
    """Regenerate a citation in a different style."""
    from .citations import format_citation
    citation = get_object_or_404(
        Citation, pk=pk, summary__project__owner=request.user,
    )
    new_style = request.POST.get('style', Citation.APA)
    if new_style not in dict(Citation.STYLE_CHOICES):
        new_style = Citation.APA
    citation.style = new_style
    citation.citation_text = format_citation(citation.resource, new_style)[:1000]
    citation.save(update_fields=['style', 'citation_text'])
    return JsonResponse({
        'ok': True, 'citation_text': citation.citation_text,
        'style': new_style,
    })


@login_required
@require_POST
def citation_delete(request, pk):
    citation = get_object_or_404(
        Citation, pk=pk, summary__project__owner=request.user,
    )
    citation.delete()
    return redirect(request.META.get('HTTP_REFERER', '/researchdoc/dashboard/'))


# ====
# Comparison tables the spreadsheet-style "compare three tools" view
# ====

@login_required
def comparison_create(request, project_pk):
    project = get_object_or_404(
        ResearchProject, pk=project_pk, owner=request.user,
    )
    if request.method == 'POST':
        form = ComparisonTableForm(request.POST)
        if form.is_valid():
            table = form.save(commit=False)
            table.project = project
            table.save()
            # Seed a default 4-column / 4-row layout
            for i, name in enumerate(['Feature', 'Tool A', 'Tool B', 'Tool C']):
                ComparisonColumn.objects.create(table=table, name=name, order=i)
            for i, label in enumerate(['Accuracy', 'Speed', 'Cost', 'Integration']):
                ComparisonRow.objects.create(table=table, label=label, order=i)
            return redirect('comparison_edit', pk=table.pk)
    else:
        form = ComparisonTableForm()
    return render(request, 'comparison_form.html', {
        'form': form, 'project': project,
    })


@login_required
def comparison_edit(request, pk):
    table = get_object_or_404(
        ComparisonTable, pk=pk, project__owner=request.user,
    )
    rows = list(table.rows.all())
    columns = list(table.columns.all())
    cells = {(c.row_id, c.column_id): c for c in table.cells.all()}

    matrix = []
    for r in rows:
        row_cells = []
        for c in columns:
            cell = cells.get((r.id, c.id))
            row_cells.append({
                'row_id': r.id, 'col_id': c.id,
                'value': cell.value if cell else '',
            })
        matrix.append({'row': r, 'cells': row_cells})

    return render(request, 'comparison_edit.html', {
        'table': table, 'rows': rows, 'columns': columns,
        'matrix': matrix, 'project': table.project,
    })


@login_required
@require_POST
def comparison_save(request, pk):
    """AJAX endpoint that accepts JSON and rewrites table contents."""
    table = get_object_or_404(
        ComparisonTable, pk=pk, project__owner=request.user,
    )
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    title = data.get('title', '').strip()
    if title:
        table.title = title
        table.save(update_fields=['title', 'updated_at'])

    table.cells.all().delete()
    table.columns.all().delete()
    table.rows.all().delete()

    cols = [
        ComparisonColumn.objects.create(table=table, name=n, order=i)
        for i, n in enumerate(data.get('columns', []))
    ]
    rows = [
        ComparisonRow.objects.create(table=table, label=l, order=i)
        for i, l in enumerate(data.get('rows', []))
    ]
    for r_idx, row_values in enumerate(data.get('cells', [])):
        for c_idx, value in enumerate(row_values):
            if r_idx < len(rows) and c_idx < len(cols):
                ComparisonCell.objects.create(
                    table=table, row=rows[r_idx],
                    column=cols[c_idx], value=value or '',
                )
    return JsonResponse({'ok': True})


@login_required
@require_POST
def comparison_delete(request, pk):
    table = get_object_or_404(
        ComparisonTable, pk=pk, project__owner=request.user,
    )
    project_pk = table.project.pk
    table.delete()
    messages.success(request, "Comparison deleted.")
    return redirect('project_detail', pk=project_pk)
