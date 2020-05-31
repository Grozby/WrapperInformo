import logging
import sys

from wrapper import Wrapper


def main():
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    wrapper = Wrapper()
    wrapper.scrape_injuries_ids()
    wrapper.scrape_injuries_details()


if __name__ == "__main__":
    main()
