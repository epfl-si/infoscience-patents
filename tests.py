import os
import unittest
import argparse

from mock import Mock, patch

from log_utils import add_logging_argument, set_logging_from_args
from Espacenet.query import EspacenetQuery


class TestSearchPatents(unittest.TestCase):

    def test_search_patents(self):
        s = EspacenetQuery()
        fs = s.fetch('liquid')
        assertNotEquals(len(fs), 0, "An Espacenet search should not be empty")


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
    unittest.main()
