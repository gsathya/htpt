#! /usr/bin/python
# Ben Jones
# Fall 2013
# Georgia Tech
# htpt.py: this file contains the code to run the HTPT transport

# imports
from datetime import datetime
import select
import socket
import socks
import sys
import urllib2

#flask stuff
from flask import Flask, request, make_response
app = Flask(__name__)

# local imports
import frame
import urlEncode
import imageEncode
from socks4a.htptProxy import ThreadingSocks4Proxy, ReceiveSocksReq, ForwardSocksReq

#from htpt import frame
#from htpt import urlEncode
#from htpt import imageEncode

#Constants
CLIENT_SOCKS_PORT=8000 # communication b/w Tor and SOCKS server
SERVER_SOCKS_PORT=9150 # communication b/w Tor and SOCKS client
HTPT_CLIENT_SOCKS_PORT=8002   # communication b/w htpt and SOCKS
#HTPT_SERVER_SOCKS_PORT=8003   # communication b/w htpt and SOCKS
TIMEOUT = 0.5 #max number of seconds between calls to read from the server

#Constants just to make this work-> remove
#TODO
TOR_BRIDGE_ADDRESS = "localhost:5000"
TOR_BRIDGE_PASSWORD = "hello"
PASSWORDS = [TOR_BRIDGE_PASSWORD]

# Note: I wrote this hastily, so the function names within our modules
# are likely different

class HTPT():
  def __init__(self):
    self.addressList = []
    self.disassembler = frame.Disassembler(callback)

  def run_client(self):
    # initialize the connection
    while 1:
      self.assembler = frame.Assembler()
      # bind to a local address and wait for Tor to connect
      self.torBinder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.torBinder.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      self.torBinder.bind(('localhost', HTPT_CLIENT_SOCKS_PORT))
      self.torBinder.listen(1)
      (self.torSock, address) = self.torBinder.accept()

      #now that we have a Tor connection, start sending data to server
      self.bridgeConnect(TOR_BRIDGE_ADDRESS, TOR_BRIDGE_PASSWORD)
      self.timeout = datetime.now()

      while 1:
        # wait for data to send from Tor. Wait at most
        readyToRead, readyToWrite, inError = \
           select.select([self.torSock], [], [], TIMEOUT)
        if readyToRead != []:
          dataToSend = readyToRead[0].recv(1024*1000)
          #        print "Client Sending: {}".format(dataToSend)
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
        if (datetime.now() - self.timeout).total_seconds() > 30:
        # close the local socket to tor
          self.torSock.send("closing")
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
#    print "htpt: {}".format(data)
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
        sender, receiver = frame.initServerConnection(decoded, PASSWORDS, callback)
        # if the client sent a bad password, print an error message
        # and return an empty image
        if sender == False:
          print "Bad password entered"
          return sendToImageGallery(request)
        # Note: this will need to change to accomodate multiple client sessions
        htptObject.assembler = sender
        htptObject.disassembler = receiver
        addressList.append(request.remote_addr)
        #send back a blank image with the new session id
        framed = htptObject.assembler.assemble('')
        image = imageEncode.encode(framed, 'png')
        return serveImage(image)
          #TODO
          #setup some way to maintain a single Internet connection per client
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
#      print "Server Sending: {}".format(dataToSend)
    else:
      dataToSend = ''
    # put the headers on the data (not the actual function name)
    framed = htptObject.assembler.assemble(dataToSend)
    # encode the data
    encoded = imageEncode.encode(framed, 'png')
    # send the data with apache
    return serveImage(encoded)

def sendToImageGallery(request):
  image = imageEncode.encode('', 'png')
  response = make_response(image)
  response.headers['Content-Type'] = 'image/png'
  response.headers['Content-Disposition'] = 'attachment; filename=img.png'
  return response

def serveImage(image):
  response = make_response(image)
  response.headers['Content-Type'] = 'image/png'
  response.headers['Content-Disposition'] = 'attachment; filename=img.png'
  return response

def callback(data):
  if data == '':
    return
#  else:
#    print "Received: {}".format(data)
  htptObject.recvData(data)
  
if __name__ == '__main__':
  htptObject = HTPT()
  urlEncode.domain = TOR_BRIDGE_ADDRESS
  if str(sys.argv[1]) == "-client" and str(sys.argv[2]) == "0":
    server = ThreadingSocks4Proxy(ForwardSocksReq, CLIENT_SOCKS_PORT, HTPT_CLIENT_SOCKS_PORT)
    server.serve_forever()
  elif str(sys.argv[1]) == "-client" and str(sys.argv[2]) == "1":
    htptObject.run_client()
  elif str(sys.argv[1]) == "-server" and str(sys.argv[2]) == "0":
    server = ThreadingSocks4Proxy(ReceiveSocksReq, SERVER_SOCKS_PORT)
    server.serve_forever()
  else:
    addressList = []
    # setup the proxy server
    # bind to a local address and wait for Tor to connect
    # htptObject.torBinder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # htptObject.torBinder.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # htptObject.torBinder.bind(('localhost', SERVER_SOCKS_PORT))
    # htptObject.torBinder.listen(1)
    # (htptObject.torSock, address) = htptObject.torBinder.accept()
    # htptObject.torSock = socks.socksocket()
    # htptObject.torSock.setproxy(socks.PROXY_TYPE_SOCKS4, "localhost", SERVER_SOCKS_PORT)
    htptObject.torSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    htptObject.torSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    htptObject.torSock.connect(("localhost", SERVER_SOCKS_PORT))
    app.run(debug=True, use_reloader=False)
