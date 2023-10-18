from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("cargar-xml/", views.cargar_archivo, name="cargar-xml"),
    path("resetear-datos/", views.resetear_datos, name="resetear_datos"),
    path(
        "cargar-configuracion/", views.cargar_configuracion, name="cargar-configuracion"
    ),
    path("consultar-hashtags/", views.consultar_hashtags, name="consultar_hashtags"),
    path("resetear-datos/", views.resetear_datos, name="resetear_datos"),
]
