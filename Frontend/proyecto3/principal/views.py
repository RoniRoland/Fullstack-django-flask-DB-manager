from datetime import datetime
from django.shortcuts import render
import requests
from pathlib import Path
import xml.dom.minidom
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import matplotlib.pyplot as plt
import numpy as np
import xml.etree.ElementTree as ET


# Create your views here.
def home(request):
    return render(request, "home.html")


def datos_estudiante(request):
    return render(request, "datos_estudiante.html")


def view_pdf(request):
    # Ruta relativa al archivo PDF en la carpeta de archivos estáticos
    pdf_path = "pdfs/documentacion_ProyectoNO3.pdf"
    return render(request, "documentacion_pr3.html", {"pdf_path": pdf_path})


def cargar_archivo(request):
    resumen_content = None
    base_content = None
    resumen_data = []

    if request.method == "POST":
        # Procesar el formulario de carga de archivos
        uploaded_file = request.FILES["archivo"]

        # Preparar la solicitud POST a la aplicación Flask
        url = "http://localhost:5000/cargar-xml"  # Reemplaza con la URL de tu aplicación Flask
        files = {"archivo": ("DB_TWEETS.xml", uploaded_file)}

        # Realizar la solicitud POST a la aplicación Flask
        response = requests.post(url, files=files)

        if response.status_code == 200:
            # Obtiene la ruta absoluta del archivo views.py
            current_file = Path(__file__).resolve()

            # Navega hacia la carpeta "Backend" y accede a "resumen.xml"
            resumen_file_path = current_file.parents[3] / "Backend" / "resumen.xml"
            base_file_path = current_file.parents[3] / "Backend" / "DB_TWEETS.xml"

            # Lee el archivo resumen.xml generado por Flask
            with open(resumen_file_path, "r") as f:
                resumen_content = f.read()

            # Lee el archivo resumen.xml generado por Flask
            with open(base_file_path, "r") as f:
                base_content = f.read()

            tree_resumen = ET.parse(resumen_file_path)
            root_resumen = tree_resumen.getroot()

            for tiempo_elem in root_resumen.findall("TIEMPO"):
                fecha = tiempo_elem.find("FECHA").text
                msj_recibidos = tiempo_elem.find("MSJ_RECIBIDOS").text
                usuarios_mencionados = tiempo_elem.find("USR_MENCIONADOS").text
                hashtags_incluidos = tiempo_elem.find("HASH_INCLUIDOS").text
                resumen_data.append(
                    {
                        "fecha": fecha,
                        "msj_recibidos": msj_recibidos,
                        "usuarios_mencionados": usuarios_mencionados,
                        "hashtags_incluidos": hashtags_incluidos,
                    }
                )

            resumen_data = sorted(resumen_data, key=lambda x: x["fecha"])

            # Formatea el contenido XML
            resumen_content = xml.dom.minidom.parseString(resumen_content).toprettyxml()
            base_content = xml.dom.minidom.parseString(base_content).toprettyxml()

    return render(
        request,
        "cargar-xml.html",
        {
            "resumen_data": resumen_data,
            "resumen_content": resumen_content,
            "base_content": base_content,
        },
    )


def cargar_configuracion(request):
    resumen_config_content = None
    config_content = None
    resumen_config_data = []

    if request.method == "POST":
        uploaded_config_file = request.FILES["config_file"]
        url = "http://localhost:5000/cargar-configuracion"
        files = {"config_file": ("DB_CONFIGS_DICT.xml", uploaded_config_file)}
        response = requests.post(url, files=files)

        if response.status_code == 200:
            # Obtiene la ruta absoluta del archivo views.py
            current_file = Path(__file__).resolve()

            # Navega hacia la carpeta "Backend" y accede a "resumen.xml"
            resumen_config_file_path = (
                current_file.parents[3] / "Backend" / "resumenConfig.xml"
            )
            config_file_path = (
                current_file.parents[3] / "Backend" / "DB_CONFIGS_DICT.xml"
            )

            # Lee el archivo resumen.xml generado por Flask
            with open(resumen_config_file_path, "r") as f:
                resumen_config_content = f.read()

            with open(config_file_path, "r") as f:
                config_content = f.read()

            config_elem = ET.fromstring(resumen_config_content)
            palabras_positivas = config_elem.find("PALABRAS_POSITIVAS").text
            palabras_positivas_rechazadas = config_elem.find(
                "PALABRAS_POSITIVAS_RECHAZADA"
            ).text
            palabras_negativas = config_elem.find("PALABRAS_NEGATIVAS").text
            palabras_negativas_rechazadas = config_elem.find(
                "PALABRAS_NEGATIVAS_RECHAZADA"
            ).text

            resumen_config_data = {
                "palabras_positivas": palabras_positivas,
                "palabras_positivas_rechazadas": palabras_positivas_rechazadas,
                "palabras_negativas": palabras_negativas,
                "palabras_negativas_rechazadas": palabras_negativas_rechazadas,
            }

            # Formatea el contenido XML
            resumen_config_content = xml.dom.minidom.parseString(
                resumen_config_content
            ).toprettyxml()

            config_content = xml.dom.minidom.parseString(config_content).toprettyxml()

    return render(
        request,
        "carga_config.html",
        {
            "resumen_config_data": resumen_config_data,
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
                hashtags_por_fecha = data.get("hashtags_por_fecha", [])

                # Ordena la lista de diccionarios por fecha (asumiendo que las fechas son strings en el formato "dd/mm/yyyy")
                sorted_data = sorted(
                    hashtags_por_fecha,
                    key=lambda x: datetime.strptime(x["fecha"], "%d/%m/%Y"),
                )

                return render(
                    request,
                    "consul_hash.html",
                    {"hashtags_por_fecha": sorted_data},
                )

    return render(request, "consul_hash.html", {"hashtags_por_fecha": None})


def generar_reporte_hashtags_pdf(request):
    # Obtén los datos para el informe
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")

    # Realiza la llamada a la API de Flask para obtener los datos
    api_url = "http://127.0.0.1:5000/consultar-hashtags"
    params = {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin}
    response = requests.get(api_url, params=params)

    if response.status_code == 200:
        data = response.json()
        hashtags_por_fecha = data.get("hashtags_por_fecha", [])
    else:
        hashtags_por_fecha = []

    # Crea un objeto BytesIO para almacenar el PDF
    buffer = BytesIO()

    # Crea un documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    # Lista de elementos para agregar al PDF
    elements = []

    # Agrega el título al PDF
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Informe de Hashtags", styles["Title"]))

    total_hashtags = {}

    # Agrega los datos de hashtags al PDF
    for data in hashtags_por_fecha:
        elements.append(Paragraph(f"Fecha: {data['fecha']}", styles["Heading1"]))
        for index, (hashtag, count) in enumerate(data["hashtags"].items(), start=1):
            elements.append(
                Paragraph(f"{index}. {hashtag}: {count} mensajes", styles["Normal"])
            )
            hashtag = hashtag.lower()
            if hashtag in total_hashtags:
                total_hashtags[hashtag] += count
            else:
                total_hashtags[hashtag] = count
        elements.append(Spacer(1, 12))  # Espacio entre secciones

    # Crea una gráfica de barras resumida con el recuento total de hashtags y ajusta su tamaño
    plt.figure(figsize=(8, 6))
    hashtags = list(total_hashtags.keys())
    menciones = list(total_hashtags.values())
    x = np.arange(len(hashtags))
    plt.bar(x, menciones, align="center")
    plt.xticks(x, hashtags, rotation=45, fontsize=8)
    plt.ylabel("Cantidad de Mensajes")
    plt.title("Hashtags Utilizados (Resumen)")

    # Guarda la gráfica resumida como una imagen temporal
    temp_image = BytesIO()
    plt.savefig(temp_image, format="png", bbox_inches="tight")
    temp_image.seek(0)
    plt.close()

    # Agrega la gráfica de barras resumida al PDF con un tamaño más grande
    elements.append(Image(temp_image, width=500, height=400))
    elements.append(Spacer(1, 12))

    # Construye el PDF
    doc.build(elements)

    # Reinicia el buffer y devuelve el PDF como una respuesta
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="reporte_hashtag.pdf"'

    return response


def consultar_usuario(request):
    if request.method == "GET":
        fecha_inicio = request.GET.get("fecha_inicio")
        fecha_fin = request.GET.get("fecha_fin")

        if fecha_inicio and fecha_fin:
            # Llamar a la API de Flask para obtener los usuarios mencionados
            api_url = "http://127.0.0.1:5000/consultar-usuarios"
            params = {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin}
            response = requests.get(api_url, params=params)

            if response.status_code == 200:
                data = response.json()
                # print("Respuesta JSON:", data)

                # Asegurarse de que "usuarios_por_fecha" sea una lista
                usuarios_por_fecha = data.get("usuarios_por_fecha", [])

                # Ordena la lista de diccionarios por fecha (asumiendo que las fechas son strings en el formato "dd/mm/yyyy")
                sorted_data = sorted(
                    usuarios_por_fecha,
                    key=lambda x: datetime.strptime(x["fecha"], "%d/%m/%Y"),
                )

                return render(
                    request,
                    "consul_usuario.html",
                    {"usuarios_por_fecha": sorted_data},
                )

    return render(request, "consul_usuario.html", {"usuarios_por_fecha": None})


def generar_reporte_usuarios_pdf(request):
    # Obtén los datos para el informe
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")

    # Realiza la llamada a la API de Flask para obtener los datos
    api_url = "http://127.0.0.1:5000/consultar-usuarios"
    params = {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin}
    response = requests.get(api_url, params=params)

    if response.status_code == 200:
        data = response.json()
        usuarios_por_fecha = data.get("usuarios_por_fecha", [])
    else:
        usuarios_por_fecha = []

    # Crea un objeto BytesIO para almacenar el PDF
    buffer = BytesIO()

    # Crea un documento PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    # Lista de elementos para agregar al PDF
    elements = []

    # Agrega el título al PDF
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Informe de Usuarios", styles["Title"]))

    total_menciones = {}

    # Agrega los datos de hashtags al PDF
    for data in usuarios_por_fecha:
        elements.append(Paragraph(f"Fecha: {data['fecha']}", styles["Heading1"]))
        for index, (usuario, count) in enumerate(data["usuarios"].items(), start=1):
            elements.append(
                Paragraph(f"{index}. {usuario}: {count} menciones", styles["Normal"])
            )
            if usuario in total_menciones:
                total_menciones[usuario] += count
            else:
                total_menciones[usuario] = count
        elements.append(Spacer(1, 12))

    plt.figure(figsize=(8, 6))
    usuarios = list(total_menciones.keys())
    menciones = list(total_menciones.values())
    x = np.arange(len(usuarios))
    plt.bar(x, menciones, align="center")
    plt.xticks(x, usuarios, rotation=45, fontsize=8)
    plt.ylabel("Cantidad de Menciones")
    plt.title("Usuarios Mencionados (Resumen)")

    # Guarda la gráfica resumida como una imagen temporal
    temp_image = BytesIO()
    plt.savefig(temp_image, format="png")
    temp_image.seek(0)
    plt.close()

    # Agrega la gráfica de barras resumida al PDF
    elements.append(Image(temp_image, width=500, height=400))
    elements.append(Spacer(1, 12))  # Espacio entre secciones

    # Construye el PDF
    doc.build(elements)

    # Reinicia el buffer y devuelve el PDF como una respuesta
    buffer.seek(0)
    response = HttpResponse(buffer.read(), content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="reporte_usuarios.pdf"'

    return response


def consultar_sentimientos(request):
    if request.method == "GET":
        fecha_inicio = request.GET.get("fecha_inicio")
        fecha_fin = request.GET.get("fecha_fin")

        if fecha_inicio and fecha_fin:
            # Llamar a la API de Flask para obtener los sentimientos
            api_url = "http://127.0.0.1:5000/consultar-sentimientos"
            params = {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin}
            response = requests.get(api_url, params=params)

            if response.status_code == 200:
                data = response.json()
                # print("Respuesta JSON:", data)

                # Asegurarse de que "sentimientos_por_fecha" sea una lista
                sentimientos_por_fecha = data.get("sentimientos_por_fecha", [])

                sorted_data = sorted(
                    sentimientos_por_fecha,
                    key=lambda x: datetime.strptime(x["fecha"], "%d/%m/%Y"),
                )

                return render(
                    request,
                    "consul_sent.html",
                    {"sentimientos_por_fecha": sorted_data},
                )

    return render(request, "consul_sent.html", {"sentimientos_por_fecha": None})
    # return render("consul_sent.html", sentimientos_por_fecha=None)


def generar_reporte_sentimientos_pdf(request):
    if request.method == "GET":
        fecha_inicio = request.GET.get("fecha_inicio")
        fecha_fin = request.GET.get("fecha_fin")

        if fecha_inicio and fecha_fin:
            # Llamar a la API de Flask para obtener los sentimientos
            api_url = "http://127.0.0.1:5000/consultar-sentimientos"
            params = {"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin}
            response = requests.get(api_url, params=params)

            if response.status_code == 200:
                data = response.json()
                sentimientos_por_fecha = data.get("sentimientos_por_fecha", [])
            else:
                sentimientos_por_fecha = []

            # Resumen acumulativo de los datos
            positivos_total = 0
            negativos_total = 0
            neutros_total = 0

            for data in sentimientos_por_fecha:
                positivos_total += data["positivos"]
                negativos_total += data["negativos"]
                neutros_total += data["neutros"]

            # Crea un objeto BytesIO para almacenar el PDF
            buffer = BytesIO()

            # Crea un documento PDF
            doc = SimpleDocTemplate(buffer, pagesize=letter)

            # Lista de elementos para agregar al PDF
            elements = []

            # Agrega el título al PDF
            styles = getSampleStyleSheet()
            elements.append(
                Paragraph("Informe de Sentimientos en Mensajes", styles["Title"])
            )

            # Enumera la lista de sentimientos
            for data in sentimientos_por_fecha:
                elements.append(
                    Paragraph(f"Fecha: {data['fecha']}", styles["Heading1"])
                )
                elements.append(
                    Paragraph(
                        f"Mensajes con sentimiento positivo: {data['positivos']} mensajes",
                        styles["Normal"],
                    )
                )
                elements.append(
                    Paragraph(
                        f"Mensajes con sentimiento negativo: {data['negativos']} mensajes",
                        styles["Normal"],
                    )
                )
                elements.append(
                    Paragraph(
                        f"Mensajes neutros: {data['neutros']} mensaje", styles["Normal"]
                    )
                )
                elements.append(Spacer(1, 12))  # Espacio entre secciones

            # Crear una gráfica de barras
            plt.figure(figsize=(6, 4))
            sentimientos = ["Positivos", "Negativos", "Neutros"]
            counts = [positivos_total, negativos_total, neutros_total]
            x = np.arange(len(sentimientos))
            plt.bar(x, counts, align="center")
            plt.xticks(x, sentimientos)
            plt.ylabel("Cantidad de Mensajes")
            plt.title("Sentimientos en Mensajes (Resumen)")

            # Guardar la gráfica como una imagen temporal
            temp_image = BytesIO()
            plt.savefig(temp_image, format="png")
            temp_image.seek(0)
            plt.close()

            # Agregar la gráfica al PDF
            elements.append(Image(temp_image, width=400, height=300))
            elements.append(Spacer(1, 12))  # Espacio entre secciones

            # Construye el PDF
            doc.build(elements)

            # Reinicia el buffer y devuelve el PDF como una respuesta
            buffer.seek(0)
            response = HttpResponse(buffer.read(), content_type="application/pdf")
            response[
                "Content-Disposition"
            ] = 'attachment; filename="reporte_sentimientos.pdf"'

            return response

    return render(request, "consul_sent.html", {"sentimientos_por_fecha": None})
