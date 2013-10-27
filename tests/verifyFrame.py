# Ben Jones
# Fall 2013
# HTPT Pluggable Transport

import unittest

from htpt import frame

class TestFrame(unittest.TestCase):
  """Test the validity of the framing module in htpt"""

  def setUp(self):
    self.frame = frame.Framer(self.callback)
    
  def callback(data):
    """Dummy callback function to test the framing modules ability to
    send data up"""
    
    self.uploadedData = data

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
