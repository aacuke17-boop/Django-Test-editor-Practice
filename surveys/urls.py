from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("materials/new/", views.material_create, name="material_create"),
    path("materials/<int:pk>/", views.material_detail, name="material_detail"),
    path("materials/<int:pk>/edit/", views.material_edit, name="material_edit"),
    path("materials/<int:pk>/delete/", views.material_delete, name="material_delete"),
    path("materials/<int:pk>/access/", views.material_access, name="material_access"),
    path(
        "materials/<int:pk>/access/<int:user_id>/revoke/",
        views.material_access_revoke,
        name="material_access_revoke",
    ),
    path("materials/<int:pk>/start/", views.attempt_start, name="attempt_start"),
    path("materials/<int:pk>/results/", views.material_results, name="material_results"),
    path("materials/<int:pk>/export.csv", views.material_export_csv, name="material_export_csv"),
    path(
        "materials/<int:pk>/attempts/<int:attempt_id>/",
        views.material_attempt_detail,
        name="material_attempt_detail",
    ),
    path("attempts/<int:attempt_id>/", views.attempt_take, name="attempt_take"),
    path("attempts/<int:attempt_id>/result/", views.attempt_result, name="attempt_result"),
    path("my-attempts/", views.my_attempts, name="my_attempts"),
    path("my-materials/", views.my_materials, name="my_materials"),
]
