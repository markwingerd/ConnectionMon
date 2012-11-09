import unittest

from connectionmon import ConnectionMonitor

class ConnectionMonitorTest(unittest.TestCase):
    """"""

    def test_get_connections(self):
        """Tests if .get_connections returns data from procfs."""
        monitor = ConnectionMonitor()
        monitor.get_connections()
        self.assertIn('rem_address',monitor.raw_proc[0])

    def test_null_address(self):
        """Tests if get_connections removes null ip address data (0.0.0.0)."""
        monitor = ConnectionMonitor()
        monitor.get_connections()
        self.assertNotIn( '0.0.0.0' ,monitor.raw_proc[0]['rem_address'][0])

    def test_cleaned_connections(self):
        """Tests the cleaned information from procfs."""
        monitor = ConnectionMonitor()
        monitor.get_connections()
        self.assertIn('local_address',monitor.connections[0])
        self.assertIn('rem_address',monitor.connections[0])

if __name__ == '__main__':
    unittest.main()