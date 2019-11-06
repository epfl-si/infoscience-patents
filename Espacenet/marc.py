from datetime import datetime
import xml.etree.ElementTree as ET
import xml.dom.minidom
import logging
import unicodedata

from Espacenet.models import EspacenetPatent

from .patent_models import Patent, \
                           PatentClassificationWithDefault, \
                           _convert_to_date

from .utils import _get_best_patent_for_data

from .marc_xml_utils import \
    _get_controlfield_element, \
    _get_controlfield_value, \
    _get_datafield_element, \
    _get_subfield_element, \
    _get_datafield_values, \
    _get_multifield_values, \
    _controlfield, \
    _datafield, \
    _subfield


logger_infoscience = logging.getLogger('INFOSCIENCE')
logger_epo = logging.getLogger('EPO')


class MarcCollection(ET.Element):
    def __init__(self):
        self = super().__init__('collection')

    def tostring(self, pretty_print=False):
        to_marc_string = ET.tostring(self, encoding='unicode')

        if not pretty_print:
            return to_marc_string
        else:
            # fix to pretty print without all the blank lines
            reparsed = xml.dom.minidom.parseString(to_marc_string)
            return '\n'.join([line for line in reparsed.toprettyxml(indent=' '*2).split('\n') if line.strip()])

    def write(self, path):
        # add namespace before write
        self.set('xmlns', "http://www.loc.gov/MARC21/slim")

        with open(path, 'w') as f:
            f.write(self.tostring(True))


class MarcPatent:
    """
    Represent an infoscience record
    Parameter :
        record_subfield : is the subfield of datafield 013
    """
    def __init__(self, record_subfield: str):
        self.epodoc = record_subfield.get('a')
        self.country = record_subfield.get('b')
        self.kind = record_subfield.get('c')
        self.date = _convert_to_date(record_subfield.get('d'))  # data is same format as espacenet

    def to_marc(self, record):
        logger_infoscience.debug("Adding this patent %s to a record %s" % (self, record))
        # export data to a marc format that is put inside record
        datafield_013 = _datafield(record, '013')
        subfield_013__a = _subfield(datafield_013, 'a')
        subfield_013__a.text = self.epodoc
        subfield_013__b = _subfield(datafield_013, 'b')
        subfield_013__b.text = self.country
        subfield_013__c = _subfield(datafield_013, 'c')
        subfield_013__c.text = self.kind
        subfield_013__d = _subfield(datafield_013, 'd')
        subfield_013__d.text = self.date.strftime('%Y%m%d')

    def __unicode__(self):
        return "Patent %s-%s" % (self.epodoc, self.kind)

    def __repr__(self):
        return super(MarcPatent, self).__repr__() + ' ' + self.__unicode__()


class MarcRecordBuilder:
    def get_empty_record(self):
        m_record = MarcRecord()
        m_record.marc_record = ET.Element('record')
        return m_record

    def from_infoscience_record(self, record):
        m_record = MarcRecord()
        # init from a marc record
        assert isinstance(record, ET.Element)
        m_record.marc_record = record
        return m_record

    def from_epo_patents(self, family_id, patents, fulfilled_patent):
        m_record = MarcRecord()

        m_record.marc_record = ET.Element('record')
        # we are in a new record mode, so build essential information, in same order as infoscience
        m_record.content_type = True  # use setter default values
        m_record.epfl_id = True  # use setter default values
        m_record.doctype = True  # use setter default values
        m_record.sort_record_content()

        m_record.family_id = family_id
        patent_for_data = fulfilled_patent

        self.set_titles(m_record, patent_for_data)
        m_record.publication_date = patent_for_data.date
        abstract = self.best_abstract(patents)
        if abstract:
            m_record.abstract = abstract
        m_record.authors = [author for author in patent_for_data.inventors]

        m_record.update_patents_from_espacenet(patents)

        # sort only if this a new one from patent_family
        m_record.sort_record_content()

        return m_record

    def set_titles(self, m_record, patent):
        """
        try to find at least an english title in all patents,
        it will be our main title if no title is already set
        otherwise get the french one.
        Other titles that is not the main are fullfiled in a note if not already
        Return a boolean saying if we changed anything
        """
        has_changed = False
        titles_by_code = {}

        for title, code in patent.invention_titles:
            titles_by_code[code] = title

        # try to get the en, or fr
        if 'en' in titles_by_code:
            if not m_record.title:
                m_record.title = titles_by_code['en']
                has_changed = True
                del titles_by_code['en']
            elif m_record.title == titles_by_code['en']:
                del titles_by_code['en']
        elif 'fr' in titles_by_code:
            if not m_record.title:
                m_record.title = titles_by_code['fr']
                del titles_by_code['fr']
                has_changed = True
            elif m_record.title == titles_by_code['fr']:
                del titles_by_code['fr']

        # do we already a build alternative titles ?
        found_alternative_titles = False
        if m_record.notes:
            for note in m_record.notes:
                if note and 'Alternative title(s)' in note:
                    found_alternative_titles = True

        # fullfil alternative titles is not already set
        if not found_alternative_titles:
            final_note_text = ""

            for code, title in titles_by_code.items():
                final_note_text += "\n\t(" + code + ")" + " " + title

            if final_note_text:
                final_note_text = "Alternative title(s) :" + final_note_text
                m_record.add_a_note(final_note_text)
                has_changed = True

        return has_changed

    def best_abstract(self, patent):
        """
        try to find at least an english abstract in the patent,
        otherwise a french version
        """
        best_abstract = ""

        if hasattr(patent, "abstract_en") and patent.abstract_en != "":
            return patent.abstract_en
        else:
            # no english title, try in french
            if hasattr(patent, "abstract_fr") and patent.abstract_fr != "":
                return patent.abstract_fr

    def oldest_date(self, patents):
        """
        try to find the oldest date
        """
        oldest_date = None
        for patent in patents:
            if patent.date:
                if oldest_date:
                    if patent.date < oldest_date:
                        oldest_date = patent.date
                else:
                    oldest_date = patent.date

        return oldest_date


class MarcRecord:
    """
    Represent a record, same as an entry is espacenet with a family id
    The marc_record attribute has always the nicest marc xml counterpart
    and this class offers properties to access them
    Use the MarcRecordBuilder instead of initiating it by yourself
    """

    def sort_record_content(self):
        """
        sort the xml by tag number
        """
        self.marc_record[:] = sorted(self.marc_record, key=lambda child: (child.tag,child.get('tag')))

    @property
    def update_at(self):
        try:
            return _get_controlfield_value(self.marc_record, '005')
        except AttributeError:
            pass

    @update_at.setter
    def update_at(self, value):
        timestamp_field = self.update_at
        new_timestamp = datetime.now().strftime('%Y%m%d%H%M%S.0')

        if timestamp_field:
            _get_controlfield_element(self.marc_record, '005').text = new_timestamp
        else:
            controlfield_005 = _controlfield(self.marc_record, '005')
            controlfield_005.text = new_timestamp

    @property
    def record_id(self):
        try:
            return _get_controlfield_value(self.marc_record, '001')
        except AttributeError:
            pass

    @record_id.setter
    def record_id(self, value):
        raise NotImplementedError("Setting a new recid is not advised")

    @property
    def epodoc_for_query(self):
        # find the best epodoc trough the list of patents
        patent = _get_best_patent_for_data(self.patents)
        if patent:
            epodoc_with_space = patent.epodoc.split(' ')
            if len(epodoc_with_space) > 1:
                epodoc_for_query = epodoc_with_space[0]
            else:
                epodoc_for_query = patent.epodoc

            return epodoc_for_query

    @property
    def patents(self):
        patents = []

        for subfield in _get_multifield_values(self.marc_record, '013'):
            patents.append(MarcPatent(subfield))

        return patents

    @patents.setter
    def patents(self, value):
        """
        should be a list of MarcPatent
        """
        for patent_element in self.marc_record.findall('datafield[@tag="013"]'):
            self.marc_record.remove(patent_element)

        for patent in value:
            datafield_013 = _datafield(self.marc_record, '013')
            subfield_013__a = _subfield(datafield_013, 'a')
            subfield_013__a.text = patent.epodoc
            subfield_013__b = _subfield(datafield_013, 'b')
            subfield_013__b.text = patent.country
            subfield_013__c = _subfield(datafield_013, 'c')
            subfield_013__c.text = patent.kind
            subfield_013__d = _subfield(datafield_013, 'd')
            subfield_013__d.text = patent.date.strftime('%Y%m%d')

    @property
    def family_id(self):
        # EPO family id
        record_family_id = None
        sources_data = _get_multifield_values(self.marc_record, '024', '7', '0')

        for source in sources_data:
            if source.get("2") == 'EPO Family ID':
                record_family_id = source.get("a")

        return record_family_id

    @family_id.setter
    def family_id(self, value):
        datafield_024 = _datafield(self.marc_record, '024', '7', '0')
        subfield_024__a = _subfield(datafield_024, 'a')
        subfield_024__a.text = value
        subfield_024__2 = _subfield(datafield_024, '2')
        subfield_024__2.text = "EPO Family ID"

    @property
    def title(self):
        return _get_datafield_values(self.marc_record, '245').get('a')

    @title.setter
    def title(self, value):
        datafield_245 = _datafield(self.marc_record, '245')
        subfield_245__a = _subfield(datafield_245, 'a')
        subfield_245__a.text = value

    @property
    def collection_id(self):
        return _get_datafield_values(self.marc_record, '037').get('a')

    @collection_id.setter
    def collection_id(self, value):
        datafield_037 = _datafield(self.marc_record, '037')
        subfield_037__a = _subfield(datafield_037, 'a')
        subfield_037__a.text = value

    @property
    def publication_date(self):
        date_as_string = _get_datafield_values(self.marc_record, '260').get('c')
        # date is mainly a year thing
        return datetime.strptime(date_as_string, "%Y").date()

    @publication_date.setter
    def publication_date(self, value):
        datafield_260 = _datafield(self.marc_record, '260')
        subfield_260__c = _subfield(datafield_260, 'c')
        subfield_260__c.text = value.strftime('%Y')
        datafield_269 = _datafield(self.marc_record, '269')
        subfield_269__a = _subfield(datafield_269, 'a')
        subfield_269__a.text = value.strftime('%Y')

    @property
    def content_type(self):
        return _get_datafield_values(self.marc_record, '336').get('a')

    @content_type.setter
    def content_type(self, value):
        datafield_336 = _datafield(self.marc_record, '336')
        subfield_336__a = _subfield(datafield_336, 'a')
        subfield_336__a.text = "Patents"

    @property
    def notes(self):
        notes_datafields = _get_multifield_values(self.marc_record, '500')
        notes = []

        for field in notes_datafields:
            notes.append(field.get('a'))

        return notes

    def add_a_note(self, value):
        datafield_500 = _datafield(self.marc_record, '500')
        subfield_500__a = _subfield(datafield_500, 'a')
        subfield_500__a.text = value

    @property
    def abstract(self):
        return _get_datafield_values(self.marc_record, '520').get('a')

    @abstract.setter
    def abstract(self, value):
        datafield_520 = _datafield(self.marc_record, '520')
        subfield_520__a = _subfield(datafield_520, 'a')
        subfield_520__a.text = value

    @property
    def authors(self):
        authors = []
        authors_datafields = _get_multifield_values(self.marc_record, '700')

        for field in authors_datafields:
            authors.append(field.get('a'))

        return authors

    @authors.setter
    def authors(self, value):
        for author in value:
            datafield_700 = _datafield(self.marc_record, '700')
            subfield_700__a = _subfield(datafield_700, 'a')
            subfield_700__a.text = "%s" % author

    @property
    def epfl_id(self):
        return _get_datafield_values(self.marc_record, '973').get('a')

    @epfl_id.setter
    def epfl_id(self, value):
        datafield_973 = _datafield(self.marc_record, '973')
        subfield_973__a = _subfield(datafield_973, 'a')
        subfield_973__a.text = "EPFL"

    @property
    def tagged_done(self):
        """ we don't want to redo patent with this tag set"""
        datafield_974 = _datafield(self.marc_record, '974')
        subfield_974__b = _subfield(datafield_974, 'b')

        if subfield_974__b and subfield_974__b.text:
            return True

    @property
    def doctype(self):
        return _get_datafield_values(self.marc_record, '980').get('a')

    @doctype.setter
    def doctype(self, value):
        # doctype
        datafield_980 = _datafield(self.marc_record, '980')
        subfield_980__a = _subfield(datafield_980, 'a')
        subfield_980__a.text = "PATENT"

    @property
    def S2_collection(self):
        return _get_datafield_values(self.marc_record, '981').get('a')

    @S2_collection.setter
    def S2_collection(self, value):
        datafield_981 = _datafield(self.marc_record, '981')
        datafield_981__a = _subfield(datafield_981, 'a')
        datafield_981__a.text = "S2"

    @property
    def TTO_collection(self):
        return _get_datafield_values(self.marc_record, '999', 'C', '0')

    @TTO_collection.setter
    def TTO_collection(self, value):
        subfield_999C0 = _datafield(self.marc_record, '999', 'C', '0')
        subfield_999C00 = _subfield(subfield_999C0, '0')
        subfield_999C00.text = '252085'
        subfield_999C0p = _subfield(subfield_999C0, 'p')
        subfield_999C0p.text = 'TTO'
        subfield_999C0x = _subfield(subfield_999C0, 'x')
        subfield_999C0x.text = 'U10021'

    def update_patents_from_espacenet(self, espacenet_patents):
        """
        -* Updating patents *-

        Les entrées manuelles qui ne sont pas dans la liste Espacenet sont placée à la fin (fin = en dernière position = tout en bas)
        Les entrées manuelles qui sont reconnus dans la liste Espacenet sont enlevés (pour être remis juste après, voir l'étape suivante)
        La liste Espacenet est triée par date et ajouter de haut en bas.
        Cela peut donner par exemple :
        [Brevet1_Espacenet, Brevet2_Manuel_Espacenet, Brevet3_Espacenet, Brevet4_Manuel_Espacenet, Brevet5_Manuel]
        """
        # patents that are already in are from infoscience
        infoscience_patents = self.patents
        final_patent_list = []

        # Desc sorting espacenet entry
        espacenet_patents.sort(key=lambda p: p.date, reverse=True)

        # ajouter les entrées manuelles d'infoscience
        espacenet_epodocs = list(map(lambda p: p.epodoc, espacenet_patents))
        for infoscience_patent in infoscience_patents:
            if infoscience_patent.epodoc not in espacenet_epodocs:
                espacenet_epodocs.append(infoscience_patent)

        # Insérer la nouvelle donnée
        self.patents = espacenet_patents
        self.sort_record_content()

        #assert len(self.patents) != 0

    def to_marc_string(self, pretty_print=False):
        to_marc_string = ET.tostring(self.marc_record, encoding='unicode')

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
        subfield_013__b.text = self.country
        subfield_013__c = _subfield(datafield_013, 'c')
        subfield_013__c.text = self.kind
        subfield_013__d = _subfield(datafield_013, 'd')
        subfield_013__d.text = self.date.strftime('%Y%m%d')
