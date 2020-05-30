from enum import Enum
from entities.base import Base
from sqlalchemy import Column, String, Integer, Date, Enum as EnumSQL, ForeignKey
from sqlalchemy.orm import relationship

from entities.fattore import Fattore
from entities.lavoratore import Lavoratore


class Locazione(Enum):
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


class Infortunio(Base):
    __tablename__ = 'infortuni'

    id = Column(String(16), primary_key=True)
    stato = Column(EnumSQL(StatoInfortunio))
    settore_attivita = Column(EnumSQL(Settore))
    descrizione = Column(String(5000))
    locazione = Column(EnumSQL(Locazione))
    data = Column(Date)
    ora_ordinale = Column(Integer, nullable=True)
    fattori = relationship("Fattore", order_by=Fattore.fattore_id, back_populates="infortunio")
    lavoratori = relationship("Lavoratore", order_by=Lavoratore.lavoratore_id, back_populates="infortunio")
