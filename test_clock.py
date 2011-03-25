
import PyOrgMode
import time
import unittest


class TestClockElement(unittest.TestCase):
    def test_duration_format(self):
        """Durations are formatted identically to org-mode"""
        clock_elem = PyOrgMode.Clock.Element('2011-03-25 06:53',
                                             '2011-03-25 09:12',
                                             '2:19')
        for hour in '0', '1', '5', '10', '12', '13', '19', '23':
            for minute in '00', '01', '29', '40', '59':
                orig_str = '%s:%s' % (hour, minute)
                orig_tuple = time.strptime(orig_str,clock_elem.timeformat)
                formatted_str = clock_elem.format_duration(orig_tuple)
                self.assertEqual(formatted_str, orig_str)


if __name__ == '__main__':
    unittest.main()
