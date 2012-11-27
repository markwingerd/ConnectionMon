import socket
from procfs import Proc #https://github.com/pmuller/procfs

class ConnectionMonitor:
    """"""

    def __init__(self):
        """Constructor"""
        self._proc = Proc()

    def show_connections(self):
        """"""
        conn = self._get_tcp()
        conn = self._get_nonblank_connections(conn)
        conn = self._clean_connections(conn)
        for item in conn:
            print '{:<23}{:<50}{:<30}{:<30}'.format(item['name'], item['domain'], item['rem_address'], item['local_address'])

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

    def _clean_connections(self, conn):
        """"""
        output = []
        for item in conn:
            domain, name = self._get_domain(item['rem_address'][0])
            output.append({
                'name': name,
                'domain': domain,
                'local_address': item['local_address'],
                'rem_address': item['rem_address']})
        return output

    def _get_domain(self, ip):
        """"""
        domain = ''
        try:
            domain = socket.gethostbyaddr(ip)[0]
            name, ext = domain.split('.')[-2:]
        except:
            domain = 'unknown'
            name = 'unknown'
        return domain, name


if __name__ == '__main__':
    monitor = ConnectionMonitor()
    monitor.show_connections()
