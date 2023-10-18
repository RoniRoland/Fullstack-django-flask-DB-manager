from datetime import datetime
from flask import Flask, request, jsonify
import os
from pathlib import Path
from flask_cors import CORS
import xml.etree.ElementTree as ET
from Mensaje import Mensajes
import re


app = Flask(__name__)
CORS(app)


@app.route("/cargar-xml", methods=["POST"])
def cargar_xml():
    try:
        uploaded_file = request.files["archivo"]
        if uploaded_file.filename != "":
            # Guardar el archivo XML en el servidor
            uploaded_file.save("uploaded.xml")

            # Procesar el archivo XML
            mensajes = []
            tree = ET.parse("uploaded.xml")
            root = tree.getroot()
            for mensaje_elem in root.findall(".//MENSAJE"):
                fecha = mensaje_elem.find("FECHA").text
                texto = mensaje_elem.find("TEXTO").text
                mensajes.append(Mensajes(fecha, texto))

            # Crear un elemento raíz para el archivo resumen.xml
            resumen = ET.Element("MENSAJES_RECIBIDOS")
            fecha_actual = ""
            usuarios_mencionados = set()
            hashtags_incluidos = set()

            for mensaje in mensajes:
                fecha = mensaje.fecha.split(", ")[1]
                if fecha != fecha_actual:
                    # Si cambió la fecha, crear un nuevo intervalo
                    if fecha_actual:
                        tiempo = ET.SubElement(resumen, "TIEMPO")
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

            # Agregar el último intervalo
            tiempo = ET.SubElement(resumen, "TIEMPO")
            fecha_elem = ET.SubElement(tiempo, "FECHA")
            fecha_elem.text = fecha_actual
            msj_recibidos = ET.SubElement(tiempo, "MSJ_RECIBIDOS")
            msj_recibidos.text = str(mensajes_en_intervalo)
            usr_mencionados = ET.SubElement(tiempo, "USR_MENCIONADOS")
            usr_mencionados.text = str(len(usuarios_mencionados))
            hash_incluidos = ET.SubElement(tiempo, "HASH_INCLUIDOS")
            hash_incluidos.text = str(len(hashtags_incluidos))

            tree = ET.ElementTree(resumen)
            tree.write("resumen.xml")

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

            palabras_positivas = set()
            palabras_negativas = set()

            for palabra in root_config.find(".//sentimientos_positivos"):
                palabras_positivas.add(palabra.text.lower())
            for palabra in root_config.find(".//sentimientos_negativos"):
                palabras_negativas.add(palabra.text.lower())

            # print(palabras_positivas)  # Agrega esta línea para depurar
            # print(palabras_negativas)

            # Procesa la base de datos
            tree_data = ET.parse("uploaded.xml")
            root_data = tree_data.getroot()

            palabras_positivas_contador = 0
            palabras_negativas_contador = 0

            # Limpia el diccionario
            palabras_positivas = set(
                [palabra.strip().lower() for palabra in palabras_positivas]
            )
            palabras_negativas = set(
                [palabra.strip().lower() for palabra in palabras_negativas]
            )

            for mensaje_elem in root_data.findall(".//MENSAJE"):
                texto = mensaje_elem.find("TEXTO").text.lower()
                # print("Texto del mensaje:", texto)

                # Utiliza una expresión regular para dividir el texto en palabras
                palabras_en_texto = re.findall(r"\b\w+\b", texto)
                # print("Palabras en el texto:", palabras_en_texto)

                for palabra in palabras_en_texto:
                    # Elimina caracteres no alfabéticos de la palabra
                    palabra = re.sub(r"[^a-zA-Z]", "", palabra)
                    palabra = palabra.lower()  # Convierte la palabra a minúsculas

                    if palabra in palabras_positivas:
                        palabras_positivas_contador += 1
                    elif palabra in palabras_negativas:
                        palabras_negativas_contador += 1

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
