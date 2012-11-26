from procfs import Proc #https://github.com/pmuller/procfs

class ConnectionMonitor:
    """"""

    def __init__(self):
        """Constructor"""
        self._proc = Proc()

    def _get_tcp(self):
        """Retrieves a list of connections and quits on error."""
        output = []
        try:
            for item in self._proc.net.tcp:
                output.append(item)
        except TypeError:
            # This will silently crash by design.
            # Nov 8th 2012: procfs will throw a type error when there are no
            # more sockets to display.
            pass
        return output

    def _get_nonblank_connections(self, conn):
        """Returns any connection that doesn't have 0.0.0.0 in its 
        rem_address"""
        conn = [item for item in conn if item['rem_address'][0] != '0.0.0.0']
        return conn


if __name__ == '__main__':
    monitor = ConnectionMonitor()
    conn = monitor._get_tcp()
    print conn
    conn = monitor._get_nonblank_connections(conn)
    print conn
