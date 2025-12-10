"""
URL configuration for custom-rag project.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("custom_rag/", include("custom_rag.urls")),
]
