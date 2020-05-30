import logging
import sys

import pandas as pd

from entities.infortunio import StatoInfortunio, Locazione, Settore
from wrapper import Wrapper
from wrapper_selenium import WrapperInformoSelenium


def main():
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    wrapper = Wrapper()
    wrapper.read_dataframe()
    wrapper.scrape_ids()

    # # Genera lo schema.
    # Base.metadata.create_all(engine)
    #
    # try:
    #     session = Session()
    #
    #     infortunio = wrapper.retrieve_injury_details(
    #         "11394",
    #         **{
    #             "StatoInfortunio": StatoInfortunio["Grave"],
    #             "Settore": Settore["Metallurgia"],
    #             "Locazione": Locazione["Centro"]
    #         }
    #     )
    #
    #     session.add(infortunio)
    #     session.commit()
    #     session.close()
    # except IntegrityError:
    #     logging.debug('ID already present. ')


if __name__ == "__main__":
    main()
