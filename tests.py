import os
import unittest
import argparse

from log_utils import add_logging_argument, set_logging_from_args

from Espacenet.builder import EspacenetBuilderClient
from Espacenet.epo_secrets import get_secret
from Espacenet.models import EspacenetPatent
from Espacenet.patent_models import PatentFamilies

import epo_ops


client_id = get_secret()["client_id"]
client_secret = get_secret()["client_secret"]

class TestEspacenetBuilder(unittest.TestCase):
    
    client = EspacenetBuilderClient(key=client_id, secret=client_secret)

    def fftest_should_fetch_family_from_api(self):
        
        patents = self.__class__.client.family(  # Retrieve bibliography data
            input = epo_ops.models.Docdb('1000000', 'EP', 'A1'),  # original, docdb, epodoc
            endpoint = 'biblio',  # optional, defaults to biblio in case of published_data
            constituents = []  # optional, list of constituents
            )

        self.assertGreater(len(patents), 0)
        self.assertIsInstance(patents, PatentFamilies)

        patent = patents['19768124'][0]
        self.assertIsInstance(patent, EspacenetPatent)
        self.assertEqual(patent.number, '1000000')
        self.assertEqual(patent.epodoc, 'EP1000000')

    def test_search_patents(self):
        results = self.__class__.client.published_data_search(  # Retrieve bibliography data
            cql = 'pa all "Ecole Polytech* Lausanne" and pd>=2016',
            constituents = ['biblio']  # optional, list of constituents
            )
        
        self.assertGreater(len(results.patent_families), 0)
        self.assertIsInstance(results.patent_families, PatentFamilies)
        #FIX: set range correctly
        self.assertGreater(len(results.patent_families), 500)


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
