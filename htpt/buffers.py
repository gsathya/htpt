from constants import *

class BufferingException(Exception):
  pass


class Buffer:
  """Stores data, buffers it and sends it to the Framer"""
  def __init__(self, **kArgs):
    """ParametersL kArgs- additional keyword arguments specified for
    the function. Currently, the only additional option has the keyword
    of 'minSeqNum' and an integer value which tells Framer the min
    acceptable sequence number. Example syntax: Buffer(minSeqNum=5)"""

    # Defining buffers like Ben's original Framer code to make recvData() work
    # TODO Check if this is how we want to implement it finally
    self.buffer = [None] * BUFFER_SIZE
    self.callback = None
    if 'minSeqNum' in kArgs:
      self.minAcceptableSeqNum = kArgs['minSeqNum']
      self.maxAcceptableSeqNum = BUFFER_SIZE + self.minAcceptableSeqNum
    else:
      self.minAcceptableSeqNum = 0
      self.maxAcceptableSeqNum = BUFFER_SIZE

  def addCallback(self, callback):
    self.callback = callback

  def addData(self, data):
    # TODO: this function does not make sense anymore as buffer is a list
    # of lendth buffer size. Buffers are only used for reassembly, data sender
    # doesn't need access. Sending decisions will be made in the main file
    # now which will call take tor stream, assemble() it with appropriate
    # headers and encode() it, before flush() to internet.

    # we can't add all the data, there's not enough space
    if len(self.buffer) + len(data) > BUFFER_SIZE:
      # compute remaining space
      buffer_space_rem = BUFFER_SIZE - len(self.buffer)
      self.buffer.append(data[:buffer_space_rem])
      data = data[buffer_space_rem:]

      # set flags to pass to encode function
      # currently we have only one flag to denote more data
      # kwargs = {'more_data':1}
      # flush the buffer
      self.flushBuffer(more_data=1)

      # repeat till we have no data
      self.addData(data)
    else:
      self.buffer.append(data)

  def flushBuffer(self, **kwargs):
    self.callback(self.buffer, **kwargs)
    self.buffer = []

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

  def recvData(self, data, seqNum):
    """Add the given data to the buffer at the right index and flush it
    in the right order.

    Parameters: data- the data from the decoded and disassembled frame
    seqNum- the sequence number of the frame from disassembled header

    Note: the acceptable window is based on available buffer space,
    not unacked packets

    This also keeps flushing out data as received at minimum sequence number
    and advancing the window. For data out of order, we wait for buffer to
    receive packets and then flush it above."""

    if not self.isSeqNumInBuffer(seqNum):
      raise BufferingException("seqNum already received/Not enough space in the buffer")
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
      # keep sending recvData until it finishes
      # TODO what about the seqNum - keep it the same?
      self.recvData(availableData, seqNum)
