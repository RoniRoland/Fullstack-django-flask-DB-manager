from datetime import datetime
from flask import Flask, request, jsonify
import os
from pathlib import Path
from flask_cors import CORS
import xml.etree.ElementTree as ET
from Mensaje import Mensajes
from Sentimiento import Sentimientos
import re
from unidecode import unidecode


app = Flask(__name__)
CORS(app)


@app.route("/cargar-xml", methods=["POST"])
def cargar_xml():
    try:
        uploaded_file = request.files["archivo"]
        # print("==========================================================")
        if uploaded_file.filename != "":
            uploaded_file.save("nuevo_archivo.xml")
            # print("=============================DEBUGGGGG=============================")

            mensajes = []

            uploaded_exists = os.path.exists("uploaded.xml")

            if uploaded_exists:
                tree = ET.parse("uploaded.xml")
                root = tree.getroot()
                for mensaje_elem in root.findall(".//MENSAJE"):
                    fecha = mensaje_elem.find("FECHA").text
                    texto = mensaje_elem.find("TEXTO").text
                    mensajes.append(Mensajes(fecha, texto))

            tree_nuevo = ET.parse("nuevo_archivo.xml")
            root_nuevo = tree_nuevo.getroot()
            for mensaje_elem in root_nuevo.findall(".//MENSAJE"):
                fecha = mensaje_elem.find("FECHA").text
                texto = mensaje_elem.find("TEXTO").text
                texto_limpio = unidecode(texto)
                mensaje_nuevo = Mensajes(fecha, texto_limpio)

                if mensaje_nuevo not in mensajes:
                    mensajes.append(mensaje_nuevo)

            resumen = ET.Element("MENSAJES")
            for mensaje in mensajes:
                mensaje_elem = ET.SubElement(resumen, "MENSAJE")
                fecha_elem = ET.SubElement(mensaje_elem, "FECHA")
                fecha_elem.text = mensaje.fecha
                texto_elem = ET.SubElement(mensaje_elem, "TEXTO")
                texto_elem.text = mensaje.texto

            tree = ET.ElementTree(resumen)
            tree.write("uploaded.xml")

            resumen_xml = ET.Element("MENSAJES_RECIBIDOS")
            tiempo_anterior = ""
            usuarios_mencionados_total = set()
            hashtags_total = set()

            for mensaje in mensajes:
                try:
                    fecha = mensaje.fecha.split(", ")[1]
                    usuarios_mencionados = mensaje.obtener_usuarios_mencionados()
                    hashtags = mensaje.obtener_hashtags()
                    # print("Usuarios válidos en este mensaje:", usuarios_mencionados)

                    if fecha != tiempo_anterior:
                        if tiempo_anterior:
                            tiempo = ET.SubElement(resumen_xml, "TIEMPO")
                            fecha_elem = ET.SubElement(tiempo, "FECHA")
                            fecha_elem.text = tiempo_anterior
                            usr_mencionados = ET.SubElement(tiempo, "USR_MENCIONADOS")
                            usr_mencionados.text = str(len(usuarios_mencionados_total))
                            hash_incluidos = ET.SubElement(tiempo, "HASH_INCLUIDOS")
                            hash_incluidos.text = str(len(hashtags_total))
                        tiempo_anterior = fecha
                        usuarios_mencionados_total = set()
                        hashtags_total = set()

                    usuarios_mencionados_total.update(usuarios_mencionados)
                    hashtags_total.update(hashtags)

                except Exception as e:
                    print(f"Error al procesar el mensaje: {str(e)}")

            tiempo = ET.SubElement(resumen_xml, "TIEMPO")
            fecha_elem = ET.SubElement(tiempo, "FECHA")
            fecha_elem.text = tiempo_anterior
            usr_mencionados = ET.SubElement(tiempo, "USR_MENCIONADOS")
            usr_mencionados.text = str(len(usuarios_mencionados_total))
            hash_incluidos = ET.SubElement(tiempo, "HASH_INCLUIDOS")
            hash_incluidos.text = str(len(hashtags_total))

            tree_resumen = ET.ElementTree(resumen_xml)
            tree_resumen.write("resumen.xml")

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
            # Guardar el archivo XML de configuración en el servidor
            uploaded_config_file.save("nuevo_config.xml")

            # Verificar si el archivo configuracion.xml existe
            config_exists = os.path.exists("configuracion.xml")

            # Cargar las palabras de sentimientos positivos y negativos
            sentimientos = Sentimientos()

            if config_exists:
                # Cargar palabras existentes desde configuracion.xml
                tree = ET.parse("configuracion.xml")
                root = tree.getroot()

                for palabra_elem in root.findall(".//sentimientos_positivos/palabra"):
                    palabra = palabra_elem.text.strip()
                    sentimientos.palabras_positivas.add(palabra)
                    # print(f"Agregada palabra positiva: {palabra}")

                for palabra_elem in root.findall(".//sentimientos_negativos/palabra"):
                    palabra = palabra_elem.text.strip()
                    sentimientos.palabras_negativas.add(palabra)
                    # print(f"Agregada palabra negativa: {palabra}")

                # print(
                #   "Palabras positivas en la clase Sentimientos:",
                #   sentimientos.palabras_positivas,
                # )
                # print(
                # "Palabras negativas en la clase Sentimientos:",
            # sentimientos.palabras_negativas,
            # )

            # Cargar las palabras desde el archivo recién cargado
            tree_nuevo = ET.parse("nuevo_config.xml")
            root_nuevo = tree_nuevo.getroot()

            for palabra_elem in root_nuevo.findall(".//sentimientos_positivos/palabra"):
                palabra = palabra_elem.text.strip()

                palabra = unidecode(palabra)

                sentimientos.palabras_positivas.add(palabra)
                # print(f"Agregada palabra positiva: {palabra}")

            for palabra_elem in root_nuevo.findall(".//sentimientos_negativos/palabra"):
                palabra = palabra_elem.text.strip()

                palabra = unidecode(palabra)

                sentimientos.palabras_negativas.add(palabra)
                # print(f"Agregada palabra negativa: {palabra}")

            # Actualizar el archivo configuracion.xml
            resumen = ET.Element("diccionario")
            sentimientos_positivos = ET.SubElement(resumen, "sentimientos_positivos")
            for palabra in sentimientos.palabras_positivas:
                palabra_elem = ET.SubElement(sentimientos_positivos, "palabra")
                palabra_elem.text = palabra

            sentimientos_negativos = ET.SubElement(resumen, "sentimientos_negativos")
            for palabra in sentimientos.palabras_negativas:
                palabra_elem = ET.SubElement(sentimientos_negativos, "palabra")
                palabra_elem.text = palabra

            # print(
            # "Palabras positivas en la clase Sentimientos:",
            # sentimientos.palabras_positivas,
            # )
            # print(
            #   "Palabras negativas en la clase Sentimientos:",
            #   sentimientos.palabras_negativas,
            # )
            tree = ET.ElementTree(resumen)
            tree.write("configuracion.xml")

            # Contar las palabras positivas y negativas
            palabras_positivas_rechazadas = len(sentimientos.palabras_positivas) - len(
                sentimientos.palabras_positivas
            )
            palabras_negativas_rechazadas = len(sentimientos.palabras_negativas) - len(
                sentimientos.palabras_negativas
            )

            # Crear el archivo resumenConfig.xml
            resumen_config = ET.Element("CONFIG_RECIBIDA")
            ET.SubElement(resumen_config, "PALABRAS_POSITIVAS").text = str(
                len(sentimientos.palabras_positivas)
            )
            ET.SubElement(resumen_config, "PALABRAS_POSITIVAS_RECHAZADA").text = str(
                palabras_positivas_rechazadas
            )
            ET.SubElement(resumen_config, "PALABRAS_NEGATIVAS").text = str(
                len(sentimientos.palabras_negativas)
            )
            ET.SubElement(resumen_config, "PALABRAS_NEGATIVAS_RECHAZADA").text = str(
                palabras_negativas_rechazadas
            )

            tree_resumen_config = ET.ElementTree(resumen_config)
            tree_resumen_config.write("resumenConfig.xml")

            # Eliminar el archivo temporal del nuevo archivo cargado
            os.remove("nuevo_config.xml")

            # print(
            #   "Palabras positivas en la clase Sentimientos:",
            #  sentimientos.palabras_positivas,
            # )
            # print(
            #   "Palabras negativas en la clase Sentimientos:",
            #  sentimientos.palabras_negativas,
            # )

            return jsonify(
                {
                    "message": "Archivo de configuración XML procesado y resumen generado."
                }
            )
        else:
            return jsonify(
                {"error": "No se ha seleccionado un archivo XML de configuración."}
            )

    except Exception as e:
        return jsonify({"error": str(e)})


# Define rutas para consultar hashtags
@app.route("/consultar-hashtags", methods=["GET"])
def consultar_hashtags():
    fecha_inicio = request.args.get("fecha_inicio")
    fecha_fin = request.args.get("fecha_fin")
    # print("===================prubea si========================")

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

            if fecha not in hashtags_por_fecha:
                hashtags_por_fecha[fecha] = {}

            hashtag_registrados = set()
            for hashtag in hashtags:
                if hashtag not in hashtag_registrados:
                    hashtag_registrados.add(hashtag)
                    if hashtag in hashtags_por_fecha[fecha]:
                        hashtags_por_fecha[fecha][hashtag] += 1
                    else:
                        hashtags_por_fecha[fecha][hashtag] = 1

    # Formatear las fechas como cadenas de texto
    result = []
    for fecha, _hashtag in hashtags_por_fecha.items():
        fecha_str = fecha.strftime("%d/%m/%Y")
        result.append({"fecha": fecha_str, "hashtags": _hashtag})
    # print("hashtags_por_fecha:", hashtags_por_fecha)
    return jsonify({"hashtags_por_fecha": result})


@app.route("/consultar-sentimientos", methods=["GET"])
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
    tree1 = ET.parse("configuracion.xml")
    root1 = tree1.getroot()

    sentimientos = Sentimientos()  # Debes inicializar tus sentimientos aquí
    # Carga palabras positivas
    for palabra_elem in root1.findall(".//sentimientos_positivos/palabra"):
        palabra = palabra_elem.text.strip().lower()
        sentimientos.palabras_positivas.add(palabra)

    # Carga palabras negativas
    for palabra_elem in root1.findall(".//sentimientos_negativos/palabra"):
        palabra = palabra_elem.text.strip().lower()
        sentimientos.palabras_negativas.add(palabra)

    resultados = {}

    for mensaje_elem in root.findall(".//MENSAJE"):
        fecha_str = mensaje_elem.find("FECHA").text.split(", ")[1]
        fecha = datetime.strptime(fecha_str, "%d/%m/%Y")
        texto = mensaje_elem.find("TEXTO").text

        if fecha_inicio <= fecha <= fecha_fin:
            mensaje = Mensajes(fecha, texto)

            # Obtener las palabras en el mensaje
            palabras = mensaje.texto.split()

            palabras_positivas = 0
            palabras_negativas = 0

            for palabra in palabras:
                palabra = palabra.lower()
                if palabra in sentimientos.palabras_positivas:
                    palabras_positivas += 1
                elif palabra in sentimientos.palabras_negativas:
                    palabras_negativas += 1

            # Calcular el sentimiento del mensaje
            if palabras_positivas > palabras_negativas:
                sentimiento = "positivo"
            elif palabras_negativas > palabras_positivas:
                sentimiento = "negativo"
            else:
                sentimiento = "neutro"

            if fecha not in resultados:
                resultados[fecha] = {"positivos": 0, "negativos": 0, "neutros": 0}

            if sentimiento == "positivo":
                resultados[fecha]["positivos"] += 1
            elif sentimiento == "negativo":
                resultados[fecha]["negativos"] += 1
            else:
                resultados[fecha]["neutros"] += 1

            # print("==============================DEPURACION==========================")

            # print(
            # "Palabras positivas en la clase Sentimientos:",
            # sentimientos.palabras_positivas,
            # )
            # print(
            # "Palabras negativas en la clase Sentimientos:",
            # sentimientos.palabras_negativas,
            # )
            # print(f"Palabras en el mensaje ({fecha_str}): {palabras}")
            # print(f"Palabras positivas en el mensaje: {palabras_positivas}")
            # print(f"Palabras negativas en el mensaje: {palabras_negativas}")
            # print(f"Sentimiento del mensaje: {sentimiento}")

    # Formatear las fechas como cadenas de texto
    result = []
    for fecha, sentimientos in resultados.items():
        fecha_str = fecha.strftime("%d/%m/%Y")
        result.append(
            {
                "fecha": fecha_str,
                "positivos": sentimientos["positivos"],
                "negativos": sentimientos["negativos"],
                "neutros": sentimientos["neutros"],
            }
        )

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
            # print(usuarios_mencionados)

            if fecha not in usuarios_por_fecha:
                usuarios_por_fecha[fecha] = {}

            usuarios_registrados = set()
            for usuario in usuarios_mencionados:
                if usuario not in usuarios_registrados:
                    usuarios_registrados.add(usuario)
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
    sent = Sentimientos()
    sent.resetear_sentimientos()

    return "Datos reseteados correctamente", 200


if __name__ == "__main__":
    app.run(debug=True)
