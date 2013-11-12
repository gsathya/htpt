# Ben Jones
# Fall 2013
# htpt
# frame.py: ensure in-order delivery of frames for the htpt project

import threading
import struct
from random import randint

import urlEncode
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
      if self.buffer[index] is None:
        #we have found all sendable data
        break
      else:
        dataToSend = dataToSend + len(self.buffer[index])
    #if we have enough data to send up, pass it to the callback
    #function
    if dataToSend > MIN_SIZE_TO_PASS_UP:
      availableData = ''
      #coalesce every data element up to the first missing sequence
      while self.buffer[0] is not None:
        availableData += self.buffer.pop(0)
        self.minAcceptableSeqNum = ((self.minAcceptableSeqNum +1) % BUFFER_SIZE)
        self.maxAcceptableSeqNum = ((self.minAcceptableSeqNum +1) % BUFFER_SIZE)
        self.buffer.append(None)
      self.recvData(availableData)

  def flushBuffer(self):
    """Send all in order data up to the callback function"""

    availableData = ''
    while self.buffer[0] is not None:
      availableData += self.buffer.pop(0)
      self.minAcceptableSeqNum = ((self.minAcceptableSeqNum +1) % BUFFER_SIZE)
      self.maxAcceptableSeqNum = ((self.minAcceptableSeqNum +1) % BUFFER_SIZE)
      self.buffer.append(None)
    self.recvData(availableData)


class Encoder:
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

    if 'more_data' in kwargs:
      more_data = kwargs['more_data']
      if more_data:
        flags = '1000'
    else:
      flags = '0000'
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

    seqNum = self.getSeqNum()
    sessionID = self.getSessionID()
    flags = self.generateFlags(**kwargs)
    nonce = self.generateNonce()

    flags_and_nonce = (int(flags,2) << 4) | nonce
    headerString = struct.pack('!HBB', seqNum, sessionID, flags_and_nonce)

    return headerString

  def flush(self):
    # TODO: send self.output to the interwebz
    self.output = None

  def encode(self, data, **kwargs):
    """Assemble frame as headers + data

    **kwargs is dict of flags to be set in headers"""

    headers = self.getHeaders(**kwargs)
    self.output = urlEncode.encode(headers+data, 'market')
    # when unassembling: data = headers+data[4:]
    self.flush()


class Decoder:
  def __init__(self):
    self.output = None

  def decode(self, frame):
    """Unassemble received frame to headers and data

    headers are the first 4 bytes"""

    headers = frame[:4]
    self.retrieveHeaders(headers)

    data = frame[4:]
    for datum in data:
      self.output = urlEncode.decode(datum)
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
