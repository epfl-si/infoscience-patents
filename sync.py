import argparse
import datetime
import logging
import os
import time
from datetime import datetime
import xml.etree.ElementTree as ET

from log_utils import add_logging_argument, set_logging_from_args

logger = logging.getLogger('main')
logger_infoscience = logging.getLogger('INFOSCIENCE')
logger_epo = logging.getLogger('EPO')

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


def valid_input_date(s):
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

def main():
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-s",
                        "--startdate",
                        help="The start date - format YYYY-MM-DD",
                        required=True,
                        type=valid_input_date)

    parser.add_argument("-e",
                        "--enddate",
                        help="The end date - format YYYY-MM-DD. Default to today",
                        required=False,
                        type=valid_input_date)

    parser.add_argument("-f",
                        "--infoscience_patents_file",
                        help="The infoscience file of patents, in a MarcXML format",
                        required=False,
                        type=argparse.FileType('r'))


    parser = add_logging_argument(parser)
    args = parser.parse_args()
    set_logging_from_args(args)

    main()

    #SOON:
    try:
        BASE_DIR = os.path.join(__location__, '..')
        os.mkdir('./output')
    except FileExistsError:
        pass

    timestamp = time.strftime("%Y%m%d-%H%M%S")

    new_xml_path=""
    update_xml_path = os.path.join(
        BASE_DIR,
        "output",
        "patents-update-%s.xml" % timestamp
        )
