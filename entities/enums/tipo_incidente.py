from enum import Enum


class TipoIncidente(Enum):
    """
    # Nella pagina di ricerca principale, il parametro URL tipoEvento=0 corrisponde
    # agli infortuni gravi, tipoEvento=1 a quelli mortali.
    """
    VariazioneInterfaccia = 0
    VariazioneEnergia = 1