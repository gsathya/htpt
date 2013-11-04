# Ben Jones
# Fall 2013
# htpt
# frame.py: ensure in-order delivery of frames for the htpt project

import threading
import numpy as np
import struct as struct

import urlEncode
from constants import *

class FramingException(Exception):
  pass

initialized = False
class SeqNumber():
  _seqNum = 0
  _lock = threading.Lock()
  _initialized = False

  @staticmethod
  def init(*args):
    """Initialize the framing package with the given sequence number"""

    if len(args) > 0:
      SeqNumber._seqNum = args[0]
    else:
      SeqNumber._seqNum = 0
    SeqNumber._initialized = True

  @staticmethod
  def getSequenceAndIncrement():
    """In a thread safe manner, get the sequence number"""
    
    #if the code has not been initialized, do that now
    if not SeqNumber._initialized:
      SeqNumber.init()
    SeqNumber._lock.acquire()
    SeqNumber._seqNum = ((SeqNumber._seqNum + 1) % MAX_SEQ_NUM)
    SeqNumber._lock.release()
    return SeqNumber._seqNum

#make this methods available without having to access the class
getSequenceAndIncrement = SeqNumber.getSequenceAndIncrement
init = SeqNumber.init

class Framer():
  """Class to reassemble the Tor stream"""

  def __init__(self, callback, **kArgs):
    """Initialize the class to frame all of the packages

    Parameters: callback- a function which the received data will be
    passed to once it is in the correct order
    kArgs- additional keyword arguments specified for the
    function. Currently, the only additional option has the keyword of
    'minSeqNum' and an integer value which tells Framer the min
    acceptable sequence number. Example syntax: Framer(callback,
    minSeqNum=5)

    """

    self.buffer = [None] * BUFFER_SIZE
    if 'minSeqNum' in kArgs:
      self.minAcceptableSeqNum = kArgs['minSeqNum']
      self.maxAcceptableSeqNum = BUFFER_SIZE + self.minAcceptableSeqNum
    else:
      self.minAcceptableSeqNum = 0
      self.maxAcceptableSeqNum = BUFFER_SIZE
    #setup a function to call when there is data to receive
    self.recvData = callback

  def isSeqNumInBuffer(self, seqNum):
    """If the sequence number is in the buffer, return True, else False"""
    if seqNum >= self.minAcceptableSeqNum:
      if seqNum <= self.maxAcceptableSeqNum:
        return True
      #explore the case where the sequence number wraps
      elif (self.minAcceptableSeqNum + BUFFER_SIZE) >= MAX_SEQ_NUM:
        #case where maxSeqNum wrapped, so seqNum > min > max
        if(seqNum <= MAX_SEQ_NUM):
          return True
      else:
        return False
    else:
      #case where the max seq num and seqNum have wrapped, but min has
      #not
      if(self.minAcceptableSeqNum + BUFFER_SIZE) > MAX_SEQ_NUM:
        if(seqNum < self.maxAcceptableSeqNum):
          return True
      else:
        return False
    return False

  def recvFrame(self, data, seqNum):
    """Add the given frame to the buffer

    Parameters: data- the data from the frame
    seqNum- the sequence number of the frame

    Note: the acceptable window is based on available buffer space,
    not unacked packets
    
    """
    if not self.isSeqNumInBuffer(seqNum):
      raise FramingException("Not enough space in the buffer")
    index = (seqNum - self.minAcceptableSeqNum) % MAX_SEQ_NUM
    self.buffer[index] = data
    #see if we have enough data to pass up by coalescing all of the
    #frames and seeing if we meet the min threshold to send up
    dataToSend = 0
    for index in range(BUFFER_SIZE):
      if self.buffer[index] == None:
        #we have found all sendable data
        break
      else:
        dataToSend = dataToSend + len(self.buffer[index])
    #if we have enough data to send up, pass it to the callback
    #function
    if dataToSend > MIN_SIZE_TO_PASS_UP:
      availableData = ''
      #coalesce every data element up to the first missing sequence
      while self.buffer[0] != None:
        availableData += self.buffer.pop(0)
        self.minAcceptableSeqNum = ((self.minAcceptableSeqNum +1) % BUFFER_SIZE)
        self.maxAcceptableSeqNum = ((self.minAcceptableSeqNum +1) % BUFFER_SIZE)
        self.buffer.append(None)
      self.recvData(availableData)

  def flushBuffer(self):
    """Send all in order data up to the callback function"""

    availableData = ''
    while self.buffer[0] != None:
      availableData += self.buffer.pop(0)
      self.minAcceptableSeqNum = ((self.minAcceptableSeqNum +1) % BUFFER_SIZE)
      self.maxAcceptableSeqNum = ((self.minAcceptableSeqNum +1) % BUFFER_SIZE)
      self.buffer.append(None)
    self.recvData(availableData)

class Assembler:
  def __init__(self):
    self.output = None

  def generateFlags(self, more_data):
    """Generates a 4-bit string of bits

    Parameters: more_data- boolean True if more data
    currently, the only flag we set is the MSB for more data"""

    if more_data:
      flags = '1000'
    else:
      flags = '0000'
    return flags
  
  def generateNonce(self)
    """Generate a random integer value between 0 and 16"""
    nonce = np.random.randint(0,15)
    return nonce

  def getSeqNum(self)
    # TODO
    seqNum = None
    return seqNum

  def getSessionID(self)
    # TODO
    sessionID = None
    return sessionID

  def getHeaders(self, seqNum, sessionID, flags, nonce):
    """Create a 4 byte struct header in network byte order
    
    Parameters: seqNum- 2 byte sequence number of the frame
    sessionID - 1 byte
    flags - 4 bit string. currently only '1000' if More data
    nonce - integer. randomized value [0,15]
    
    returns: header string (struct) packedused in assemble function

    """
    # 16-bit sequence num | 8-bit session ID | 4-bit flag | 4-bit nonce
    # unsigned short (H) | unsigned char (B) | unsigned char (B) packed
    flags_and_nonce = (int(flags,2) << 4) | nonce
    headerString = struct.pack('!HBB', seqNum, sessionID, flags_and_nonce)

    return headerString

  def flush(self):
    # TODO: send self.output to the interwebz
    self.output = None

  def assemble(self, data):
    headers = self.getHeaders()
    self.output = urlEncode.encode(headers+data, 'market')
    # when unassembling: data = headers+data[4:]
    self.flush()


class UnAssembler:
  def __init__(self):
    self.output = None

  def unassemble(self, frame):
    """Unassemble received frame to headers and data

    headers are the first 4 bytes"""

    data = frame[4:]
    # TODO send data to upper layer - add flush function ?

    headers = frame[:4]
    self.retrieveHeaders(headers)

  def retrieveHeaders(self, headers):
    """Extract 4 byte header to seqNum, sessionID, Flags, Nonce"""

    headerTuple = struct.unpack('!HBB', headers)
    self.seqNum = headerTuple[0]
    self.sessionID = headerTuple[1]
    mask = int('0b1111',2)
    self.flags = bin(headerTuple[2] & (mask << 4)) >> 4)[2:]
    self.nonce = headerTuple[2] & mask 
