# -*- coding: utf-8 -*-

"""
    (c) All rights reserved. ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE, Switzerland, VPSI, 2017
"""

from invenio.search_engine import search_pattern
from invenio.search_engine import get_record
from datetime import datetime
import csv, re
import logging, sys


def usage():
    print "This script fetches all the existing patents and produces a CSV file"
    print "with the field 013__a cleaned and separated in a/b/c/d subfields."
    print ""
    print "See http://infoscience-wiki.epfl.ch/MARC21 for more info."
    print ""
    print "Usage:"
    print "    (empty)        run script, output -> patents_report.csv"
    print "    -t | --test    run unit tests"
    print "    --debug        set level logging.DEBUG"
    print ""


### setup logger ###############################################################
class LevelFilterOut(logging.Filter):
    def filter(self, rec):
        return rec.levelno <= logging.WARNING

class LevelFilterErr(logging.Filter):
    def filter(self, rec):
        return rec.levelno > logging.WARNING

logger = logging.getLogger(__name__)
out = logging.StreamHandler(sys.stdout)
out.addFilter(LevelFilterOut())
logger.addHandler(out)
err = logging.StreamHandler(sys.stderr)
err.addFilter(LevelFilterErr())
logger.addHandler(err)
logger.setLevel(logging.INFO)
################################################################################

g_country = r'(?P<country>[a-zA-Z]{2})'
g_number = r'(?P<number>\d{4,})'
g_kind = r'\(?(?P<kind>[a-zA-Z]\d?)'
g_kind_opt_empty = r'(?P<kind>|[a-zA-Z]\d?)'
regex_013 = re.compile(r"^"+g_country+g_number+"[\s|-]?"+g_kind+"?")

def regex_013_match(data):
    """
    Matches the input string in the expected format.
    """
    (number, country, kind, date) = (None, None, None, None)
    
    matched = regex_013.match(data or '')
    if matched:
        patent_dict = matched.groupdict()
        country = patent_dict['country']
        number = patent_dict['number']
        kind = patent_dict['kind']
        # if the 4 first number are near our year, it may be the year
        if len(number) > 4:
            current_year = datetime.now().year
            maybe_date = int(number[0:4])
            if current_year - 100 <= maybe_date <= current_year + 1:
                date = maybe_date
                # if the year is < 2004, YYYYnumber = YYnumber, but not for US patents
                if country != 'US' and maybe_date < 2004:
                    number = number[2:]
    
    return (number, country, kind, date)

# definition of cleaning rules, order is important
cleaning_rules = [
    (re.compile(r"^U.S. Patent No.\s?"), 'US'),
    (re.compile(r"^United States Patent\s?"), 'US'),
    (re.compile(r"^U\.?S\.?"), 'US'),
    (re.compile(r"^US\s?\d+(,\d{3})+"), lambda m: m.group().replace(',', '')),
    (re.compile(r"^"+g_country+"\s*"+g_number+"\s*"+g_kind_opt_empty), '\g<country>\g<number>\g<kind>'),
    (re.compile(r"^"+g_country+"[\s/]?"+"(?P<year>\d{4})"+"[\s/]?"+g_number+"[\s/]?"+g_kind_opt_empty), '\g<country>\g<year>\g<number>\g<kind>'),
    (re.compile(r"^[a-zA-Z]{2}\d{4}(?P<keepit>[a-zA-Z]{2}\d{4,})"), '\g<keepit>'), # "WO2007EP123456" -> "EP123456"
    (re.compile(r"^[^E][^P]\d{4}.*?(?P<keepit>EP.*)"), '\g<keepit>'), # "WO123456, EP78910" -> "EP78910"
    (re.compile(r"^"+g_country+"\s*(?P<n1>\d+)\s*(?P<n2>\d+)\s*(?P<n3>\d+)"), '\g<country>\g<n1>\g<n2>\g<n3>'), # remove spaces between first 3 numbers
    (re.compile(r"^"+g_country+"[\d\s]+\.\d"), 'contains a number with "."'),
    (re.compile(r"^[a-zA-Z]{2}\d{16}"), 'too long !'),
]

regex_pct = re.compile(r"^PCT/(?P<country>\D{2})(?P<year>\d{2,4})/0?(?P<number>\d{5})")

def parse(r_013__a):
    """
    Applies cleaning rules and splits the input in a/b/c and d subfields.
    """
    result = (None, None, None, None)
    
    pct_matched = regex_pct.match(r_013__a or '')
    
    if pct_matched:
        result = (r_013__a, None, None, None)
    else:
        for rule, replacement in cleaning_rules:
            _org = r_013__a
            (r_013__a, nr) = rule.subn(replacement, r_013__a or '')
            
            if nr > 0 and _org != r_013__a:
                logger.debug("*   %s -> %s" % (rule.pattern, replacement))
                logger.debug("    %s -> %s" % (_org, r_013__a))
        
        result = regex_013_match(r_013__a)
    
    if result[0] and result[1]:
        # 013__a = epodoc, thus the country appears both in a and b subfields
        result = ('%s%s' % (result[1], result[0]), result[1], result[2], result[3])
    
    return result

# utility function
def get_subfield(rec, subfield):
    return map(lambda x: x.get(subfield),
               filter(lambda d : d.has_key(subfield),
                      map(lambda e: dict(e[0]), rec)))

def main():
    rec_ids = search_pattern(p="980__a:'PATENT'").tolist()
    logger.info('IN:  %s patents ...' % len(rec_ids))
    
    n_to_update = 0
    n_error = 0
    n_already_good = 0
    
    with open('patents_report.csv', 'wb') as f:
        fields = ['status', 'id', 'n_013', 'original', '013__a', '013__b', '013__c', '013__d', '260__c', 'n_500', '500__a']
        wr = csv.DictWriter(f, fieldnames=fields, delimiter=';')
        # write header row
        wr.writerow(dict(zip(fields, fields)))
        
        # loop over each patent
        for i in rec_ids:
            rec = get_record(i)
            
            n_013 = len(rec['013']) if rec.has_key('013') else 0
            if n_013:
                r_013__a = ', '.join(get_subfield(rec['013'], 'a'))
                r_013__b = ', '.join(get_subfield(rec['013'], 'b'))
                #r_013__c = ', '.join(get_subfield(rec['013'], 'c'))
                #r_013__d = ', '.join(get_subfield(rec['013'], 'd'))
            else:
                #(r_013__a, r_013__b, r_013__c, r_013__d) = (None, None, None, None)
                (r_013__a, r_013__b) = (None, None)
            
            # publication year
            if len(rec.get('260', [])) > 0:
                publication_date = ', '.join(get_subfield(rec['260'], 'c'))
            else:
                publication_date = None
            
            # notes
            n_500 = len(rec['500']) if rec.has_key('500') else 0
            if n_500:
                r_500__a = ', '.join(get_subfield(rec['500'], 'a'))
            else:
                r_500__a = None
            
            # if no 'country' subfield
            if not r_013__b:
                original = r_013__a
                
                (number, country, kind, date) = parse(r_013__a)
                
                if number:
                    status = 'TO_UPDATE'
                    n_to_update += 1
                else:
                    status = 'ERROR'
                    n_error += 1
                
                wr.writerow({'status': status,
                             'id': i,
                             'n_013': n_013,
                             'original': original,
                             '013__a': number,
                             '013__b': country,
                             '013__c': kind,
                             '013__d': date,
                             '260__c': publication_date,
                             'n_500' : n_500,
                             '500__a': r_500__a
                })
            else:
                n_already_good += 1
        
        logger.info('OUT: results written to %s' % (f.name,))
    
    logger.info('OUT: %s already good (not written to file)' % (n_already_good,))
    logger.info('OUT: %s can be automatically corrected' % (n_to_update,))
    logger.info('OUT: %s need manual correction' % (n_error,))

### unit tests #################################################################
import unittest
import difflib
import pprint

# this class comes from a recent (> 2.6) unittest.py
class TestCase2(unittest.TestCase):
    def assertSequenceEqual(self, seq1, seq2, msg=None, seq_type=None):
        """An equality assertion for ordered sequences (like lists and tuples).

        For the purposes of this function, a valid orderd sequence type is one
        which can be indexed, has a length, and has an equality operator.

        Args:
            seq1: The first sequence to compare.
            seq2: The second sequence to compare.
            seq_type: The expected datatype of the sequences, or None if no
                    datatype should be enforced.
            msg: Optional message to use on failure instead of a list of
                    differences.
        """
        if seq_type != None:
            seq_type_name = seq_type.__name__
            if not isinstance(seq1, seq_type):
                raise self.failureException('First sequence is not a %s: %r' 
                                            % (seq_type_name, seq1))
            if not isinstance(seq2, seq_type):
                raise self.failureException('Second sequence is not a %s: %r' 
                                            % (seq_type_name, seq2))
        else:
            seq_type_name = "sequence"

        differing = None
        try:
            len1 = len(seq1)
        except (TypeError, NotImplementedError):
            differing = 'First %s has no length.    Non-sequence?' % (
                    seq_type_name)

        if differing is None:
            try:
                len2 = len(seq2)
            except (TypeError, NotImplementedError):
                differing = 'Second %s has no length.    Non-sequence?' % (
                        seq_type_name)

        if differing is None:
            if seq1 == seq2:
                return

            for i in xrange(min(len1, len2)):
                try:
                    item1 = seq1[i]
                except (TypeError, IndexError, NotImplementedError):
                    differing = ('Unable to index element %d of first %s\n' %
                                 (i, seq_type_name))
                    break

                try:
                    item2 = seq2[i]
                except (TypeError, IndexError, NotImplementedError):
                    differing = ('Unable to index element %d of second %s\n' %
                                 (i, seq_type_name))
                    break

                if item1 != item2:
                    differing = ('First differing element %d:\n%s\n%s\n' %
                                 (i, item1, item2))
                    break
            else:
                if (len1 == len2 and seq_type is None and
                    type(seq1) != type(seq2)):
                    # The sequences are the same, but have differing types.
                    return
                # A catch-all message for handling arbitrary user-defined
                # sequences.
                differing = '%ss differ:\n' % seq_type_name.capitalize()
                if len1 > len2:
                    differing = ('First %s contains %d additional '
                                 'elements.\n' % (seq_type_name, len1 - len2))
                    try:
                        differing += ('First extra element %d:\n%s\n' %
                                      (len2, seq1[len2]))
                    except (TypeError, IndexError, NotImplementedError):
                        differing += ('Unable to index element %d '
                                      'of first %s\n' % (len2, seq_type_name))
                elif len1 < len2:
                    differing = ('Second %s contains %d additional '
                                 'elements.\n' % (seq_type_name, len2 - len1))
                    try:
                        differing += ('First extra element %d:\n%s\n' %
                                      (len1, seq2[len1]))
                    except (TypeError, IndexError, NotImplementedError):
                        differing += ('Unable to index element %d '
                                      'of second %s\n' % (len1, seq_type_name))
        if not msg:
            msg = '\n'.join(difflib.ndiff(pprint.pformat(seq1).splitlines(),
                                          pprint.pformat(seq2).splitlines()))
        self.fail(differing + msg)
    
    def assertTupleEqual(self, tuple1, tuple2, msg=None):
        self.assertSequenceEqual(tuple1, tuple2, msg, seq_type=tuple)

class SOMETHING(TestCase2):
    """
    Non-empty results are expected in these cases.
    """
    
    def test_162(self):
        self.assertTupleEqual(('WO9829819', 'WO', 'A', None), parse('WO9829819-A'))
    
    def test_163(self):
        self.assertTupleEqual(('US6175604', 'US', 'B1', None), parse('US6175604-B1'))
    
    # NB: the patent number starts with the year < 2004, then the patent number is only YY instead of YYYY
    def test_350(self):
        self.assertTupleEqual(('WO0184761', 'WO', 'A1', 2001), parse('WO200184761-A1'))
    
    # but don't do it for US patents ...
    def test_395(self):
        self.assertTupleEqual(('US2003163729', 'US', 'A1', 2003), parse('US2003163729-A1'))
    
    def test_52859(self):
        self.assertTupleEqual(('US5369837', 'US', None, None), parse('US 5369837'))
    
    def test_99790(self):
        self.assertTupleEqual(('US5422742', 'US', None, None), parse('U.S. Patent No. 5,422,742'))
    
    def test_99869(self):
        self.assertTupleEqual(('EP1073257', 'EP', 'A1', None), parse('EP 1073257A1'))
    
    def test_104852(self):
        self.assertTupleEqual(('US20070011111', 'US', 'A', 2007), parse('US 2007/0011111 Al'))
    
    def test_112206(self):
        self.assertTupleEqual(('WO2006125452', 'WO', None, 2006), parse('WO/2006/125452'))
    
    def test_116214(self):
        self.assertTupleEqual(('US2007210282', 'US', None, 2007), parse('US  2007210282  '))
    
    def test_128420(self):
        self.assertTupleEqual(('WO2008102292', 'WO', 'A2', 2008), parse('WO 2008/102292 A2'))
    
    def test_139450(self):
        self.assertTupleEqual(('US7547872', 'US', None, None), parse('U.S. 7,547,872'))
    
    def test_187144(self):
        self.assertTupleEqual(('US20130070570', 'US', 'A1', 2013), parse('US2013/0070570A1'))
    
    def test_138903(self):
        self.assertTupleEqual(('EP2019109', 'EP', None, None), parse('EP 2019109'))

    def test_165089(self):
        self.assertTupleEqual(('WO2005017598', 'WO', 'A1', 2005), parse('WO2005017598-A1; DE10336080-A1; US2006226374-A1'))
    
    # enlever WO2007 si suivi de 2 lettres + chiffres
    def test_113854(self):
        self.assertTupleEqual(('EP06014449', 'EP', None, None), parse('WO2007EP06014449'))
    
    # on prend le 1er EP si existe parmi une liste
    def test_147563(self):
        self.assertTupleEqual(('EP1879039', 'EP', None, None), parse('US7626386, EP1879039'))
    
    def test_165094(self):
        self.assertTupleEqual(('EP1625427', 'EP', 'A1', None), parse('WO2004104647-A1; DE10323922-A1; EP1625427-A1; JP2007500872-W; EP1625427-B1; DE502004003287-G; US2007285813-A1'))
    
    def test_165096(self):
        self.assertTupleEqual(('EP1225454', 'EP', 'A2', None), parse('EP1225454-A2; DE10100335-A1; US2002120424-A1; JP2002243414-A; US6741948-B2; EP1225454-A3; JP2010054520-A; JP4500913-B2'))
    
    def test_187043(self):
        self.assertTupleEqual(('EP2290471', 'EP', 'A1', None), parse('EP 2 290 471 A1'))
    
    # les PCT sont considérés comme OK (ne pas envoyer à la bibliothèque)
    def test_174462(self):
        self.assertTupleEqual(('PCT/IB2010/055047', None, None, None), parse('PCT/IB2010/055047'))
    
    def test_101125(self):
        self.assertTupleEqual(('WO2006047628', 'WO', 'A3', 2006), parse('WO2006047628 (A3)'))

class NOTHING(TestCase2):
    """
    Empty results are expected in these cases.
    """
    
    def test_29421(self):
        self.assertTupleEqual((None, None, None, None), parse('CH-96-10763'))

    def test_29460(self):
        self.assertTupleEqual((None, None, None, None), parse('EP97/05495'))
    
    def test_77931(self):
        self.assertTupleEqual((None, None, None, None), parse('2001042220'))
    
    def test_78733(self):
        self.assertTupleEqual((None, None, None, None), parse('75-2513746-2513746'))
    
    def test_99923(self):
        self.assertTupleEqual((None, None, None, None), parse('U.S. Patent No. 7'))
    
    def test_111820(self):
        self.assertTupleEqual((None, None, None, None), parse('US60/412.315'))

    # '.'
    def test_155482(self):
        self.assertTupleEqual((None, None, None, None), parse('DE 10 2008 022 349.2'))
    
    # '.'
    def test_112281(self):
        self.assertTupleEqual((None, None, None, None), parse('EP 07007600.5'))
    
    # too short
    def test_165879(self):
        self.assertTupleEqual((None, None, None, None), parse('WO/2010/076'))

################################################################################
import getopt

if __name__ == "__main__":
    try:
        (optlist, args) = getopt.gnu_getopt(sys.argv, 't', ['debug', 'test', 'help'])
    except getopt.GetoptError as err:
        logger.critical('%s', err)
        usage()
        sys.exit(2)
    
    optdict = dict(optlist)
    
    test_mode = optdict.has_key('-t') or optdict.has_key('--test')
    debug_mode = optdict.has_key('--debug')
    display_help = optdict.has_key('--help')
    
    if display_help:
        usage()
        sys.exit()
    
    if debug_mode:
        logger.setLevel(logging.DEBUG)
    
    if test_mode:
        sys.argv = args
        unittest.main()
    else:
        main()
