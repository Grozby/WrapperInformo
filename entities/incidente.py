from sqlalchemy import Column, String, Integer, Enum as EnumSQL, ForeignKey
from sqlalchemy.orm import relationship

from entities.base import Base
from entities.enums.stato_infortunio import StatoInfortunio
from entities.enums.tipo_incidente import TipoIncidente
from entities.fattore import Fattore


class Incidente(Base):
    __tablename__ = 'incidenti'

    id = Column(String(16), primary_key=True)

    # Descrizione generale incidente
    stato_infortunio = Column(EnumSQL(StatoInfortunio))
    descrizione_della_dinamica = Column(String(3000))

    #
    luogo_infortunio = Column(String(400))
    attivita_lavoratore_durante_infortunio = Column(String(800))
    ambiente = Column(String(400))
    tipo_incidente = Column(EnumSQL(TipoIncidente))
    descrizione_incidente = Column(String(400))
    agente_materiale = Column(String(400))

    # Conseguenze
    sede_lesione = Column(String(400))
    natura_lesione = Column(String(400))
    giorni_assenza_lavoro = Column(Integer, nullable=True)  # Specificato se l'incidente non è mortale

    # One to One
    lavoratore = relationship("Lavoratore", uselist=False, back_populates="incidente")

    # Many to One
    infortunio_id = Column(String(16), ForeignKey('infortuni.id', ondelete='CASCADE'))
    infortunio = relationship("Infortunio", back_populates="incidenti")

    # One to Many
    fattori = relationship("Fattore", order_by=Fattore.fattore_id, back_populates="incidente", cascade="all, delete-orphan")
