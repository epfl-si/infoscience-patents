import unittest

import epo_ops

from .builder import EspacenetBuilderClient
from .utils import p_json


class TestEspacenetBuilderStructure(unittest.TestCase):
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
        patents_family = self.__class__.client.family(  # Retrieve bibliography data
                input = epo_ops.models.Epodoc('EP3487508'),  # original, docdb, epodoc
            )

        json_parsed = self.__class__.client.json_parsed

        self._test_has_default_structure(self.__class__.client.json_parsed)
        world_patent_data = json_parsed['ops:world-patent-data']

        self.assertTrue('ops:patent-family' in world_patent_data,
            "There is no ops:patent-family wrapper in returned data, %s" % p_json(world_patent_data))
        patents_family = world_patent_data['ops:patent-family']

        """
        ...
        To be continued
        ...
        """

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
