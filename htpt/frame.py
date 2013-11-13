# Ben Jones
# Fall 2013
# htpt
# frame.py: ensure in-order delivery of frames for the htpt project

import threading
import struct
from random import randint

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
  def __init__(self, sessionID=0):
    """Initialize SeqNumber object and sessionID"""
    self.seqNum = SeqNumber()
    self.output = None
    self.setSessionID(sessionID)

  def setSessionID(self, sessionID):
    """Function to allow upper abstraction to set sessionID for sender"""
    self.sessionID = sessionID

  def getSessionID(self):
    """Function to retrieve the client's or server's session ID

    server assigns a new session ID when a new client connects to
    it. server maintains sessionID on its end. client should retrieve
    sessionID from the ACK packet (from SYN-ACK) and set it as
    self.sessionID"""
    return self.sessionID

  def generateFlags(self, **kwargs):
    """Generates a 4-bit string of bits

    Parameters: kwargs- additional keyword arguments specified for the
    function. Currently, the only additional option is 'more_data' and
    'SYN', which are assigned a boolean integer value (0/1). These
    set appropriate bits in flags.
    Example syntax: generateFlags(more_data=1, SYN=0)

    flags format: [ more_data | SYN | X | X ]"""

    flags = '0000'
    flag_list = list(flags)
    if 'more_data' in kwargs:
      more_data = kwargs['more_data']
      flag_list[0]=str(more_data)
    if 'SYN' in kwargs:
      SYN_flag = kwargs['SYN']
      flag_list[1]=str(SYN_flag)
    flags = "".join(flag_list)
    return flags

  def generateNonce(self):
    """Generate a random integer value between 0 and 16"""
    nonce = randint(0,15)
    return nonce

  def getSeqNum(self):
    """Get sequence number after incrementing"""
    seqNum = self.seqNum.getSequenceAndIncrement()
    return seqNum

  def getHeaders(self, **kwargs):
    """Create a 4 byte struct header in network byte order

    16-bit sequence num | 8-bit session ID | 4-bit flag | 4-bit nonce
    unsigned short (H) | unsigned char (B) | unsigned char (B) packed

    Calls functions to get:
    seqNum- 2 byte sequence number of the frame
    sessionID - 1 byte char int assigned by server
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
    # allocate a buffer to receive data and flush it
    self.buffer = Buffer()
    # TODO CHECK if flush() should be added here as a callback to buffer
    self.buffer.addCallback(self.flush)

  def disassemble(self, frame):
    """
    Disassemble received (decoded) frame to headers and data

    Parameters: frame is the raw bytes after decoding url or cookie
    headers are the first 4 bytes, data is what follows.

    should be called from main() after urlEncode.decode(). raw data,
    seqNum are then sent to Buffer.recvData() to flush it.

    we assume data is simply a string
    """

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
    # TODO: At main, call getSessionID()
    self.sessionID = self.setSessionID(headerTuple[1])
    mask = int('0b1111',2)
    self.flags = bin((headerTuple[2] & (mask << 4)) >> 4)[2:]
    # TODO: At main: if flags = '1000' i.e. more_data, then send pull_request to
    # server for more data
    self.nonce = headerTuple[2] & mask

  def getSessionID(self):
    """Return session ID to upper abstraction"""
    return self.sessionID

  def setSessionID(self, sessionID=0):
    """Set sessionID at client or server"""
    self.sessionID = sessionID

  def flush(self):
    # send self.output to Tor
    print self.output
    self.output = None
