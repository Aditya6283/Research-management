"""
Project-level URL configuration for ResearchDoc.

Following the pattern from Applied Class 2, all app URLs are prefixed
with `researchdoc/` so multiple Django apps can coexist on a single
UQCloud Zone (each with their own Nginx route).
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('researchapp.urls')),

    path('accounts/', include('allauth.urls')),

    path('admin/', admin.site.urls),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
