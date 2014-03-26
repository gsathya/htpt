#!/usr/bin/env python
# Ben Jones
# Georgia Tech
# Spring 2014
#
# htpt-socks.py: this file builds upon the work of Zavier Lagraula's
# PySocks code to create a SOCKS server for our HTTP circumvention tool
import socks

"""SOCKS 4 proxy server class.

Copyright (C) 2001  Xavier Lagraula
See COPYRIGHT.txt and GPL.txt for copyrights information.

Build upon the TCPServer class of the SocketServer module, the Socks4Proxy
class is an implementation of the SOCKS protocol, version 4.

This server uses one thread per connection request.

Known bugs:
- Some CONNECT request closed by the client are not detected and finish in an
  infinite loop of select always returning the "request" socket as ready to
  read even if there is nothing more to read on it. This situation is now
  detected and lead to a Closed_Connection exception.

Implementation choices:
- Protocol errors are handled by exceptions
- The function that creates a socket is responsible for its closing -> never
  close a socket passed in as a parameter, and always use a try/finally block
  after creating a socket to ensure correct closing of sockets.
"""

import SocketServer2
import time
import select
import thread
import IDENT_Client
import IPv4_Tools
import getopt
import os
import sys
import socket
import ConfigFile

__all__ = [
    'DEFAULT_OPTIONS',
    'SocksError',
    'Connection_Closed',
    'Bind_TimeOut_Expired',
    'Request_Error',
    'Client_Connection_Closed',
    'Remote_Connection_Closed',
    'Remote_Connection_Failed',
    'Remote_Connection_Failed_Invalid_Host',
    'Request_Failed',
    'Request_Failed_No_Identd',
    'Request_Failed_Ident_failed',
    'Request_Refused',
    'Request_Bad_Version',
    'Request_Unknown_Command',
    'Request_Unauthorized_Client',
    'Request_Invalid_Port',
    'Request_Invalid_Format',
    'ThreadingSocks4Proxy'
    ]

# Default server options.
# Options are stored in a dictionary.

DEFAULT_OPTIONS = {}
OPTION_TYPE = {}
# The interface on which the server listens for incoming SOCKS requests.
DEFAULT_OPTIONS['bind_address']         = '127.0.0.1'
# The port on which the server listens for incoming SOCKS requests.
DEFAULT_OPTIONS['bind_port']            = 10000
# Will the server use IDENT request to authenticate the user making a request?
DEFAULT_OPTIONS['use_ident']            = 0
# Maximum request size taken in consideration.
DEFAULT_OPTIONS['req_buf_size']         = 1024
# Data is forwarded between the client and the remote peer by blocks of max
# 'data_buf_size' bytes.
DEFAULT_OPTIONS['data_buf_size']        = 1500
# After this delay n seconds without any activity on a connection between the
# client and the remote peer, the connection is closed.
DEFAULT_OPTIONS['inactivity_timeout']   = 360
# The SOCKS proxy waits no more than this number of seconds for an incoming
# connection (BIND requests). It then rejects the client request.
DEFAULT_OPTIONS['bind_timeout']         = 120

DEFAULT_OPTIONS['send_port']         = 8000

SHORT_OPTIONS   = 'a:p:i:r:d:t:b:'
# The map trick is useful here as all options 
LONG_OPTIONS    = [
    'bind_address=',
    'bind_port=',
    'use_ident',
    'req_buf_size=',
    'data_buf_size=',
    'inactivity_timeout=',
    'bind_timeout='
    ]


DEFAULT_OPTIONS['configfile'] = ''
OPTION_TYPE['configfile'] = ['string']


# SOCKS 4 protocol constant values.
SOCKS_VERSION                   = 4

COMMAND_CONNECT                 = 1
COMMAND_BIND                    = 2
COMMANDS                        = [
    COMMAND_CONNECT,
    COMMAND_BIND
    ]

REQUEST_GRANTED                 = 90
REQUEST_REJECTED_FAILED         = 91
REQUEST_REJECTED_NO_IDENTD      = 92
REQUEST_REJECTED_IDENT_FAILED   = 93

# Sockets protocol constant values.
ERR_CONNECTION_RESET_BY_PEER    = 10054
ERR_CONNECTION_REFUSED          = 10061


# For debugging only.
def now():
    return time.ctime(time.time())


# Exception classes for the server
class SocksError(Exception): pass
class Connection_Closed(SocksError): pass
class Bind_TimeOut_Expired(SocksError): pass
class Request_Error(SocksError): pass

class Client_Connection_Closed(Connection_Closed): pass
class Remote_Connection_Closed(Connection_Closed): pass
class Remote_Connection_Failed(Connection_Closed): pass
class Remote_Connection_Failed_Invalid_Host(Remote_Connection_Failed): pass

class Request_Failed(Request_Error): pass
class Request_Failed_No_Identd(Request_Failed): pass
class Request_Failed_Ident_failed(Request_Failed): pass

class Request_Refused(Request_Error): pass
class Request_Bad_Version(Request_Refused): pass
class Request_Unknown_Command(Request_Refused): pass
class Request_Unauthorized_Client(Request_Refused): pass
class Request_Invalid_Port(Request_Refused): pass
class Request_Invalid_Format(Request_Refused): pass


# Server class
class ThreadingSocks4Proxy(SocketServer2.ThreadingTCPServer):
    """Threading SOCKS4 proxy class.

Note: this server maintains two lists of all CONNECTION and BIND requests being
handled. This is not really useful for now but may become in the future.
Moreover, it has been a good way to learn about the semaphores of the threading
module :)"""

    def __Decode_Command_Line(self, argv = [], definitions = {}, defaults = {}):
        result = {}
        line_opts, rest = getopt.getopt(argv, SHORT_OPTIONS, LONG_OPTIONS)

        for item in line_opts:
            opt, value = item

            # First trying "opt" value against options that use an argument.            
            if opt in ['-a', '--bind_adress']:
                opt = 'bind_adress'
            elif opt in ['-p', '--bind_port']:
                opt = 'bind_port'
            elif opt in ['-i', '--use_ident']:
                opt = 'use_ident'
                value = 1
            elif opt in ['-r', '--req_buf_size']:
                opt = 'req_buf_size'
            elif opt in ['-d', '--data_buf_size']:
                opt = 'data_buf_size'
            elif opt in ['-d', '--inactivity_timeout']:
                opt = 'inactivity_timeout'
            elif opt in ['-b', '--bind_timeout']:
                opt = 'bind_timeout'

            result[opt] = value

        return ConfigFile.evaluate(definitions, result, defaults)

    def __init__(self, RequestHandlerClass, *args):
        """Constructor of the server."""
        self.Options = DEFAULT_OPTIONS
        listenPort = args[0]
        if len(args) > 1:
            sendPort = args[1]
            self.Options['send_port'] = sendPort

        self.Options['bind_port'] = listenPort
        print "Server starting with following options:"
        for i in self.Options.keys(): print i, ':', self.Options[i]

        print 'The choosen ip adress is', DEFAULT_OPTIONS['bind_address']
        SocketServer2.ThreadingTCPServer.__init__(
            self,
            (self.Options['bind_address'], self.Options['bind_port']),
            RequestHandlerClass)

class ForwardSocksReq(SocketServer2.BaseRequestHandler):
    """This request handler class handles sOCKS 4 requests."""

    def handle(self):
        """This function is the main request handler function.

It delegates each step of the request processing to a different function and
handles raised exceptions in order to warn the client that its request has
been rejected (if needed).
The steps are:
- decode_request: reads the request and splits it into a dictionary. it checks
  if the request is well-formed (correct socks version, correct command number,
  well-formed port number.
- validate_request: checks if the current configuration accepts to handle the
  request (client identification, authorization rules)
- handle_connect: handles CONNECT requests
- handle_bind: handles BIND requests
"""

        print thread.get_ident(), '-'*40
        print thread.get_ident(), 'Request from ', self.client_address

        try:
            # Read and decode the request from the client and verify that it
            # is well-formed.
            req = self.decode_request()
            print thread.get_ident(), 'Decoded request:', req
            
            # We have some well-formed request to handle.
            # Let's validate it.
            self.validate_request(req)

            # We are here so the request is valid.
            # We must decide of the action to take according to the "command"
            # part of the request.
            if req['command'] == COMMAND_CONNECT:
                self.handle_connect(req)
            elif req['command'] == COMMAND_BIND:
                self.handle_bind(req)

        # Global SOCKS errors handling.
        except Request_Failed_No_Identd:
            self.answer_rejected(REQUEST_REJECTED_NO_IDENTD)
        except Request_Failed_Ident_failed:
            self.answer_rejected(REQUEST_REJECTED_IDENT_FAILED)
        except Request_Error:
            self.answer_rejected()
        except Remote_Connection_Failed:
            self.answer_rejected()
        except Bind_TimeOut_Expired:
            self.answer_rejected()
        # Once established, if the remote or the client connection is closed
        # we must exit silently. This exception is in fact the way the function
        # used to forward data between the client and the remote server tells
        # us it has finished working.
        except Connection_Closed:
            pass

    def validate_request(self, req):
        """This function validates the request against any validating rule.

Two things are taken in consideration:
- where does the request come from? (address check)
- who is requesting? (identity check)

Note: in fact, identity verification is disabled for now because ICQ does
stupid things such as always providing a "a" user that doesn't exists in bind
requests."""
        
        # Address check. As for now, only requests from non routable addresses
        # are accepted. This is because of security issues and will later be
        # configurable with a system of validating rules.
        if IPv4_Tools.is_routable(self.client_address[0]):
            raise Request_Unauthorized_Client(req)
        
        # If a user ID is provided, we must make an identd control. As for now,
        # we accept request without userid without control but this behaviour
        # will be changed when configurations options will be provided.
        if req['userid'] and self.server.Options['use_ident']:
           # We must get some information about the request socket to build
           # the identd request.
           local_ip, local_port         = self.request.getsockname()
           ident_srv_ip, ident_srv_port = self.request.getpeername()
           if (not IDENT_Client.check_IDENT(
               ident_srv_ip, ident_srv_port, local_port, req['userid'])):
               raise Request_Failed_Ident_failed(req)
        # If we managed to get here, then the request is valid.
            

    def decode_request(self):
        """This function reads the request socket for the request data, decodes
it and checks that it is well formed."""
        
        # reading the data from the socket.        
        data = self.request.recv(self.server.Options['req_buf_size'])

        # It is useless to process too short a request.
        if len(data) < 9: raise Request_Invalid_Format(data)
        
        # Extracting components of the request. Checks are made at each step.
        req = {}

        # SOCKS version of the request.
        req['version']  = ord(data[0])
        if req['version'] != SOCKS_VERSION:
            raise Request_Bad_Version(req)

        # Command used.
        req['command']  = ord(data[1])
        if not req['command'] in COMMANDS:
            raise Request_Unknown_Command(req)

        # Address of the remote peer.
        req['address']  = (
            socket.inet_ntoa(data[4:8]),
            self.string2port(data[2:4]))
        if not IPv4_Tools.is_port(req['address'][1]):
            raise Request_Invalid_Port(req)
        # Note: only the fact that the port is in [1, 65535] is checked here.
        # Address and port legitimity are later checked in validate_request.

        # Requester user ID. May not be provided.
        req['userid']   = self.get_string(data[8:])
        req['data'] = data

        # If we are here, then the request is well-formed. Let us return it to
        # the caller.
        return req


    def handle_connect(self, req):
        """This function handles a CONNECT request.

The actions taken are:
- create a new socket,
- register the connection into the server,
- connect to the remote host,
- tell the client the connection is established,
- forward data between the client and the remote peer."""
        
        # Create a socket to connect to the remote server
        print "Here- address: {}".format(req['address'])
#        remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote = socks.socksocket()
        remote.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        remote.setproxy(socks.PROXY_TYPE_SOCKS4, "localhost", self.server.Options['send_port'])

        # From now on, we must not forget to close this socket before leaving.
        try:
            try:
                # Connection to the remote server
                print thread.get_ident(), 'Connecting to', req['address']


                # Possible way to handle the timeout defined in the protocol!
                # Make the connect non-blocking, then do a select and keep
                # an eye on the writable socket, just as I did with the
                # accept() from BIND requests.
                # Do this tomorrow... Geez... 00:47... Do this this evening.
#                remote.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#                print "Trying to connect to server: {}".format(self.server.Options['send_port'])
#                remote.connect(("127.0.0.1",self.server.Options['send_port']))
                remote.connect(req['address'])
                print "Success!"
#                remote.send(req['data'])
                
            # The only connection that can be reset here is the one of the
            # client, so we don't need to answer. Any other socket
            # exception forces us to try to answer to the client.
            except socket.error as e:
                print e
                exception, value, traceback = sys.exc_info()
                if value[0] == ERR_CONNECTION_RESET_BY_PEER:
                    raise Client_Connection_Closed((ERR_CONNECTION_RESET_BY_PEER, socket.errorTab[ERR_CONNECTION_RESET_BY_PEER]))
                else:
                    raise Remote_Connection_Failed
            except:
                raise Remote_Connection_Failed
        
            # From now on we will already have answered to the client.
            # Any exception occuring now must make us exit silently.
            try:
                # Telling the client that the connection it asked for is
                # granted.
                self.answer_granted()
                # Starting to relay information between the two peers.
                self.forward(self.request, remote)
            # We don't have the right to "speak" to the client anymore.
            # So any socket failure means a "connection closed" and silent
            # exit.
            except socket.error:
                raise Connection_Closed
        # Mandatory closing of the remote socket.
        finally:
            remote.close()

    def answer_granted(self, dst_ip = '0.0.0.0', dst_port = 0):
        """This function sends a REQUEST_GRANTED answer to the client."""
        self.answer(REQUEST_GRANTED, dst_ip, dst_port)

    def answer_rejected(self, reason = REQUEST_REJECTED_FAILED, dst_ip = '0.0.0.0', dst_port = 0):
        """This function send a REQUEST_REJECTED answer to the client."""
        self.answer(reason, dst_ip, dst_port)

    def answer(self, code = REQUEST_GRANTED, ip_str = '0.0.0.0', port_int = 0):
        """This function sends an answer to the client. This has been
factorised because all answers follow the same format."""

        # Any problem occuring here means that we are unable to "speak" to
        # the client -> we must act as if the connection to it had already
        # been closed.
        try:
            ip      = socket.inet_aton(ip_str)
            port    = self.port2string(port_int)
            packet  = chr(0)        # Version number is 0 in answer
            packet += chr(code)     # Error code
            packet += port
            packet += ip
            print thread.get_ident(), 'Sending back:', code, self.string2port(port), socket.inet_ntoa(ip)
            self.request.send(packet)
        except:
            # Trying to keep a trace of the original exception.
            raise Client_Connection_Closed(sys.exc_info())

    def forward(self, client_sock, server_sock):
        """This function makes the forwarding of data by listening to two
sockets, and writing to one everything it reads on the other.

This is done using select(), in order to be able to listen on both sockets
simultaneously and to implement an inactivity timeout."""
        
        # Once we're here, we are not supposed to "speak" with the client
        # anymore. So any error means for us to close the connection.
        print thread.get_ident(), 'Forwarding.'
        # These are not used to anything significant now, but I keep them in
        # case I would want to do some statistics/logging.
        octets_in, octets_out = 0, 0
        try:
            try:
                # Here are the sockets we will be listening.
                sockslist = [client_sock, server_sock]
                while 1:
                    # Let us listen...
                    readables, writeables, exceptions = select.select(
                        sockslist, [], [],
                        self.server.Options['inactivity_timeout'])
                    # If the "exceptions" list is not empty or if we are here
                    # because of the timer (i.e. all lists are empty), then
                    # we must must bail out, we have finished our work.
                    if (exceptions
                        or (readables, writeables, exceptions) == ([], [], [])):
                        raise Connection_Closed

                    # Only a precaution.                    
                    data = ''

                    # Just in case we would be in the improbable case of data
                    # awaiting to be read on both sockets, we treat the
                    # "readables" list as if it oculd contain more than one
                    # element. Thus the "for" loop...
                    for readable_sock in readables:
                        # We know the socket we want to read of, but we still
                        # must find what is the other socket. This method
                        # builds a list containing one element.
                        writeableslist = [client_sock, server_sock]
                        writeableslist.remove(readable_sock)

                        # We read one chunk of data and then send it to the
                        # other socket
                        data = readable_sock.recv(
                            self.server.Options['data_buf_size'])
                        # We must handle the case where data=='' because of a
                        # bug: we sometimes end with an half-closed socket,
                        # i.e. a socket closed by the peer, on which one can
                        # always read, but where there is no data to read.
                        # This must be detected or it would lead to an infinite
                        # loop.
                        if data:
                            writeableslist[0].send(data)
                            # This is only for future logging/stats.
                            if readable_sock == client_sock:
                                octets_out += len(data)
                            else:
                                octets_in += len(data)
                        else:
                            # The sock is readable but nothing can be read.
                            # This means a poorly detected connection close.
                            raise Connection_Closed
            # If one peer closes its conenction, we have finished our work.
            except socket.error:
                exception, value, traceback = sys.exc_info()
                if value[0] == ERR_CONNECTION_RESET_BY_PEER:
                    raise Connection_Closed
                raise
        finally:
            print thread.get_ident(), octets_in, 'octets in and', octets_out, 'octets out. Connection closed.'


    def string2port(self, port_str):
        """This function converts between a packed (16 bits) port number to an
integer."""
        return (ord(port_str[0]) << 8) + ord(port_str[1])

    def port2string(self, port):
        """This function converts a port number (16 bits integer) into a packed
string (2 chars)."""
        return chr((port & 0xff00) >> 8)+ chr(port & 0x00ff)

    def get_string(self, nullterminated):
        """This function converts a null terminated string stored in a Python
string to a "normal Python string."""
        return nullterminated[0: nullterminated.index(chr(0))]

class ReceiveSocksReq(SocketServer2.BaseRequestHandler):
    """This request handler class handles sOCKS 4 requests."""

    def handle(self):
        """This function is the main request handler function.

It delegates each step of the request processing to a different function and
handles raised exceptions in order to warn the client that its request has
been rejected (if needed).
The steps are:
- decode_request: reads the request and splits it into a dictionary. it checks
  if the request is well-formed (correct socks version, correct command number,
  well-formed port number.
- validate_request: checks if the current configuration accepts to handle the
  request (client identification, authorization rules)
- handle_connect: handles CONNECT requests
- handle_bind: handles BIND requests
"""

        print thread.get_ident(), '-'*40
        print thread.get_ident(), 'Request from ', self.client_address

        try:
            # Read and decode the request from the client and verify that it
            # is well-formed.
            req = self.decode_request()
            print thread.get_ident(), 'Decoded request:', req
            
            # We have some well-formed request to handle.
            # Let's validate it.
            self.validate_request(req)

            # We are here so the request is valid.
            # We must decide of the action to take according to the "command"
            # part of the request.
            if req['command'] == COMMAND_CONNECT:
                self.handle_connect(req)
            elif req['command'] == COMMAND_BIND:
                self.handle_bind(req)

        # Global SOCKS errors handling.
        except Request_Failed_No_Identd:
            self.answer_rejected(REQUEST_REJECTED_NO_IDENTD)
        except Request_Failed_Ident_failed:
            self.answer_rejected(REQUEST_REJECTED_IDENT_FAILED)
        except Request_Error:
            self.answer_rejected()
        except Remote_Connection_Failed:
            self.answer_rejected()
        except Bind_TimeOut_Expired:
            self.answer_rejected()
        # Once established, if the remote or the client connection is closed
        # we must exit silently. This exception is in fact the way the function
        # used to forward data between the client and the remote server tells
        # us it has finished working.
        except Connection_Closed:
            pass

    def validate_request(self, req):
        """This function validates the request against any validating rule.

Two things are taken in consideration:
- where does the request come from? (address check)
- who is requesting? (identity check)

Note: in fact, identity verification is disabled for now because ICQ does
stupid things such as always providing a "a" user that doesn't exists in bind
requests."""
        
        # Address check. As for now, only requests from non routable addresses
        # are accepted. This is because of security issues and will later be
        # configurable with a system of validating rules.
        if IPv4_Tools.is_routable(self.client_address[0]):
            raise Request_Unauthorized_Client(req)
        
        # If a user ID is provided, we must make an identd control. As for now,
        # we accept request without userid without control but this behaviour
        # will be changed when configurations options will be provided.
        if req['userid'] and self.server.Options['use_ident']:
           # We must get some information about the request socket to build
           # the identd request.
           local_ip, local_port         = self.request.getsockname()
           ident_srv_ip, ident_srv_port = self.request.getpeername()
           if (not IDENT_Client.check_IDENT(
               ident_srv_ip, ident_srv_port, local_port, req['userid'])):
               raise Request_Failed_Ident_failed(req)
        # If we managed to get here, then the request is valid.
            

    def decode_request(self):
        """This function reads the request socket for the request data, decodes
it and checks that it is well formed."""
        
        # reading the data from the socket.        
        data = self.request.recv(self.server.Options['req_buf_size'])

        # It is useless to process too short a request.
        if len(data) < 9: raise Request_Invalid_Format(data)
        
        # Extracting components of the request. Checks are made at each step.
        req = {}

        # SOCKS version of the request.
        req['version']  = ord(data[0])
        if req['version'] != SOCKS_VERSION:
            raise Request_Bad_Version(req)

        # Command used.
        req['command']  = ord(data[1])
        if not req['command'] in COMMANDS:
            raise Request_Unknown_Command(req)

        # Address of the remote peer.
        req['address']  = (
            socket.inet_ntoa(data[4:8]),
            self.string2port(data[2:4]))
        if not IPv4_Tools.is_port(req['address'][1]):
            raise Request_Invalid_Port(req)
        # Note: only the fact that the port is in [1, 65535] is checked here.
        # Address and port legitimity are later checked in validate_request.

        # Requester user ID. May not be provided.
        req['userid']   = self.get_string(data[8:])

        # If we are here, then the request is well-formed. Let us return it to
        # the caller.
        return req


    def handle_bind(self, req):
        """This function handles a BIND request.

The actions taken are:
- create a new socket,
- bind it to the external ip chosen on init of the server,
- listen for a connection on this socket,
- register the bind into the server,
- tell the client the bind is ready,
- accept an incoming connection,
- tell the client the connection is established,
- forward data between the client and the remote peer."""
        
        # Create a socket to receive incoming connection.
        remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # From now on, whatever we do, we must close the "remote" socket before
        # leaving. I love try/finally blocks.
        try:
            # In this block, the only open connection is the client one, so a
            # ERR_CONNECTION_RESET_BY_PEER exception means "exit silently
            # because you won't be able to send me anything anyway".
            # Any other exception must interrupt processing and exit from here.
            try:
                # Binding the new socket to the chosen external ip
                remote.bind((self.server.external_ip, 0))
                remote.listen(1)

                # Collecting information about the socket to store it in the
                # "waiting binds" list.
                socket_ip, socket_port = remote.getsockname()
            except socket.error:
                # A "connection reset by peer" here means the client has closed
                # the connection.
                exception, value, traceback = sys.exc_info()
                if value[0] == ERR_CONNECTION_RESET_BY_PEER:
                    raise Client_Connection_Closed((ERR_CONNECTION_RESET_BY_PEER, socket.errorTab[ERR_CONNECTION_RESET_BY_PEER]))
                else:
                    # We may be able to make a more precise diagnostic, but
                    # in fact, it doesn't seem useful here for now.
                    raise Remote_Connection_Failed

            # Sending first answer meaning request is accepted and socket
            # is waiting for incoming connection.
            self.answer_granted(socket_ip, socket_port)

            try:
                # Waiting for incoming connection. I use a select here to
                # implement the timeout stuff.
                read_sock, junk, exception_sock = select.select(
                    [remote], [], [remote],
                    self.server.Options['bind_timeout'])
                # If all lists are empty, then the select has ended because
                # of the timer.
                if (read_sock, junk, exception_sock) == ([], [], []):
                    raise Bind_TimeOut_Expired
                # We also drop the connection if an exception condition is
                # detected on the socket. We must also warn the client that
                # its request is rejecte (remember that for a bind, the client
                # expects TWO answers from the proxy).
                if exception_sock:
                    raise Remote_Connection_Failed

                # An incoming connection is pending. Let us accept it
                incoming, peer = remote.accept()
            except:
                # We try to keep a trace of the previous exception
                # for debugging purpose.
                raise Remote_Connection_Failed(sys.exc_info())

            # From now on , we must not forget to close this connection.
            try:
                # We must now check that the incoming connection is from
                # the expected server.
                if peer[0] != req['address'][0]:
                    raise Remote_Connection_Failed_Invalid_Host

                # We can now tell the client the connection is OK, and
                # start the forwarding process.
                self.answer_granted()
                self.forward(self.request, incoming)
            # Mandatory closing of the socket with the remote peer.
            finally:
                incoming.close()

        # Mandatory closing ofthe listening socket
        finally:
            remote.close()


    def handle_connect(self, req):
        """This function handles a CONNECT request.

The actions taken are:
- create a new socket,
- register the connection into the server,
- connect to the remote host,
- tell the client the connection is established,
- forward data between the client and the remote peer."""
        
        # Create a socket to connect to the remote server
        remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # From now on, we must not forget to close this socket before leaving.
        try:
            try:
                # Connection to the remote server
                print thread.get_ident(), 'Connecting to', req['address']


                # Possible way to handle the timeout defined in the protocol!
                # Make the connect non-blocking, then do a select and keep
                # an eye on the writable socket, just as I did with the
                # accept() from BIND requests.
                # Do this tomorrow... Geez... 00:47... Do this this evening.
                
                remote.connect(req['address'])
                
            # The only connection that can be reset here is the one of the
            # client, so we don't need to answer. Any other socket
            # exception forces us to try to answer to the client.
            except socket.error:
                exception, value, traceback = sys.exc_info()
                if value[0] == ERR_CONNECTION_RESET_BY_PEER:
                    raise Client_Connection_Closed((ERR_CONNECTION_RESET_BY_PEER, socket.errorTab[ERR_CONNECTION_RESET_BY_PEER]))
                else:
                    raise Remote_Connection_Failed
            except:
                raise Remote_Connection_Failed
        
            # From now on we will already have answered to the client.
            # Any exception occuring now must make us exit silently.
            try:
                # Telling the client that the connection it asked for is
                # granted.
                self.answer_granted()
                # Starting to relay information between the two peers.
                self.forward(self.request, remote)
            # We don't have the right to "speak" to the client anymore.
            # So any socket failure means a "connection closed" and silent
            # exit.
            except socket.error:
                raise Connection_Closed
        # Mandatory closing of the remote socket.
        finally:
            remote.close()

    def answer_granted(self, dst_ip = '0.0.0.0', dst_port = 0):
        """This function sends a REQUEST_GRANTED answer to the client."""
        self.answer(REQUEST_GRANTED, dst_ip, dst_port)

    def answer_rejected(self, reason = REQUEST_REJECTED_FAILED, dst_ip = '0.0.0.0', dst_port = 0):
        """This function send a REQUEST_REJECTED answer to the client."""
        self.answer(reason, dst_ip, dst_port)

    def answer(self, code = REQUEST_GRANTED, ip_str = '0.0.0.0', port_int = 0):
        """This function sends an answer to the client. This has been
factorised because all answers follow the same format."""

        # Any problem occuring here means that we are unable to "speak" to
        # the client -> we must act as if the connection to it had already
        # been closed.
        try:
            ip      = socket.inet_aton(ip_str)
            port    = self.port2string(port_int)
            packet  = chr(0)        # Version number is 0 in answer
            packet += chr(code)     # Error code
            packet += port
            packet += ip
            print thread.get_ident(), 'Sending back:', code, self.string2port(port), socket.inet_ntoa(ip)
            self.request.send(packet)
        except:
            # Trying to keep a trace of the original exception.
            raise Client_Connection_Closed(sys.exc_info())

    def forward(self, client_sock, server_sock):
        """This function makes the forwarding of data by listening to two
sockets, and writing to one everything it reads on the other.

This is done using select(), in order to be able to listen on both sockets
simultaneously and to implement an inactivity timeout."""
        
        # Once we're here, we are not supposed to "speak" with the client
        # anymore. So any error means for us to close the connection.
        print thread.get_ident(), 'Forwarding.'
        # These are not used to anything significant now, but I keep them in
        # case I would want to do some statistics/logging.
        octets_in, octets_out = 0, 0
        try:
            try:
                # Here are the sockets we will be listening.
                sockslist = [client_sock, server_sock]
                while 1:
                    # Let us listen...
                    readables, writeables, exceptions = select.select(
                        sockslist, [], [],
                        self.server.Options['inactivity_timeout'])
                    # If the "exceptions" list is not empty or if we are here
                    # because of the timer (i.e. all lists are empty), then
                    # we must must bail out, we have finished our work.
                    if (exceptions
                        or (readables, writeables, exceptions) == ([], [], [])):
                        raise Connection_Closed

                    # Only a precaution.                    
                    data = ''

                    # Just in case we would be in the improbable case of data
                    # awaiting to be read on both sockets, we treat the
                    # "readables" list as if it oculd contain more than one
                    # element. Thus the "for" loop...
                    for readable_sock in readables:
                        # We know the socket we want to read of, but we still
                        # must find what is the other socket. This method
                        # builds a list containing one element.
                        writeableslist = [client_sock, server_sock]
                        writeableslist.remove(readable_sock)

                        # We read one chunk of data and then send it to the
                        # other socket
                        data = readable_sock.recv(
                            self.server.Options['data_buf_size'])
                        # We must handle the case where data=='' because of a
                        # bug: we sometimes end with an half-closed socket,
                        # i.e. a socket closed by the peer, on which one can
                        # always read, but where there is no data to read.
                        # This must be detected or it would lead to an infinite
                        # loop.
                        if data:
                            writeableslist[0].send(data)
                            # This is only for future logging/stats.
                            if readable_sock == client_sock:
                                octets_out += len(data)
                            else:
                                octets_in += len(data)
                        else:
                            # The sock is readable but nothing can be read.
                            # This means a poorly detected connection close.
                            raise Connection_Closed
            # If one peer closes its conenction, we have finished our work.
            except socket.error:
                exception, value, traceback = sys.exc_info()
                if value[0] == ERR_CONNECTION_RESET_BY_PEER:
                    raise Connection_Closed
                raise
        finally:
            print thread.get_ident(), octets_in, 'octets in and', octets_out, 'octets out. Connection closed.'


    def string2port(self, port_str):
        """This function converts between a packed (16 bits) port number to an
integer."""
        return (ord(port_str[0]) << 8) + ord(port_str[1])

    def port2string(self, port):
        """This function converts a port number (16 bits integer) into a packed
string (2 chars)."""
        return chr((port & 0xff00) >> 8)+ chr(port & 0x00ff)

    def get_string(self, nullterminated):
        """This function converts a null terminated string stored in a Python
string to a "normal Python string."""
        return nullterminated[0: nullterminated.index(chr(0))]


if __name__ == "__main__":
    server = ThreadingSocks4Proxy(ReceiveSocksReq, sys.argv[1:])
    server.serve_forever()
