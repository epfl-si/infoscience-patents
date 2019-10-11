import os
import unittest
import argparse
import tempfile
import xml.etree.ElementTree as ET

from log_utils import set_logging_configuration

import epo_ops

from Espacenet.marc_xml_utils import \
    filter_out_namespace, \
    _get_controlfield_value, \
    _get_datafield_element, \
    _get_datafield_values, \
    _get_multifield_values

from updater import update_infoscience_export

from Espacenet.builder_test import *
from Espacenet.marc_tester import *

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


class TestLoadingInfoscienceExport(unittest.TestCase):
    # a sample that is used as reference
    patent_sample_xml_path = os.path.join(__location__, "infoscience_patents_export.xml")
    # a sample that need to be updated
    patent_incomplete_sample_xml_path = os.path.join(__location__, "fixtures", "infoscience_incomplete_patent_sample_marc.xml")
    # a big samples full of need to update data
    one_big_year_of_patent_xml_path = os.path.join(__location__, "fixtures", "infoscience_patents_some_from_2016_export.xml")
    # a full export
    all_patents_xml_path = os.path.join(__location__, "fixtures", "infoscience_patents_all.xml")

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
            patent_xml_str = patent_xml.read()
            patent_xml = filter_out_namespace(patent_xml_str)
            collection = ET.fromstring(patent_xml)
            original_records = collection.findall(".//record")
            original_record = original_records[0]
            original_patents_datafield = _get_multifield_values(original_record, '013')
            original_patents_epodocs = list(map(lambda d: d.get('a'), original_patents_datafield))
            self.assertEqual(len(original_patents_epodocs), 2)

        with open(self.__class__.patent_incomplete_sample_xml_path) as patent_xml:
            patent_str = patent_xml.read()
            updated_xml_collection = update_infoscience_export(patent_str)
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

    def test_should_update_a_big_export(self):
        with open(self.__class__.all_patents_xml_path) as patent_xml:
            # load before update, to check the fixture is complete
            patent_xml_str = patent_xml.read()
            patent_xml_str = filter_out_namespace(patent_xml_str)
            collection = ET.fromstring(patent_xml_str)
            original_records = collection.findall(".//record")
            self.assertGreater(len(original_records), 1)

        with open(self.__class__.all_patents_xml_path) as full_infoscience_export_xml:
            updated_patent_xml_str = full_infoscience_export_xml.read()
            updated_xml_collection = update_infoscience_export(updated_patent_xml_str,
                                            len(original_records)-10,
                                            len(original_records))

        self.assertTrue(updated_xml_collection)

        # we should have some records that need update
        records = updated_xml_collection.findall(".//record")
        self.assertGreater(len(records), 1)
        self.assertNotEqual(len(original_records), len(records), "Update result have more records to update than export provided")
        self.assertGreater(len(original_records), len(records), "Update result have more records to update than export provided")

        # do some check on update
        record = records[0]

        # only one ID pls
        self.assertEqual(len(record.findall('datafield[@tag="024"]/subfield[@code="2"][.="EPO Family ID"]')), 1)
        # only one timestamp pls
        self.assertEqual(len(record.findall('controlfield[@tag="005"]')), 1)

    def test_should_set_as_new_collection_of_new_patents(self):
        # fetch all results for a specific year, and assert the incoming infoscience export is set to the good year
        with open(self.__class__.one_big_year_of_patent_xml_path) as patent_xml:
            # load before update, to check the fixture is complete
            patent_xml_str = patent_xml.read()
            patent_xml = filter_out_namespace(patent_xml_str)
            collection = ET.fromstring(patent_xml)
            original_records = collection.findall(".//record")
            self.assertGreater(len(original_records), 1)
            year_of_ref = original_records[0].find('datafield[@tag="260"]/subfield[@code="c"]').text

            for record in original_records:
                # we want only one year
                self.assertEqual(
                    record.find('datafield[@tag="260"]/subfield[@code="c"]').text,
                    year_of_ref,
                    "Only one year for fetching new patents"
                    )


if __name__ == '__main__':
    # force debug logging
    parser = argparse.ArgumentParser()
    set_logging_configuration(debug=True)
    unittest.main()
