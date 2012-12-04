import socket
import time
from procfs import Proc #https://github.com/pmuller/procfs

def timeit(method):

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        #print '{:2.2f} sec - {:25} - {:100} - {:5} - {:100}'.format(te-ts, method.__name__, result, kw, args)
        return result

    return timed


class ConnectionMonitor:
    """"""

    def __init__(self):
        """Constructor"""
        self._proc = Proc()
        self._dnd = {} # Domain Name Dictionary

    @timeit
    def show_connections(self):
        """"""
        raw = self._get_tcp()
        raw = self._get_nonblank_connections(raw)
        conn = self._clean_connections(raw, 'tcp')
        for item in conn:
            print '{:<23}{:<50}{:<5}{:<30}{:<30}'.format(item['name'], item['domain'], item['transport_layer'], item['rem_address'], item['local_address'])

    @timeit
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

    @timeit
    def _get_nonblank_connections(self, conn):
        """Returns any connection that doesn't have 0.0.0.0 in its 
        rem_address"""
        conn = [item for item in conn if item['rem_address'][0] != '0.0.0.0']
        return conn

    @timeit
    def _clean_connections(self, conn, type):
        """"""
        output = []
        for item in conn:
            domain, name = self._get_domain(item['rem_address'][0])
            output.append({
                'name': name,
                'domain': domain,
                'transport_layer': type,
                'local_address': item['local_address'],
                'rem_address': item['rem_address']})
        return output

    @timeit
    def _get_domain(self, ip):
        """"""
        domain = ''
        if ip in self._dnd:
            domain = self._dnd[ip]
            name, ext = domain.split('.')[-2:]
        else:
            try:
                domain = socket.gethostbyaddr(ip)[0]
                name, ext = domain.split('.')[-2:]
                self._dnd[ip] = domain
            except:
                domain = 'unknown.na'
                name = 'unknown'
                self._dnd[ip] = domain
        return domain, name


if __name__ == '__main__':
    monitor = ConnectionMonitor()
    monitor.show_connections()
    #print monitor._proc.net.udp
