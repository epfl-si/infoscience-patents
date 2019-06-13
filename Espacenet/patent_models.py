"""
    (c) All rights reserved. ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE, Switzerland, VPSI, 2017
"""

import collections
import datetime
import re


class PatentFamilies(collections.defaultdict):
    """ family_id as key, patents as values
    """
    def __init__(self, *args, **kwargs):
        collections.defaultdict.__init__(self, list)

    def __repr__(self):
        families = []

        for fam_id, patents in self.items():
            inside_patents = []
            for patent in patents:
                inside_patents.append(str(patent))

            families.append("Family %s : [%s]" % (fam_id, ", ".join(inside_patents)))

        return "default list dict : %s" % " ".join(families)

    @property
    def patents(self):
        return [patent for patents_list in self.values() for patent in patents_list]

PatentClassification = collections.namedtuple("PatentClassification",
                                              """sequence
                                                 class_nr
                                                 classification_scheme
                                                 classification_value
                                                 main_group
                                                 section
                                                 subclass
                                                 subgroup""")

class PatentClassificationWithDefault(PatentClassification):
    def __new__(cls, sequence = '',
                     class_nr = '',
                     classification_scheme = '',
                     classification_value = '',
                     main_group = '',
                     section = '',
                     subclass = '',
                     subgroup = ''):
        # add default values, make it not mandatory
        return super(PatentClassificationWithDefault, cls).__new__(cls, sequence,
                                                                         class_nr,
                                                                         classification_scheme,
                                                                         classification_value,
                                                                         main_group,
                                                                         section,
                                                                         subclass,
                                                                         subgroup)


def _convert_to_date(value):
    result = None

    if value and isinstance(value, str):
        # try to convert the date string to a real date
        try:
            result = datetime.datetime.strptime(value, "%Y%m%d").date()
        except ValueError:
            result = None
    elif isinstance(value, datetime.date):
        result = value

    return result


class BasePatent(object):
    """ Represent a patent (pct or accepted), with common property access
        direct_update params allow to directly launch a query from this patent
        inventors are in the format [(sequence, name), ...]
    """
    def __init__(self, family_id=None, invention_title = '', inventors = []):

        if family_id:
            self.family_id = family_id

        self.invention_title = invention_title
        self.inventors = inventors

    def querystring(self):
        """ this is the string used when searching
        """
        return self.epodoc

    @property
    def epodoc(self):
        """ By defautl return the epodoc if any"""
        if self._epodoc:
            return self._epodoc

    @epodoc.setter
    def epodoc(self, value):
        self._epodoc = value

    def __repr__(self):
        return super(BasePatent, self).__repr__() + ' ' + self.__unicode__()

    @property
    def details(self):
        """ get everything we have """
        output = self.__unicode__()
        output += " : %s\n" % str(self.__dict__)
        return output

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, value):
        self._date = value


class Patent(BasePatent):
    """ Represent a patent, for easy query on espacenet """
    _date = None
    _application_date = None

    patent_regex = r"^(?P<country>\D{2})(?P<number>\d{1,})[\s|-]?(?P<kind>\w\d)?"

    def __init__(self, epodoc = '', country = '', number = '', kind=None, date=None, **kwargs):
        """
        set epodoc if you want to try an automatic dispatch country+number
        """
        if epodoc:
            if number or country or kind:
                raise AttributeError("Don't set number, country or kind if you set epodoc")

            matched = re.match(self.patent_regex, epodoc)

            if matched:
                patent_dict = matched.groupdict()
                country = patent_dict['country']
                number = patent_dict['number']
                kind = patent_dict['kind']
            else:
                raise AttributeError("Epodoc format not valid: %s" % epodoc)

        if number and not country:
            raise AttributeError

        if country and not number:
            raise AttributeError

        if not hasattr(self, 'number') or (not(self.number) and number):
            self.number = number

        if not hasattr(self, 'country') or (not(self.country) and country):
            self.country = country

        if not hasattr(self, 'kind') or (not(self.kind) and kind):
            self.kind = kind

        if not hasattr(self, 'date') or (not(self.date) and date):
            self.date = date

    def __unicode__(self):
        if self.kind:
            output = "Patent %s%s-%s" % (self.country, self.number, self.kind)
        else:
            output = "Patent %s%s" % (self.country, self.number)
        return output

    @property
    def epodoc(self):
        """ epodoc is a format consisting of country + number """
        return "%(country)s%(number)s" % self.__dict__

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, value):
        self._date = _convert_to_date(value)

    @property
    def application_date(self):
        return self._application_date

    @application_date.setter
    def application_date(self, value):
        self._application_date = _convert_to_date(value)
