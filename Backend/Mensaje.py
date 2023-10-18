import re


class Mensajes:
    def __init__(self, fecha, texto) -> None:
        self.fecha = fecha
        self.texto = texto

    def obtener_hashtags(self):
        return re.findall(r"#\w+", self.texto)

    def obtener_usuarios_mencionados(self):
        return re.findall(r"@\w+", self.texto)

    def resetear(self):
        self.fecha = ""
        self.texto = ""
