from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("materials/new/", views.material_create, name="material_create"),
    path("materials/<int:pk>/", views.material_detail, name="material_detail"),
    path("materials/<int:pk>/edit/", views.material_edit, name="material_edit"),
    path("materials/<int:pk>/delete/", views.material_delete, name="material_delete"),
    path("materials/<int:pk>/access/", views.material_access, name="material_access"),
    path("my-materials/", views.my_materials, name="my_materials"),
]
