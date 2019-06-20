import os
import re
import unittest
import argparse
import tempfile
import xml.etree.ElementTree as ET

from log_utils import add_logging_argument, set_logging_from_args

import epo_ops

from Espacenet.builder import EspacenetBuilderClient
from Espacenet.models import EspacenetPatent
from Espacenet.marc import MarcPatentFamilies as PatentFamilies, MarcRecord, MarcCollection
from updater import update_infoscience_export
from Espacenet.marc_xml_utils import \
    filter_out_namespace, \
    _get_controlfield_element, \
    _get_controlfield_value, \
    _get_datafield_element, \
    _get_subfield_element, \
    _get_datafield_values, \
    _get_multifield_values


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

    client = EspacenetBuilderClient(use_cache=True)

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

    def test_allow_to_write_marc_change(self):
        r = MarcRecord()
        self.assertTrue(r.marc_record)
        self.assertNotEqual(r.marc_record, "")
        self.assertFalse(r.family_id)
        r.family_id = "121212"
        self.assertEqual(r.family_id, "121212")


    def test_should_have_a_well_defined_marc_patent(self):
        client = EspacenetBuilderClient(use_cache=True)

        # search a patent
        patent_family = client.family(  # Retrieve bibliography data
            input = epo_ops.models.Epodoc('EP2936195')
            )

        # get the marc transformation
        #marcxml_collection = ET.Element('collection', attrib={'xmlns':"http://www.loc.gov/MARC21/slim"})
        marcxml_collection = MarcCollection()

        marcxml_collection.append(MarcRecord(patent_family=patent_family).marc_record)
        #marc_collection_dumped = MarcRecord(patent_family=patent_family).marc_record #.to_marc(marcxml_collection)

        # check the result look like the reference file
        with open(self.__class__.patent_sample_xml_path) as patent_xml:
            reference_root = ET.parse(patent_xml)
            result_root = marcxml_collection

            control_fields = reference_root.findall(".//{http://www.loc.gov/MARC21/slim}controlfield")
            subfields = reference_root.findall(".//{http://www.loc.gov/MARC21/slim}subfield")
            result_control_fields = result_root.findall(".//controlfield")
            result_subfields = result_root.findall(".//subfield")

            try:
                self.assertNotEqual(len(list(result_control_fields)), 0)
                self.assertNotEqual(len(result_subfields), 0)
                self.assertEqual(len(result_control_fields), len(control_fields))
                self.assertEqual(len(result_subfields), len(subfields))
            except AssertionError as e:
                raise AssertionError("XML from patent is bad : %s" % marcxml_collection.tostring(True)) from e

        # Check when we write that the namespace is correct
        tmp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        marcxml_collection.write(tmp_file.name)
        tmp_file.close()

        with open(tmp_file.name) as tmp_file_readed:
            tmp_file_readed.seek(0)
            read_it = tmp_file_readed.read()

            self.assertTrue('<collection xmlns="http://www.loc.gov/MARC21/slim">' in read_it,
                "Missing namespace in xml result %s" % read_it)


class TestLoadingInfosciencExport(unittest.TestCase):
    patent_sample_xml_path = os.path.join(__location__, "infoscience_patents_export.xml")
    # a sample that need to be updated
    patent_incomplete_sample_xml_path = os.path.join(__location__, "fixtures", "infoscience_incomplete_patent_sample_marc.xml")

    # what I removed from the original
    """
            <datafield tag="013" ind1=" " ind2=" ">
                <subfield code="a">WO9629715</subfield>
                <subfield code="c">A1</subfield>
                <subfield code="b">WO</subfield>
                <subfield code="d">19960926</subfield>
            </datafield>
            <datafield tag="024" ind1="7" ind2="0">
                <subfield code="a">4196246</subfield>
                <subfield code="2">EPO Family ID</subfield>
            </datafield>
    """

    def test_should_update_existing_patents(self):
        with open(self.__class__.patent_incomplete_sample_xml_path) as patent_xml:
            # load before update, to check the fixture is not complete
            patent_xml = filter_out_namespace(patent_xml.read())
            collection = ET.fromstring(patent_xml)
            original_records = collection.findall(".//record")
            original_record = original_records[0]
            original_patents_datafield = _get_multifield_values(original_record, '013')
            original_patents_epodocs = list(map(lambda d: d.get('a'), original_patents_datafield))
            self.assertEqual(len(original_patents_epodocs), 2)

        with open(self.__class__.patent_incomplete_sample_xml_path) as patent_xml:
            updated_xml_collection = update_infoscience_export(patent_xml)

        self.assertTrue(updated_xml_collection)

        records = updated_xml_collection.findall(".//record")

        self.assertEqual(len(records), 1)

        record = records[0]

        record_id = _get_controlfield_value(record, '001')
        self.assertEqual(record_id, "229047")

        # initially has 2 patents, we want more at the end
        patents_datafield = _get_multifield_values(record, '013')
        patents_epodocs = list(map(lambda d: d.get('a'), patents_datafield))
        self.assertGreater(len(patents_epodocs), 2, "patents_epodocs  : %s" % patents_epodocs)

        ## test rules about updates
        # should be ordered by date
        patents_date = list(map(lambda d: d.get('d'), patents_datafield))
        self.assertEqual(patents_date, sorted(patents_date, reverse=True))
        # should the manually added

        # initially we have no family id
        self.assertGreater(len(_get_controlfield_value(record, "005")), 0)

        # check that the missing fields we see here are present now
        # check other field are kept in place
        try:
            self.assertGreater(len(_get_controlfield_value(record, "005")), 0)
            self.assertGreater(len(_get_datafield_values(record, "024", "7", "0")), 0)
            self.assertGreater(len(_get_datafield_values(record, "037")), 0)
            self.assertGreater(len(_get_datafield_values(record, "973")), 0)
            self.assertGreater(len(_get_datafield_values(record, "980")), 0)
            self.assertEqual(len(_get_datafield_values(record, "012")), 0)  # counter-test
        except AttributeError as e:  # problem that the attribute don't exist
            raise AssertionError("Updating the patents has removed some information") from e

        # open file
        # for every record, create the corresponding patent (family)
        # then we build a big PatentFamilies with all data
        # then we modify the inputted file "in memory"
        # at the end we generate a new file from it
        # ...

        # sample of copy
        #    if tind_author != epfl_author:
        #        logger.debug("Author will be updated, from %s to %s" % (
        #            tind_author, epfl_author))
        #
        #        # update record in a new instance, as we will move it to a new file
        #        to_update_record = copy.deepcopy(record)
        #
        #        updated_record = update_marc_record(to_update_record, epfl_author)
        #        create_update_collection.append(updated_record)


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
