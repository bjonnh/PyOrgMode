
"""Tests for headline validity
 """

import PyOrgMode
try:
    import unittest2 as unittest
except ImportError:
    import unittest


class TestHeadlineValidity(unittest.TestCase):
    def setUp(self):
        self.tree = PyOrgMode.OrgDataStructure()
        self.tree.add_todo_state('TODO')
        self.tree.load_from_file("headlines.org")
        self.todolist = self.tree.extract_todo_list()

    def test_recognize_heading(self):
        """The file has three top-level headings"""
        node = self.tree.root.content[0]
        self.assertIsInstance(node.content[1],
                              PyOrgMode.OrgNode.Element)

    def test_not_recognize_starredtext_asheading(self):
        """The file has three top-level headings"""
        node = self.tree.root.content[0]
        self.assertNotIsInstance(node.content[0],
                                 PyOrgMode.OrgNode.Element)

if __name__ == '__main__':
    unittest.main()
