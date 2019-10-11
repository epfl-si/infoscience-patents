import unittest
import tempfile

import epo_ops

from .marc import MarcRecord, MarcCollection, MarcRecordBuilder
from .models import EspacenetPatent
from .patent_models import PatentFamilies
from .builder import EspacenetBuilderClient
from .utils import p_json


class TestEspacenetBuilderStructure(unittest.TestCase):
    """
    Check that the model returned by the API correspond to what the code await.
    This serve as reference about data we use, too.
    """
    client = EspacenetBuilderClient(use_cache=True)

    def _test_has_default_structure(self, json_parsed):
        self.assertNotEqual(json_parsed, "", "Nothing has been returned from the API")

        self.assertTrue('ops:world-patent-data' in json_parsed,
            "There is ops:world-patent-data in returned data, %s" % p_json(json_parsed))

    def test_patent_service_structure(self):
        patent = self.__class__.client.patent(  # Retrieve bibliography data
            input = epo_ops.models.Docdb('1000000', 'EP', 'A1'),  # original, docdb, epodoc
            )

        json_parsed = self.__class__.client.json_parsed

        self._test_has_default_structure(self.__class__.client.json_parsed)
        world_patent_data = json_parsed['ops:world-patent-data']

        self.assertTrue('exchange-documents' in world_patent_data,
            "There is no main wrapper in returned data")
        exchange_document = world_patent_data['exchange-documents']['exchange-document']

        self.assertTrue('@family-id' in exchange_document,
            "Can't find the family ID in the exchange-document, %s" % p_json(exchange_document))

        self.assertTrue('bibliographic-data' in exchange_document,
        "Can't find the bibliographic data in the exchange-document, %s" % p_json(exchange_document))
        bibliographic_data = exchange_document['bibliographic-data']

    def test_family_service_structure(self):
        patents_family, fulfilled_patent = self.__class__.client.family(  # Retrieve bibliography data
                input = epo_ops.models.Epodoc('EP3487508'),  # original, docdb, epodoc
            )

        json_parsed = self.__class__.client.json_parsed

        self._test_has_default_structure(self.__class__.client.json_parsed)
        world_patent_data = json_parsed['ops:world-patent-data']

        self.assertTrue('ops:patent-family' in world_patent_data,
            "There is no ops:patent-family wrapper in returned data, %s" % p_json(world_patent_data))
        patents_family = world_patent_data['ops:patent-family']

        self.assertTrue('ops:family-member' in patents_family,
            "There is no ops:family-member wrapper in returned data, %s" % p_json(patents_family))
        patents_member = patents_family['ops:family-member'][0]

        self.assertTrue('@family-id' in patents_member,
            "There is no @family-id wrapper in returned data, %s" % p_json(patents_member))
        family_id = patents_member['@family-id']
        self.assertTrue('publication-reference' in patents_member,
            "There is no publication-reference wrapper in returned data, %s" % p_json(patents_member))
        pubication_reference = patents_member['publication-reference']

        self.assertTrue('document-id' in pubication_reference,
            "There is no pdocument-id wrapper in returned data, %s" % p_json(pubication_reference))
        document_ids = pubication_reference['document-id']
        self.assertTrue(document_ids[0]['@document-id-type'] in ['docdb', 'epodoc'],
            "There is no valid numbers in a family fetch in returned data, %s" % p_json(document_ids))

    def test_published_data_search(self):
        range_begin = 1
        range_end = 2

        results = self.__class__.client.search(
            value = 'pa all "Ecole Polytech* Lausanne" and pd>=2016',
            range_begin = range_begin,
            range_end = range_end
            )

        json_parsed = self.__class__.client.json_parsed
        self._test_has_default_structure(self.__class__.client.json_parsed)
        world_patent_data = json_parsed['ops:world-patent-data']

        self.assertTrue('ops:biblio-search' in world_patent_data,
            "There is no 'ops:biblio-search' wrapper in returned data, %s" % p_json(world_patent_data))
        biblio_search = world_patent_data['ops:biblio-search']

        self.assertTrue('ops:search-result' in biblio_search,
            "There is no 'ops:search-result' wrapper in returned data, %s" % p_json(world_patent_data))
        search_result = biblio_search['ops:search-result']

        self.assertTrue('exchange-documents' in search_result,
            "There is no 'exchange-documents' wrapper in returned data, %s" % p_json(search_result))
        self.assertIsInstance(search_result['exchange-documents'], list)
        exchange_document = search_result['exchange-documents'][0]['exchange-document']

        self.assertTrue('bibliographic-data' in exchange_document,
        "Can't find the bibliographic data in the exchange-document, %s" % p_json(exchange_document))
        bibliographic_data = exchange_document['bibliographic-data']


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

    def test_should_fetch_inventor_unicode_correctly(self):
        patents_family, fulfilled_patent = self.__class__.client.family(  # Retrieve bibliography data
                input = epo_ops.models.Epodoc('EP3487508'),  # original, docdb, epodoc
            )

        # get the marc transformation
        marcxml_collection = MarcCollection()
        new_record = MarcRecordBuilder().from_epo_patents(family_id="56550084", patents=patents_family.patents, fulfilled_patent=fulfilled_patent)
        marcxml_collection.append(new_record.marc_record)

        # Check when we write that the authors list is correct
        tmp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        marcxml_collection.write(tmp_file.name)
        tmp_file.close()

        with open(tmp_file.name) as tmp_file_readed:
            tmp_file_readed.seek(0)
            read_it = tmp_file_readed.read()

            self.assertTrue('Stellacci' in read_it,
                "Missing or badly formatted authors in xml result %s" % read_it)

    def test_should_fetch_family_from_patent(self):
        patents_families, fulfilled_patent = self.__class__.client.family(  # Retrieve bibliography data
            input = epo_ops.models.Epodoc('EP1000000'),  # original, docdb, epodoc
            )

        self.assertGreater(len(patents_families), 0)
        self.assertIsInstance(patents_families, PatentFamilies)
        self.assertIn('19768124', patents_families.keys(), "Unable to find the awaited family id")
        self.assertGreater(len(patents_families['19768124']), 1)
        patent = fulfilled_patent
        self.assertIsInstance(patent, EspacenetPatent)
        self.assertEqual(patent.number, '1000000')
        self.assertEqual(patent.epodoc, 'EP1000000')
        #TODO: Patent family has patent numbers, but no data. We need this data for at least one patent
        self.assertNotEqual(patent.abstract_en, '')
        self.assertGreater(len(patent.inventors), 0)
        self.assertNotEqual(patent.inventors[0], '')

    def test_should_fetch_family_from_patent2(self):
        client = EspacenetBuilderClient(use_cache=True)
        patents_families, fulfilled_patent = client.family(  # Retrieve bibliography data
            input = epo_ops.models.Epodoc('WO2017102593'),  # original, docdb, epodoc
            )

        self.assertGreater(len(patents_families), 0)
        self.assertIsInstance(patents_families, PatentFamilies)
        self.assertIn('57629569', patents_families.keys(), "Unable to find the awaited family id")

        patent = fulfilled_patent
        self.assertIsInstance(patent, EspacenetPatent)
        self.assertEqual(patent.number, '2017102593')
        self.assertEqual(patent.epodoc, 'WO2017102593')
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