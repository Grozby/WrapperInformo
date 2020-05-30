from sqlalchemy import Column, String, ForeignKey, Enum as EnumSQL
from sqlalchemy.orm import relationship

from entities.base import Base
from entities.enums.determinante_modulatore import DeterminanteModulatore
from entities.enums.stato_processo import StatoProcesso


class Fattore(Base):
    __tablename__ = 'fattori'

    fattore_id = Column(String(16), primary_key=True)

    descrizione = Column(String(500))
    determinante_modulatore = Column(EnumSQL(DeterminanteModulatore))
    tipo_modulazione = Column(String(100))
    classificazione = Column(String(100))
    stato_processo = Column(EnumSQL(StatoProcesso))
    tipologia = Column(String(100))

    problema_sicurezza = Column(String(400))
    confronto_standard = Column(String(100))
    valutazione_rischi = Column(String(400))

    # Many to One
    incidente_id = Column(String(16), ForeignKey('incidenti.id', ondelete='CASCADE'))
    incidente = relationship("Incidente", back_populates="fattori")
