
"""Tests for parsing and outputting a simple .org test file
 
 You need the fr_FR.UTF-8 locale to run these tests
 """
 
import locale
import PyOrgMode
try:
    import unittest2 as unittest
except ImportError:
    import unittest
 
 
def _normalize_ignored(line):
    """Normalize a line to ignore differences which aren't yet handled"""
    line = line.replace(':ORDERED:  t', ':ORDERED: t')
    return line


class TestExampleOrgFile(unittest.TestCase):
    def test_test_org(self):
        test = PyOrgMode.OrgDataStructure()
        test.load_from_file("test.org")
        locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
        test.save_to_file("output.org")
        original = [_normalize_ignored(line) for line in open("test.org")]
        saved = [_normalize_ignored(line) for line in open("output.org")]
        self.assertEqual(saved, original)

if __name__ == '__main__':
    unittest.main()
