

class Fattori:
    def __init__(
            self,
            descrizione: str,
            determinante_modulatore,
            tipo_modulazione,
            classificazione,
            stato_processo,
            problema_sicurezza,
            confronto_standard,
            valutazione_rischi
    ):
        self.descrizione: str = descrizione
        self.determinante_modulatore = determinante_modulatore
        self.tipo_modulazione = tipo_modulazione
        self.classificazione = classificazione
        self.stato_processo = stato_processo
        self.problema_sicurezza = problema_sicurezza
        self.confronto_standard = confronto_standard
        self.valutazione_rischi = valutazione_rischi
