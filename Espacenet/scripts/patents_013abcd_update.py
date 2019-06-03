# -*- coding: utf-8 -*-

"""
    (c) All rights reserved. ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE, Switzerland, VPSI, 2017
"""

import logging, tempfile, sys, csv
from Infoscience.Fetch import fetch_record
from Infoscience.Invenio import bibupload


def usage():
    print ""
    print "This script updates the patent field (013) of records, taking the"
    print "values of subfields a, b, c and d from a CSV file."
    print ""
    print "Usage:"
    print "    --input <file> CSV file, if not specified => read CSV from stdin"
    print "                   mandatory columns are: id, 013__a, 013__b, 013__c, 013__d"
    print "    --dry          do not run bibupload"
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

def update(rowdict, dryrun_mode):
    recid = rowdict.get('id', None)
    thirteen_a = rowdict.get('013__a', None)
    thirteen_b = rowdict.get('013__b', None)
    thirteen_c = rowdict.get('013__c', None)
    thirteen_d = rowdict.get('013__d', None)
    
    if not(thirteen_a and thirteen_b):
        raise Exception('skipping update of record-id %s: $a and $b are mandatory' % (recid,))
    
    db = fetch_record(recid=recid, reader=None, db=None)
    
    if len(db.entries) == 1:
        (key, rec) = db.entries.iteritems().next()
        
        logger.info("record-id = %s%s" % (', '.join(rec.get('record-id')), ' (dry run, no bibupload)' if dryrun_mode else ''))
        
        if rec.has_key('patent'):
            rec_patent = rec.get('patent')
            if len(rec_patent) == 1:
                rc = rec_patent[0]
                
                logger.info("    - 0013__ a='%s', b='%s', c='%s', d='%s'" % (rc.number, rc.country, rc.kind, rc.date))
                
                rc.number = thirteen_a
                rc.country = thirteen_b
                rc.kind = thirteen_c if thirteen_c else None
                rc.date = thirteen_d if thirteen_d else None
                
                logger.info("    + 0013__ a='%s', b='%s', c='%s', d='%s'" % (rc.number, rc.country, rc.kind, rc.date))
                
                del rec['patent']
                rec.add('patent', rc)
                db[key] = rec
                
                if not dryrun_mode:
                    tmpfile = tempfile.mktemp(prefix='tmpBibupload_', suffix='.xml')
                    bibupload(db, tmpfile, mode='r') # r = replace
            else:
                raise Exception('record-id %s: more than 1 patent field' % (recid,))
    elif len(db.entries) > 1:
        raise Exception('record-id %s: more than 1 record' % (recid,))
    else:
        raise Exception('record-id %s not found' % (recid,))

def main(f, dryrun_mode=True):
    for rowdict in csv.DictReader(f, delimiter=';'):
        try:
            update(rowdict, dryrun_mode)
        except Exception as x:
            logger.error('Error, %s', x)

################################################################################
import getopt

if __name__ == "__main__":
    try:
        (optlist, args) = getopt.gnu_getopt(sys.argv, '', ['debug', 'dry', 'input=', 'help'])
    except getopt.GetoptError as err:
        logger.critical('%s', err)
        usage()
        sys.exit(2)
    
    optdict = dict(optlist)

    if optdict.has_key('--help'):
        usage()
        sys.exit()
    
    input_file = optdict.get('--input', None)
    if sys.stdin.isatty() and not input_file:
        logger.critical("missing input file parameter --input=<path>")
        usage()
        sys.exit(2)
    
    if not sys.stdin.isatty() and optdict.has_key('--input'):
        logger.critical("taking input from <stdin>, conflict with --input parameter")
        usage()
        sys.exit(2)
    
    dryrun_mode = optdict.has_key('--dry')
    debug_mode = optdict.has_key('--debug')
    
    if debug_mode:
        logger.setLevel(logging.DEBUG)
    
    if sys.stdin.isatty():
        with open(input_file) as f:
            main(f, dryrun_mode)
    else:
        main(iter(sys.stdin.readline, ''), dryrun_mode)
