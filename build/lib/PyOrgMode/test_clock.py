
import PyOrgMode
import time
import unittest


class TestClockElement(unittest.TestCase):
    def test_duration_format(self):
        """Durations are formatted identically to org-mode"""

        for hour in '0', '1', '5', '10', '12', '13', '19', '23':
            for minute in '00', '01', '29', '40', '59':
                orig_str = '%s:%s' % (hour, minute)
                orgdate_element = PyOrgMode.OrgDate(orig_str)
                formatted_str = orgdate_element.get_value()
                self.assertEqual(formatted_str, orig_str)
  
if __name__ == '__main__':
    unittest.main()
