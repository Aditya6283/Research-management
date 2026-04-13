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


