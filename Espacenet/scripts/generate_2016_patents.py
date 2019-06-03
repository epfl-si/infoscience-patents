# -*- coding: utf-8 -*-

"""
    (c) All rights reserved. ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE, Switzerland, VPSI, 2017
"""

"""From Espacenet, query all patents that are linked to EPFL"""

# pd within "20051212 20051214"  All publications published 12, 13 or 14 December 2005
# pd="20051212 20051214"  Same as above

import csv
from Curator.harvest.Espacenet.query import EspacenetQuery
#from harvest.Espacenet.patent_models import PatentFamilies
#from importer.TTO.models import PatentItem
from Infoscience.Fetch import fetch_recids

import logging


level = logging.getLevelName('DEBUG')
Log = logging.getLogger('requests')
Log.setLevel(level)

query = 'pa all "Ecole Polytech* Lausanne" and pd>=2016'
querier = EspacenetQuery(auto_range=True)

result = querier.fetch(query)
print querier.total_count
len(result)

##################
# Verify with the TTO export
##################

# csvfile = open('/home/kis/src/infoscience/Curator/importer/TTO/Export_2016_publicationsxls.csv')
# rows = csv.reader(csvfile)
#
# TTO_2016_patent = []
# i = 0
#
# for (rownum, rowdata) in enumerate(rows, start=1): # header row
#     print "fetch an item"
#     patent_item = PatentItem(*rowdata, rownum=rownum)
#     TTO_2016_patent.append(patent_item)
#
#     if patent_item.nr_international:
#         print "Found a %s nr_international" % (patent_item.nr_international)
#
#     if patent_item.epodoc:
#         i += 1
#         print "Found a %s patent %s" % (patent_item.epodoc, i)
#
# csvfile.close()

###################
# print results
###################
i_family = 0
i_patent = 0
i_family_in_infoscience = 0

print "EPO ID (family); patent number; Known by Infoscience"

for family_nb, patents in result.iteritems():
    i_family += 1
    to_print = str(family_nb) + ';'
    patent_to_print = []
    for patent in patents:
        i_patent += 1
        print_number = unicode(patent).replace('Patent ', '')
        patent_to_print.append(print_number)

        # # check if exist in TTO list
        # if next((x for x in TTO_2016_patent if x.epodoc == patent.epodoc), None):
        #     patent_to_print.append("found in TTO")

    to_print += ', '.join(patent_to_print)

    # check if exist in Infoscience
    if fetch_recids(p="035__a:'%s (EPO Family ID)'" % family_nb):
        i_family_in_infoscience += 1
        to_print += "; found in Infoscience"

    print to_print

print """result has %s families, %s patent.
       "%s families are already in Infoscience""" \
      % (i_family, i_patent, i_family_in_infoscience)
