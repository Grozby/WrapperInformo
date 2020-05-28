from enum import Enum


class Localita(Enum):
    """
    Id corrispondente nella pagina di ricerca:
    Localizzazioneterritoriale-*, dove * corrisponde al numero associato alla locazione.
    """
    NordEst = 1
    NordOvest = 2
    Centro = 3
    SudEIsole = 4


class Settore(Enum):
    """
    Id corrispondente nella pagina di ricerca:
    Settore_Attività-*, dove * corrisponde al numero associato alla locazione.
    """
    Metallurgia = 4
    FabbricazioneMacchine = 6


class StatoInfortunio(Enum):
    """
    # Nella pagina di ricerca principale, il parametro URL tipoEvento=0 corrisponde
    # agli infortuni gravi, tipoEvento=1 a quelli mortali.
    """
    Grave = 0
    Mortale = 1


class Infortunio:
    def __init__(self,
                 caso_id,
                 stato: StatoInfortunio,
                 settore_attivita: Settore,
                 descrizione: str,
                 locazione,
                 data,
                 ora_ordinale,
                 fattori,
                 lavoratori
                 ):

        self.caso_id = caso_id
        self.stato: StatoInfortunio = stato
        self.locazione = locazione
        self.descrizione: str = descrizione
        self.settore_attivita: Settore = settore_attivita
        self.fattori = fattori
        self.data = data
        self.ora_ordinale = ora_ordinale
        self.lavoratori = lavoratori
