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


# ====
# Search across resources + summaries uses extracted PDF text
# ====

@login_required
def insight_search(request):
    query = request.GET.get('q', '').strip()
    project_filter = request.GET.getlist('project')

    resource_qs = Resource.objects.filter(project__owner=request.user)
    summary_qs = ResearchSummary.objects.filter(project__owner=request.user)

    if query:
        resource_qs = resource_qs.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(extracted_text__icontains=query)
        )
        summary_qs = summary_qs.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )

    if project_filter:
        resource_qs = resource_qs.filter(project_id__in=project_filter)
        summary_qs = summary_qs.filter(project_id__in=project_filter)

    combined = []
    for r in resource_qs:
        combined.append({
            'type': 'resource', 'title': r.title,
            'description': r.description, 'project': r.project,
            'url': r.project.get_absolute_url(),
            'badge': r.get_resource_type_display(),
        })
    for s in summary_qs:
        combined.append({
            'type': 'summary', 'title': s.title,
            'description': (s.content or '')[:200], 'project': s.project,
            'url': s.project.get_absolute_url(),
            'badge': 'Summary',
        })

    paginator = Paginator(combined, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    user_projects = ResearchProject.objects.filter(owner=request.user)
    return render(request, 'insight.html', {
        'query': query, 'results': page_obj,
        'user_projects': user_projects,
        'selected_projects': [
            int(p) for p in project_filter if p.isdigit()
        ],
        'total_count': len(combined),
    })


# AI features
# All four AI endpoints follow the same shape:
#   1. Build a PromptTemplate.
#   2. Compose `chain = prompt | llm` (or `| parser` for structured output).
#   3. Call chain.invoke(...) and return the result.
# When there's no API key set, each view falls back to a deterministic
# algorithm so the demo doesn't break on a fresh machine.

@login_required
@require_POST
@_feature_required('ai_refine_summary',
                   'AI summary refinement is a Pro-tier feature.')
def ai_refine_summary(request):
    """Polish an existing summary improves tone without changing facts."""
    from django.conf import settings

    summary_pk = request.POST.get('summary_pk')
    summary = get_object_or_404(
        ResearchSummary, pk=summary_pk, project__owner=request.user,
    )
    resources = summary.project.resources.all()
    resource_context = "\n".join(
        f"- {r.title}: {r.description or '(no description)'}"
        for r in resources
    )

    if not settings.OPENAI_API_KEY:
        return JsonResponse({
            'ok': False,
            'error': 'No LLM API key configured on the server.',
        }, status=503)

    try:
        llm = _build_llm(temperature=0.7)
        from langchain_core.prompts import PromptTemplate
        prompt = PromptTemplate(
            template=(
                "You are an academic editor helping a researcher polish a "
                "literature-review summary. Improve clarity, flow, and "
                "academic tone while preserving every claim already in the "
                "draft. Use the project's resources for context only never "
                "introduce citations, numbers, or claims that are not present "
                "in the draft.\n\n"
                "Project resources (context only):\n{resources}\n\n"
                "Current draft:\n{draft}\n\n"
                "Return ONLY the refined Markdown text no preamble, no "
                "explanation of what you changed. Preserve any existing "
                "**Section Headers** the user has used."
            ),
            input_variables=['resources', 'draft'],
        )
        chain = prompt | llm
        result = chain.invoke({
            'resources': resource_context,
            'draft': summary.content,
        })
        refined = getattr(result, 'content', str(result))
        return JsonResponse({'ok': True, 'content': refined})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@login_required
@require_POST
@_feature_required('ai_suggest_citations',
                   'AI citation suggestions require a Plus or Pro plan.')
def ai_suggest_citations(request):
    """
    Suggest which uploaded resources are most relevant to a summary.

    Uses a Pydantic schema + JsonOutputParser so we get back a clean list
    of IDs instead of having to regex-parse the LLM's text response.
    """
    from django.conf import settings
    from typing import List
    from pydantic import BaseModel, Field

    summary_pk = request.POST.get('summary_pk')  # noqa: F841 used below
    summary = get_object_or_404(
        ResearchSummary, pk=summary_pk, project__owner=request.user,
    )
    resources = list(summary.project.resources.all())
    if not resources:
        return JsonResponse({
            'ok': False, 'error': 'No resources in this project yet.',
        })

    # Fallback algorithm if no API key keyword overlap
    if not settings.OPENAI_API_KEY:
        words = set(w.lower() for w in summary.content.split() if len(w) > 4)
        scored = []
        for r in resources:
            res_words = set(
                w.lower() for w in (r.title + ' ' + r.description).split()
                if len(w) > 4
            )
            scored.append((len(words & res_words), r))
        scored.sort(reverse=True, key=lambda x: x[0])
        return JsonResponse({
            'ok': True,
            'suggestions': [
                {'id': r.id, 'title': r.title}
                for s, r in scored[:3] if s > 0
            ],
            'fallback': True,
        })

    try:
        # Pydantic schema JsonOutputParser will validate the LLM response
        # against this and hand us back a real dict, not a JSON string.
        class CitationSuggestions(BaseModel):
            ids: List[int] = Field(
                description="List of relevant resource IDs in order of relevance",
            )

        from langchain_core.output_parsers import JsonOutputParser
        from langchain_core.prompts import PromptTemplate
        parser = JsonOutputParser(pydantic_object=CitationSuggestions)

        llm = _build_llm(temperature=0.3)

        resource_lines = "\n".join(
            f"[{r.id}] {r.title}: {r.description}" for r in resources
        )
        prompt = PromptTemplate(
            template=(
                "You are an academic citation assistant. The researcher has "
                "drafted the summary below and uploaded the listed resources. "
                "Identify which resources are MOST cite-worthy support for "
                "specific claims in the summary. Rank by topical overlap and "
                "the specificity of evidence each resource provides.\n\n"
                "Summary text:\n{summary}\n\n"
                "Available resources (id, title, description):\n{resources}\n\n"
                "{format_instructions}\n"
                "Return the 3 most relevant resource IDs ordered from most to "
                "least relevant. If fewer than 3 resources are genuinely "
                "relevant, return only those that are. Do not invent IDs."
            ),
            input_variables=['summary', 'resources'],
            partial_variables={
                'format_instructions': parser.get_format_instructions(),
            },
        )
        chain = prompt | llm | parser
        result = chain.invoke({
            'summary': summary.content,
            'resources': resource_lines,
        })
        ids = result.get('ids', []) if isinstance(result, dict) else []
        suggestions = [
            {'id': r.id, 'title': r.title}
            for r in resources if r.id in ids
        ]
        return JsonResponse({'ok': True, 'suggestions': suggestions})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@login_required
@require_POST
@_feature_required('ai_project_summary',
                   'Project-wide AI synthesis is a Pro-tier feature.')
def ai_summarize_project(request):
    """
    Generate a full-project research summary.

    Pulls every Resource (title, description, extracted_text excerpt),
    every existing ResearchSummary, and every ComparisonTable from the
    project, then asks the LLM to produce a single cohesive overview.
    Useful for the demo flow described in the assessment brief.
    """
    from django.conf import settings

    project_pk = request.POST.get('project_pk')
    project = get_object_or_404(
        ResearchProject, pk=project_pk, owner=request.user,
    )
    resources = list(project.resources.all())
    summaries = list(project.summaries.all())
    comparisons = list(project.comparisons.all())

    if not resources and not summaries and not comparisons:
        return JsonResponse({
            'ok': False,
            'error': 'This project has no resources, summaries, or comparison '
                     'tables yet add some content before requesting a summary.',
        }, status=400)

    # Build a compact corpus from project contents
    blocks = [f"Project title: {project.title}\nDescription: {project.description}"]
    if resources:
        res_lines = []
        for r in resources:
            excerpt = (r.extracted_text or r.description or '')[:600]
            res_lines.append(
                f"- [{r.get_resource_type_display()}] {r.title}\n"
                f"  authors: {r.authors or 'n/a'}, year: {r.year or 'n/a'}, venue: {r.venue or 'n/a'}\n"
                f"  excerpt: {excerpt}"
            )
        blocks.append("Resources:\n" + "\n".join(res_lines))
    if summaries:
        blocks.append("Existing summaries:\n" + "\n\n".join(
            f"== {s.title} ==\n{s.content[:1200]}" for s in summaries
        ))
    if comparisons:
        cmp_lines = []
        for c in comparisons:
            cols = [col.name for col in c.columns.all()]
            rows = [row.label for row in c.rows.all()]
            cmp_lines.append(
                f"- {c.title} ({len(rows)} rows × {len(cols)} columns; "
                f"columns: {', '.join(cols)})"
            )
        blocks.append("Comparison tables:\n" + "\n".join(cmp_lines))

    corpus = "\n\n".join(blocks)
    if len(corpus) > 12000:
        corpus = corpus[:12000] + "\n\n[... truncated for length ...]"

    # Fallback when no API key is available produce a deterministic
    # extractive summary so demos still show something useful.
    if not settings.OPENAI_API_KEY:
        bullet_lines = [f"**Project overview** {project.title}", '']
        if project.description:
            bullet_lines.append(project.description)
            bullet_lines.append('')
        bullet_lines.append('**Resources**')
        for r in resources[:8]:
            bullet_lines.append(
                f"- {r.title}" + (f" {r.authors} ({r.year})" if r.authors else '')
            )
        if summaries:
            bullet_lines.append('')
            bullet_lines.append('**Key takeaways from existing summaries**')
            for s in summaries:
                first = (s.content.split('.')[0] if s.content else s.title).strip()
                bullet_lines.append(f"- {first}.")
        if comparisons:
            bullet_lines.append('')
            bullet_lines.append('**Comparison tables**')
            for c in comparisons:
                bullet_lines.append(f"- {c.title}")
        return JsonResponse({
            'ok': True, 'summary': '\n'.join(bullet_lines),
            'fallback': True,
        })

    try:
        from langchain_core.prompts import PromptTemplate
        llm = _build_llm(temperature=0.3, max_tokens=1500)

        prompt = PromptTemplate(
            template=(
                "You are a senior research assistant writing a synthesis for a "
                "researcher's literature-review folder. Synthesise the entire "
                "project corpus below its resources, existing summaries, and "
                "comparison tables into a single Markdown overview.\n\n"
                "Project corpus:\n{corpus}\n\n"
                "Write the output with EXACTLY these section headers and order. "
                "Use clean Markdown, no extraneous preamble:\n\n"
                "**Project Overview**\n"
                "Two to four sentences naming the project's scope, the core "
                "research question, and the type of evidence assembled "
                "(empirical, theoretical, comparative, etc.).\n\n"
                "**Themes & Findings**\n"
                "Four to six bullet points (- prefix). Each bullet must:\n"
                "1. lead with a substantive theme or finding,\n"
                "2. cite supporting resources inline in parentheses using their "
                "   exact titles, e.g. (\"Attention Is All You Need\"),\n"
                "3. note any disagreement between resources when present.\n\n"
                "**Methodological Patterns**\n"
                "Two sentences identifying recurring methods or evaluation "
                "approaches across the resources.\n\n"
                "**Comparisons**\n"
                "Two sentences summarising what the comparison tables reveal "
                "(which axes most differentiate the items), or "
                "'No comparison tables in this project.' if none exist.\n\n"
                "**Gaps & Open Questions**\n"
                "Two to three bullet points (- prefix) naming concrete next "
                "research directions or unresolved tensions. Tie each one back "
                "to a specific resource where possible.\n\n"
                "Rules:\n"
                "- Use only information present in the corpus.\n"
                "- Never invent new citations or papers.\n"
                "- Quote numbers and named entities verbatim when supplied.\n"
                "- Keep the entire summary under 450 words."
            ),
            input_variables=['corpus'],
        )
        chain = prompt | llm
        result = chain.invoke({'corpus': corpus})
        summary_text = getattr(result, 'content', str(result))
        return JsonResponse({'ok': True, 'summary': summary_text})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


@login_required
@require_POST
@_feature_required('ai_paper_summary',
                   'AI paper summarisation requires a Plus or Pro plan.')
def ai_summarize_paper(request):
    """
    Summarise a single uploaded paper.

    We pull the text out of the PDF at upload time (see resource_upload),
    so by the time we get here the paper's content is already sitting in
    resource.extracted_text. We send the first ~8000 chars to the LLM and
    ask for a structured Markdown summary that the frontend can paste
    straight into the editor.
    """
    from django.conf import settings
    resource_id = request.POST.get('resource_id')
    resource = get_object_or_404(
        Resource, pk=resource_id, project__owner=request.user,
    )

    paper_text = resource.extracted_text or resource.description or ''
    if not paper_text.strip():
        return JsonResponse({
            'ok': False,
            'error': 'No text could be extracted from this resource. '
                     'For PDFs, make sure the file contains selectable text '
                     '(not just scanned images).',
        }, status=400)

    # Truncate to ~8000 chars so we don't blow the context window
    if len(paper_text) > 8000:
        paper_text = paper_text[:8000] + '\n\n[... truncated for length ...]'

    if not settings.OPENAI_API_KEY:
        # Fallback: extract first sentences if no API key configured
        sentences = [s.strip() for s in paper_text.split('.') if len(s.strip()) > 20]
        summary = '. '.join(sentences[:5]) + '.'
        return JsonResponse({
            'ok': True, 'summary': summary, 'fallback': True,
            'message': 'No LLM API key returned first sentences as fallback.',
        })

    try:
        from langchain_core.prompts import PromptTemplate
        llm = _build_llm(temperature=0.3, max_tokens=1024)

        prompt = PromptTemplate(
            template=(
                "You are an experienced academic research assistant writing for "
                "a graduate student preparing a literature review. Read the "
                "paper carefully and produce a precise, faithful summary.\n\n"
                "Paper title: {title}\n\n"
                "Paper content (extracted text):\n{content}\n\n"
                "Write the summary in clean Markdown using EXACTLY these "
                "section headers and order:\n\n"
                "**Overview**\n"
                "Two to three sentences identifying the topic, the problem the "
                "authors are solving, and their key contribution. Be specific "
                "mention concrete techniques, datasets, or systems where the "
                "text supports it.\n\n"
                "**Key Findings**\n"
                "Three to five bullet points (- prefix). Each bullet should "
                "lead with the finding, then a short supporting clause. Quote "
                "metrics (percentages, accuracy, p-values) verbatim when the "
                "text gives them.\n\n"
                "**Methodology**\n"
                "Two to three sentences naming the dataset(s), model(s), or "
                "experimental setup. Mention controls, sample sizes, or "
                "evaluation benchmarks when they are stated.\n\n"
                "**Limitations**\n"
                "Two sentences. Distinguish between author-acknowledged "
                "limitations and gaps you can infer from the text. Mark "
                "inferred items with '(inferred)'.\n\n"
                "**Why It Matters**\n"
                "One sentence connecting this paper to broader research "
                "directions or downstream applications.\n\n"
                "Rules:\n"
                "- Be factual and concise. Do not invent numbers, names, or "
                "  citations not present in the text.\n"
                "- Prefer specific verbs ('demonstrates', 'measures', 'proves') "
                "  over hedge words.\n"
                "- If a section truly cannot be filled from the text, write "
                "  'Not stated in the available text.' do not pad it."
            ),
            input_variables=['title', 'content'],
        )
        chain = prompt | llm
        result = chain.invoke({'title': resource.title, 'content': paper_text})
        summary_text = getattr(result, 'content', str(result))
        return JsonResponse({'ok': True, 'summary': summary_text})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


# AI Research Coach Chatbot
# This is the "Interview Coach" pattern from the AC7 lab, rebranded for
# research. The chat history lives in the Django session so the LLM keeps
# context between turns. HTMX swaps in the user bubble + bot reply as one
# fragment per turn no full page reloads, no JavaScript we have to write.
#
# Four routes:
#   /chat/<project_pk>/   GET   render the chat page, reset session
#   /chat/init/           POST  get the bot's opening message (fires on load)
#   /chat/                POST  handle one user message; returns both bubbles
#   /chat/<pk>/reset/     POST  clear history and reload

def _build_project_context(project):
    """Compact corpus of a project for the chatbot system prompt."""
    parts = [
        f"Project title: {project.title}",
        f"Project description: {project.description or '(none)'}",
    ]
    resources = list(project.resources.all()[:12])
    if resources:
        lines = []
        for r in resources:
            lines.append(
                f"- [{r.get_resource_type_display()}] {r.title}"
                + (f" (authors: {r.authors}, year: {r.year})" if r.authors else '')
            )
        parts.append("Resources:\n" + "\n".join(lines))
    summaries = list(project.summaries.all()[:4])
    if summaries:
        parts.append("Existing summaries:\n" + "\n\n".join(
            f"=== {s.title} ===\n{(s.content or '')[:600]}" for s in summaries
        ))
    return "\n\n".join(parts)[:6000]


@login_required
@_feature_required('ai_project_summary',
                   'The AI Research Coach is a Pro-tier feature.')
def research_chat_ui(request, project_pk):
    """Render the chat interface for a project; reset its session history."""
    project = get_object_or_404(
        ResearchProject, pk=project_pk, owner=request.user,
    )
    request.session['chat_project_pk'] = project.pk
    request.session['chat_history'] = []
    request.session['chat_context'] = _build_project_context(project)
    return render(request, 'chatui.html', {'project': project})


@login_required
@require_POST
@_feature_required('ai_project_summary',
                   'The AI Research Coach is a Pro-tier feature.')
def research_chat_reset(request, project_pk):
    """Clear chat history and reload the page."""
    project = get_object_or_404(
        ResearchProject, pk=project_pk, owner=request.user,
    )
    request.session['chat_project_pk'] = project.pk
    request.session['chat_history'] = []
    request.session['chat_context'] = _build_project_context(project)
    messages.info(request, "Chat cleared. Coach is back at the start.")
    return redirect('research_chat_ui', project_pk=project.pk)


@login_required
@require_POST
@_feature_required('ai_project_summary',
                   'The AI Research Coach is a Pro-tier feature.')
def research_chat_init(request):
    """
    POST fired on page load by hx-trigger="load". Generates the
    opening greeting from the coach and returns a single chat bubble
    partial.
    """
    context = request.session.get(
        'chat_context', 'No project loaded.'
    )

    system_prompt = (
        "You are a senior academic Research Coach helping a researcher think "
        "through their project. You have read the project's full context "
        "below.\n\n"
        f"PROJECT CONTEXT:\n{context}\n\n"
        "Behavioural rules:\n"
        "- Greet the researcher warmly and reference the project by name.\n"
        "- Ask ONE concrete opening question that helps you understand "
        "  what they want to focus on (e.g., scope clarification, gap "
        "  analysis, methodology critique, literature framing).\n"
        "- Keep the greeting under 80 words.\n"
        "- Use Markdown for emphasis but no headings.\n"
        "- Never invent papers, authors, or citations not present in the "
        "  PROJECT CONTEXT above."
    )

    llm = _build_llm(temperature=0.7)
    if llm is None:
        bot_message = mark_safe(_md_lib.markdown(
            "Hi! I'm your **Research Coach**. I've read your project's "
            "resources and summaries. What would you like to dig into first "
            "the literature gaps, the methodology, or the framing of your "
            "key claims?\n\n*(Note: running in fallback mode no API key "
            "configured.)*"
        ))
    else:
        try:
            from langchain_core.prompts import ChatPromptTemplate
            prompt = ChatPromptTemplate.from_messages([
                ('system', system_prompt),
                ('human', 'Start the conversation.'),
            ])
            chain = prompt | llm
            response = chain.invoke({})
            bot_message = mark_safe(_md_lib.markdown(response.content))
        except Exception as e:
            bot_message = mark_safe(f"Sorry, couldn't reach the LLM: {e}")

    # Persist initial system + assistant turn in session history
    request.session['chat_history'] = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'assistant', 'content': str(bot_message)},
    ]
    request.session.modified = True

    return render(request, 'partials/_chat_message.html', {
        'message': bot_message, 'is_user': False,
    })


@login_required
@require_POST
@_feature_required('ai_project_summary',
                   'The AI Research Coach is a Pro-tier feature.')
def research_chat(request):
    """
    POST handles each user message. Returns both the user's bubble
    AND the bot's reply in one HTMX response (the _chat_exchange.html
    partial). The session keeps the full conversation so the LLM has
    context.
    """
    user_message = request.POST.get('message', '').strip()
    if not user_message:
        return HttpResponse('')

    history = request.session.get('chat_history', [])
    history.append({'role': 'human', 'content': user_message})

    llm = _build_llm(temperature=0.7)
    if llm is None:
        bot_reply = (
            "Running in fallback mode (no API key configured). To use the "
            "live coach, set OPENAI_API_KEY in .env and restart the server."
        )
    else:
        try:
            from langchain_core.prompts import ChatPromptTemplate
            lc_messages = []
            for msg in history:
                role = msg['role']
                if role == 'system':
                    lc_messages.append(('system', msg['content']))
                elif role in ('human', 'user'):
                    lc_messages.append(('human', msg['content']))
                elif role == 'assistant':
                    lc_messages.append(('assistant', msg['content']))
            prompt = ChatPromptTemplate.from_messages(lc_messages)
            chain = prompt | llm
            response = chain.invoke({})
            bot_reply = response.content
        except Exception as e:
            bot_reply = f"Sorry, an error occurred: {e}"

    history.append({'role': 'assistant', 'content': bot_reply})
    request.session['chat_history'] = history
    request.session.modified = True

    return render(request, 'partials/_chat_exchange.html', {
        'user_message': user_message,
        'bot_message': mark_safe(_md_lib.markdown(bot_reply)),
    })
