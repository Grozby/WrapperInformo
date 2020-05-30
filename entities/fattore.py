from entities.base import Base
from sqlalchemy import Column, String, Integer, Date, Enum, ForeignKey
from sqlalchemy.orm import relationship


class Fattore(Base):
    __tablename__ = 'fattori'

    fattore_id = Column(String(16), primary_key=True)
    descrizione = Column(String(500))
    tipologia = Column(String(100))
    determinante_modulatore = Column(String(16))
    tipo_modulazione = Column(String(100))
    classificazione = Column(String(100))
    stato_processo = Column(String(16))
    problema_sicurezza = Column(String(400))
    confronto_standard = Column(String(100))
    valutazione_rischi = Column(String(400))

    infortunio_id = Column(String(16), ForeignKey('infortuni.id', ondelete='CASCADE'))
    infortunio = relationship("Infortunio", back_populates="fattori")


