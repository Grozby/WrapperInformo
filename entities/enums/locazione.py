from enum import Enum


class Locazione(Enum):
    """
    Id corrispondente nella pagina di ricerca:
    Localizzazioneterritoriale-*, dove * corrisponde al numero associato alla locazione.
    """
    NordEst = 1
    NordOvest = 2
    Centro = 3
    SudEIsole = 4