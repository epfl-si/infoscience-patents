import argparse
import datetime
import logging

from log_utils import add_logging_argument, set_logging_from_args

from Espacenet.query import EspacenetQuery


logger = logging.getLogger('main')
logger_infoscience = logging.getLogger('INFOSCIENCE')
logger_epo = logging.getLogger('EPO')


def main(args):
    logger.info("Searching for %s" % args)
    s = EspacenetQuery()
    fs = s.fetch('liquid')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    # Required positional argument
    parser.add_argument('search_value', 
                    help='A text to search',
                    nargs="*")

    parser = add_logging_argument(parser)
    args = parser.parse_args()
    set_logging_from_args(args)

    main(args)
