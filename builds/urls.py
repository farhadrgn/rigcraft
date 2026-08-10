from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("builder/", views.builder, name="builder"),
    path("builder/save/", views.builder_save, name="builder_save"),
    path("builds/", views.build_list, name="build_list"),
    path("builds/<int:build_id>/", views.build_detail, name="build_detail"),
    path("builds/<int:build_id>/edit/", views.build_edit, name="build_edit"),
    path("builds/<int:build_id>/delete/", views.build_delete, name="build_delete"),
]