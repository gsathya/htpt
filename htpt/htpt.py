# Ben Jonesp
# Fall 2013
# Georgia Tech
# htpt.py: this file contains the code to run the HTPT transport

# imports
from datetime import datetime
import socket
# local imports
from htpt import frame

#Constants
LISTEN_PORT=8000 #local port to communicate to Tor with
TIMEOUT = 1 #max number of seconds between calls to read from the server

#Constants just to make this work-> remove
#TODO
TOR_BRIDGE_ADDRESS = 192.168.142.1
TOR_BRIDGE_PASSWORD = "hello"

# TODO-change this from pseudocode to actual code

# Note: I wrote this hastily, so the function names within our modules
# are likely different

class HTPT():
  def run_client():
    # initialize the connection
    self.assembler = frame.Assemble()
    self.receivedData = False
    # bind to a local address and wait for Tor to connect
    self.torBinder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.torBinder.bind(('localhost', LISTEN_PORT))
    self.torBinder.listen(1)
    (self.torSock, address) = self.torBinder.accept()
    self.torSock.setblocking(0)

    #now that we have a Tor connection, start sending data to server
    self.bridgeConn = bridgeConnect(TOR_BRIDGE_ADDRESS, TOR_BRIDGE_PASSWORD)

    self.timeout = datetime.now()

    while 1:
      # wait for data to send from Tor. Wait at most
      readyToRead, readyToWrite, inError = \
          select.select(torSock, None, None, TIMEOUT)
      if readyToWrite != None:
        dataToSend = readyToWrite.recv()
        for index in range(35, len(dataToSend)-1, 35):
          segment = dataToSend[:index]
          dataToSend = dataToSend[index:]
          # put the headers on the data (not the actual function name)
          framed = self.assembler.assemble(segment)
          # encode the data
          encoded = urlEncode.encode(framed, 'market')
          # send the data with headless web kit
          readData = self.bridgeConn.send(encoded)
          # if we have received data from the Internet, then send it up to Tor
          decoded = imageEncode.decode(readData, 'png')
          self.disassembler.disassemble(decoded)
          self.timeout = datetime.now()
      # if we go have not received or send data for 10 min, end the program
      if (datetime.now() - conns[0].timeout).total_seconds() > 60*10:
        # close the local socket to tor
        torSock.close()
        # close the headless web kit connection to the server
        self.bridgeConn.close()
        break

  def bridgeConnect(address, password):
    """
    Create a connection to a bridge from a client

    Parameters:
    address- the ip address to connect to
    password- the password to send in the payload of the packet
  
    Notes: this function will send a packet to the server via market
    encoding with the password hidden in the payload

    Note: the function will initiate a connection with the bridge by
    sending a market encoded url with a payload of just the connect
    password. After sending the GET request, the function will use the
    returned image (just padding) to initialize the session ID

    Returns: whatever state you need to keep using headless web kit
    """
    headlessWebKit.connect(address)
    data = self.assembler.assemble(password)
    encodedData = urlEncode.encodeAsMarket(data)
    image = headlessWebKit.send(encodedData)
    # use the returned image to initialize the session ID
    #TODO how do we get the type of image?
    decodedData = imageEnode.decode(image, 'png')
    self.disassembler = frame.Disassemble()
    self.disassembler.disassemble(decodedData)
    self.assembler.setSessionID(self.disassembler.getSessionID())
    return headlessWebKit

  def serverRecvData(data):

  def run_server():
    """run a server for htpt"""

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
          encoded = imageEncode.encode(framed)
          # send the data with apache
          conn.send(encoded)
        # if we go have not received or sent data for 10 min, break out
        if (datetime.now() - conns.timeout).total_seconds() > 60*10:
          conn.closeConnection()
          gallery.remove(conn.Address)
          conns.remove(conn)

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

if __name__ == '__main__':
  run_client()
