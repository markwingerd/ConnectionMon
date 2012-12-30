import socket
import time
import sched, time
import curses
from procfs import Proc #https://github.com/pmuller/procfs

def timeit(method):

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print '{:2.2f} sec - {:25} - {:100} - {:5} - {:100}'.format(te-ts, method.__name__, result, kw, args)
        return result

    return timed


class ConnectionMonitor:
    """"""

    def __init__(self):
        """Constructor"""
        self._proc = Proc()
        self.connections = {}
        self._dnd = {} # Domain Name Dictionary
        # Curses management
        self.screen = curses.initscr()
        self.screen_width = 80
        self.screen_height = 20

    @timeit
    def update(self):
        """This method will add any new connections to the self.connections
        attribute, update variables to self.connections, and call the display
        method."""
        #Add connections to list and Set open connections to active
        self.update_active_connections()
        #Inactivate connections that just closed
        self.update_inactivate_connections()
        self.show_connections()

    def update_active_connections(self):
        """Adds any new connections listed in the conn argument or
        updates the attributes of any currently active connections."""
        def get_elapsed_time(t):
            return time.time() - t
        def reset_time(tmp):
            """Used to reset the timer if this item has been
            reactivated on this check"""
            if  not tmp['is_active']:
                #hotfix for inaccurate times. This connection just went active.
                tmp['time_established'] = get_elapsed_time(tmp['time_connected'])
            return tmp

        for item in self._get_tcp():
            if item['rem_address'] not in self.connections:
                # Add new connection.
                item['is_active'] = True
                self.connections[item['rem_address']] = item
            else:
                # Update known connection.
                tmp = self.connections[item['rem_address']]
                tmp = reset_time(tmp)
                tmp['time_connected'] = get_elapsed_time(tmp['time_established'])
                tmp['is_active'] = True
                self.connections[item['rem_address']] = tmp

    def update_inactivate_connections(self):
        """"""
        active = []
        for item in self._get_tcp():
            active.append(item['rem_address'])
        for item in self.connections.values():
            if item['rem_address'] not in active:
                item['is_active'] = False

    def show_connections(self):
        """"""
        conn = self.connections
        output = '      {:<15.15} {:>10.10} {:<40.40} {:<5.5} {:<15.15} {:<15.15}'.format('NAME', 'TIME', 'DOMAIN', 'LAYER', 'REMOTE ADDRESS', 'LOCAL ADDRESS')
        self.screen.addstr(0,0,output)
        for i, item in enumerate(conn.values()):
            if self.screen.enclose(i+2,0):
                output = '{:<5.5} {:<15.15} {:>10.2f} {:<40.40} {:<5.5} {:<15.15} {:<15.15}'.format(str(item['is_active']), item['name'], item['time_connected'], item['domain'], item['transport_layer'], item['rem_address'], item['local_address'])
                self.screen.addstr(i+1,0,output)
        self.screen.refresh()

    def auto_show_connections(self, sc):
        """"""
        self.update()
        sc.enter(5, 1, self.auto_show_connections, (sc,))

    def _get_tcp(self):
        """Retrieves a list of connections and quits on error.
        - This should be called as few times as possible. Currently 
        called two times. Work on reducing that to one."""
        output = []
        try:
            for item in self._proc.net.tcp:
                output.append(item)
        except TypeError:
            # This will silently crash by design.
            # Nov 8th 2012: procfs will throw a type error when there are no
            # more sockets to return.
            pass
        finally:
            output = self._remove_blank_connections(output)
            output = self._clean_connections(output, 'tcp')
        return output

    def _remove_blank_connections(self, conn):
        """Returns any connection that doesn't have 0.0.0.0 in its 
        rem_address"""
        conn = [item for item in conn if item['rem_address'][0] != '0.0.0.0']
        return conn

    def _clean_connections(self, conn, type):
        """"""
        output = []
        for item in conn:
            domain, name = self._get_domain(item['rem_address'][0])
            output.append({
                'name': name,
                'domain': domain,
                'transport_layer': type,
                'local_address': item['local_address'][0],
                'local_port': item['local_address'][1],
                'rem_address': item['rem_address'][0],
                'rem_port': item['rem_address'][1],
                'time_established': time.time(),
                'time_connected': 0})
        return output

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
    
    s = sched.scheduler(time.time, time.sleep)
    try:
        s.enter(1, 1, monitor.auto_show_connections, (s,))
        s.run()
    except KeyboardInterrupt:
        # Catches when Ctrl-C is pressed.
        print '\nExited'
    finally:
        curses.endwin()