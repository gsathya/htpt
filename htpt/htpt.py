#! /usr/bin/python
# Ben Jones
# Fall 2013
# Georgia Tech
# htpt.py: this file contains the code to run the HTPT transport

# imports
from datetime import datetime
import select
import socket
import sys
import urllib2

#flask stuff
from flask import Flask, request
app = Flask(__name__)

# local imports
import frame
import urlEncode
#from htpt import frame
#from htpt import urlEncode
#from htpt import imageEncode

#Constants
LISTEN_PORT=8000 #local port to communicate to Tor with
TIMEOUT = 0.1 #max number of seconds between calls to read from the server

#Constants just to make this work-> remove
#TODO
TOR_BRIDGE_ADDRESS = "192.168.142.1"
TOR_BRIDGE_PASSWORD = "hello"

# Note: I wrote this hastily, so the function names within our modules
# are likely different

class HTPT():
  def init(self):
    self.addressList = []
    self.disassembler = frame.Disassemble(self.recvData)
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
    bridgeConnect(TOR_BRIDGE_ADDRESS, TOR_BRIDGE_PASSWORD)

    self.timeout = datetime.now()

    while 1:
      # wait for data to send from Tor. Wait at most
      readyToRead, readyToWrite, inError = \
          select.select([torSock], [], [], TIMEOUT)
      if readyToRead != None:
        dataToSend = readyToRead.recv()
        for index in range(35, len(dataToSend)-1, 35):
          segment = dataToSend[:index]
          dataToSend = dataToSend[index:]
          # put the headers on the data (not the actual function name)
          framed = self.assembler.assemble(segment)
          # encode the data
          encoded = urlEncode.encode(framed, 'market')
          # send the data with headless web kit
          request = urllib2.Request(encoded[0], cookies=encoded[1])
          reader = urllib2.urlopen(request)
          readData = reader.read()
          # if we have received data from the Internet, then send it up to Tor
          decoded = imageEncode.decode(readData, 'png')
          self.disassembler.disassemble(decoded)
          self.timeout = datetime.now()
      # if we go have not received or send data for 10 min, end the program
      if (datetime.now() - self.timeout).total_seconds() > 60*10:
        # close the local socket to tor
        torSock.close()
        break

  def bridgeConnect(self, address, password):
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

    data = self.assembler.assemble(password)
    encodedData = urlEncode.encodeAsMarket(data)
    request = urllib2.Request(encodedData[0], cookies=encodedData[1])
    reader = urllib2.urlopen(request)
    image = reader.read()
    # use the returned image to initialize the session ID
    decodedData = imageEnode.decode(image, 'png')
    self.disassembler.disassemble(decodedData)
    self.assembler.setSessionID(self.disassembler.getSessionID())

  def recvData(self, data):
    """
    Callback function for the dissassemblers
    
    Parameters:
    data- the string of received data to be passed up to Tor
    
    Notes: this functions is used by both the client and server to
    pass data up to Tor

    Returns: nothing

    """
    self.torSock.send(data)
    return

@app.route('/')
def processRequest():
  """Process incoming requests from Apache
  
  Structure: this function determines whether data should go through
  to htpt decoding or if it should be passed to the image
  gallery. This is a function due to constraints from flask

  """
  # if we are not in the address list, then this is not an initialized connection
  if ipAddress not in addressList:
      # if the address is not in the list and it is not a market
      # request, then it is web gallery traffic
      if not urlEncode.isMarket(request):
        sendToImageGallery(request)
        return
      # if this is a market request, then proceed with new session initialization
      else:
        decoded = urlEncode.decode(request.url)
        password = htptObject.disassembler.initServerConnection(decoded)
        # if they successfully authenticate, continue
        if password == TOR_BRIDGE_PASSWORD:
          addressList.append(ipAddress)
          htptObject.conn = htptObject.dissassembler(htptObject.disassember.getSeqNum())
          sessionID = htptObject.sessionIDs.getSessionIDAndIncrement()
          htptObject.conn.setSessionID(sessionID)
          #send back a blank image with the new session id
          htptObject.assembler.setSessionID(sessionID)
          image = imageEncode.encode('', 'png')
          return serveImage(image)
          #TODO
          #set the session id to the next value
          #setup some way to maintain a single Internet connection per client
    # if this is an initialized client, then receive the data and see
    # if we have anything to send
  else:
    decoded = urlEncode.decode([request.url, request.cookies])
    readyToRead, readyToWrite, inError = \
        select.select(htptObject.torSock, None, None, 0)
    # if we have received data from the Tor network for the Tor
    # client, then send it
    if readyToRead != None:
      # get up to a megabyte
      dataToSend = readyToRead.recv(1024*1000)
      # put the headers on the data (not the actual function name)
      framed = self.assembler.assemble(dataToSend)
      # encode the data
      encoded = imageEncode.encode(framed, 'png')
      # send the data with apache
      self.buffer.append(encoded)
      return serveImage(htptObject.buffer.pop())

def serveImage(image):
  response = make_response(image)
  response.headers['Content-Type'] = 'image/png'
  response.headers['Content-Disposition'] = 'attachment; filename=img.png'
  return response
  
if __name__ == '__main__':
  htptObject = HTPT()
  if str(sys.argv[1]) == "-client":
    htptObject.run_client()
  else:
    addressList = []
    # initialize the connection
    htptObject.sessionIDs = SessionID()
    htptObject.assembler = frame.Assemble()
    htptObject.receivedData = False
    # bind to a local address and wait for Tor to connect
    htptObject.torBinder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    htptObject.torBinder.bind(('localhost', LISTEN_PORT))
    htptObject.torBinder.listen(1)
    (htptObject.torSock, address) = htptObject.torBinder.accept()
    app.run()
