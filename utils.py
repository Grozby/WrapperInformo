import time
from datetime import datetime


def parse_int(string):
    try:
        return int(string)
    except ValueError:
        return None


def parse_date(string):
    try:
        datetime.strptime("25/02/2016", "%d/%m/%Y")
    except ValueError:
        return None


def sleep(val):
    if isinstance(val, float) and val > 0:
        time.sleep(float(val))
