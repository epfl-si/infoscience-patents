import argparse
import logging
import xml.etree.ElementTree as ET
import time
import os

import epo_ops
from requests.exceptions import HTTPError

from log_utils import set_logging_configuration

from Espacenet.marc import MarcRecordBuilder, MarcCollection
from Espacenet.patent_models import Patent
from Espacenet.builder import EspacenetBuilderClient, fetch_abstract_from_all_patents
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


def is_full_export(xml_file):
    # do a basic check on how many records we are provided
    xml_file = filter_out_namespace(xml_file)
    provided_collection = ET.fromstring(xml_file)
    records = provided_collection.findall('record')
    # assert we have +1000 records or cancel the update
    assert len(records) > 1000, """It looks like you did not provide the full export,
                                    we have only %s records, and we need more than 1000""" % len(records)

def update_infoscience_export(xml_str, range_start=None, range_end=None):
    """
    Load patents inside the xml provided
    and an updated version of it (aka added new patent to existing ones)
    args:
        xml_file: the marcXML of infoscience patents
        range_start, range_end: set one if you want to update only a range of patents (mainly used in tests)
    """
    logger_infoscience.info("Loading provided xml file for an update...")
    client = EspacenetBuilderClient(use_cache=True)

    xml_str = filter_out_namespace(xml_str)
    provided_collection = ET.fromstring(xml_str)

    update_collection = MarcCollection()
    records = provided_collection.findall('record')

    logger_infoscience.info("Starting the update with the provided xml...")

    # some counters for logs
    patent_updated = 0
    family_updated = 0
    alternative_titles_updated = 0
    abstract_added = 0

    # limit as asked
    records = records[range_start:range_end]

    for i, record in enumerate(records):
        has_been_patent_updated = False
        has_been_family_updated = False
        has_been_notes_for_alternatives_title_changed = False
        has_been_abstract_added = False
        marc_record = MarcRecordBuilder().from_infoscience_record(record=record)

        family_id_text = ""
        if marc_record.family_id:
            family_id_text = "family id = %s" % marc_record.family_id
        else:
            family_id_text = "No family id"

        logger_infoscience.info("--------")
        logger_infoscience.info("Parsing record %s, %s (%s/%s)" % (
                marc_record.record_id,
                family_id_text,
                i+1,
                len(records),
                )
            )

        # is it good to go ?
        if not marc_record.record_id:
            logger_infoscience.info(
                "Skipping record %s, the record has no id" % marc_record.record_id
                )
            continue

        if marc_record.tagged_done:
            logger_infoscience.info(
                "Skipping record %s, the tag 974__b is set" % marc_record.record_id
                )
            continue

        if len(marc_record.patents) == 0:
            logger_infoscience.info(
                "Skipping record %s, no patents have been found in it" % marc_record.record_id
                )
            continue

        # get the best epodoc to do queries or abort
        epodoc_for_query = marc_record.epodoc_for_query
        if not epodoc_for_query:
            logger_infoscience.info(
                "Skipping record %s, patent(s) are not in a known format" % marc_record.record_id
                )
            continue

        # check family
        if not marc_record.family_id:
            # try to get the family_id before going to update
            logger_infoscience.info("Missing family id for this record, parsing one...")

            try:
                patent = client.patent(
                    input = epo_ops.models.Epodoc(epodoc_for_query),
                )
            except HTTPError as e:
                logger_epo.warning(
                    "Skipping this record, it crash Espacenet: %s, error was %s" % (epodoc_for_query, e)
                    )
                continue

            marc_record.family_id = patent.family_id
            logger_infoscience.info("Updating Family id to %s" % marc_record.family_id)
            has_been_family_updated = True
            family_updated += 1

        try:
            patents_families, fulfilled_patent = client.family(
                input = epo_ops.models.Epodoc(epodoc_for_query)
            )
        except HTTPError as e:
            #TODO:
            # voir si une attaque sur l'api que du brevet nous retourne les meta données, sinon :
            # si erreur 413, essayer de parser le contenu sans le /biblio (ce qui devrait nous
            # fournir la liste des brevets sans les meta données)
            if e.response.status_code == 413:
                # retry without pyblio, so get at least some patents
                try:
                    logger_epo.info("Retrying this record without biblio information, Espacenet has problem with it: %s, error was %s" % (epodoc_for_query, e))
                    patents_families = client.family(
                        input = epo_ops.models.Epodoc(epodoc_for_query),
                        endpoint = ''
                    )
                except HTTPError as e:
                    logger_epo.warning("Skipping this record, Espacenet has a problem with it: %s, error was %s" % (epodoc_for_query, e))
                    continue
            else:
                logger_epo.warning("Skipping this record, Espacenet has a problem with it: %s, error was %s" % (epodoc_for_query, e))
                continue

        # comparing the length should do the trick, the epodoc don't change everytimes
        if len(patents_families.patents) != len(marc_record.patents):
            # we have a different number of patents, update the marc record
            logger_infoscience.info("The record need a patent update, doing the update with through patent %s..." % epodoc_for_query)

            marc_record.update_patents_from_espacenet(patents_families.patents)

            assert(len(marc_record.patents) != 0)
            has_been_patent_updated = True
            patent_updated += 1

            logger_infoscience.info("Updated patents for this record to : %s" % marc_record.patents)
        else:
            logger_infoscience.info("This record does not need an update of his patents")

        # set alternative titles
        has_been_notes_for_alternatives_title_changed = MarcRecordBuilder().set_titles(marc_record, fulfilled_patent)

        if has_been_notes_for_alternatives_title_changed:
            logger_infoscience.info("This record need an update of his alternative titles")
            alternative_titles_updated += 1

        # set abstract if needed
        if not marc_record.abstract:
            new_abstract = fetch_abstract_from_all_patents(patents_families.patents)
            if new_abstract:
                marc_record.abstract = new_abstract
                logger_infoscience.info("This record need an update of his abstract")
                has_been_abstract_added = True
                abstract_added += 1

        if has_been_patent_updated or has_been_family_updated or has_been_notes_for_alternatives_title_changed or has_been_abstract_added:
            marc_record.sort_record_content()
            # save record to the update collection
            update_collection.append(marc_record.marc_record)

    logger.info("End of parsing, %s records will be updated from this batch" % len(update_collection.findall("record")))
    logger.info("%s have a new family_id" % family_updated)
    logger.info("%s have an update for at least a patent" % patent_updated)
    logger.info("%s have new alternative titles" % alternative_titles_updated)
    logger.info("%s have a new abstract" % abstract_added)

    return update_collection

if __name__ == '__main__':
    # force debug logging
    parser = argparse.ArgumentParser()

    parser.add_argument("-f",
                        "--infoscience_patents_export",
                        help="The infoscience file of patents, in a MarcXML format",
                        required=True,
                        type=argparse.FileType('r'))

    parser.add_argument("-s",
                        "--start",
                        help="the range to start patents update",
                        required=False,
                        type=int)

    parser.add_argument("-e",
                        "--end",
                        help="the range to end patents update",
                        required=False,
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
    update_xml_path = os.path.join(
        BASE_DIR,
        "output",
        "patents-update-%s.xml" % time.strftime("%Y%m%d-%H%M%S")
        )

    export_as_string = args.infoscience_patents_export.read()

    is_full_export(export_as_string)

    if (args.start or args.start == 0) and args.end:
        updated_xml_collection = update_infoscience_export(export_as_string, args.start, args.end)
    else:
        updated_xml_collection = update_infoscience_export(export_as_string)
    logger_infoscience.info("Writing the updated record(s) in %s" % update_xml_path)
    updated_xml_collection.write(update_xml_path)
