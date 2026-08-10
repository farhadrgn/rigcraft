from django.urls import path

from . import views

urlpatterns = [
    path("builder/check/", views.builder_check, name="builder_check"),
]