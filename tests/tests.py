import os
import unittest

from unittest.mock import Mock


# set Mocks
#https://realpython.com/python-mock-library/

recids = perform_request_search(p="collection:PATENT",
                        d1=yesterday.strftime("%Y-%m-%d %H:%M:%S"),
                        d2=now.strftime("%Y-%m-%d %H:%M:%S"),
                        dt="m")


class TestFilesValidity(unittest.TestCase):
    patents_sample_xml_path = os.path.join(CURRENT_DIRECTORY, "infoscience_patents_sample.xml")

    def test_can_read_marc_file():
        

class TestNewPatents(unittest.TestCase):
    



    def test_can_write_a_blog_post(self):
        # Goes to the her dashboard
        ...
        # Clicks "New Post"
        ...
        # Fills out the post form
        ...
        # Clicks "Submit"
        ...
        # Can see the new post
        ...

class TestUpdatingPatents(unittest.TestCase):

    def test_can_write_a_blog_post(self):
        # Goes to the her dashboard
        ...
        # Clicks "New Post"
        ...
        # Fills out the post form
        ...
        # Clicks "Submit"
        ...
        # Can see the new post
        ...

if __name__ == '__main__':
    unittest.main()