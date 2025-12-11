from django.urls import path

from custom_rag import views

urlpatterns = [
    path("execute/", views.execute_pipeline, name="execute_pipeline"),
]
