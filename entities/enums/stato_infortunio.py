from enum import Enum


class StatoInfortunio(Enum):
    """
    # Nella pagina di ricerca principale, il parametro URL tipoEvento=0 corrisponde
    # agli infortuni gravi, tipoEvento=1 a quelli mortali.
    """
    Grave = 0
    Mortale = 1