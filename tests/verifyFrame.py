# Ben Jones
# Fall 2013
# HTPT Pluggable Transport

import unittest

from htpt import constants
from htpt import frame

class TestSeqNum(unittest.TestCase):
  """Test sequence number module and lock"""

  def test_init(self):
    aNum = 10
    self.SN = frame.SeqNumber(aNum)
    self.SN.seqNum += 500
    self.assertEqual(aNum, SN.seqNum)
    self.assertTrue(SN._initialized)

  def test_getSequenceAndIncrement(self):
    """Ensure that sequence numbers are handed out properly and that
    wrapping occurs correctly"""

    #ensure that we get the next sequence number
    self.SN = frame.SeqNumber(5)
    self.assertEqual(6, SN.getSequenceAndIncrement())
    #ensure that we do wrapping
    self.SN = frame.SeqNumber(65534)
    self.assertEqual(0, SN.getSequenceAndIncrement())


class TestSessionID(unittest.TestCase):
  """Test sessionID module and lock"""

  def test_init(self):
    aID = 10
    self.SI = frame.SessionID(aID)
    self.SI.sessionID += 500
    self.assertEqual(aID, SI.sessionID)
    self.assertTrue(SI._initialized)

  def test_getSessionIDAndIncrement(self):
    """Ensure that session ID are handed out properly and that
    wrapping occurs correctly"""

    #ensure that we get the next session ID on new client
    self.SI = frame.SessionID(5)
    self.assertEqual(6, SI.getSessionIDAndIncrement())
    #ensure that we do wrapping
    self.SI = frame.SessionID(255)
    self.assertEqual(0, SI.getSessionIDAndIncrement())


class TestAssemble(unittest.TestCase):
  """Test the validity of the Assemble framing module in htpt"""

  def setUp(self):
    self.callback= self.flush
    self.uploadedData = ''

  def flush(self, data):
    """Dummy callback function to test the framing modules ability to
    send data up"""
    print "flush data up"
    self.uploadedData = data

  def test_init(self):
    """Ensure that the init method works correctly on the SeqNumber
    object by initializing the sequence number to the correct value"""

    # check initialization with default session ID
    self.Assembler = frame.Assemble()
    self.assertEqual(self.Assembler.seqNum, 0)
    self.assertEqual(self.Assembler.sessionID, 0)

  def test_sessionID(self):
    """Test arbit session ID and set/get"""
    aID = 10
    self.Assembler.setSessionID(aID)
    self.assertEqual(aID, Assembler.getSessionID())

  def test_generateFlags(self):
    # default case no flags
    self.flags = self.Assembler.generateFlags()
    self.assertEqual(self.flags, '0000')
    # only more_data flag
    self.flags = self.Assembler.generateFlags(more_data=1)
    self.assertEqual(self.flags, '1000')
    # only SYN flag
    self.flags = self.Assembler.generateFlags(SYN=1)
    self.assertEqual(self.flags, '0100')
    # more_data and SYN flag
    self.flags = self.Assembler.generateFlags(more_data=1, SYN=1)
    self.assertEqual(self.flags, '1100')
    # some random flag should still be like default case
    self.flags = self.Assembler.generateFlags(no_fucks_to_give=1)
    self.assertEqual(self.flags, '0000', "flags break with arbit data")

  def test_generateNonce(self):
    self.nonce = self.Assembler.generateNonce()
    self.assertLessEqual(self.nonce, 15, "nonce out of range")
    self.assertGreaterEqual(self.nonce, 0, "nonce out of range")

if __name__ == "__main__":
  unittest.main()
