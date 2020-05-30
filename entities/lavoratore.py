from entities.base import Base
from sqlalchemy import Column, String, Integer, Date, Enum, ForeignKey, Enum as EnumSQL
from sqlalchemy.orm import relationship

from entities.fattore import Fattore
from entities.enums.stato_infortunio import StatoInfortunio


class Lavoratore(Base):
    __tablename__ = 'lavoratori'
    id = Column(String(16), primary_key=True)

    # Informazioni lavoratore
    sesso = Column(String(16))
    nazionalita = Column(String(50))
    tipo_contratto = Column(String(200))
    mansione = Column(String(400))
    anzianita = Column(String(100))

    # Informazioni azienda
    numero_addetti_azienda = Column(Integer)
    attivita_prevalente_azienda = Column(String(400))

    # One to One
    incidente = relationship("Incidente", back_populates="lavoratore")



