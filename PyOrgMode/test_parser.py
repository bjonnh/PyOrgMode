
import PyOrgMode
import tempfile
import unittest


class TestParser(unittest.TestCase):
    """Test the org file parser with a simple org structure"""

    def setUp(self):
        """Parse the org structure from a temporary file"""
        orgfile = tempfile.NamedTemporaryFile()
        orgfile.write('\n'.join((
            '* one',
            '* two',
            '** two point one',
            '* three',
            '')).encode('UTF-8'))
        orgfile.flush()
        self.tree = PyOrgMode.OrgDataStructure()
        try:
            self.tree.load_from_file(orgfile.name)
        finally:
            orgfile.close()

    def test_has_three_top_level_headings(self):
        """The example has three top-level headings"""
        self.assertEqual(len(self.tree.root.content), 3)

    def test_second_item_has_a_subheading(self):
        """The second top-level heading has one subheading"""
        self.assertEqual(len(self.tree.root.content[1].content), 1)


if __name__ == '__main__':
    unittest.main()
