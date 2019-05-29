
import argparse
import datetime
import logging

from log_utils import add_logging_argument, set_logging_from_args

logger = logging.getLogger('main')
logger_infoscience = logging.getLogger('INFOSCIENCE')
logger_epo = logging.getLogger('EPO')




def valid_input_date(s):
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

def main():
    # load the file
    #with open(args1) as input_patents_file:
    #    print(input_patents_file)
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

    parser = add_logging_argument(parser)
    args = parser.parse_args()
    set_logging_from_args(args)
    

    #TODO: put this somewhere
    logger.info("Loading the provided MarcXML file")
    # or
    logger.info("Loading Infoscience patents")    
    # TOREMOVE:
    logger.info("logger info")
    logger_infoscience.warning("info warning")
    logger_epo.debug("a debug msg")

    main()
