from datetime import datetime
from django.shortcuts import render
import requests
from pathlib import Path
import xml.dom.minidom
import os


# Create your views here.
def home(request):
    return render(request, "home.html")


def cargar_archivo(request):
    resumen_content = None
    base_content = None
    if request.method == "POST":
        # Procesar el formulario de carga de archivos
        uploaded_file = request.FILES["archivo"]

        # Preparar la solicitud POST a la aplicación Flask
        url = "http://localhost:5000/cargar-xml"  # Reemplaza con la URL de tu aplicación Flask
        files = {"archivo": ("uploaded.xml", uploaded_file)}

        # Realizar la solicitud POST a la aplicación Flask
        response = requests.post(url, files=files)

        if response.status_code == 200:
            # Obtiene la ruta absoluta del archivo views.py
            current_file = Path(__file__).resolve()

            # Navega hacia la carpeta "Backend" y accede a "resumen.xml"
            resumen_file_path = current_file.parents[3] / "Backend" / "resumen.xml"
            base_file_path = current_file.parents[3] / "Backend" / "uploaded.xml"

            # Lee el archivo resumen.xml generado por Flask
            with open(resumen_file_path, "r") as f:
                resumen_content = f.read()

            # Lee el archivo resumen.xml generado por Flask
            with open(base_file_path, "r") as f:
                base_content = f.read()

            # Formatea el contenido XML
            resumen_content = xml.dom.minidom.parseString(resumen_content).toprettyxml()

    return render(
        request,
        "cargar-xml.html",
        {"resumen_content": resumen_content, "base_content": base_content},
    )


def cargar_configuracion(request):
    resumen_config_content = None
    config_content = None
    if request.method == "POST":
        uploaded_config_file = request.FILES["config_file"]
        url = "http://localhost:5000/cargar-configuracion"
        files = {"config_file": ("configuracion.xml", uploaded_config_file)}
        response = requests.post(url, files=files)

        if response.status_code == 200:
            # Obtiene la ruta absoluta del archivo views.py
            current_file = Path(__file__).resolve()

            # Navega hacia la carpeta "Backend" y accede a "resumen.xml"
            resumen_config_file_path = (
                current_file.parents[3] / "Backend" / "resumenConfig.xml"
            )
            config_file_path = current_file.parents[3] / "Backend" / "configuracion.xml"

            # Lee el archivo resumen.xml generado por Flask
            with open(resumen_config_file_path, "r") as f:
                resumen_config_content = f.read()

            with open(config_file_path, "r") as f:
                config_content = f.read()

            # Formatea el contenido XML
            resumen_config_content = xml.dom.minidom.parseString(
                resumen_config_content
            ).toprettyxml()

    return render(
        request,
        "carga_config.html",
        {
            "resumen_config_content": resumen_config_content,
            "config_content": config_content,
        },
    )


def resetear_datos(request):
    if request.method == "POST":
        # Realiza una solicitud POST a la ruta de Flask para el reseteo
        reset_url = "http://127.0.0.1:5000/resetear-datos"
        response = requests.post(reset_url)

        if response.status_code == 200:
            return render(request, "home.html")

    return render(request, "home.html")


def consultar_hashtags(request):
    if request.method == "GET":
        fecha_inicio = request.GET.get("fecha_inicio")
        fecha_fin = request.GET.get("fecha_fin")

        if fecha_inicio and fecha_fin:
            # Llamar a la API de Flask para obtener los hashtags
            api_url = "http://127.0.0.1:5000/consultar-hashtags"
            params = {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin}
            response = requests.get(api_url, params=params)

            if response.status_code == 200:
                data = response.json()
                # print("Respuesta JSON:", data)

                # Asegurarse de que "hashtags_por_fecha" sea una lista
                # hashtags_por_fecha = data.get("hashtags_por_fecha", [])
                # Ordena la lista de diccionarios por fecha (asumiendo que las fechas son strings en el formato "dd/mm/yyyy")
                sorted_data = sorted(
                    data["hashtags_por_fecha"],
                    key=lambda x: datetime.strptime(x["fecha"], "%d/%m/%Y"),
                )

                return render(
                    request,
                    "consul_hash.html",
                    {"hashtags_por_fecha": sorted_data},
                )

    return render(request, "consul_hash.html", {"hashtags_por_fecha": None})
