import os
import re
import unittest
import argparse
import xml.etree.ElementTree as ET

from log_utils import add_logging_argument, set_logging_from_args

from Espacenet.builder import EspacenetBuilderClient
from Espacenet.epo_secrets import get_secret
from Espacenet.models import EspacenetPatent
from Espacenet.marc import MarcPatentFamilies as PatentFamilies

import epo_ops


client_id = get_secret()["client_id"]
client_secret = get_secret()["client_secret"]

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


#TO_DECIDE: move this in code has import filter or not?
def is_patent_from_epfl(patent):
    """ check if the patent has any link with the epfl """
    valid_applicants = ['ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (EPFL)',
                        'ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE',
                        'ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE,',
                        'ECOLE POLYTECHNIC FEDERAL DE LAUSANNE (EPFL)',
                        'ECOLE POLYTECHNIQUE FED DE LAUSANNE(EPFL)']

    if hasattr(patent, 'applicants'):
        for pos, applicant in patent.applicants:  # @UnusedVariable
            if applicant in valid_applicants or 'EPFL' in applicant or \
                'POLYTECHNIQUE FÉDÉRALE DE LAUSANNE':
                return True

    return False


class TestEspacenetBuilder(unittest.TestCase):

    client = EspacenetBuilderClient(key=client_id, secret=client_secret, use_cache=True)

    def test_should_fetch_a_patent(self):
        patent = self.__class__.client.patent(  # Retrieve bibliography data
            input = epo_ops.models.Docdb('1000000', 'EP', 'A1'),  # original, docdb, epodoc
            )

        self.assertIsInstance(patent, EspacenetPatent)
        self.assertEqual(patent.number, '1000000')
        self.assertEqual(patent.epodoc, 'EP1000000')
        self.assertNotEqual(patent.abstract_en, '')
        self.assertGreater(len(patent.inventors), 0)
        self.assertNotEqual(patent.inventors[0], '')

    def test_should_fetch_family_from_patent(self):
        patents_families = self.__class__.client.family(  # Retrieve bibliography data
            input = epo_ops.models.Docdb('1000000', 'EP', 'A1'),  # original, docdb, epodoc
            )

        self.assertGreater(len(patents_families), 0)
        self.assertIsInstance(patents_families, PatentFamilies)

        patent = patents_families['19768124'][0]
        self.assertIsInstance(patent, EspacenetPatent)
        self.assertEqual(patent.number, '1000000')
        self.assertEqual(patent.epodoc, 'EP1000000')
        self.assertNotEqual(patent.abstract_en, '')
        self.assertGreater(len(patent.inventors), 0)
        self.assertNotEqual(patent.inventors[0], '')

    def test_search_patents_specific_range(self):
        range_begin = 1
        range_end = 12
        results = self.__class__.client.search(
            value = 'pa all "Ecole Polytech* Lausanne" and pd>=2016',
            range_begin = range_begin,
            range_end = range_end
            )

        # assert we don't have double entries
        patents_epodoc_list = [x.epodoc for x in results.patent_families['66532418']]
        self.assertEqual(
            len(patents_epodoc_list),
            len(set(patents_epodoc_list)),
            "Returned result should not have double entries"
            )

        self.assertGreater(len(results.patent_families), 0)
        self.assertIsInstance(results.patent_families, PatentFamilies)
        self.assertEqual(len(results.patent_families.patents), range_end)

    def test_patents_search(self):
        """
        as EPO has a hard limit of 100 results, this test
        verify that the auto-range is doing his job
        """
        results = self.__class__.client.search(
            value = 'pa all "Ecole Polytech* Lausanne" and pd=2014'
            )

        # assert we don't have double entries
        patents_epodoc_list = [x.epodoc for x in results.patent_families['66532418']]
        self.assertEqual(
            len(patents_epodoc_list),
            len(set(patents_epodoc_list)),
            "Returned result should not have double entries"
            )

        # be sure this search has more results than the range limit
        self.assertGreater(results.total_count, 100)
        self.assertGreater(len(results.patent_families.patents), 100)

        self.assertIsInstance(results.patent_families, PatentFamilies)
        self.assertEqual(len(results.patent_families.patents), results.total_count)

        # we only want patents from epfl
        for family_id, patents in results.patent_families.items():
            for patent in patents:
                if not is_patent_from_epfl(patent):
                    # assert at least one patent of the family is epfl
                    has_one_epfl = False
                    for o_patent in results.patent_families[family_id]:
                        if is_patent_from_epfl(o_patent):
                            has_one_epfl = True
                            break

                    self.assertFalse(has_one_epfl,
                     "This family has nothing to do with EPFL {}. Patent sample : {}".format(
                         family_id,
                         o_patent
                         ))


class TestPatentToMarc(unittest.TestCase):
    patent_sample_xml_path = os.path.join(__location__, "fixtures", "infoscience_patent_sample_marc.xml")

    def test_should_have_a_well_defined_marc_patent(self):
        client = EspacenetBuilderClient(key=client_id, secret=client_secret, use_cache=True)

        # search a patent
        patent_family = client.family(  # Retrieve bibliography data
            input = epo_ops.models.Epodoc('EP2936195')
            )

        # get the marc transformation
        marc_collection_dumped = patent_family.to_marc()

        # check the result look like the reference file
        with open(self.__class__.patent_sample_xml_path) as patent_xml:
            reference_root = ET.parse(patent_xml)
            result_root = marc_collection_dumped

            control_fields = reference_root.findall(".//controlfield")
            subfields = reference_root.findall(".//subfield")
            result_control_fields = result_root.findall(".//controlfield")
            result_subfields = result_root.findall(".//subfield")

            try:
                self.assertNotEqual(len(list(result_control_fields)), 0)
                self.assertNotEqual(len(result_subfields), 0)
                self.assertEqual(len(result_control_fields), len(control_fields))
                self.assertEqual(len(result_subfields), len(subfields))
            except AssertionError as e:
                raise AssertionError("XML from patent is bad : %s" % patent_family.to_marc_string(True)) from e

            # namespace check
            self.assertTrue('<collection xmlns="http://www.loc.gov/MARC21/slim">' in
                    patent_family.to_marc_string(True), "Missing namespace in xml result")


class TestLoadingInfosciencExport(unittest.TestCase):
    patent_sample_xml_path = os.path.join(__location__, "fixtures", "infoscience_patent_sample_marc.xml")

    def test_should_create_patents_from_infoscience_export(self):
        with open(self.__class__.patent_sample_xml_path) as patent_xml:
            pass

        # open file
        # for every record, create the corresponding patent (family)
        # ...


class TestNewPatents(unittest.TestCase):

    def test_new_patents_process(self):
        # Get a (dated? like the latest from [month|year]) list of Infoscience patents (as MarcXML)

        # Set date to search Espacenet correctly, based on the preceding list

        # Crawl Espacenet for EPFL data from this date

        # Compare results and generate a MarcXML file to update Infoscience

        # Test new file
        pass


class TestUpdatingPatents(unittest.TestCase):

    def test_update_patents_process(self):
        # Get an infoscience patents db as marcxml

        # Set date to search from this db

        # Crawl Espacenet
        pass


if __name__ == '__main__':
    # force debug logging
    parser = argparse.ArgumentParser()
    parser = add_logging_argument(parser)
    args = parser.parse_args(['--debug'])
    set_logging_from_args(args)
    unittest.main()
