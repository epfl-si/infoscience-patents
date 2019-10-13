import os
import unittest
import xml.etree.ElementTree as ET
import tempfile

import epo_ops

from .builder import EspacenetBuilderClient

from .marc import MarcRecordBuilder, MarcCollection

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))


class TestPatentToMarc(unittest.TestCase):
    patent_sample_xml_path = os.path.join(os.path.dirname(__location__), "fixtures", "infoscience_patent_sample_marc.xml")

    def test_allow_to_write_marc_change(self):
        r = MarcRecordBuilder().get_empty_record()
        self.assertIsInstance(r.marc_record, ET.Element)
        self.assertNotEqual(r.marc_record, "")
        self.assertFalse(r.family_id)
        r.family_id = "121212"
        self.assertEqual(r.family_id, "121212")

    def test_should_have_a_well_defined_marc_patent(self):
        client = EspacenetBuilderClient(use_cache=True)

        # search a patent
        patents_family, fulfilled_patent = client.family(  # Retrieve bibliography data
            input = epo_ops.models.Epodoc('EP2936195')
            )

        # get the marc transformation
        marcxml_collection = MarcCollection()
        new_record = MarcRecordBuilder().from_epo_patents(family_id="50975639", patents=patents_family.patents, fulfilled_patent=fulfilled_patent)
        marcxml_collection.append(new_record.marc_record)
        # print(ET.dump(marcxml_collection))

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
