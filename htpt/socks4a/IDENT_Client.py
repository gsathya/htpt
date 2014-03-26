"""IDENT_Client - IDENT protocol client module written in Python

Copyright (C) 2001  Xavier Lagraula
See COPYRIGHT.txt and GPL.txt for copyrights information.
"""
# Implementation of an ident client. Should take the form of a standalone function that
# connects to the given server on port 113, send the request, compares the answer to
# the given user, and validates it.
# It sends errors back as exceptions, answers as a tuple (sopsysfield, userid) if the user
# is identical to the one given in the request, and () if it is not.


import socket
from select import select
import IPv4_Tools

ANSWER_MAX_SIZE = 1000
USERID_MAX_SIZE = 512
EOL = chr(15) + chr(12)

class IDENT_Error(Exception): pass
class IDENT_Invalid_Port(IDENT_Error): pass
class IDENT_No_User(IDENT_Error): pass
class IDENT_Hidden_User(IDENT_Error): pass
ErrorClasses = {}
ErrorClasses['INVALID-PORT']    = IDENT_Invalid_Port
ErrorClasses['NO-USER']         = IDENT_No_User
ErrorClasses['HIDDEN-USER']     = IDENT_Hidden_User
ErrorClasses['UNKNOWN-ERROR']   = IDENT_Error

def build_IDENT_request(srv_port, client_port, userid):
    """def build_IDENT_request(srv_port, client_port, userid)

This function returns a well-formed IDENT request.

Parameters:
- srv_port: server port (integer)
- client_port: client port (integer)
- userid: user identification (string)

Return value:
- a non-empty string: the IDENT request, ready to be sent to an IDENT server
- exception IDENT_Invalid_Port: one of the provided port is not a valid IPv4
    port number"""

    if not IPv4_Tools.is_port(srv_port) or not IPv4_Tools.is_port(client_port):
        raise IDENT_Invalid_Port
    return '%u,%u%s' % (srv_port, client_port, EOL)

def check_IDENT(server_address, conn_srv_port, conn_client_port, userid, server_port = 113):
    """def check_IDENT(server_address, conn_srv_port, conn_client_port, userid)

This function send a request to an IDENT server in order to ask for information
about a specific connection.

Parameters:
- server_adress: IPv4 address of the IDENT server (string, 4-dots notation)
- conn_srv_port: connection server port
- conn_client_port: connection client port
- userid: username of the owner of the connection
- server_port (optional): IDENT port on the IDENT server, defaults to 113

Return values:
- (): the real owner of the connection is not the one provided or the
    connection does not exist
- (<opsys-field>, <userid>): the connection exists, and is owned by the correct
    user. <opsys-field> and <userid> are the values returned in answer from
    the IDENT server
- exceptions IDENT_Error, IDENT_Invalid_Port, IDENT_No_User, IDENT_Hidden_User:
    the server answered with an error ('UNKNOWN-ERROR', 'INVALID-PORT',
    'NO-USER', 'HIDDEN-USER' respectively) or the socket with the IDENT
    server entered an exception state (IDENT_Error case)"""

    # Building the IDENT request from the parameters.    
    request = build_IDENT_request(conn_srv_port, conn_client_port, userid)

    # Creating a socket to connect to the server.
    ident_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Connecting to the server.
        ident_sock.connect((server_address, server_port))

        # Sending the request.
        ident_sock.send(request)

        # Awaiting for the answer.
        readable, writeable, exception = select([ident_sock], [], [ident_sock], 30)
        if exception:
            # Well, this situation is not a true IDENT error returned by the
            # server, but how else could I handle it?
            raise IDENT_Error

        # Reading the answer from the server.
        answer = readable[0].recv(ANSWER_MAX_SIZE)
        ports, answer_type, data = answer.split(':', 2)

        # If the server tells us aboutt an error, raise the corresponding
        # exception.
        if answer_type == 'ERROR':
            if data in ErrorClasses.keys():
                raise ErrorClasses[data]
            else:
                raise IDENT_Error

        # There is no error, let us tests the answer against the provided user.
        opsys_field, user_id = data.split(':', 1)
        # Note that, as specified in the IDENT protocol, only the first 512
        # characters of the username are significants.
        if user_id[:USERID_MAX_SIZE] != userid[:USERID_MAX_SIZE]:
            return ()

        # All's right, returning detail information.
        return (opsys_field, userid)
    
    # Closing the socket to the IDENT server
    finally:
        ident_sock.close()
    