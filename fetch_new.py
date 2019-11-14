import argparse
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
import time
import os

import epo_ops

from log_utils import set_logging_configuration

from Espacenet.builder import EspacenetBuilderClient, fetch_abstract_from_all_patents

from Espacenet.marc import MarcRecordBuilder, MarcCollection, _get_best_patent_for_data
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

from updater import is_full_export


logger = logging.getLogger('main')
logger_infoscience = logging.getLogger('INFOSCIENCE')
logger_epo = logging.getLogger('EPO')

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


def fetch_new_infoscience_patents(xml_str, starting_year):
    """
    Load patents inside the xml provided
    and an updated version of it (aka added new patent to existing ones)
    """
    logger_infoscience.info("Loading provided xml file for fetching new patents...")

    xml_str = filter_out_namespace(xml_str)
    provided_collection = ET.fromstring(xml_str)

    new_collection = MarcCollection()
    records = provided_collection.findall('record')

    logger_infoscience.info(
        "Reference xml file as %s records, starting the fetch of new patents from the year %s..." % (
            len(records),
            starting_year
            )
    )

    # some counters for logs
    current_patent_in_infoscience = len(records)
    new_patents_for_infoscience_found = 0
    patent_found_espacenet = 0

    client = EspacenetBuilderClient(use_cache=True)
    patents_for_year = client.search(
        value = 'pa all "Ecole Polytech* Lausanne" and pd>%s' % starting_year,
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
            logger_infoscience.info("The family id %s is not in Infoscience, adding it to our xml" % family_id)

            # add it to collection
            # but fist, get some data from a patent
            best_patent_to_fetch = _get_best_patent_for_data(patents)
            client = EspacenetBuilderClient(use_cache=True)

            fulfilled_patent = client.patent(  # Retrieve bibliography data
                input = epo_ops.models.Docdb(best_patent_to_fetch.number, best_patent_to_fetch.country, best_patent_to_fetch.kind),  # original, docdb, epodoc
            )
            m_record = MarcRecordBuilder().from_epo_patents(family_id=family_id,
                                                            patents=patents,
                                                            fulfilled_patent=fulfilled_patent,
                                                            auto_year=True)
            # set abstract if needed
            if not m_record.abstract:
                new_abstract = fetch_abstract_from_all_patents(patents)
                if new_abstract:
                    m_record.abstract = new_abstract

            # Set to collection S2 for SISB
            m_record.S2_collection = True  # use setter default values
            # Set to collection TTO
            m_record.TTO_collection = True  # use setter default values
            m_record.collection_id = 'PATENT'

            new_collection.append(m_record.marc_record)
            new_patents_for_infoscience_found += 1

    logger_infoscience.info("%s new record to add" % new_patents_for_infoscience_found)

    return new_collection


if __name__ == '__main__':
    # force debug logging
    parser = argparse.ArgumentParser()

    parser.add_argument("-f",
                        "--infoscience_patents_export",
                        help="The infoscience file of patents, in a MarcXML format",
                        required=True,
                        type=argparse.FileType('r'))

    parser.add_argument("-y",
                        "--starting_year",
                        help="The starting year to compare Espacenet with the infoscience data",
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
        "patents-new-from-%s-%s.xml" % (
            args.starting_year,
            time.strftime("%Y%m%d-%H%M%S")
            )
        )

    export_as_string = args.infoscience_patents_export.read()

    is_full_export(export_as_string)

    new_xml_collection = fetch_new_infoscience_patents(export_as_string, args.starting_year)
    logger_infoscience.info("Writing the new record(s) in %s" % new_xml_path)
    new_xml_collection.write(new_xml_path)
