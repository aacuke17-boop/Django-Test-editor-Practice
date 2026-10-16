from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("materials/<int:pk>/", views.material_detail, name="material_detail"),
    path("my-materials/", views.my_materials, name="my_materials"),
]
