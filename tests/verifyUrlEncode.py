# Ben Jones
# Georgia Tech Fall 2013
# verifyUrlEncode.py: unit tests for the urlEncode module

import unittest
import re
import binascii
from base64 import urlsafe_b64decode, urlsafe_b64encode
from random import randint, choice

from htpt import urlEncode

class TestUrlEncode(unittest.TestCase):
  """Class with methods to test the functions in urlEncode"""

  def test_encode(self):
    """Verify that the encode method works correctly"""
    testData = ['this is a test', 'some text'
                'this is a longer sequence of characters'
                'which should be longer than a normal url']
    for datum in testData:
      testOutput = urlEncode.encode(datum, 'market')
      testDecode = urlEncode.decode(testOutput)
      self.assertEqual(datum, testDecode)
      testOutput = urlEncode.encode(datum, 'baidu')
      testDecode = urlEncode.decode(testOutput)
      self.assertEqual(datum, testDecode)

  def test_encodeAsCookies(self):
    """
    Test that data is correctly inserted into multiple cookies and
    can be correctly retrieved
    """

    testData = ['by jove, this string seems like it may continue for'
               'eternity, possibly to the end of time',
               'this is a shorter message, but still longish',
               'some messages are not too long',
               'some messages can become very verbose and by the intrinsic'
               'nature of their character, they are forced to become'
               'eloquent prose which drags on for lines and lines',
               'Remember, remember, the 5th of November, the gunpowder'
               'treason and plot. I can think of no reason why the 5th of'
               'november should ever be forgot']
    for datum in testData:
      testOutput = urlEncode.encodeAsCookies(datum)
      data = []
      for cookie in testOutput:
        data.append(urlEncode.decodeAsCookie(cookie))
      data = ''.join(data)
      self.assertEqual(data, datum)

  def test_encodeAsCookie(self):
    """Test that data is correctly stored as a cookie"""
    testData = ['text','some text', 'perhaps some more text',
                'a little more text wont hurt',
                'that may have been too much']
    for datum in testData:
      testOutput = urlEncode.encodeAsCookie(datum)
      #verify that the cookie matches our regular expression
      pattern = 'Cookie: (?P<key>[a-zA-Z0-9+_\-/]+)=' \
                '(?P<value>[a-zA-Z0-9+_=\-/]*)'
      match = re.search(pattern, testOutput)
      self.assertIsNotNone(match)
      #verify that the cookie matches the original datum
      key = match.group('key')
      key = key.replace('+', '=')
      value = match.group('value')
      key = urlsafe_b64decode(key)
      if key == 'keyForPadding':
        key = ''
      value = urlsafe_b64decode(value)
      self.assertEqual(key + value, datum)

  def test_decodeAsCookie(self):
    """Test that cookies can be correctly decoded"""
    testData = ['something', 'whisper, whisper','longer text than this'
                'a much longer text than you expected', 'tiny']
    for datum in testData:
      if len(datum) < 10 and len(datum) > 5:
        keyLen = 3
      elif len(datum) <= 5:
        key = 'keyForPadding' #longer than 10 chars, so no need to escape
        key = urlsafe_b64encode(key)
        key = key.replace('=', '+')
        value = urlsafe_b64encode(datum)
        cookie = 'Cookie: ' + key + '=' + value
        self.assertEqual(urlEncode.decodeAsCookie(cookie), datum)
        break
      else:
        keyLen = randint(3, 10)
      key = datum[:keyLen]
      value = datum[keyLen:]
      key = urlsafe_b64encode(key)
      key = key.replace('=', '+')
      value = urlsafe_b64encode(value)
      cookie = 'Cookie: ' + key + '=' + value
      self.assertEqual(urlEncode.decodeAsCookie(cookie), datum)

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
                'even more text that seems moderately longish']
    for datum in testData:
        output = urlEncode.encodeAsMarket(datum)
        testOutput = output['url']
        #verify that the output is in the correct form
        pattern = 'http://[a-zA-Z0-9.]*[.]com\?qs=(?P<hash>[0-9a-fA-F]*)'
        matches = re.match(pattern, testOutput)
        self.assertNotEqual(matches, None)
        #verify that the output is actually the hex representation of
        #the data
        hashPart = matches.group('hash')
        self.assertEqual(len(hashPart), 80)
        #as with the real code in urlEncode, this is a one liner to
        #convert the data length counter from hex into an integer that
        #we can use later
        dataLen = int(hashPart[:2], 16)
        testDatum = hashPart[2:dataLen+2]
        testDatum = binascii.unhexlify(testDatum)
        for cookie in output['cookie']:
          testDatum += urlEncode.decodeAsCookie(cookie)
        self.assertEqual(testDatum, datum)

  def test_isMarket(self):
    """
    Verify that isMarket correctly identifies urls in the proper
    form
    """
    trueData = ['http://click.live.com?qs=1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
                'http://click.google.com?qs=fedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321']
    falseData = ['http://click.live.com?qs=123fad', 'fake', 'bad url', 'google.com']
    for datum in trueData:
      self.assertTrue(urlEncode.isMarket(datum))
    for datum in falseData:
      self.assertFalse(urlEncode.isMarket(datum))

  def test_decodeAsMarket(self):
    """Verify that decodeAsMarket correctly decodes data"""

    testData = [ self.gen_random_hex_chars() for index in range(5)]
    testData[4] = testData[4][:78]
    testData[4] = hex(70)[2:] + testData[4]
    testStrings = []
    for datum in testData:
      dataLen = int(datum[:2], 16)
      testStrings.append(binascii.unhexlify(datum[2:dataLen+2]))

    #include a test to be sure that we can correctly decode padding
    for datum in testData:
      #Note: as with urlEncode, we cannot use urlparse because it
      #converts hex to uppercase and we are using uppercase for
      #padding, lowercase for data
      url = 'http://' + 'click.live.com?qs=' + datum
      testOutput = urlEncode.decodeAsMarket(url)
      dataLen = int(datum[:2], 16)
      testString = binascii.unhexlify(datum[2:dataLen+2])
      self.assertEqual(testOutput, testString)

  def gen_random_hex_chars(self):
    """Create random 80 character strings of hex for testing"""

    characters = ['0','1','2','3','4','5','6','7',
                  '8','9','a','b','c','d','e','f']
    stringy = []
    length = randint(1, 39)
    length = length *2
    lenStr = hex(length)[2:]
    if len(lenStr) == 1:
      stringy.append('0'+lenStr)
    else:
      stringy.append(lenStr)
    for x in range(78):
      stringy.append(choice(characters))
    return ''.join(stringy)

  def test_isBaidu(self):
    """verify that we can detect urls of the form
    http://www.baidu.com/s?wd=text+other"""

    trueUrls = ['http://www.baidu.com/s?wd=mao+is+cool&rsv_bp='
            '0&ch=&tn=baidu&bar=&rsv_spt=3&ie=utf-8',
            'http://www.baidu.com/s?wd=freedom+is+nice'
            '&rsv_bp=0&rsv_spt=3&ie=utf-8']
    falseUrls = ['http://www.google.com', 'stirngy']
    for url in trueUrls:
      self.assertTrue(urlEncode.isBaidu(url))
    for url in falseUrls:
      self.assertFalse(urlEncode.isBaidu(url))

  def test_decodeAsBaidu(self):
    """
    Verify that we correctly decode Baidu urls

    Note: we are just testing that we can decode what we encode. We
    are relying on the test_encodeAsBaidu functionality to make sure
    that the encoding correctly hides the data

    Dependencies: this function depends on encodeAsBaidu and decodeAsCookie

    """
    testData = ['this is a string', 'some-data-that-appears-mildly'
                '-long-and-hopefully-_exceeds40chars',
                'another string']
    for datum in testData:
      testOutput = urlEncode.encodeAsBaidu(datum)
      cookieData = []
      for cookie in testOutput['cookie']:
        cookieData.append(urlEncode.decodeAsCookie(cookie))
      cookieData = ''.join(cookieData)
      urlData = urlEncode.decodeAsBaidu(testOutput['url'])
      self.assertEqual(datum, urlData + cookieData)

  def test_encodeAsBaidu(self):
    """
    Verify that the Baidu encoding actually looks like it should

    Dependencies: decodeAsEnglish, decodeAsCookie

    """
    testData = ['this is a string', 'some-data-that-appears-mildly'
                '-long-and-hopefully-_exceeds40chars',
                'another string']
    for datum in testData:
      testOutput = urlEncode.encodeAsBaidu(datum)
      #assert that cookies were created if needed
      if len(datum) > 40:
        self.assertNotEqual(testOutput['cookie'], [])
      #assert that the url is in the correct form
      pattern = 'http://www.baidu.com/s\?wd=(?P<data>[\S+]+)'
      matches = re.match(pattern, testOutput['url'])
      self.assertIsNotNone(matches)
      #assert that the url and cookies correctly decode
      words = matches.group('data')
      words = words.split('+')
      decoded = urlEncode.decodeAsEnglish(words)
      for cookie in testOutput['cookie']:
        decoded += urlEncode.decodeAsCookie(cookie)
      self.assertEqual(datum, decoded)

  def test_encodeAsEnglish(self):
    """Verify that we are correctly encoding text as english"""

    testData = ['some text', 'more texty things',
                'but wait, there is even more and you even get a :']
    for datum in testData:
      testOutput = urlEncode.encodeAsEnglish(datum)
      #test that we are using the correct format
      for word in testOutput:
        self.assertIn(word, urlEncode.LOOKUP_TABLE)
      #verify that test decodes correctly
      testString = []
      for word in testOutput:
        testString.append(urlEncode.REVERSE_LOOKUP_TABLE[word])
      testString = ''.join(testString)
      self.assertEqual(datum, binascii.unhexlify(testString))

  def test_decodeAsEnglish(self):
    """Verify that we can correctly decode the hidden data"""

    testData = ['somethinga45lkh;asf wonddeasdful', 'other',
                'stuffy awesomeness']
    for datum in testData:
      testOutput = urlEncode.encodeAsEnglish(datum)
      self.assertEqual(datum, urlEncode.decodeAsEnglish(testOutput))

  def test_isGoogle(self):
    """Verify that urls are correctly identified as Google url"""

    trueData = ['http://www.google.com/search?q=this+is+a+test',
                'http://www.google.com/search?q=a+the+adsfasd']
    falseData = ['http://www.baidu.com/search?q=this+is+a+test',
                 'http://www.google.com/search?q=%09808']
    for datum in trueData:
      self.assertTrue(urlEncode.isGoogle(datum))
    for datum in falseData:
      self.assertFalse(urlEncode.isGoogle(datum))

  def test_decodeAsGoogle(self):
    """Verify that encoded text can be decoded again
    
    Dependencies: encodeAsGoogle

    """
    testData = ['some text', 'another test', 'still more text',
                'an example that is liable to introduce cookies'
                '- scrumptous, scrumptous cookies']
    for datum in testData:
      testOutput = urlEncode.encodeAsGoogle(datum)
    cookieData = []
    for cookie in testOutput['cookie']:
      cookieData.append(urlEncode.decodeAsCookie(cookie))
    cookieData = ''.join(cookieData)
    urlData = urlEncode.decodeAsGoogle(testOutput['url'])
    self.assertEqual(datum, urlData + cookieData)

  def test_encodeAsGoogle(self):
    """Verify that data can be properly hidden as a google search
    string

    Dependencies: decodeAsEnglish, decodeAsCookie
    
    """
    testData = ['some text', 'another test', 'still more text',
                'an example that is liable to introduce cookies'
                '- scrumptous, scrumptous cookies']
    for datum in testData:
      testOutput = urlEncode.encodeAsGoogle(datum)
      #assert that cookies were created if needed
      if len(datum) > 40:
        self.assertNotEqual(testOutput['cookie'], [])
      #assert that the url is in the correct form
      pattern = 'http://www.google.com/search\?q=(?P<data>[a-zA-Z+]+)'
      matches = re.match(pattern, testOutput['url'])
      self.assertIsNotNone(matches)
      #assert that the url and cookies correctly decode
      words = matches.group('data')
      words = words.split('+')
      decoded = urlEncode.decodeAsEnglish(words)
      for cookie in testOutput['cookie']:
        decoded += urlEncode.decodeAsCookie(cookie)
      self.assertEqual(datum, decoded)

if __name__ == '__main__':
  unittest.main()
