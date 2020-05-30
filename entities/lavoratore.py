from entities.base import Base
from sqlalchemy import Column, String, Integer, Date, Enum, ForeignKey
from sqlalchemy.orm import relationship


class Lavoratore(Base):
    __tablename__ = 'lavoratori'

    # Informazioni lavoratore
    lavoratore_id = Column(String(16), primary_key=True)
    sesso = Column(String(16))
    nazionalita = Column(String(50))
    tipo_contratto = Column(String(200))
    mansione = Column(String(400))
    anzianita = Column(String(100))

    # Informazioni azienda
    numero_addetti_azienda = Column(Integer)
    attivita_prevalente_azienda = Column(String(400))

    #
    sede_lesione = Column(String(400))
    natura_lesione = Column(String(400))
    giorni_assenza_lavoro = Column(Integer, nullable=True)  # Specificato se l'incidente non è mortale
    luogo_infortunio = Column(String(400))
    attivita_lavoratore_durante_infortunio = Column(String(800))
    ambiente_infortunio = Column(String(400))
    tipo_incidente = Column(String(400))
    incidente = Column(String(400))
    agente_materiale_incidente = Column(String(400))

    infortunio_id = Column(String(16), ForeignKey('infortuni.id', ondelete='CASCADE'))
    infortunio = relationship("Infortunio", back_populates="lavoratori")
