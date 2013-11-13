# Ben Jonesp
# Fall 2013
# Georgia Tech
# htpt.py: this file contains the code to run the HTPT transport

# imports
from datetime import datetime
# local imports
from htpt import frame.py

# Constants
conns = []

# TODO-change this from pseudocode to actual code
# Note: I wrote this hastily, so the function names within our modules
# are likely different
def run_client():
  # initialize the connection
  conns.append(frame.initConn())
  conns[0].connect(torBridgeAddress, torBridgePassword)
  conns[0].timeout = datetime.now()
  while 1:
    # if we have received data from tor, then send it
    if (data = recv(torConn)) != None:
      conns[0].timeout = datetime.now()
      # put the headers on the data (not the actual function name)
      framed = conns[0].frameData(data)
      # encode the data
      encoded = urlEncode.encode(framed, 'market')
      # send the data with headless web kit
      conns[0].send(encoded)
    # if we have received data from the Internet, then send it
    if (data = conns[0].recv()) != None:
      conns[0].timeout = datetime.now()
      decoded = urlEncode.decode(data)
      conns[0].receiveData(decoded)
    # if we go have not received or send data for 10 min, break out
    if (datetime.now() - conns[0].timeout).total_seconds() > 60*10:
      break
  conns[0].closeConnection()

def create_connection(url):
  """
  Create a connection with a client who has successfully
  authenticated with one of the authentication cookies

  Parameters:
  url- the url from the HTTP GET request with the authentication
  cookie. The url will not contain any data, but will have a valid
  frame header. This header should contain a SYN flag and a sequence
  number
  
  Note: The server will initialize the minimum acceptable sequence
  number to the value give in the URL's frame header

  Note: HTPT will manage all state. Since the image gallery needs to
  maintain a list of authenticated IP addresses so it knows what
  traffic to pass through, HTPT will manage a list of IP addresses for
  the image gallery. The image gallery exposes this list to HTPT
  through an add and remove function

  """
  conn = conns.append(frame.initConn())
  gallery.add(conn.Address)

def receive_data(data):
  """Receive data from the image gallery"""
 
  #find the connection in the list of connections
  decoded = urlEncode.decode(data)
  conn = findConnBySessionID(data[:4])
  conn.timeout = datetime.now()
  conn.receive(decoded)

def run_server():
  """run a server for htpt"""

  #integrate with apache
  initialize_connection_with_wsgi

  #when Apache gets a new connection with a cookie which matches one
  #of the authenticated cookies for this Tor bridge, the gallery code
  #will call the create_connection function, which adds connections to
  #our connection array, conns
  while 1:
    for conn in conns:
      # if we have received data from the Tor network for the Tor
      # client, then send it
      if (data = recv(torConn)) != None:
        conn.timeout = datetime.now()
        # put the headers on the data (not the actual function name)
        framed = conn.frameData(data)
        # encode the data
        encoded = urlEncode.encode(framed, 'market')
        # send the data with apache
        conn.send(encoded)
      # if we go have not received or sent data for 10 min, break out
      if (datetime.now() - conns.timeout).total_seconds() > 60*10:
        conn.closeConnection()
        gallery.remove(conn.Address)
        conns.remove(conn)

if __name__ == '__main__':
    run_client()
