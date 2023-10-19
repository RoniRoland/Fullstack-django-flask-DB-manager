import re


class Mensajes:
    contador_id = 1

    def __init__(self, fecha, texto) -> None:
        self.fecha = fecha
        self.texto = texto
        self.id = Mensajes.contador_id
        Mensajes.contador_id += 1

    def __eq__(self, other):
        return self.fecha == other.fecha and self.texto == other.texto

    def obtener_texto(self):
        return self.texto

    def obtener_hashtags(self):
        return re.findall(r"#\w+", self.texto)

    def obtener_usuarios_mencionados(self):
        return re.findall(r"@\w+", self.texto)

    def resetear(self):
        self.fecha = ""
        self.texto = ""
