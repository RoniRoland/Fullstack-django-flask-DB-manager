from datetime import datetime
from flask import Flask, request, jsonify
import os
from pathlib import Path
from flask_cors import CORS
import xml.etree.ElementTree as ET
from Mensaje import Mensajes
from Sentimiento import Sentimientos
import re


app = Flask(__name__)
CORS(app)


@app.route("/cargar-xml", methods=["POST"])
def cargar_xml():
    try:
        uploaded_file = request.files["archivo"]
        if uploaded_file.filename != "":
            # Guardar el archivo XML en el servidor
            uploaded_file.save("nuevo_archivo.xml")

            # Crear una lista para almacenar los mensajes existentes o nuevos mensajes
            mensajes = []

            # Verificar si el archivo uploaded.xml existe
            uploaded_exists = os.path.exists("uploaded.xml")

            if uploaded_exists:
                # Cargar los mensajes existentes desde uploaded.xml
                tree = ET.parse("uploaded.xml")
                root = tree.getroot()
                for mensaje_elem in root.findall(".//MENSAJE"):
                    fecha = mensaje_elem.find("FECHA").text
                    texto = mensaje_elem.find("TEXTO").text
                    mensajes.append(Mensajes(fecha, texto))

            # Cargar los nuevos mensajes desde el archivo recién cargado
            tree_nuevo = ET.parse("nuevo_archivo.xml")
            root_nuevo = tree_nuevo.getroot()
            for mensaje_elem in root_nuevo.findall(".//MENSAJE"):
                fecha = mensaje_elem.find("FECHA").text
                texto = mensaje_elem.find("TEXTO").text
                mensaje_nuevo = Mensajes(fecha, texto)

                # Verificar si el mensaje ya existe en la lista de mensajes
                if mensaje_nuevo not in mensajes:
                    mensajes.append(mensaje_nuevo)

            # Guardar todos los mensajes en uploaded.xml (sobrescribirlo o crearlo si no existe)
            resumen = ET.Element("MENSAJES")
            for mensaje in mensajes:
                mensaje_elem = ET.SubElement(resumen, "MENSAJE")
                fecha_elem = ET.SubElement(mensaje_elem, "FECHA")
                fecha_elem.text = mensaje.fecha
                texto_elem = ET.SubElement(mensaje_elem, "TEXTO")
                texto_elem.text = mensaje.texto

            tree = ET.ElementTree(resumen)
            tree.write("uploaded.xml")

            # Crear el archivo resumen.xml con la información de los mensajes
            resumen_xml = ET.Element("MENSAJES_RECIBIDOS")
            fecha_actual = ""
            mensajes_en_intervalo = 0
            usuarios_mencionados = set()
            hashtags_incluidos = set()

            for mensaje in mensajes:
                fecha = mensaje.fecha.split(", ")[1]
                if fecha != fecha_actual:
                    if fecha_actual:
                        tiempo = ET.SubElement(resumen_xml, "TIEMPO")
                        fecha_elem = ET.SubElement(tiempo, "FECHA")
                        fecha_elem.text = fecha_actual
                        msj_recibidos = ET.SubElement(tiempo, "MSJ_RECIBIDOS")
                        msj_recibidos.text = str(mensajes_en_intervalo)
                        usr_mencionados = ET.SubElement(tiempo, "USR_MENCIONADOS")
                        usr_mencionados.text = str(len(usuarios_mencionados))
                        hash_incluidos = ET.SubElement(tiempo, "HASH_INCLUIDOS")
                        hash_incluidos.text = str(len(hashtags_incluidos))
                    fecha_actual = fecha
                    mensajes_en_intervalo = 1
                    usuarios_mencionados = set()
                    hashtags_incluidos = set()
                else:
                    mensajes_en_intervalo += 1
                usuarios_mencionados.update(
                    set(
                        usuario[1:]
                        for usuario in mensaje.texto.split()
                        if usuario.startswith("@")
                    )
                )
                hashtags_incluidos.update(
                    set(
                        hashtag[1:-1]
                        for hashtag in mensaje.texto.split()
                        if hashtag.startswith("#")
                    )
                )

            tiempo = ET.SubElement(resumen_xml, "TIEMPO")
            fecha_elem = ET.SubElement(tiempo, "FECHA")
            fecha_elem.text = fecha_actual
            msj_recibidos = ET.SubElement(tiempo, "MSJ_RECIBIDOS")
            msj_recibidos.text = str(mensajes_en_intervalo)
            usr_mencionados = ET.SubElement(tiempo, "USR_MENCIONADOS")
            usr_mencionados.text = str(len(usuarios_mencionados))
            hash_incluidos = ET.SubElement(tiempo, "HASH_INCLUIDOS")
            hash_incluidos.text = str(len(hashtags_incluidos))

            tree_resumen = ET.ElementTree(resumen_xml)
            tree_resumen.write("resumen.xml")

            # Eliminar el archivo temporal del nuevo archivo cargado
            os.remove("nuevo_archivo.xml")

            return jsonify({"message": "Archivo XML procesado y resumen generado."})
        else:
            return jsonify({"error": "No se ha seleccionado un archivo XML."})

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/cargar-configuracion", methods=["POST"])
def cargar_configuracion():
    try:
        uploaded_config_file = request.files["config_file"]
        if uploaded_config_file.filename != "":
            # Guarda el archivo de configuración XML en el servidor
            uploaded_config_file.save("configuracion.xml")

            # Procesa el archivo de configuración
            tree_config = ET.parse("configuracion.xml")
            root_config = tree_config.getroot()

            sentimientos = Sentimientos()

            for palabra in root_config.find(".//sentimientos_positivos"):
                sentimientos.palabras_positivas.add(palabra.text.lower())

            for palabra in root_config.find(".//sentimientos_negativos"):
                sentimientos.palabras_negativas.add(palabra.text.lower())

            # Obtener el recuento de palabras positivas y negativas
            palabras_positivas_contador = len(sentimientos.palabras_positivas)
            palabras_negativas_contador = len(sentimientos.palabras_negativas)

            # Genera el archivo resumenConfig.xml
            resumen_config = ET.Element("CONFIG_RECIBIDA")
            palabras_positivas_elem = ET.SubElement(
                resumen_config, "PALABRAS_POSITIVAS"
            )
            palabras_positivas_elem.text = str(palabras_positivas_contador)
            palabras_negativas_elem = ET.SubElement(
                resumen_config, "PALABRAS_NEGATIVAS"
            )
            palabras_negativas_elem.text = str(palabras_negativas_contador)

            tree = ET.ElementTree(resumen_config)
            tree.write("resumenConfig.xml")

            return jsonify(
                {"message": "Archivo de configuración procesado y resumen generado."}
            )

        else:
            return jsonify(
                {"error": "No se ha seleccionado un archivo de configuración."}
            )

    except Exception as e:
        return jsonify({"error": str(e)})


# Define rutas para consultar hashtags
@app.route("/consultar-hashtags", methods=["GET"])
def consultar_hashtags():
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")

    if not fecha_inicio or not fecha_fin:
        return jsonify({"error": "Las fechas de inicio y fin son requeridas"})

    # Convertir las fechas de inicio y fin a objetos datetime
    fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")

    # Procesa el archivo uploaded.xml
    tree = ET.parse("uploaded.xml")
    root = tree.getroot()
    hashtags_por_fecha = {}

    for mensaje_elem in root.findall(".//MENSAJE"):
        fecha_str = mensaje_elem.find("FECHA").text.split(", ")[1]
        fecha = datetime.strptime(fecha_str, "%d/%m/%Y")
        texto = mensaje_elem.find("TEXTO").text

        if fecha_inicio <= fecha <= fecha_fin:
            mensaje = Mensajes(fecha, texto)
            hashtags = mensaje.obtener_hashtags()
            for hashtag in hashtags:
                if fecha not in hashtags_por_fecha:
                    hashtags_por_fecha[fecha] = {}
                if hashtag in hashtags_por_fecha[fecha]:
                    hashtags_por_fecha[fecha][hashtag] += 1
                else:
                    hashtags_por_fecha[fecha][hashtag] = 1

    # Formatear las fechas como cadenas de texto
    result = []
    for fecha, hashtags in hashtags_por_fecha.items():
        fecha_str = fecha.strftime("%d/%m/%Y")
        result.append({"fecha": fecha_str, "hashtags": hashtags})
    # print("hashtags_por_fecha:", hashtags_por_fecha)
    return jsonify({"hashtags_por_fecha": result})


@app.route("/consultar-sentimiento", methods=["GET"])
def consultar_sentimientos():
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")

    if not fecha_inicio or not fecha_fin:
        return jsonify({"error": "Las fechas de inicio y fin son requeridas"})

    # Convertir las fechas de inicio y fin a objetos datetime
    fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")

    # Procesa el archivo uploaded.xml
    tree = ET.parse("uploaded.xml")
    root = tree.getroot()
    sentimientos_por_fecha = {"positivo": 0, "negativo": 0, "neutro": 0}
    sentimientos = Sentimientos()

    for mensaje_elem in root.findall(".//MENSAJE"):
        fecha_str = mensaje_elem.find("FECHA").text.split(", ")[1]
        fecha = datetime.strptime(fecha_str, "%d/%m/%Y")
        texto = mensaje_elem.find("TEXTO").text

        if fecha_inicio <= fecha <= fecha_fin:
            mensaje = Mensajes(fecha, texto)
            texto_mensaje = mensaje.obtener_texto()

            # Contadores de palabras positivas y negativas en el mensaje
            contador_positivas = 0
            contador_negativas = 0

            # Analizar cada palabra del mensaje
            for palabra in texto_mensaje.split():
                palabra = palabra.lower()
                if palabra in sentimientos.palabras_positivas:
                    contador_positivas += 1
                elif palabra in sentimientos.palabras_negativas:
                    contador_negativas += 1

            # Clasificar el mensaje
            if contador_positivas > contador_negativas:
                sentimiento = "positivo"
            elif contador_negativas > contador_positivas:
                sentimiento = "negativo"
            else:
                sentimiento = "neutro"

            # Actualizar el conteo de sentimientos por fecha
            sentimientos_por_fecha[sentimiento] += 1

    # Formatear las fechas como cadenas de texto
    result = []
    for sentimiento, count in sentimientos_por_fecha.items():
        result.append({"sentimiento": sentimiento, "count": count})
    return jsonify({"sentimientos_por_fecha": result})


@app.route("/consultar-usuarios", methods=["GET"])
def consultar_usuarios():
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")

    if not fecha_inicio or not fecha_fin:
        return jsonify({"error": "Las fechas de inicio y fin son requeridas"})

    # Convertir las fechas de inicio y fin a objetos datetime
    fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")

    # Procesa el archivo uploaded.xml
    tree = ET.parse("uploaded.xml")
    root = tree.getroot()
    usuarios_por_fecha = {}

    for mensaje_elem in root.findall(".//MENSAJE"):
        fecha_str = mensaje_elem.find("FECHA").text.split(", ")[1]
        fecha = datetime.strptime(fecha_str, "%d/%m/%Y")
        texto = mensaje_elem.find("TEXTO").text

        if fecha_inicio <= fecha <= fecha_fin:
            mensaje = Mensajes(fecha, texto)
            usuarios_mencionados = mensaje.obtener_usuarios_mencionados()
            for usuario in usuarios_mencionados:
                if fecha not in usuarios_por_fecha:
                    usuarios_por_fecha[fecha] = {}
                if usuario in usuarios_por_fecha[fecha]:
                    usuarios_por_fecha[fecha][usuario] += 1
                else:
                    usuarios_por_fecha[fecha][usuario] = 1

    # Formatear las fechas como cadenas de texto y usuarios
    result = []
    for fecha, usuarios in usuarios_por_fecha.items():
        fecha_str = fecha.strftime("%d/%m/%Y")
        result.append({"fecha": fecha_str, "usuarios": usuarios})
    return jsonify({"usuarios_por_fecha": result})


@app.route("/resetear-datos", methods=["POST"])
def resetear_datos():
    # Define la ruta al archivo resumen.xml
    current_file = Path(__file__).resolve()

    resumen_file_path = current_file.parents[1] / "Backend" / "resumen.xml"
    uploaded_file_path = current_file.parents[1] / "Backend" / "uploaded.xml"
    config_file_path = current_file.parents[1] / "Backend" / "configuracion.xml"
    resumenConfig_file_path = current_file.parents[1] / "Backend" / "resumenConfig.xml"
    files_to_remove = [
        resumen_file_path,
        uploaded_file_path,
        config_file_path,
        resumenConfig_file_path,
    ]

    for file_path in files_to_remove:
        if os.path.exists(file_path):
            os.remove(file_path)

    mensaje = Mensajes("", "")
    mensaje.resetear()
    return "Datos reseteados correctamente", 200


if __name__ == "__main__":
    app.run(debug=True)
