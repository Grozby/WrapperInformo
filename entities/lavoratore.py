from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship

from entities.base import Base
from entities.incidente import Incidente


class Lavoratore(Base):
    __tablename__ = 'lavoratori'

    id = Column(String(16), ForeignKey("incidenti.id", ondelete='CASCADE'),primary_key=True)

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
