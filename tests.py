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

    def test_clean_connections(self):
        """Tests the ability to remove useless data."""
        monitor = ConnectionMonitor()
        conn = monitor._get_nonblank_connections(monitor._get_tcp())
        conn = monitor._clean_connections(conn, 'tcp')
        self.assertEqual(len(conn[0]),5)
        self.assertEqual('local_address' in conn[0], True)
        self.assertEqual('rem_address' in conn[0], True)
        self.assertEqual('domain' in conn[0], True)
        self.assertEqual('name' in conn[0], True)
        self.assertEqual('transport_layer' in conn[0], True)

if __name__ == '__main__':
    unittest.main()