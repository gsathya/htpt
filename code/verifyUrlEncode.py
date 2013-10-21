# Ben Jones
# Georgia Tech Fall 2013
# verifyUrlEncode.py: unit tests for the urlEncode module

import unittest
import re
import binascii
from random import randint

import urlEncode

class TestUrlEncode(unittest.TestCase):
  """Class with methods to test the functions in urlEncode"""

  def test_encode(self):
    """Verify that the encode method works correctly"""
    testData = ['this is a test', 'some text']
    #            'this is a longer sequence of characters \
    #            which should be longer than a normal url']
    for datum in testData:
      #todo update this to enumerate all types of valid url encoding
      #schemes and test each one
      testOutput = urlEncode.encode(datum, 'market')
      testDecode = urlEncode.decode(testOutput)
      self.assertEqual(datum, testDecode)

  def test_encodeAsCookies(self):
    """Test that data is correctly inserted into multiple cookies"""
    #todo write the function and the test
    pass

  def test_encodeAsCookie(self):
    """Test that data is correctly stored as a cookie"""
    #todo write the function and the test
    pass

  def test_pickDomain(self):
    """Test that a domain is correctly returned"""
    
    for iteration in range(5):
      domain = urlEncode.pickDomain()
      pattern = '[0-9a-zA-Z]*[.]com'
      matches = re.search(pattern, domain)
      self.assertNotEqual(matches, None)

  def test_pickRandomHexChar(self):
    """Valdiate that the function retuns a valid hex char"""
    
    characters = ['A','B','C','D','E','F']
    for i in range(50):
      char = urlEncode.pickRandomHexChar()
      self.assertIn(char, characters)

  def test_encodeAsMarket(self):
    """Verify that data are correctly stored in the url market form"""
    
    testData = ['some text', 'more text', 
                'even more text that seems moderately lon']
    for datum in testData:
        output = urlEncode.encodeAsMarket(datum)
        testOutput = output['url']
        #verify that the output is in the correct form
        pattern = '[a-zA-Z0-9.]*[.]com\?qs=(?P<hash>[0-9a-fA-F]*)'
        matches = re.match(pattern, testOutput)
        self.assertNotEqual(matches, None)
        #verify that the output is actually the hex representation of
        #the data
        hashPart = matches.group('hash')
        self.assertEqual(len(hashPart), 80)
        hashPart = hashPart.rstrip('ABCDEF')
        self.assertEqual(binascii.unhexlify(hashPart), datum)

  def test_isMarket(self):
    """Verify that isMarket correctly identifies urls in the proper
    form"""

    trueData = ['click.live.com?qs=1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef', 
                'click.google.com?qs=fedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321']
    falseData = ['click.live.com?qs=123fad', 'fake', 'bad url', 'google.com']
    for datum in trueData:
      self.assertTrue(urlEncode.isMarket(datum))
    for datum in falseData:
      self.assertFalse(urlEncode.isMarket(datum))

  def test_decodeAsMarket(self):
    """Verify that decodeAsMarket correctly decodes data"""

    testData = [ self.gen_random_hex_chars() for index in range(5)]
    testData[4] = testData[4][:76]
    testStrings = [binascii.unhexlify(testData[index]) for index in range(5)]
    #include a test to be sure that we can correctly decode padding
    testData[4] += "ABCD"
    for datum in testData:
      url = 'click.live.com' + '?qs=' + datum
      testOutput = urlEncode.decodeAsMarket(url)
      testString = binascii.unhexlify(datum.rstrip('ABCDEF'))
      self.assertEqual(testOutput, testString)

  def gen_random_hex_chars(self):
    """Create random 80 character strings of hex for testing"""

    characters = ['0','1','2','3','4','5','6','7',
                  '8','9','a','b','c','d','e','f']
    index = 0
    stringy = ''
    while index < 80:
      stringy += characters[randint(0,15)]
      index += 1
    return stringy

if __name__ == '__main__':
  unittest.main()
