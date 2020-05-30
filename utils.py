import time
from datetime import datetime

from entities.enums.stato_infortunio import StatoInfortunio
from entities.enums.tipo_incidente import TipoIncidente


def parse_int(string):
    try:
        return int(string)
    except ValueError:
        return None


def parse_date(string):
    try:
        return datetime.strptime(string, "%d/%m/%Y").date()
    except ValueError:
        return None


def sleep(val):
    if isinstance(val, float) and val > 0:
        time.sleep(float(val))


def get_injury_state(val):
    if val == "":
        return StatoInfortunio.Mortale
    else:
        return StatoInfortunio.Grave


def type_incident(val):
    if "energia" in val or "Energia" in val:
        return TipoIncidente.VariazioneEnergia
    elif "interfaccia" in val or "interfaccia" in val:
        return TipoIncidente.VariazioneInterfaccia
    else:
        print("??")
        return None
