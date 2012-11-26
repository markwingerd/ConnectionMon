import unittest

from connectionmon import ConnectionMonitor

class ConnectionMonitorTest(unittest.TestCase):
    """"""

    def test_get_tcp(self):
        """Tests that procfs can get tcp connections"""
        monitor = ConnectionMonitor()
        self.assertIn('rem_address',monitor._get_tcp()[0])

    def test_get_nonblank_connections(self):
        """Tests that NULL addresses in procfs are removed."""
        monitor = ConnectionMonitor()
        ip = []
        for item in monitor._get_nonblank_connections(monitor._get_tcp()):
            ip.append(item['rem_address'][0])
        self.assertNotIn('0.0.0.0',ip)

if __name__ == '__main__':
    unittest.main()