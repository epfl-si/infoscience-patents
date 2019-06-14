import logging
import xml.etree.ElementTree as ET

from .marc import MarcPatentFamilies as PatentFamilies
from .patent_models import Patent

logger_infoscience = logging.getLogger('INFOSCIENCE')


def _get_controlfield_element(record, tag):
    for controlfield in record.iter('{http://www.loc.gov/MARC21/slim}controlfield'):
        if controlfield.attrib.get('tag') == tag:
            return controlfield

def _get_controlfield_value(record, tag):
    return _get_controlfield_element(record, tag).text

def _get_datafield_element(record, tag, ind1=' ', ind2=' '):
    for datafield in record.iter('{http://www.loc.gov/MARC21/slim}datafield'):
        if datafield.attrib.get('tag') == tag and datafield.attrib.get('ind1') == ind1 and datafield.attrib.get('ind2') == ind2:
            return datafield

def _get_subfield_element(datafield, code):
    for subfield in datafield.iter('{http://www.loc.gov/MARC21/slim}subfield'):
        if subfield.attrib.get('code') == code:
            return subfield

def _get_datafield_values(record, tag, ind1=' ', ind2=' '):
    result = {}

    for datafield in record.iter('{http://www.loc.gov/MARC21/slim}datafield'):
        if datafield.attrib.get('tag') == tag and datafield.attrib.get('ind1') == ind1 and datafield.attrib.get('ind2') == ind2:
            for subfield in datafield.iter('{http://www.loc.gov/MARC21/slim}subfield'):
                result.update({subfield.attrib.get('code'): subfield.text})

    return result

def _get_multifield_values(record, tag, ind1=' ', ind2=' '):
    result = []

    for datafield in record.iter('{http://www.loc.gov/MARC21/slim}datafield'):
        if datafield.attrib.get('tag') == tag and datafield.attrib.get('ind1') == ind1 and datafield.attrib.get('ind2') == ind2:
            r = {}
            result.append(r)
            for subfield in datafield.iter('{http://www.loc.gov/MARC21/slim}subfield'):
                r.update({subfield.attrib.get('code'): subfield.text})

    return result

def load_infoscience_export(xml_file):
    """
    Load patents inside the xml and
    return a tuple (Family patent big dictionary, no family records)
    """
    tree = ET.parse(xml_file)
    collection = tree.getroot()

    patent_families = PatentFamilies()

    no_family_id_records = []

    logger_infoscience.info("Loading provided xml file")

    for record in collection.iter('{http://www.loc.gov/MARC21/slim}record'):
        record_id = _get_controlfield_value(record, '001')
        # patents = list(map(lambda d: d.get('a'), _get_multifield_values(record, '013')))

        record_one_epodoc = _get_datafield_values(record, '013').get('a')
        # EPO family id
        record_family_id = None
        sources_data = _get_multifield_values(record, '024', '7', '0')
        for source in sources_data:
            if source.get("2") == 'EPO Family ID':
                record_family_id = source.get("a")

        if record_family_id:
            patent_families[record_family_id] = [Patent]
        else:
            no_family_id_records.append(record)

    logger_infoscience.debug("%s patents with family id has been crawled from the xml file" % len(patent_families.patents))
    logger_infoscience.debug("%s patents without family id has been crawled from the xml file" % len(no_family_id_records))

    return patent_families, no_family_id_records
