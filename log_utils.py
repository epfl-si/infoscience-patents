import logging
import sys
import os
import time


__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


class InfoFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno in (logging.DEBUG, logging.INFO)


def set_logging_configuration(debug=False):
    """
    Use --verbose and/or --debug from arguments to fix level of logging
    """
    # https://stackoverflow.com/questions/16061641/python-logging-split-between-stdout-and-stderr/16066513#16066513

    default_formatter = logging.Formatter('%(asctime)s - %(levelname)s:%(name)s: %(message)s')
    loglevel = logging.WARNING
    if debug:
        loglevel = logging.DEBUG

    logger = logging.getLogger('main')
    logger.setLevel(loglevel)

    logger_infoscience = logging.getLogger('INFOSCIENCE')
    logger_infoscience.setLevel(loglevel)

    logger_epo = logging.getLogger('EPO')
    logger_epo.setLevel(loglevel)

    stdout_handler = logging.StreamHandler(sys.stdout)
    if debug:
        stdout_handler.setLevel(logging.DEBUG)
    else:
        stdout_handler.setLevel(logging.WARNING)
    stdout_handler.setFormatter(default_formatter)

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

    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(default_formatter)

    logger.addHandler(stdout_handler)
    logger.addHandler(file_handler)

    logger_infoscience.addHandler(stdout_handler)
    logger_infoscience.addHandler(file_handler)

    logger_epo.addHandler(stdout_handler)
    logger_epo.addHandler(file_handler)
