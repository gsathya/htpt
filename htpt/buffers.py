from constants import *

class Buffer:
  """Stores data, buffers it and sends it to the Framer"""
  def __init__(self):
    self.buffer = []
    self.callback = None

  def addCallback(self, callback):
    self.callback = callback

  def addData(self, data):
    # we can't add all the data, there's not enough space
    if len(self.buffer) + len(data) > BUFFER_SIZE:
      # compute remaining space
      buffer_space_rem = BUFFER_SIZE - len(self.buffer)
      self.buffer.append(data[:buffer_space_rem])
      data = data[buffer_space_rem:]

      # flush the buffer
      self.flushBuffer()

      # repeat till we have no data
      self.addData(data)
    else:
      self.buffer.append(data)

  def flushBuffer(self):
    self.callback(self.buffer)
    self.buffer = []