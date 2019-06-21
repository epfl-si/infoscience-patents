import logging
import xml.etree.ElementTree as ET

import epo_ops
from requests.exceptions import HTTPError

from Espacenet.marc import MarcPatentFamilies as PatentFamilies, MarcRecord, MarcCollection
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


def update_infoscience_export(xml_file):
    """
    Load patents inside the xml provided
    and an updated version of it (aka added new patent to existing ones)
    """
    logger_infoscience.info("Loading provided xml file for an update...")
    client = EspacenetBuilderClient(use_cache=True)

    xml_file = filter_out_namespace(xml_file.read())
    provided_collection = ET.fromstring(xml_file)

    update_collection = MarcCollection()
    records = provided_collection.findall('record')
    logger_infoscience.info("Provided xml file as %s records, starting the update..." % len(records))

    # some counters for logs
    patent_updated = 0
    family_updated = 0

    for i, record in enumerate(records):
        has_been_patent_updated = False
        has_been_family_updated = False
        marc_record = MarcRecord(record=record)

        logger_infoscience.info("Parsing %s/%s record %s, family id %s" % (
            i,
            len(records),
            marc_record.record_id,
            marc_record.family_id)
            )

        # is it good to go ?
        if not marc_record.record_id:
            logger_infoscience.info("Skipping record %s, the record has no id" % marc_record.record_id)
            continue

        if len(marc_record.patents) == 0:
            logger_infoscience.info("Skipping record %s, no patents have been found in it" % marc_record.record_id)
            continue

        # get the best epodoc to do queries or abort
        epodoc_for_query = marc_record.epodoc_for_query
        if not epodoc_for_query:
            logger_infoscience.info("Skipping record %s, patents in it are not well formated" % marc_record.record_id)
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
                logger_epo.warning("Skipping this record, it crash Espacenet: %s, error was %s" % (epodoc_for_query, e))
                continue

            marc_record.family_id = patent.family_id
            has_been_family_updated = True
            family_updated += 1

            logger_infoscience.debug("Fetched family id %s" % marc_record.family_id)

        try:
            patents_families = client.family(
                input = epo_ops.models.Epodoc(epodoc_for_query)
            )
        except HTTPError as e:
            logger_epo.warning("Skipping this record, it crash Espacenet: %s, error was %s" % (epodoc_for_query, e))
            continue

        # comparing the length should do the trick, the epodoc don't change everytimes
        if len(patents_families.patents) != len(marc_record.patents):
            # we have a different number of patents, update the marc record
            logger_infoscience.info("The record need an patent update, doing the update...")

            marc_record.update_patents_from_espacenet(patents_families)

            assert(len(marc_record.patents) != 0)
            has_been_patent_updated = True
            patent_updated += 1

            logger_infoscience.debug("Updated this record to : %s" % marc_record.patents)
        else:
            logger_infoscience.info("This record does not need an update")

        if has_been_patent_updated or has_been_family_updated:
            # save record to the update collection
            update_collection.append(marc_record.marc_record)

    logger.info("End of parsing, %s records will be updated from this batch" % len(update_collection.findall("record")))
    logger.info("%s were missing their family_id, and/or %s for their patent list" % (family_updated, patent_updated))
    return update_collection
