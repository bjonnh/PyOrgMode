
"""Tests for parsing a file containing no headline
 but that contains a bold element (thanks whacked)
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
        with open("no_headline.org") as f:
            original = [line for line in f]
        with open("output.org") as f:
            saved = [line for line in f]
        self.assertEqual(saved, original)


if __name__ == '__main__':
    unittest.main()
