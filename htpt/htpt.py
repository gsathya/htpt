# Ben Jones
# Fall 2013
# Georgia Tech
# htpt.py: this file contains the code to run the HTPT transport

# imports
from datetime import datetime
# local imports
from htpt import frame.py

# TODO-change this from pseudocode to actual code
def run():
  # initialize the connection
  conn1 = frame.initConn(torBridgeAddress, torBridgePassword)
  timeout = datetime.now()
  while 1:
    # if we have received data from tor, then send it
    if (data = recv(torConn)) != None:
      timeout = datetime.now()
      # put the headers on the data (not the actual function name)
      framed = conn1.frameData(data)
      # encode the data
      encoded = urlEncode.encode(framed, 'market')
      # send the data with headless web kit
      conn1.send(encoded)
    # if we have received data from the Internet, then send it
    if (data = recv(conn1)) != None:
      timeout = datetime.now()
      decoded = urlEncode.decode(data)
      conn1.receiveData(decoded)
    # if we go have not received or send data for 10 min, close the
    # connection
    # Note: I am writing this quickly, so I am unsure if this is the
    # correct syntax
    if (timeout - datetime.now()) > 60*10:
      conn1.closeConnection()
      
if __name__ == '__main__':
    run()
