# Ben Jones
# Fall 2013
# htpt
# frame.py: ensure in-order delivery of frames for the htpt project

import threading
import struct
from random import randint

import urlEncode
import buffers
from constants import *


class FramingException(Exception):
  pass


class SeqNumber():
  def __init__(self, seqNum = 0):
    """Initialize the framing package with the given sequence number"""
    self.seqNum = seqNum
    self.initialized = True
    self._lock = threading.Lock()

  def getSequenceAndIncrement(self):
    """In a thread safe manner, get the sequence number"""
    self._lock.acquire()
    self.seqNum = ((self.seqNum + 1) % MAX_SEQ_NUM)
    self._lock.release()
    return self.seqNum


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


class Assemble():
  def __init__(self):
    """Initialize SeqNumber object"""
    self.seqNum = SeqNumber()
    self.output = None

  def generateFlags(self, **kwargs):
    """Generates a 4-bit string of bits

    Parameters: kwargs- additional keyword arguments specified for the
    function. Currently, the only additional option has the keyword of
    'more_data' and a boolean value (0/1) which sets the more_data bit
    (MSB) in the header. Example syntax: generateFlags(more_data=1)"""

    flags = '0000'
    if 'more_data' in kwargs:
      more_data = kwargs['more_data']
      if more_data==1:
        flags = '1000'
    return flags

  def generateNonce(self):
    """Generate a random integer value between 0 and 16"""
    nonce = randint(0,15)
    return nonce

  def getSeqNum(self):
    """Get sequence number after incrementing"""
    seqNum = self.seqNum.getSequenceAndIncrement()
    return seqNum

  def getSessionID(self):
    # TODO not sure how to set session IDs
    sessionID = 0
    return sessionID

  def getHeaders(self, **kwargs):
    """Create a 4 byte struct header in network byte order

    16-bit sequence num | 8-bit session ID | 4-bit flag | 4-bit nonce
    unsigned short (H) | unsigned char (B) | unsigned char (B) packed

    Calls functions to get:
    seqNum- 2 byte sequence number of the frame
    sessionID - 1 byte (currently None)
    flags - 4 bit string. check kwargs and set appropriate bit
    nonce - integer. randomized value [0,15]

    returns: header string (struct) packedused in assemble function

    """

    self.seqNum = self.getSeqNum()
    self.sessionID = self.getSessionID()
    self.flags = self.generateFlags(**kwargs)
    self.nonce = self.generateNonce()

    flags_and_nonce = (int(self.flags,2) << 4) | self.nonce
    headerString = struct.pack('!HBB', self.seqNum, self.sessionID, flags_and_nonce)

    return headerString

  def flush(self):
    # TODO: send self.output to the interwebz
    print self.output
    self.output = None

  def assemble(self, data, **kwargs):
    """Assemble frame as headers + data

    Parameters: data, **kwargs
    data is simply a string
    **kwargs is dict of flags to be set in headers"""

    headers = self.getHeaders(**kwargs)
    frame = headers+data
    # encode frame to packet and send output packet to flush()
    self.output = urlEncode.encode(headers+data, 'market')
    # when unassembling: decoded data = headers+data[4:]
    self.flush()


class Disassemble:
  def __init__(self):
    self.output = None
    self.buffer = Buffer()

  def disassemble(self, packet):
    """Decode, then Unassemble received frame to headers and data

    Parameters: frame is the encoded url or cookie. It should first
    be decoded by urlEncode.decode(), which will return bytes to be
    unassembled.
    headers are the first 4 bytes, data is what follows.

    we assume data is simply a string"""

    # first decode received frame
    frame = urlEncode.decode(packet)
    # then split to headers + data
    headers = frame[:4]
    self.retrieveHeaders(headers)

    data = frame[4:]
    self.output = data

    self.flush()

  def retrieveHeaders(self, headers):
    """Extract 4 byte header to seqNum, sessionID, Flags, Nonce"""

    headerTuple = struct.unpack('!HBB', headers)
    self.seqNum = headerTuple[0]
    self.sessionID = headerTuple[1]
    mask = int('0b1111',2)
    self.flags = bin((headerTuple[2] & (mask << 4)) >> 4)[2:]
    # TODO: if flags = '1000' i.e. more_data, then send pull_request to
    # server for more data
    self.nonce = headerTuple[2] & mask

  def flush(self):
    # TODO: send self.output to Tor
    print self.output
    self.output = None
    pass
