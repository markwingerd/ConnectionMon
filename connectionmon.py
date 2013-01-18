#!/usr/bin/env python
# connectionmon.py - Views your network connections.
# Copyright (C) 2013 Mark Wingerd <markwingerd@yahoo.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Views your network connections."""

__author__ = 'Mark Wingerd'
__email__ = 'markwingerd@yahoo.com'
__version__ = '0.1.1a1'
__copyright__ = 'Copyright (C) 2013 Mark Wingerd'
__license__ = 'GPLv3'
__maintainer__ = 'Mark Wingerd'
__credits__ = ['Wingerd']

import socket
import time
import sched
import time
import curses
import os
import sys
import argparse
from procfs import Proc #https://github.com/pmuller/procfs

def timeit(method):
    """Decorator for timing functions."""
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        # Longer display
        #print '{:2.2f} sec - {:25} - {:100} - {:5} - {:100}'.format(
        #    te-ts,  method.__name__, result, kw, args)

        # Shorter display
        print '{:2.2f} sec - {:25}'.format(te-ts, method.__name__)
        return result
    return timed


class ConnectionViewer:
    """Displays connections from ConnectionMonitor."""
    def __init__(self):
        self.monitor = ConnectionMonitor()
        # Curses management
        self.screen = curses.initscr()
        self.screen_width = 80
        self.screen_height = 20

    def display_once(self):
        """Displays the connections once."""
        self.monitor.update()
        sorted_conn = sorted(self.monitor.connections, cmp=self._comparator)
        self._show(sorted_conn)

    def display_repeatedly(self, sch, delay=15, priority=1):
        """Displays the connections repeatedly by calling 
        display_once repeatedly with sched."""
        self.display_once()
        sch.enter(delay, priority, self.display_repeatedly, 
                  (sch,delay, priority))

    def _show(self, conn):
        """Output to terminal using curses screen."""
        # Displays column titles
        output = ('      {:<15.15} {:>10.10} {:<40.40} {:<5.5} {:<15.15} '
                '{:<15.15}').format('NAME', 'TIME', 'DOMAIN', 'LAYER', 
                                    'REMOTE ADDRESS', 'LOCAL ADDRESS')
        self.screen.addstr(0,0,output)

        # Writes every line in conn
        for i, item in enumerate(conn):
            # Prints only if there is enough screen space. Leaves 2 lines of
            # extra space.
            if self.screen.enclose(i+2,0):
                output = ('{:<5.5} {:<15.15} {:>10.2f} {:<40.40} {:<5.5} '
                          '{:<15.15} {:<15.15}').format(str(item['is_active']), 
                                item['name'], item['time_connected'], 
                                item['domain'], item['transport_layer'], 
                                item['rem_address'], item['local_address'])
                self.screen.addstr(i+1,0,output)
        self.screen.refresh()

    def _comparator(self, a, b):
        """Used by sorted which compares two given dictionaries in a 
        list."""
        def compare_two(c, d, direction='asc'):
            if direction == 'desc':
                c, d = d, c
            if c < d:
                return -1
            elif c > d:
                return 1
            else:
                return 0
        
        cmp_active = compare_two(a['is_active'], b['is_active'], 'desc')
        if cmp_active:
            return cmp_active
        cmp_name = compare_two(a['name'], b['name'])
        if cmp_name:
            return cmp_name
        return compare_two(a['time_connected'], b['time_connected'])


class ConnectionMonitor:
    """Gets and stores connection data."""
    def __init__(self):
        self._proc = Proc()
        self.connections = [] # List of dictionaries
        self._dnd = {} # Domain Name Dictionary

    def update(self):
        """This method will add any new connections to the self.connections
        attribute, update variables to self.connections."""
        conn = self._get_tcp()
        self.update_active_connections(conn)
        self.update_inactivate_connections(conn)

    def update_active_connections(self, conn):
        """Adds any new connections listed in the conn argument or
        updates the attributes of any currently known active connections."""
        def get_elapsed_time(start_time):
            return time.time() - start_time
        def reset_time(tmp):
            """Modifies time_connected cell in the tmp dictionary."""
            # If this item is being reactivated, reset the timer
            if not tmp['is_active']:
                #hotfix for inaccurate times. This connection just went active.
                tmp['time_est'] = get_elapsed_time(tmp['time_connected'])
            return tmp
        def get_item_index(conn, rem_address):
            """Returns the index of a dictionary in the list based on
            the rem_address."""
            for i, item in enumerate(conn):
                if rem_address == item['rem_address']:
                    return i
            return 'ERROR' #This should not happen. Fix if it does.

        # List of all remote addresses collected to compare to current remote
        # addresses.
        rem_list = self._get_value_list(self.connections, 'rem_address')
        for item in conn:
            if item['rem_address'] not in rem_list:
                # Add new connection. Line order is important here.
                item['is_active'] = True
                self.connections.append(item)
                rem_list.append(item['rem_address'])
            else:
                # Update known connection. Line order is important here.
                index = get_item_index(self.connections, item['rem_address'])
                tmp = self.connections[index]

                tmp = reset_time(tmp)
                tmp['time_connected'] = get_elapsed_time(tmp['time_est'])
                tmp['is_active'] = True

                self.connections[index] = tmp

    def update_inactivate_connections(self, conn):
        """Scans all known connections and if any are not in the list of 
        current connections, their is_active cell will be set to False."""
        active_list = self._get_value_list(conn, 'rem_address')
        for item in self.connections:
            if item['rem_address'] not in active_list:
                item['is_active'] = False

    def _get_value_list(self, conn, key):
        """Returns a list of values when given the dictionaries
        key."""
        output = []
        for item in conn:
            output.append(item[key])
        return output

    def _get_tcp(self):
        """Retrieves a list of connections and quits on error.
        Returns a list of dictionaries which are the current connections found
        on the network.
        - This should be called as few times as possible."""
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
        return [item for item in conn if item['rem_address'][0] != '0.0.0.0']

    def _clean_connections(self, conn, type):
        """Takes the raw connections found on the network and collects all the
        useful information needed to output."""
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
                'time_est': time.time(),
                'time_connected': 0})
        return output

    def _get_domain(self, ip):
        """Uses the ip address to get the domain name. When a new ip is given
        it will add it and its domain information to the _dnd dictionary so
        few calls to gethostbyaddr are needed."""
        
        # If the domain has already been found
        if ip in self._dnd:
            domain = self._dnd[ip]
            name, ext = domain.split('.')[-2:]
        # If the domain is currently unknown.
        else:
            try:
                domain = socket.gethostbyaddr(ip)[0]
                name, ext = domain.split('.')[-2:]
                self._dnd[ip] = domain
            # gethostbyaddr could not find a name.
            except:
                domain = 'unknown.na'
                name = 'unknown'
                self._dnd[ip] = domain
        return domain, name


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Display network connections.')
    parser.add_argument('-i', '--interval', type=int, 
                        help='time between updates')
    args = parser.parse_args()

    viewer = ConnectionViewer()
    sch = sched.scheduler(time.time, time.sleep)
    try:
        sch.enter(1, 1, viewer.display_repeatedly, (sch, args.interval))
        sch.run()
    except KeyboardInterrupt:
        # Catches when Ctrl-C is pressed.
        print '\nExited'
    finally:
        curses.endwin()

    """
    viewer = ConnectionViewer()
    viewer.display_once()
    time.sleep(5)
    curses.endwin()
    """