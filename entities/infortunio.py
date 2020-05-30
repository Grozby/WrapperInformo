from entities.base import Base
from sqlalchemy import Column, String, Integer, Date, Enum as EnumSQL
from sqlalchemy.orm import relationship

from entities.enums.locazione import Locazione
from entities.enums.settore import Settore
from entities.incidente import Incidente
from entities.lavoratore import Lavoratore


class Infortunio(Base):
    __tablename__ = 'infortuni'

    id = Column(String(16), primary_key=True)

    settore_attivita = Column(EnumSQL(Settore))
    locazione = Column(EnumSQL(Locazione))
    data = Column(Date)
    ora_ordinale = Column(Integer, nullable=True)

    # One to Many
    incidenti = relationship("Incidente", order_by=Incidente.id, back_populates="infortunio")
