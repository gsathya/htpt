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
  # initialize this to -1 so that the first sequence number comes out to 0
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

class Assembler():
  """Class to Assemble a data frame with headers before sending to encoder"""

  def __init__(self, sessionID=0):
    """Initialize SeqNumber object and sessionID"""
    # initialize the seq number to 0 and start sending frames
    self.seqNum = SeqNumber()
    self.setSessionID(sessionID)

  def setSessionID(self, sessionID):
    """
    Set the session ID for this sender

    Note: this should be called by the client upon receiving the ACK
    packet (first packet) back from the server. The client should get
    the session ID from the Disassembler and add it here

    """
    self.sessionID = sessionID

  def getSessionID(self):
    """
    Get the sessionID for this assembler

    Note: this is not an instance of the SessionID class which
    generates unique sessionIDs. This stores the generated ID.

    Note: this function will be called when creating the flags for an
    outgoing frame

    """
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


class Disassembler:
  """Class to Disassemble a decoded packet into headers+data before sending to buffers"""
  def __init__(self, callback):
    self.callback = callback
    # allocate a buffer to receive data
    self.buffer = Buffer()
    self.buffer.addCallback(self.callback)

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
#    print "In disassemble: {} {}".format(data, self.buffer.buffer)
    self.buffer.recvData(data, self.seqNum)
    return data

  def retrieveHeaders(self, headers):
    """Extract 4 byte header to seqNum, sessionID, Flags"""

    seqNum, sessionID, flags = parseHeaders(headers)

    self.seqNum = seqNum

    # retrieve flags
    self.flags = flags

    # retrieved header sets the session ID if SYN flag is set
    # also add a check: if SYN flag not checked then
    # self.sessionid == headerTuple[1]

    #if self.flags & (1<<7):
    self.setSessionID(sessionID)

    # TODO: if flags = '1000' i.e. more_data, then send pull_request to
    # server for more data

  def getSessionID(self):
    """Return session ID to upper abstraction"""
    return self.sessionID

  def setSessionID(self, sessionID=0):
    """Set sessionID at client or server"""
    self.sessionID = sessionID

  #def flush(self):
  #  self.buffer.flush()

def parseHeaders(headers):
  """ Parse the headers and return the values"""
  headerTuple = struct.unpack('!HBB', headers)
  seqNum = headerTuple[0]
  sessionID = headerTuple[1]
  flags = headerTuple[2]
  return seqNum, sessionID, flags

def initServerConnection(frame, passwords, callback):
  """
  Respond to an initialization request from a client

  1. ensure that the password is correct-> do this by verifying that
  it matches one of the passwords in the list
  2. initialize the sessionID for this client
  3. return an assembler and disassembler for this client

  Note: this is a module method, it is not associated with an object

  """

  # parse the headers
  headers = frame[:4]
  seqNum, sessionID, flags = parseHeaders(headers)
  data = frame[4:]

  # Part 1: validate the password
  # if this is a bad login attempt, then return False
  if data not in passwords:
    print "len: {} frame: {} seqNum: {} sessionID: {} flags: {} ".format(len(frame), frame, str(seqNum), str(sessionID), str(flags))
    return False, False

  # Part 2: initialize the session id using the SessionID class methods
  sessionID = SessionID.getSessionIDAndIncrement()

  # Part 3: return an assembler and disassembler for the client
  sender = Assembler()
#  print "seqNum: {}".format(sender.seqNum._seqNum)
  sender.setSessionID(sessionID)
  receiver = Disassembler(callback)
  receiver.setSessionID(sessionID)

  return sender, receiver

