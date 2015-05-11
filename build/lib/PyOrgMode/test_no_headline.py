
"""Tests for parsing a file containing no headline
 
 You need the fr_FR.UTF-8 locale to run these tests
 """
 
import locale
import PyOrgMode
try:
    import unittest2 as unittest
except ImportError:
    import unittest
 
 
class TestExampleOrgFile(unittest.TestCase):
    def test_noheadline_org(self):
        test = PyOrgMode.OrgDataStructure()
        test.load_from_file("no_headline.org")
        locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
        test.save_to_file("output.org")
        original = [line for line in open("no_headline.org")]
        saved = [line for line in open("output.org")]
        self.assertEqual(saved, original)

if __name__ == '__main__':
    unittest.main()
