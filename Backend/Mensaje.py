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
        texto_en_minusculas = self.texto.lower()
        return re.findall(r"#\w+#", texto_en_minusculas)

    def obtener_usuarios_mencionados(self):
        self.texto = self.texto.strip()
        # print("Texto antes de analizar:", self.texto)

        usuarios = []
        mencionando = False

        palabras = self.texto.split()

        for palabra in palabras:
            if palabra.startswith("@"):
                usuario = palabra.lstrip("@").lower()
                if usuario and all(char.isalnum() or char == "_" for char in usuario):
                    usuarios.append("@" + usuario)
                    mencionando = True
                else:
                    mencionando = False
            elif mencionando:
                mencionando = False

        # print("Usuarios válidos en este mensaje:", usuarios)

        return usuarios

    def resetear(self):
        self.fecha = ""
        self.texto = ""
        self.id = 0
