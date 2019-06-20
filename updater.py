import logging
import xml.etree.ElementTree as ET

import epo_ops

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
    logger_infoscience.info("Loading provided xml file")
    client = EspacenetBuilderClient(use_cache=True)

    xml_file = filter_out_namespace(xml_file.read())
    provided_collection = ET.fromstring(xml_file)

    update_collection = MarcCollection()

    for record in provided_collection:
        marc_record = MarcRecord(record=record)

        # is it good to go ?
        if len(marc_record.patents) == 0:
            logger_infoscience.debug("Skipping record %s has no patents in it" % marc_record.record_id)
            continue

        logger_infoscience.debug("Itering record %s" % marc_record.record_id)

        family_id = marc_record.family_id

        # is it good to go ?
        if not family_id:
            # then try to get the family_id then look for patents
            logger_epo.debug(
                "Fetching family id for recid %s" % marc_record.record_id
                )

            patent = client.patent(  # Retrieve bibliography data
                input = epo_ops.models.Epodoc(marc_record.patents[0].epodoc),  # original, docdb, epodoc
            )

            family_id = patent.family_id
            marc_record.family_id = family_id
            logger_epo.debug(
                "Fetched family id %s" % family_id
            )
            assert marc_record.family_id != None

        # fetch to see if we have new patents or patents to update for this family
        logger_infoscience.debug(
            "Fetching the family_id %s to see if it need to update data" % marc_record.family_id
            )

        patents_families = client.family(
            input = epo_ops.models.Epodoc(marc_record.patents[0].epodoc)
        )

        # comparing the length should do the trick, the epodoc don't change everytimes
        if len(patents_families.patents) != len(marc_record.patents):
            # we have a different number of patents, update the marc record
            logger_infoscience.debug("This patent family {} has {} in infoscience and {} in espacenet, doing the update...".format(
                family_id,
                marc_record.patents,
                patents_families.patents
            ))

            marc_record.update_patents_from_espacenet(patents_families)

            assert(len(marc_record.patents) != 0)

            logger_infoscience.debug("Updated this record to : %s" % marc_record.patents)

            # save record to the update collection
            update_collection.append(marc_record.marc_record)
        else:
            logger_infoscience("The patent does not need an update")

    logger.info("Successfully parsed and updated an infoscience export")
    return update_collection
