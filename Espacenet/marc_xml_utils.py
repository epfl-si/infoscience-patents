import re
import xml.etree.ElementTree as ET


def filter_out_namespace(xmlstring):
    """
    Because I don't want to add everywhere namespaces values when we have only one
    """
    return re.sub(' xmlns="[^"]+"', '', xmlstring, count=1)

def _get_controlfield_element(record, tag):
    for controlfield in record.iter('controlfield'):
        if controlfield.attrib.get('tag') == tag:
            return controlfield

def _get_controlfield_value(record, tag):
    return _get_controlfield_element(record, tag).text

def _get_datafield_element(record, tag, ind1=' ', ind2=' '):
    for datafield in record.iter('datafield'):
        if datafield.attrib.get('tag') == tag and datafield.attrib.get('ind1') == ind1 and datafield.attrib.get('ind2') == ind2:
            return datafield

def _get_subfield_element(datafield, code):
    for subfield in datafield.iter('subfield'):
        if subfield.attrib.get('code') == code:
            return subfield

def _get_datafield_values(record, tag, ind1=' ', ind2=' '):
    result = {}

    for datafield in record.iter('datafield'):
        if datafield.attrib.get('tag') == tag and datafield.attrib.get('ind1') == ind1 and datafield.attrib.get('ind2') == ind2:
            for subfield in datafield.iter('subfield'):
                result.update({subfield.attrib.get('code'): subfield.text})

    return result

def _get_multifield_values(record, tag, ind1=' ', ind2=' '):
    result = []

    for datafield in record.iter('datafield'):
        if datafield.attrib.get('tag') == tag and datafield.attrib.get('ind1') == ind1 and datafield.attrib.get('ind2') == ind2:
            r = {}
            result.append(r)
            for subfield in datafield.iter('subfield'):
                r.update({subfield.attrib.get('code'): subfield.text})

    return result

def _controlfield(parent, tag):
    controlfield = ET.SubElement(parent, 'controlfield')
    controlfield.set('tag', tag)
    return controlfield

def _datafield(parent, tag, ind1=' ', ind2=' '):
    datafield = ET.SubElement(parent, 'datafield')
    datafield.set('tag', tag)
    datafield.set('ind1', ind1)
    datafield.set('ind2', ind2)
    return datafield

def _subfield(parent, code):
    subfield = ET.SubElement(parent, 'subfield')
    subfield.set('code', code)
    return subfield
