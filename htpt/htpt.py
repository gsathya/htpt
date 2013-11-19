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
  def init(self):
    self.addressList = []
    self.disassembler = frame.Disassemble()
    self.socks = []
    self.conns = []

  def run_client(self):
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
    self.disassembler.disassemble(decodedData)
    self.assembler.setSessionID(self.disassembler.getSessionID())
    return headlessWebKit

  def serverRecvData(request, ipAddress):
    """
    Code which basically runs the server

    Parameters:
    request- the headers for the interaction the client just made with Apache
    ipAddress- the IP address for the host

    Structure: the wsgi code is pretty dumb, so it will call this
    function every time it receives something. This function will 1)
    determine whether this is HTPT or image gallery traffic 2) route
    gallery traffic to the appropriate location and 3) receive and
    respond to the htpt traffic

    """
    # if we are not in the address list, then this is not an initialized connection
    if ipAddress not in self.addressList:
      # if the address is not in the list and it is not a market
      # request, then it is web gallery traffic
      if not isMarket(request):
        sendToImagegallery(request)
        return
      # if this is a market request, then proceed with new session initialization
      else:
        decoded = urlEncode.decode(request)
        self.disassembler.disassemble(decoded)
        password = self.disassembler.flush()
        # if they successfully authenticate, continue
        if password == TOR_BRIDGE_PASSWORD:
          self.addressList.append(ipAddress)
          conn = frame.Dissassemble(self.disassember.getSeqNum())
          #TODO
          #set the session id to the next value
          #setup some way to maintain a single Internet connection per client

  def run_server():
    """
    run a server for htpt

    Structure: this method basically just receives data back from the
    Internet and forwards the traffic onto the client
    
    """
    
    #TODO-> finish implementing this code after we come up with new abstraction
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

if __name__ == '__main__':
  run_client()
