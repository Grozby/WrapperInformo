import logging
import sys

import pandas as pd

from entities.enums.stato_infortunio import StatoInfortunio
from entities.enums.settore import Settore
from entities.enums.locazione import Locazione
from wrapper import Wrapper
from wrapper_selenium import WrapperInformoSelenium


def main():
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    wrapper = Wrapper()
    wrapper.read_ids_dataframe()
    wrapper.scrape_injuries_ids()
    wrapper.scrape_injuries_details()


if __name__ == "__main__":
    main()
