from datetime import datetime
import xml.etree.ElementTree as ET
import xml.dom.minidom

from Espacenet.models import EspacenetPatent

from .patent_models import PatentFamilies, \
                           Patent, \
                           PatentClassificationWithDefault


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


#NOT_USED, as sample at the moment
class MarcCollection:
    def __init__(self):
        self.marcxml_collection = ET.Element('collection', attrib={'xmlns':"http://www.loc.gov/MARC21/slim"})

    def write(self, path):
        tree = ET.ElementTree(self.marcxml_collection)
        tree.write("path",
           xml_declaration=True,encoding='utf-8',
           method="xml",
           default_namespace='http://www.loc.gov/MARC21/slim')


class MarcPatentFamilies(PatentFamilies):
    """
    Add converter to marc for a family
    """
    @property
    def best_abstract(self):
        """
        try to find at least an abstract in all patents
        """
        for patent in self.patents:
            if patent.abstract_en != "":
                return patent.abstract_en
        return ""

    @property
    def oldest_date(self):
        """
        try to find the oldest date
        """
        oldest_date = None
        for patent in self.patents:
            if patent.date:
                if oldest_date:
                    if patent.date < oldest_date:
                        oldest_date = patent.date
                else:
                    oldest_date = patent.date

        return oldest_date

    def to_marc(self):
        marcxml_collection = ET.Element('collection', attrib={'xmlns':"http://www.loc.gov/MARC21/slim"})

        patent_for_data = self.patents[0]

        record = ET.SubElement(marcxml_collection, 'record')

        controlfield_005 = _controlfield(record, '005')
        controlfield_005.text = datetime.now().strftime('%Y%m%d%H%M%S.0')

        # patents info
        for patent in self.patents:
            patent.to_marc(record)

        # title
        datafield_024 = _datafield(record, '024')
        subfield_024__a = _subfield(datafield_024, 'a')
        subfield_024__a.text = patent_for_data.family_id
        subfield_024__2 = _subfield(datafield_024, '2')
        subfield_024__2.text = "EPO Family ID"

        # title
        datafield_245 = _datafield(record, '245')
        subfield_245__a = _subfield(datafield_245, 'a')
        subfield_245__a.text = patent_for_data.invention_title_en

        # publication date
        date_to_set = self.oldest_date
        datafield_260 = _datafield(record, '260')
        subfield_260__a = _subfield(datafield_260, 'a')
        subfield_260__a.text = date_to_set.strftime('%Y')

        # publication date 2
        date_to_set = self.oldest_date
        datafield_269 = _datafield(record, '269')
        subfield_269__a = _subfield(datafield_269, 'a')
        subfield_269__a.text = date_to_set.strftime('%Y')

        # content type
        datafield_336 = _datafield(record, '336')
        subfield_336__a = _subfield(datafield_336, 'a')
        subfield_336__a.text = "Patents"

        # abstract
        datafield_520 = _datafield(record, '520')
        subfield_520__a = _subfield(datafield_520, 'a')
        subfield_520__a.text = self.best_abstract

        # authors
        for author in patent_for_data.inventors:
            datafield_700 = _datafield(record, '700')
            subfield_700__a = _subfield(datafield_700, 'a')
            subfield_700__a.text = "%s" % author[1]

        # TTO id
        datafield_909 = _datafield(record, '909', 'C', '0')
        subfield_909__p = _subfield(datafield_909, 'p')
        subfield_909__p.text = "TTO"
        subfield_909__0 = _subfield(datafield_909, '0')
        subfield_909__0.text = "252085"
        subfield_909__x = _subfield(datafield_909, 'x')
        subfield_909__x.text = "U10021"

        #
        datafield_973 = _datafield(record, '973')
        subfield_973__a = _subfield(datafield_973, 'a')
        subfield_973__a.text = "EPFL"

        # doctype
        datafield_980 = _datafield(record, '980')
        subfield_980__a = _subfield(datafield_980, 'a')
        subfield_980__a.text = "PATENT"

        return marcxml_collection

    def to_marc_string(self, pretty_print=False):
        to_marc_string = ET.tostring(self.to_marc(), encoding='unicode')

        if not pretty_print:
            return to_marc_string
        else:
            return xml.dom.minidom.parseString(to_marc_string).toprettyxml()


class MarcEspacenetPatent(EspacenetPatent):
    def to_marc(self, record):
        # patent data
        datafield_013 = _datafield(record, '013')
        subfield_013__a = _subfield(datafield_013, 'a')
        subfield_013__a.text = self.epodoc
        subfield_013__b = _subfield(datafield_013, 'b')
        subfield_013__b.text = self.kind
        subfield_013__c = _subfield(datafield_013, 'c')
        subfield_013__c.text = self.country
        subfield_013__d = _subfield(datafield_013, 'd')
        subfield_013__d.text = self.date.strftime('%Y%m%d')
