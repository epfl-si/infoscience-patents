import logging
import sys
import os
import time

"""
Use it like this :
logger = logging.getLogger('main')
logger_infoscience = logging.getLogger('INFOSCIENCE')
logger_epo = logging.getLogger('EPO')
"""

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


class InfoFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno in (logging.DEBUG, logging.INFO)


def set_logging_configuration():
    """
    Use --verbose and/or --debug from arguments to fix level of logging
    """
    # https://stackoverflow.com/questions/16061641/python-logging-split-between-stdout-and-stderr/16066513#16066513

    default_formatter = logging.Formatter('%(asctime)s - %(levelname)s:%(name)s: %(message)s')
    loglevel = logging.INFO

    logger = logging.getLogger('main')
    logger.setLevel(loglevel)

    logger_infoscience = logging.getLogger('INFOSCIENCE')
    logger_infoscience.setLevel(loglevel)

    logger_epo = logging.getLogger('EPO')
    logger_epo.setLevel(loglevel)

    h1 = logging.StreamHandler(sys.stdout)
    h1.setLevel(logging.INFO)
    h1.addFilter(InfoFilter())
    h1.setFormatter(default_formatter)
    h2 = logging.StreamHandler()
    h2.setLevel(logging.WARNING)
    h2.setFormatter(default_formatter)

    try:
        BASE_DIR = __location__
        os.mkdir('./output')
    except FileExistsError:
        pass

    log_path = os.path.join(
        BASE_DIR,
        "output",
        "%s.log" % time.strftime("%Y%m%d-%H%M%S")
        )

    h3_file = logging.FileHandler(log_path)
    h3_file.setLevel(logging.DEBUG)
    h3_file.setFormatter(default_formatter)

    logger.addHandler(h1)
    logger.addHandler(h2)
    logger.addHandler(h3_file)

    logger_infoscience.addHandler(h1)
    logger_infoscience.addHandler(h2)
    logger_infoscience.addHandler(h3_file)

    logger_epo.addHandler(h1)
    logger_epo.addHandler(h2)
    logger_epo.addHandler(h3_file)
