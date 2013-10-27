# Ben Jones
# Fall 2013
# htpt
# frame.py: ensure in-order delivery of frames for the htpt project

import threading
import numpy as np

#constants
MAX_SEQ_NUM = 65535
BUFFER_SIZE = 2048
MIN_SIZE_TO_PASS_UP = 512

class FramingException(Exception):
  pass

def init(**args):
  """Initialize the framing package with the given sequence number"""

  if len(args) > 0:
    self.seqNum = args[0]
  else:
    self.seqNum = 0

lock = threading.Lock()
seq_num = 0;
def getSequenceAndIncrement(self):
  """In a thread safe manner, get the sequence number"""
    
  lock.acquire()
  seqNum = ((seqNum + 1) % MAX_SEQ_NUM)
  lock.release()
  return seqNum

class Framer():
  """Class to reassemble the Tor stream"""
  def __init__(self, callback):
    """Initialize the class to frame all of the packages"""

    self.buffer = [None] * BUFFER_SIZE
    self.minAcceptableSeqNum = 0
    self.maxAcceptableSeqNum = BUFFER_SIZE
    #setup a function to call when there is data to receive
    self.recvData = callback

  def isSeqNumInBuffer(self, seqNum):
    """If the sequence number is in the buffer, return True, else False"""
    if seqNum > self.minAcceptableSeqNum:
      if seqNum < self.maxAcceptableSeqNum:
        return True
      #explore the case where the sequence number wraps
      elif (self.minAcceptableSeqNum + BUFFER_SIZE) > MAX_SEQ_NUM:
        #case where maxSeqNum wrapped, so seqNum > min > max
        if(seqNum < MAX_SEQ_NUM):
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

  def addFrameToBuffer(self, data, seqNum):
    """Add the given frame to the buffer

    Parameters: data- the data from the frame
    seqNum- the sequence number of the frame

    Note: we assume that the sequence number is in the window 
    Note: the acceptable window is based on available buffer space,
    not unacked packets
    
    """
    index = (seqNum - self.minAcceptableSeqNum) % MAX_SEQ_NUM
    self.buffer[index] = data
    #see if we have enough data to pass up by coalescing all of the
    #frames and seeing if we meet the min threshold to send up
    dataToSend = 0
    for index in range(BUFFER_SIZE):
      if self.buffer[index == None]:
        #we have found all sendable data
        break
      else:
        dataToSend += len(self.buffer[index])
    #if we have enough data to send up, pass it to the callback
    #function
    if dataToSend > MIN_SIZE_TO_PASS_UP:
      availableData = ''
      #coalesce every data element up to the first missing sequence
      while self.buffer[0] != None:
        availableData += self.buffer.pop(0)
        self.minAcceptableSeqNum = ((self.minAcceptableSeqNum +1) % BUFFER_SIZE)
        self.maxAcceptableSeqNum = ((self.minAcceptableSeqNum +1) % BUFFER_SIZE)
      self.callback(availableData)

  def flushBuffer(self):
    """Send all in order data up to the callback function"""

    for index in range(BUFFER_SIZE):
      if self.buffer[index == None]:
        #we have found all sendable data
        break
      else:
        self.buffer[self.bufferMin] += self.buffer[index]
    self.callback(self.buffer[self.bufferMin])

  def recvFrame(self, data, seqNum):
    """Receive a frame with the specified sequence number"""

    #verify that the packet will fit in the buffer
    if self.isSeqNumInBuffer(seqNum):
      #add the packet to the buffer
      self.addFrameToBuffer(data, seqNum)
    else:
      raise FrameException("Not enough space in the buffer to fit data")