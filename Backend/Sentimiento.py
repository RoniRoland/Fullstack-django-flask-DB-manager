class Sentimientos:
    def __init__(self):
        self.palabras_positivas = set()
        self.palabras_negativas = set()

    def __eq__(self, other):
        return (
            self.palabras_positivas == other.palabras_positivas
            and self.palabras_negativas == other.palabras_negativas
        )

    def resetear_sentimientos(self):
        self.palabras_positivas = ""
        self.palabras_negativas = ""
