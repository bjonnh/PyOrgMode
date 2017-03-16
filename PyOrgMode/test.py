
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


def _normalize_output_ignored(line):
    line = line.replace(':TAG1:TAG2:', ':TAG1::TAG2:')
    line = _normalize_ignored(line)
    return line


class TestExampleOrgFile(unittest.TestCase):
    def test_test_org(self):
        test = PyOrgMode.OrgDataStructure()
        locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
        test.load_from_file("test.org")
        test.save_to_file("output.org")
        with open("test.org") as f:
            original = [_normalize_ignored(line) for line in f]
        with open("output.org") as f:
            saved = [_normalize_output_ignored(line) for line in f]

        self.assertEqual(saved, original)


if __name__ == '__main__':
    unittest.main()
