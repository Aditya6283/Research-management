"""
Safe Markdown rendering helpers.

The AI endpoints and chatbot return Markdown that we convert to HTML and
mark safe so lists, bold, headings etc. render properly. Marking raw HTML
safe is risky — python-markdown passes through any literal HTML in the
input — so we run the converted output through bleach with a small
allow-list first. That keeps the formatting we want while stripping
<script>, inline event handlers, javascript: URLs and the like.

If bleach isn't installed the helper degrades gracefully: it escapes the
input instead of trusting it, so we fail closed rather than open.
"""
from django.utils.safestring import mark_safe
from django.utils.html import escape
import markdown as _md_lib

# Tags/attributes we allow through for rendered Markdown.
ALLOWED_TAGS = [
    'p', 'br', 'hr', 'strong', 'b', 'em', 'i', 'u', 'code', 'pre',
    'blockquote', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'a', 'span', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
]
ALLOWED_ATTRS = {
    'a': ['href', 'title', 'rel'],
    'span': ['class'],
    'code': ['class'],
}
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


def render_markdown(text):
    """Convert Markdown to sanitised, safe HTML for templates."""
    if not text:
        return mark_safe('')
    html = _md_lib.markdown(text, extensions=['fenced_code', 'tables'])
    try:
        import bleach
        cleaned = bleach.clean(
            html,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRS,
            protocols=ALLOWED_PROTOCOLS,
            strip=True,
        )
        return mark_safe(cleaned)
    except ImportError:
        # bleach not available — fail closed by escaping rather than trusting.
        return escape(text)
