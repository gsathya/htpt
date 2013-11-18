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
    #self.assertEqual(aNum, self.SN.seqNum)
    self.assertTrue(self.SN.initialized)

  def test_getSequenceAndIncrement(self):
    """Ensure that sequence numbers are handed out properly and that
    wrapping occurs correctly"""

    #ensure that we get the next sequence number
    self.SN = frame.SeqNumber(5)
    self.assertEqual(6, self.SN.getSequenceAndIncrement())
    #ensure that we do wrapping
    self.SN = frame.SeqNumber(65534)
    self.assertEqual(0, self.SN.getSequenceAndIncrement())


class TestSessionID(unittest.TestCase):
  """Test sessionID module and lock"""

  def test_init(self):
    aID = 10
    self.SI = frame.SessionID(aID)
    self.SI.sessionID += 500
    #self.assertEqual(aID, self.SI.sessionID)
    self.assertTrue(self.SI.initialized)

  def test_getSessionIDAndIncrement(self):
    """Ensure that session ID are handed out properly and that
    wrapping occurs correctly"""

    #ensure that we get the next session ID on new client
    self.SI = frame.SessionID(5)
    self.assertEqual(6, self.SI.getSessionIDAndIncrement())
    #ensure that we do wrapping
    self.SI = frame.SessionID(255)
    self.assertEqual(0, self.SI.getSessionIDAndIncrement())


class TestAssemble(unittest.TestCase):
  """Test the validity of the Assemble framing module in htpt"""

  def setUp(self):
    self.callback= self.flush
    self.uploadedData = ''
    self.Assembler = frame.Assemble()

  def flush(self, data):
    """Dummy callback function to test the framing modules ability to
    send data up"""
    print "flush data up"
    self.uploadedData = data

  def test_init(self):
    """Ensure that the init method works correctly on the SeqNumber
    object by initializing the sequence number to the correct value"""

    # check initialization with default session ID
    self.assertEqual(self.Assembler.seqNum.seqNum, 0)
    self.assertEqual(self.Assembler.sessionID, 0)

  def test_sessionID(self):
    """Test arbit session ID and set/get"""
    aID = 10
    self.Assembler.setSessionID(aID)
    self.assertEqual(aID, self.Assembler.getSessionID())

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

  def test_getHeaders(self):
    self.Assembler.setSessionID(0)
    self.Assembler.seqNum.seqNum = 0
    self.headerString = self.Assembler.getHeaders()
    # sequence number should be 1
    self.assertEqual(self.headerString[:2], '\x00\x01')
    # session ID should be 0
    self.assertEqual(self.headerString[2], '\x00')
    # flags should be '0000' and nonce is random
    self.assertEqual(self.Assembler.nonce, ord(self.headerString[3]))

    # this should increase sequence number by one, and flags will change
    self.headerString = self.Assembler.getHeaders(more_data=1)
    self.assertEqual(self.headerString[:2], '\x00\x02')
    self.assertEqual((int('1000', 2) << 4) | self.Assembler.nonce, ord(self.headerString[3]))

  def test_assemble(self):
    # less data
    self.data = '0100101010101010101010101'
    self.Assembler.assemble(self.data, more_data=1, SYN=1)
    self.assertEqual(self.data, self.Assembler.output[4:])


class TestDisassemble(unittest.TestCase):
  """Test the validity of the Disassemble framing module in htpt"""

  def setUp(self):
    self.callback = self.flush
    self.downloadedData = ''
    self.Disassembler = frame.Disassemble()
    self.dummyData = '01010101010101010101010101010100101'
    # data, more_data set, seq num =1
    self.test_frame1 = '\x00\x01\x00\x8e01010101010101010101010101010100101'
    # data[:5], no flags, seq num =2
    self.test_frame2 = '\x00\x02\x00\r01010'
    # no data, SYN flag, seq num = 3
    self.test_frame3 = '\x00\x03\x00A'

  def flush(self, data):
    """Dummy callback function to test the framing modules ability to
    send data up"""
    print "flush data up"
    self.downloadedData = data

  def test_init(self):
    """Ensure that the init method works correctly by initializing
    the receive buffer"""

    # check initialization with default session ID
    self.assertEqual(len(self.Disassembler.buffer.buffer), constants.BUFFER_SIZE)

  def test_retrieveHeaders(self):
    self.header = '\x00\x02\x00\r'
    self.Disassembler.retrieveHeaders(self.header)
    self.assertEqual(self.Disassembler.seqNum, 2)
    self.assertEqual(self.Disassembler.sessionID, 0)
    self.assertEqual(self.Disassembler.flags, '0000')
    self.assertEqual(self.Disassembler.nonce, 13)

  def test_disassemble(self):
    self.Disassembler.disassemble(self.test_frame1)
    self.assertEqual(self.Disassembler.seqNum, 1)
    self.assertEqual(self.Disassembler.flags, '1000')
    self.assertEqual(self.Disassembler.output, self.dummyData)

    self.Disassembler.disassemble(self.test_frame2)
    self.assertEqual(self.Disassembler.seqNum, 2)
    self.assertEqual(self.Disassembler.flags, '0000')
    self.assertEqual(self.Disassembler.output, self.dummyData[:5])

    self.Disassembler.disassemble(self.test_frame3)
    self.assertEqual(self.Disassembler.seqNum, 3)
    self.assertEqual(self.Disassembler.flags, '0100')
    self.assertEqual(self.Disassembler.output, '')



if __name__ == "__main__":
  unittest.main()
