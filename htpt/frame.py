# Ben Jones
# Fall 2013
# htpt
# frame.py: ensure in-order delivery of frames for the htpt project

import threading
import struct
from random import randint

import urlEncode
from buffers import Buffer
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


class Assemble():
  """Class to Assemble a data frame with headers before sending to encoder"""
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
    # This function may not be needed. In main() we call
    # assembler.assemble(data, flags) and then
    # urlEncode.encode(assembler.output), and then flush() to interwebz
    print self.output
    self.output = None

  def assemble(self, data, **kwargs):
    """Assemble frame as headers + data

    Parameters: data, **kwargs
    data is simply a string
    **kwargs is dict of flags to be set in headers"""

    headers = self.getHeaders(**kwargs)
    frame = headers+data
    self.output = frame
    # TODO in main(): encode self.output to a packet and send output packet to flush()


class Disassemble:
  """Class to Disassemble a decoded packet into headers+data before sending to buffers"""
  def __init__(self):
    self.output = None
    self.buffer = Buffer()
    # TODO CHECK if flush() should be added here as a callback to buffer
    self.buffer.addCallback(self.flush)

  def disassemble(self, frame):
    """Unassemble received (decoded)frame to headers and data

    Parameters: frame is the raw bytes after decoding url or cookie
    headers are the first 4 bytes, data is what follows.

    should be called from main() after urlEncode.decode(). raw data,
    seqNum are then sent to Buffer.recvData() to flush it.

    we assume data is simply a string"""

    # split to headers + data
    headers = frame[:4]
    self.retrieveHeaders(headers)

    data = frame[4:]
    self.output = data

    # receive, reorder and flush at buffer
    self.buffer.recvData(data, self.seqNum)

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
