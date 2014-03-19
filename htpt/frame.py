# Ben Jones
# Fall 2013
# htpt
# frame.py: ensure in-order delivery of frames for the htpt project

import threading
import struct
#from random import randint

from buffers import Buffer
from constants import *


class FramingException(Exception):
  pass


class SeqNumber():
  _seqNum = -1
  _lock = threading.Lock()
  @classmethod
  def setSeqNum(cls, seqNum):
    cls._lock.acquire()
    cls._seqNum = seqNum
    cls._lock.release()

  @classmethod  
  def getSequenceAndIncrement(cls):
    """
    In a thread safe manner, get the sequence number and increment.
    
    Note: this function is called only when a new client connects
    """
    cls._lock.acquire()
    cls._seqNum = ((cls._seqNum + 1) % MAX_SEQ_NUM)
    cls._lock.release()
    return cls._seqNum

class SessionID():
  """Class to generate a new session ID when a new client connects to the server"""
  
  _sessionID = 0
  _lock = threading.Lock()
  @classmethod
  def setSessionID(cls, sessionID):
    cls._lock.acquire()
    cls._sessionID = sessionID
    cls._lock.release()

  @classmethod  
  def getSessionIDAndIncrement(cls):
    """
    In a thread safe manner, get the session ID.
    
    Note: this function is called only when a new client connects

    """
    cls._lock.acquire()
    cls._sessionID = ((cls._sessionID + 1) % MAX_SESSION_NUM)
    cls._lock.release()
    return cls._sessionID

class Assemble():
  """Class to Assemble a data frame with headers before sending to encoder"""
  def __init__(self, sessionID=0):
    """Initialize SeqNumber object and sessionID"""
    self.seqNum = SeqNumber()
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

    flags format: [ more_data | SYN | X | X | X | X | X | X ]"""

    flags = '00000000'
    flag_list = list(flags)
    if 'more_data' in kwargs:
      more_data = kwargs['more_data']
      flag_list[0]=str(more_data)
    if 'SYN' in kwargs:
      SYN_flag = kwargs['SYN']
      flag_list[1]=str(SYN_flag)
    flags = "".join(flag_list)
    return int(flags, 2)

  def getSeqNum(self):
    """Get sequence number after incrementing"""
    sequenceNumber = self.seqNum.getSequenceAndIncrement()
    return sequenceNumber

  def getHeaders(self, **kwargs):
    """Create a 4 byte struct header in network byte order

    16-bit sequence num | 8-bit session ID | 8-bit flag
    unsigned short (H) | unsigned char (B) | unsigned char (B) packed

    Calls functions to get:
    seqNum- 2 byte sequence number of the frame
    sessionID - 1 byte char int assigned by server
    flags - 8 bit int. check kwargs and set appropriate bit

    returns: header string (struct) packedused in assemble function

    """
    self.sequenceNumber = self.getSeqNum()
    self.sessionID = self.getSessionID()
    self.flags = self.generateFlags(**kwargs)

    headerString = struct.pack('!HBB', self.sequenceNumber, self.sessionID, self.flags)

    return headerString

  def assemble(self, data, **kwargs):
    """Assemble frame as headers + data

    Parameters: data, **kwargs
    data is simply a string
    **kwargs is dict of flags to be set in headers"""

    headers = self.getHeaders(**kwargs)
    frame = headers+data
    return frame


class Disassemble:
  """Class to Disassemble a decoded packet into headers+data before sending to buffers"""
  def __init__(self, callback):
    self.callback = callback
    # allocate a buffer to receive data and flush it
    self.buffer = Buffer()

    self.buffer.addCallback(self.callback)

  def initServerConnection(self, frame):
    """getting password from url; returns data"""
    #get the data
    headers = frame[:4]
    self.retrieveHeaders(headers)
    data = frame[4:]

    #initialize the session id
    #this should be done at higher layer using
    #Assembler.setSessionID(sessionID.getSessionIDAndIncrement())
    #should be done at the server only if client is new and SYN=1

    #set the seqnumber to the value from the frame -- Ben
    #no need to do this as seq num start from 0 and increment

    return data

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

    # receive, reorder and flush at buffer
    self.buffer.recvData(data, self.seqNum)
    return data

  def retrieveHeaders(self, headers):
    """Extract 4 byte header to seqNum, sessionID, Flags"""

    headerTuple = struct.unpack('!HBB', headers)
    self.seqNum = headerTuple[0]

    # retrieve flags
    self.flags = headerTuple[2]

    # retrieved header sets the session ID if SYN flag is set
    # also add a check: if SYN flag not checked then
    # self.sessionid == headerTuple[1]

    #if self.flags & (1<<7):
    self.setSessionID(headerTuple[1])

    # Future: if flags = '1000' i.e. more_data, then send pull_request to
    # server for more data

  def getSessionID(self):
    """Return session ID to upper abstraction"""
    return self.sessionID

  def setSessionID(self, sessionID=0):
    """Set sessionID at client or server"""
    self.sessionID = sessionID

  #def flush(self):
  #  self.buffer.flush()
