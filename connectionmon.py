from procfs import Proc #https://github.com/pmuller/procfs

class ConnectionMonitor:
    """"""

    def __init__(self):
        """Constructor"""
        self._proc = Proc()
        self.raw_proc = ()
        self.connections = ()

    def get_connections(self):
        """Uses procfs to get information on active sockets."""
        try:
            for sock in self._proc.net.tcp:
                # Remove entries with null ip addresses.
                if sock['rem_address'][0] != '0.0.0.0':
                    self.raw_proc += (sock,)
                    self.connections += (self._clean_connection(sock),)
        except TypeError:
            # This will silently crash by design.
            # Nov 8th 2012: procfs will throw a type error when there are no
            # more sockets to display.
            pass

    def _clean_connection(self,sock):
        """Returns only useful data from a socket entry."""
        return {'local_address': sock['local_address'],
                'rem_address': sock['rem_address']}


if __name__ == '__main__':
    monitor = ConnectionMonitor()

    monitor.get_connections()

    for item in monitor.connections:
        print item
