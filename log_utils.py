import logging
import sys


def add_logging_argument(parser):
    parser.add_argument(
        '-d', '--debug',
        help="Print debugging info into logs",
        action="store_const", dest="loglevel", const=logging.DEBUG,
        default=logging.WARNING,
    )

    parser.add_argument(
        '-v', '--verbose',
        help="Print standard information on the process",
        action="store_const", dest="loglevel", const=logging.INFO,
    )

    return parser


def set_logging_from_args(args):
    """
    Use --verbose and/or --debug from arguments to fix level of logging
    """
    # https://stackoverflow.com/questions/16061641/python-logging-split-between-stdout-and-stderr/16066513#16066513

    default_formatter = logging.Formatter('%(asctime)s - %(levelname)s:%(name)s: %(message)s')

    logger = logging.getLogger('main')
    logger.setLevel(args.loglevel)

    logger_infoscience = logging.getLogger('INFOSCIENCE')
    logger_infoscience.setLevel(args.loglevel)

    logger_epo = logging.getLogger('EPO')
    logger_epo.setLevel(args.loglevel)

    h1 = logging.StreamHandler(sys.stdout)
    h1.setLevel(logging.DEBUG)
    h1.addFilter(lambda record: record.levelno <= logging.INFO)
    h1.setFormatter(default_formatter)
    h2 = logging.StreamHandler()
    h2.setLevel(logging.WARNING)
    h2.setFormatter(default_formatter)

    logger.addHandler(h1)
    logger.addHandler(h2)

    logger_infoscience.addHandler(h1)
    logger_infoscience.addHandler(h2)

    logger_epo.addHandler(h1)
    logger_epo.addHandler(h2)
