# -*- coding: utf-8 -*-

"""
    (c) All rights reserved. ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE, Switzerland, VPSI, 2017
"""

import logging, sys, tempfile, datetime, copy

import django

from Infoscience.Fetch import fetch_record
from invenio.search_engine import search_pattern
from Curator.harvest.Espacenet.query import EspacenetPCTPatentQuery
from Curator.harvest.Espacenet.models import EspacenetPatent, EspacenetPCT
from django.utils.datetime_safe import date
from Infoscience.Invenio import bibupload
from Infoscience import mkmap
from Pyblio import Attribute

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Curator.settings")
django.setup()

from Curator.authors.models import Name


def usage():
    print ""
    print "Updates patent records with the family-id and publication date"
    print "fetched from Espacenet. Fills up the patent family."
    print ""
    print "Family-id        -> in field 035"
    print "Publication date -> subfield 013__d"
    print "Family members   -> additional 013 fields"
    print ""
    print "Usage:"
    print "    --dry          fetch data from Espacenet but do not run bibupload"
    print "    --search=abc   optional critera (=> 980__a:'PATENT' abc), useful to target"
    print "                   a subset of patents"
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


class MissingNumberCountry(Exception):
    def __init__(self):
        super(MissingNumberCountry, self).__init__('missing number and country')

class MissingField013(Exception):
    def __init__(self):
        super(MissingField013, self).__init__('missing field 013__')

class FamilyNotFound(Exception):
    def __init__(self, epodoc):
        super(FamilyNotFound, self).__init__('family not found for patent %s' % epodoc)

def fetch_family(doc):
    logger.info("fetching %s ..." % doc.epodoc)
    
    # two-phase fetch for PCTs
    if isinstance(doc, EspacenetPCT):
        q = EspacenetPCTPatentQuery()
        result = q.fetch(doc)
        
        if len(result) > 0:
            epodoc = result.itervalues().next()[0].epodoc
        else:
            raise FamilyNotFound(doc.epodoc)
        patent = EspacenetPatent(epodoc=epodoc)
    else:
        patent = doc
    
    result = patent.fetch_families() # => uses file-based cache
    
    if not result:
        raise FamilyNotFound(patent.epodoc)
    
    return (patent, result.keys(), [i for s in result.values() for i in s])

def find_date(country, number, family):
    min_date = date(9999, 12 , 31)
    
    for m in family:
        if m.country == country and m.number == number:
            if m.date < min_date:
                min_date = m.date
    
    return min_date if min_date.year != 9999 else None

def find_application_date(country, number, family):
    min_date = date(9999, 12 , 31)
    
    for m in family:
        if m.country == country and m.number == number:
            if m.application_date < min_date:
                min_date = m.application_date
    
    return min_date if min_date.year != 9999 else None

def _clean_date(the_date):
    if isinstance(the_date, datetime.date):
        return the_date.strftime('%Y%m%d')
    elif isinstance(the_date, str):
        return the_date.replace('-', '')
    else:
        return '%s' % (the_date,)

def update_013__d(patent, the_date):
    new_value = _clean_date(the_date)
    if str(patent.date) != str(new_value):
        patent.date = new_value

def merge_patent(patent_to_update, patent2):
    if patent_to_update.country != patent2.country:
        patent_to_update.country = patent2.country
    if patent_to_update.kind != patent2.kind:
        patent_to_update.kind = patent2.kind
    if str(patent_to_update.date) != str(_clean_date(patent2.date)):
        patent_to_update.date = _clean_date(patent2.date)

def update_013s(rec, family):
    """
    Les entrées manuelles qui ne sont pas dans la liste Espacenet sont placée à la fin (fin = en dernière position = tout en bas)

    Les entrées manuelles qui sont reconnus dans la liste Espacenet sont enlevés (pour être remis juste après, voir l'étape suivante)

    La liste Espacenet est triée par date et ajouter de haut en bas.

    Cela peut donner par exemple :

    [Brevet1_Espacenet, Brevet2_Manuel_Espacenet, Brevet3_Espacenet, Brevet4_Manuel_Espacenet, Brevet5_Manuel]
    """
    infoscience_patents = rec.get('patent', [])

    espacenet_patents = []

    for member in family:
        #constuire le parfait record espacenet
        espacenet_patents.append(Attribute.Patent(number=member.epodoc,
                                                  country=member.country,
                                                  kind=member.kind,
                                                  date=_clean_date(member.date)))

    # Desc sorting
    espacenet_patents.sort(key=lambda p: p.date, reverse=True)

    #enlever du record Infoscience ce qui nous vient d'espacenet
    espacenet_epodocs = map(lambda p: p.number, espacenet_patents)

    patents_filtered = filter(lambda p: p.number not in espacenet_epodocs, infoscience_patents)

    #ajouter le parfait record au début
    del rec['patent']
    rec['patent'] = espacenet_patents + patents_filtered

def update_035__a(rec, family_ids, db):
    epo = mkmap(db, 'catalogers')['EPO Family ID']
    extra_ids = rec.get('extra-id', [])
    
    original_family_ids = filter(lambda x: epo in x.q.get('source', []), extra_ids)
    
    if set(map(lambda i: int(i), family_ids)) != set(map(lambda i: int(i), original_family_ids)):
        # throw away EPO Family IDs
        extra_ids = filter(lambda x: epo not in x.q.get('source', []), extra_ids)
        
        # add all EPO Family IDs
        for family_id in family_ids:
            attrib = Attribute.ID(family_id)
            attrib.q.update({'source': [Attribute.Txo(epo)]})
            extra_ids.append(attrib)
        
        rec['extra-id'] = extra_ids

def fetch_records(pattern, recids=[]):
    if not recids:
        recids = search_pattern(p=pattern).tolist()
    for recid in recids:
        db = fetch_record(recid, reader=None, db=None)
        (key, rec) = db.entries.iteritems().next()  # @UnusedVariable
        yield (db, rec)

def is_epfl(patent):
    """ check if we can find any link with the epfl """
    valid_applicants = ['ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (EPFL)',
                        'ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE',
                        'ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE,',
                        'ECOLE POLYTECHNIC FEDERAL DE LAUSANNE (EPFL)',
                        'ECOLE POLYTECHNIQUE FED DE LAUSANNE(EPFL)']
    
    # specials case for inventors
    valid_inventors = ['Manson, Jan-Anders, E',
                       'Shokrollahi Mohammad Amin']
    
    if hasattr(patent, 'applicants'):
        for pos, applicant in patent.applicants:  # @UnusedVariable
            if applicant in valid_applicants or 'EPFL' in applicant:
                return True
    
    if hasattr(patent, 'inventors'):
        for pos, inventor in patent.inventors:  # @UnusedVariable
            inventor_name = inventor.title().rstrip(',')
                
            if inventor_name in valid_inventors:
                return True
            
            try:
                Name.objects.get(name=inventor_name)
                return True
            except Name.DoesNotExist:
                # can't find his name, maybe it's a format problem
                # dont try a different format if we have already a comma
                if ',' not in inventor_name:
                    inventor_name = inventor_name.replace(' ', ', ')
                    try:
                        Name.objects.get(name=inventor_name)
                        return True
                    except Name.DoesNotExist:
                        pass
    
    return False

def main(dryrun_mode, pattern = None, recids = []):
    # assert the_date == patent_or_pct.date, "
    """
    :param pattern: if you want to go with a pattern search
    :param recids: if you already have your ids
    :return:

    >>> for (db, rec) in fetch_records(pattern = None, recids=[29513, 213139]):
    ...     original_rec = copy.deepcopy(rec)
    ...     assert original_rec == rec
    ...     rec_patents = rec.get('patent', [])
    ...     rec_id = rec.get('record-id')[0]
    ...     patent_or_pct = rec_patents[0]
    ...     assert patent_or_pct.date
    ...     doc = EspacenetPCT(epodoc=patent_or_pct.number)
    ...     (pub, family_ids, members) = fetch_family(doc)
    ...     the_date = find_application_date(pub.country, pub.number, members)
    ...     assert original_rec == rec
    ...     update_035__a(rec, family_ids, db)
    ...     assert original_rec == rec
    ...     the_cleaned_date = _clean_date(the_date)
    ...     assert the_cleaned_date == patent_or_pct.date, "Different date %s, %s" % (the_cleaned_date, patent_or_pct.date)
    ...     update_013__d(patent_or_pct, the_date)
    ...     assert original_rec == rec
    """
    for (db, rec) in fetch_records(pattern, recids):
        try:
            original_rec = copy.deepcopy(rec)
            rec_patents = rec.get('patent', [])
            rec_id = rec.get('record-id')[0]
            if len(rec_patents) > 0:
                patent_or_pct = rec_patents[0]
                
                try:
                    doc = EspacenetPCT(epodoc=patent_or_pct.number)
                except ValueError:
                    if not(patent_or_pct.number) and not(patent_or_pct.country):
                        raise MissingNumberCountry()
                    
                    if patent_or_pct.number.isdigit():
                        doc = EspacenetPatent(number=patent_or_pct.number, country=patent_or_pct.country)
                    else:
                        doc = EspacenetPatent(epodoc=patent_or_pct.number)
            else:
                raise MissingField013()
            
            # if PCT, pub is most certainly != doc
            (pub, family_ids, members) = fetch_family(doc)
            
            logger.info("    EPO Family IDs = [%s] (%s members total)" % (", ".join(family_ids), len(members)))
            
            if isinstance(doc, EspacenetPCT):
                the_date = find_application_date(pub.country, pub.number, members)
                logger.info("    application date = %s" % the_date)
            else:
                the_date = find_date(pub.country, pub.number, members)
                logger.info("    date = %s" % the_date)
            
            update_035__a(rec, family_ids, db)

            update_013__d(patent_or_pct, the_date) # useful mainly for PCTs

            epfl_relevant_members = filter(lambda m: is_epfl(m), members)
            if members and not epfl_relevant_members:
                logger.info("    !!! members in the family, but nothing relevant to EPFL !!!")
            update_013s(rec, epfl_relevant_members)

            needs_update = original_rec != rec
            if not needs_update:
                logger.info("    all good, no need to update")

            if not dryrun_mode and needs_update:
                tmpfile = tempfile.mktemp(prefix='tmpBibupload_', suffix='.xml')
                bibupload(db, tmpfile, mode='r') # r = replace mode

        except (MissingNumberCountry, MissingField013, FamilyNotFound, AttributeError, ValueError) as e:
            # TODO: ValueError are sometimes this case (too many patents inside) :
            # ValueError: Unmanaged JSON returned for url http://ops.epo.org/3.1/rest-services/family/publication/epodoc/WO9728149/biblio
            #
            # Json : <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
            # <fault xmlns="http://ops.epo.org">
            #     <code>SERVER.LimitedServerResources</code>
            #     <message>Please request bibliographic data in smaller chunks</message>
            # </fault>

            logger.error("Record-id %s: %s" % (rec_id, e))
            continue

################################################################################
import getopt

if __name__ == "__main__":
    try:
        (optlist, args) = getopt.gnu_getopt(sys.argv, '', ['debug', 'dry', 'help', 'search=', 'test'])
    except getopt.GetoptError as err:
        logger.critical('%s', err)
        usage()
        sys.exit(2)

    optdict = dict(optlist)

    if optdict.has_key('--help'):
        usage()
        sys.exit()

    if optdict.has_key('--test'):
        import doctest
        print doctest.testmod()
        sys.exit()
    
    if optdict.has_key('--debug'):
        logger.setLevel(logging.DEBUG)
    
    pattern = "980__a:'PATENT'"
    criteria = optdict.get('--search', '')
    pattern = pattern + " " + criteria
    pattern = pattern.strip()
    
    main(optdict.has_key('--dry'), pattern)
