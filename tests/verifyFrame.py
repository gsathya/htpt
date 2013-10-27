# Ben Jones
# Fall 2013
# HTPT Pluggable Transport

import unittest

from htpt import frame

class TestFrame(unittest.TestCase):
  """Test the validity of the framing module in htpt"""

  def setUp(self):
    self.callback= self.recvData
    self.frame = frame.Framer(self.callback)
    self.uploadedData = ''

  def recvData(self, data):
    """Dummy callback function to test the framing modules ability to
    send data up"""
    self.uploadedData = data

  def test_init(self):
    """Ensure that the init method works correctly on the SeqNumber
    object by initializing the sequence number to the correct value"""
    
    aNum = 10
    frame.SeqNumber._seqNum = aNum +500
    frame.init(aNum)
    self.assertEqual(aNum, frame.SeqNumber._seqNum)
    self.assertTrue(frame.SeqNumber._initialized)

  def test_getSequenceAndIncrement(self):
    """Ensure that sequence numbers are handed out properly and that
    wrapping occurs correctly"""

    #ensure that we get the next sequence number
    frame.init(5)
    self.assertEqual(6, frame.getSequenceAndIncrement())
    #ensure that we do wrapping
    frame.init(65534)
    self.assertEqual(0, frame.getSequenceAndIncrement())

  def test_FramerConstructor(self):
    """Verify that the constructor correctly establishes the buffers
    and constants to receive data"""

    self.frame = frame.Framer(self.callback)
    #check that the buffer exists and is the correct length
    self.assertIsNotNone(self.frame.buffer)
    self.assertEqual(frame.BUFFER_SIZE, len(self.frame.buffer))

    #check that the min and max seq numbers were set up correctly
    self.assertEqual(self.frame.minAcceptableSeqNum, 0)
    self.assertEqual(self.frame.maxAcceptableSeqNum, frame.BUFFER_SIZE)
    self.frame = frame.Framer(self.callback, minSeqNum = 50)
    self.assertEqual(self.frame.minAcceptableSeqNum, 50)
    self.assertEqual(self.frame.maxAcceptableSeqNum, frame.BUFFER_SIZE + 50)

    #check that the callback is setup correctly
    self.assertEqual(self.frame.recvData, self.callback)

  def test_isSeqNumInBuffer(self):
    """Test whether this function correctly identifies when sequence
    numbers are in or out of the scope of the buffer"""

    #test 1-> no wrapping min < num < max
    self.frame.minAcceptableSeqNum = 1
    self.frame.maxAcceptableSeqNum = 10
    seqNum = 5
    self.assertEqual(True, self.frame.isSeqNumInBuffer(seqNum))
    #test 2-> wrap max, max < min < num
    self.frame.minAcceptableSeqNum = 65000
    self.frame.maxAcceptableSeqNum = 1
    seqNum = 65005
    self.assertEqual(True, self.frame.isSeqNumInBuffer(seqNum))
    #test 3-> wrap max and num, num < max < min
    self.frame.minAcceptableSeqNum = 65000
    self.frame.maxAcceptableSeqNum = 20
    seqNum = 3
    self.assertEqual(True, self.frame.isSeqNumInBuffer(seqNum))
    #test 4-> too low-> num < min < max
    self.frame.minAcceptableSeqNum = 60000
    self.frame.maxAcceptableSeqNum = 60002
    seqNum = 3
    self.assertEqual(False, self.frame.isSeqNumInBuffer(seqNum))
    #test 5-> too high-> min < max < num
    self.frame.minAcceptableSeqNum = 60000
    self.frame.maxAcceptableSeqNum = 65002
    seqNum = 65005
    self.assertEqual(False, self.frame.isSeqNumInBuffer(seqNum))
    #test 6-> bad seq num-> max < min < num, where num > max_seq_num
    self.frame.minAcceptableSeqNum = 65000
    self.frame.maxAcceptableSeqNum = 5
    seqNum = 68000
    self.assertEqual(False, self.frame.isSeqNumInBuffer(seqNum))

  def test_recvFrame(self):
    """Test that frames are correctly added to the buffer"""
    
    #initialize our window from 0-> frame.BUFFER_SIZE and set the size
    #to pass up to 10 characters
    self.framer = frame.Framer(self.callback, minSeqNum=0)
    frame.MIN_SIZE_TO_PASS_UP = 10
    self.uploadedData = ''
    #start by testing that out of order packets are queued correctly
    self.framer.recvFrame('hello', 0)
    self.framer.recvFrame(' wordy', 2)
    self.framer.recvFrame(' adverb', 3)
    self.framer.recvFrame(' otherwise', 4)
    #verify that nothing has been sent up yet
    self.assertEqual(self.uploadedData, '')
    #and verify that everything gets delivered in order
    self.framer.recvFrame(' stuffy', 1)
    self.assertEqual(self.uploadedData, 'hello stuffy wordy adverb otherwise')
    
    #verify that data gets sent as soon as the min size to pass up is hit
    self.uploadedData = ''
    self.framer = frame.Framer(self.callback, minSeqNum = 0)
    frame.MIN_SIZE_TO_PASS_UP = 10
    self.framer.recvFrame('hello', 0)
    self.framer.recvFrame(' working', 1)
    self.assertEqual(self.uploadedData, 'hello working')

    #verify that frames out of the window get dropped
    self.uploadedData = ''
    self.assertRaises(frame.FramingException, self.framer.recvFrame,'something', 50000)
    self.assertNotIn('something', self.framer.buffer)

  def test_flushBuffer(self):
    """Verify that we can correctly flush the buffer"""
    
    self.uploadedData = ''
    self.framer = frame.Framer(self.callback, minSeqNum = 0)
    self.framer.recvFrame('hello', 0)
    self.framer.flushBuffer()
    self.assertEqual(self.uploadedData, 'hello')
