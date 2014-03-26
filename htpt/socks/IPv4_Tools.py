"""IPv4_Tools - IPv4 helper functions module written in Python

Copyright (C) 2001  Xavier Lagraula
See COPYRIGHT.txt and GPL.txt for copyrights information.

This module provides a small set of classes and short functions to ease for
IPv4 protocols handling:
- is_routable: checks whether an IP address is routable or not (RFC 1918).
- is_port: checks whether an integer is a valid port number (1-65535)
"""
    
def is_routable(address):
    """def is_routable(address)

This function returns if a given IPv4 address is routable or not.
Parameters:
- address: IPv4 address - string - format: aaa.bbb.ccc.ddd
Return value:
- 0: address is not routable
- 1: address is routable

Routable addresses are defined as not pertaining to the following:
127.0.0.0       -   127.255.255.255 (127/8 prefix)
10.0.0.0        -   10.255.255.255  (10/8 prefix)
172.16.0.0      -   172.31.255.255  (172.16/12 prefix)
192.168.0.0     -   192.168.255.255 (192.168/16 prefix)"""

    # Splitting the address in its 4 components.
    first, second, junk1, junk2 = address.split('.')
    # Testing the address against the given intervals.
    if (first in ['10', '127']
        or (first == '172' and second >= '16' and second <= '31')
        or ((first, second) == ('192', '168'))):
        return 0
    return 1

def is_port(port):
    """def is_port(port)

This functions returns if a given port is valid or not.
Parameters:
- port: integer
Return value:
- 0: port is a valid port
- 1: port is not a valid port

Valid ports are defined as in the interval 1-65535."""
    return (port > 0) and (port < 65536)


