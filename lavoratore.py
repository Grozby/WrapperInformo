from enum import Enum


class TipoIncidente(Enum):
    VariazioneEnergia = 0
    VariazioneInterccia = 1

class Lavoratore:

    def __init__(self,
                 sesso,
                 nazionalita,
                 tipo_contratto,
                 mansione,
                 anzianita,
                 sede_lesione,
                 natura_lesione,
                 giorni_assenza_lavoro,  # Specificato se l'incidente non è mortale
                 azienda,
                 luogo_infortunio,
                 attivita_lavoratore_durante_infortunio,
                 ambiente_infortunio,
                 tipo_incidente: TipoIncidente,
                 incidente,
                 agente_materiale_incidente,
                 ):
        # Informazioni lavoratore
        self.sesso = sesso
        self.nazionalita = nazionalita
        self.tipo_contratto = tipo_contratto
        self.mansione = mansione
        self.anzianita = anzianita

        # Conseguenze
        self.sede_lesione = sede_lesione
        self.natura_lesione = natura_lesione
        self.giorni_assenza_lavoro = giorni_assenza_lavoro

        self.azienda = azienda
        self.luogo_infortunio = luogo_infortunio
        self.attivita_lavoratore_durante_infortunio = attivita_lavoratore_durante_infortunio
        self.ambiente_infortunio = ambiente_infortunio
        self.tipo_incidente: TipoIncidente = tipo_incidente
        self.incidente = incidente
        self.agente_materiale_incidente = agente_materiale_incidente

