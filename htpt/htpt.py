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
from flask import Flask, request, make_response
app = Flask(__name__)

# local imports
import frame
import urlEncode
import imageEncode
#from htpt import frame
#from htpt import urlEncode
#from htpt import imageEncode

#Constants
CLIENT_LISTEN_PORT=8000 #local port to communicate to Tor with
SERVER_LISTEN_PORT=8001
TIMEOUT = 0.1 #max number of seconds between calls to read from the server

#Constants just to make this work-> remove
#TODO
TOR_BRIDGE_ADDRESS = "localhost:5000"
TOR_BRIDGE_PASSWORD = "hello"

# Note: I wrote this hastily, so the function names within our modules
# are likely different

class HTPT():
  def __init__(self):
    self.addressList = []
    self.disassembler = frame.Disassemble(callback)

  def run_client(self):
    # initialize the connection
    self.assembler = frame.Assemble()
    self.assembler.seqNum = frame.SeqNumber(-1)
    # bind to a local address and wait for Tor to connect
    self.torBinder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.torBinder.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.torBinder.bind(('localhost', CLIENT_LISTEN_PORT))
    self.torBinder.listen(1)
    (self.torSock, address) = self.torBinder.accept()

    #now that we have a Tor connection, start sending data to server
    self.bridgeConnect(TOR_BRIDGE_ADDRESS, TOR_BRIDGE_PASSWORD)
    self.assembler.seqNum = frame.SeqNumber(-1)
    self.timeout = datetime.now()

    while 1:
      # wait for data to send from Tor. Wait at most
      readyToRead, readyToWrite, inError = \
          select.select([self.torSock], [], [], TIMEOUT)
      if readyToRead != []:
        dataToSend = readyToRead[0].recv(1024*1000)
        print "Client Sending: {}".format(dataToSend)
        # if there is less than 35 bytes of data to send, then make
        # sure that we still send it
        while dataToSend != '':
          segment = dataToSend[:35]
          dataToSend = dataToSend[35:]
          # put the headers on the data (not the actual function name)
          framed = self.assembler.assemble(segment)
          # encode the data
          encoded = urlEncode.encode(framed, 'market')
          # send the data with headless web kit
          request = urllib2.Request(encoded['url'])
          for cookie in encoded['cookie']:
            request.add_header('Cookie:', cookie)
          reader = urllib2.urlopen(request)
          readData = reader.read()
          # if we have received data from the Internet, then send it up to Tor
          decoded = imageEncode.decode(readData, 'png')
          self.disassembler.disassemble(decoded)
          self.timeout = datetime.now()
      else:
        dataToSend = ''
        # put the headers on the data (not the actual function name)
        framed = self.assembler.assemble(dataToSend)
        # encode the data
        encoded = urlEncode.encode(framed, 'market')
        # send the data with headless web kit
        request = urllib2.Request(encoded['url'])
        reader = urllib2.urlopen(request)
        readData = reader.read()
        # if we have received data from the Internet, then send it up to Tor
        decoded = imageEncode.decode(readData, 'png')
        self.disassembler.disassemble(decoded)

      # if we go have not received or send data for 10 min, end the program
      if (datetime.now() - self.timeout).total_seconds() > 60*10:
        # close the local socket to tor
        self.torSock.close()
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
    request = urllib2.Request(encodedData['url'])
    for cookie in encodedData['cookie']:
      request.add_header('Cookie:', cookie)
    reader = urllib2.urlopen(request)
    image = reader.read()
    # use the returned image to initialize the session ID
    decodedData = imageEncode.decode(image, 'png')
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
    print "htpt: {}".format(data)
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
  if request.remote_addr not in addressList:
      # if the address is not in the list and it is not a market
      # request, then it is web gallery traffic
      if not urlEncode.isMarket(request.url):
        sendToImageGallery(request)
        return
      # if this is a market request, then proceed with new session initialization
      else:
        encoded = {'url':request.url, 'cookie':[]}
        decoded = urlEncode.decode(encoded)
        password = htptObject.disassembler.initServerConnection(decoded)
        # if they successfully authenticate, continue
        if password == TOR_BRIDGE_PASSWORD:
          addressList.append(request.remote_addr)
#          htptObject.conn = htptObject.assembler(htptObject.disassembler.getSeqNum())
          sessionID = htptObject.sessionIDs.getSessionIDAndIncrement()
          htptObject.assembler.setSessionID(sessionID)
          htptObject.disassembler.setSessionID(sessionID)
          #we initialize it to start sending with seq number 1
          htptObject.assembler.seqNum = frame.SeqNumber(-1)
          #send back a blank image with the new session id
          framed = htptObject.assembler.assemble('')
          image = imageEncode.encode(framed, 'png')
          return serveImage(image)
          #TODO
          #setup some way to maintain a single Internet connection per client
        else:
          print "Bad password entered"
    # if this is an initialized client, then receive the data and see
    # if we have anything to send
  else:
    #receive the data
    decoded = urlEncode.decode({'url':request.url, 'cookie':request.cookies})
    htptObject.disassembler.disassemble(decoded)
    # see if we have any data to return
    readyToRead, readyToWrite, inError = \
        select.select([htptObject.torSock], [], [], 0)
    # if we have received data from the Tor network for the Tor
    # client, then send it
    if readyToRead != []:
      # get up to a megabyte
      dataToSend = readyToRead[0].recv(1024*1000)
      print "Server Sending: {}".format(dataToSend)
    else:
      dataToSend = ''
    # put the headers on the data (not the actual function name)
    framed = htptObject.assembler.assemble(dataToSend)
    # encode the data
    encoded = imageEncode.encode(framed, 'png')
    # send the data with apache
    return serveImage(encoded)


def serveImage(image):
  response = make_response(image)
  response.headers['Content-Type'] = 'image/png'
  response.headers['Content-Disposition'] = 'attachment; filename=img.png'
  return response

def callback(data):
  if data == '':
    return
  else:
    print "Received: {}".format(data)
  htptObject.recvData(data)
  
if __name__ == '__main__':
  htptObject = HTPT()
  urlEncode.domain = TOR_BRIDGE_ADDRESS
  if str(sys.argv[1]) == "-client":
    htptObject.run_client()
  else:
    addressList = []
    # initialize the connection
    htptObject.sessionIDs = frame.SessionID()
    htptObject.assembler = frame.Assemble()
    htptObject.assembler.seqNum = frame.SeqNumber(-1)
    # bind to a local address and wait for Tor to connect
    htptObject.torBinder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    htptObject.torBinder.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    htptObject.torBinder.bind(('localhost', SERVER_LISTEN_PORT))
    htptObject.torBinder.listen(1)
    (htptObject.torSock, address) = htptObject.torBinder.accept()
    app.run(debug=True, use_reloader=False)
