import argparse
import logging
import xml.etree.ElementTree as ET
import time
import os

from log_utils import set_logging_configuration

from Espacenet.builder import EspacenetBuilderClient

from Espacenet.marc import MarcRecordBuilder, MarcCollection
from Espacenet.patent_models import Patent
from Espacenet.builder import EspacenetBuilderClient
from Espacenet.marc_xml_utils import \
    filter_out_namespace, \
    _get_controlfield_element, \
    _get_controlfield_value, \
    _get_datafield_element, \
    _get_subfield_element, \
    _get_datafield_values, \
    _get_multifield_values


logger = logging.getLogger('main')
logger_infoscience = logging.getLogger('INFOSCIENCE')
logger_epo = logging.getLogger('EPO')

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


def fetch_new_infoscience_patents(xml_file):
    """
    Load patents inside the xml provided
    and an updated version of it (aka added new patent to existing ones)
    """
    logger_infoscience.info("Loading provided xml file for an update...")

    xml_file = filter_out_namespace(xml_file.read())
    provided_collection = ET.fromstring(xml_file)

    new_collection = MarcCollection()
    records = provided_collection.findall('record')
    # first assert we are in an unique year
    for i, record in enumerate(records):
        year = record.find('datafield[@tag="260"]/subfield[@code="c"]').text
        if i == 0:
            year_of_ref = year

        assert year == year_of_ref

    logger_infoscience.info(
        "Reference xml file as %s records for year %s, starting the fetch of new patents..." % (
            year,
            len(records)
            )
    )

    # some counters for logs
    current_patent_in_infoscience = len(records)
    new_patents_for_infoscience_found = 0
    patent_found_espacenet = 0

    client = EspacenetBuilderClient(use_cache=True)
    patents_for_year = client.search(
        value = 'pa all "Ecole Polytech* Lausanne" and pd=%s' % year,
        )

    infoscience_family_patent_list = []

    for element_family_id in provided_collection.findall(
        'record/datafield[@tag="024"]/subfield[@code="2"][.="EPO Family ID"]/../subfield[@code="a"]'
        ):
        infoscience_family_patent_list.append(element_family_id.text)

    logger_infoscience.debug("Fetched %s family ids from infoscience xml" % len(infoscience_family_patent_list))

    # check if patents family are found and exists in given references
    for family_id, patents in patents_for_year.patent_families.items():
        if family_id not in infoscience_family_patent_list:
            # add the patent to new
            logger_infoscience.info("The family id %s is not in Infosicence, adding it" % family_id)

            # -> create a new record with {patents}
            # add it to collection
            m_record = MarcRecordBuilder().from_epo_patents(family_id=family_id, patents=patents)

            new_collection.append(m_record.marc_record)
            new_patents_for_infoscience_found += 1

    logger_infoscience.info("%s new record to add" % new_patents_for_infoscience_found)

    return new_collection


if __name__ == '__main__':
    # force debug logging
    parser = argparse.ArgumentParser()

    parser.add_argument("-f",
                        "--infoscience_patents",
                        help="The infoscience file of patents, in a MarcXML format",
                        required=True,
                        type=argparse.FileType('r'))

    parser.add_argument("-y",
                        "--year",
                        help="The specific year to compare Espacenet with the infoscience data",
                        required=True,
                        type=int)


    # create the place where we add the results
    try:
        BASE_DIR = __location__
        os.mkdir('./output')
    except FileExistsError:
        pass

    args = parser.parse_args()
    set_logging_configuration()

    # set the name of the file
    new_xml_path = os.path.join(
        BASE_DIR,
        "output",
        "patents-new-%s-%s.xml" % (
            args.year,
            time.strftime("%Y%m%d-%H%M%S")
            )
        )

    new_xml_collection = fetch_new_infoscience_patents(args.infoscience_patents)
    new_xml_collection.write(new_xml_path)
