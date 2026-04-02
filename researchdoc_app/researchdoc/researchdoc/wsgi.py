"""
WSGI config for ResearchDoc.

This file is what Gunicorn loads to serve the application.
On UQCloud, Gunicorn binds to 127.0.0.1:8001 and Nginx proxies to it.
See deployment/UQCLOUD_DEPLOYMENT.md for details.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'researchdoc.settings')

application = get_wsgi_application()
