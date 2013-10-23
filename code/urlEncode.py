# Ben Jones
# Georgia Tech Fall 2013
# url-encode.py: collection of functions to hide small chunks of data in urls

#imports
import binascii
import re
from base64 import urlsafe_b64encode, urlsafe_b64decode
from random import choice, randint

#constants
AVAILABLE_TYPES=['market', 'baidu', 'google']
BYTES_PER_COOKIE=30

class UrlEncodeError(Exception):
  pass

def encode(data, encodingType):
  """Encode data as a url

  Parameters:
  data - a string holding the data to be encoded
  encodingType - an string indicating what type of expression to hide the data in

  Returns: a dictionary with the key 'url' referencing a string
  holding the url and the key 'cookie' holding an array of 0 or more
  cookies if data was stored in cookies.

  Note: Cookies will be used if more data is sent than the url
  encoding method can support. When this occurs, as many cookies as
  necessary will be used to encode the data. Please be mindful that
  large numbers of cookies will look suspicious

  """
  if encodingType not in AVAILABLE_TYPES:
      raise(UrlEncodeError("Bad encoding type. Please refer to"
                           "url-encode.AVAILABLE_TYPES for available options"))

  if encodingType == 'market':
    return encodeAsMarket(data)
  #todo write these functions
  elif encodingType == 'baidu':
    return encodeAsBaidu(data)
  elif encodingType == 'google':
    return encodeAsGoogle(data)

def encodeAsCookies(data):
  """Hide data inside a series of cookies"""

  cookies = []
  while data != '':
    if len(data) > BYTES_PER_COOKIE:
      cookies.append(encodeAsCookie(data[:BYTES_PER_COOKIE]))
      data = data[BYTES_PER_COOKIE:]
    else:
      cookies.append(encodeAsCookie(data))
      data = ''
  return cookies

def encodeAsCookie(data):
  """Hide data inside a cookie

  Parameters: data- a string with fewer than 30 characters to encode

  Returns: a string with the key value pair

  Methods: will hide data in a cookie by storing the first 3-10
  characters of data as a key and the rest of the data as the
  value. All data will base64 encoded before it is placed in the url

  Note: this is intended for communication from the client to the
  server so we are sending back set cookies. If decide to use this for
  server-> client communication, we will need to modify this code
  """
  if len(data) <= 5:
    key = 'keyForPadding' #longer than 10 chars, so no need to escape
    value = data
  elif len(data) < 10 and len(data) > 5:
    keyLen = 3
    key = data[:keyLen]
    value = data[keyLen:]
  else:
    keyLen = randint(3, 10)
    key = data[:keyLen]
    value = data[keyLen:]

  key = urlsafe_b64encode(key)
  key = key.replace('=', '+')
  value = urlsafe_b64encode(value)
  cookie = 'Cookie: ' + key + '=' + value
  return cookie

def decodeAsCookie(cookie):
  """Decode data from inside a cookie

  Parameters: cookie- the string of text representing the cookie. This
  will be decoded into data.
  
  Returns: a string with the hidden data
  
  Methods: will do take out the key and value, decode them, and
  concatenate them into the original string

  Note: As with the encodeAsCookie function, this function is designed
  to send data from the client to the server and modifications are
  necessary for convincing traffic from server to client

  """
  pattern = 'Cookie: (?P<key>[a-zA-Z0-9+_\-/]+)=(?P<value>[a-zA-Z0-9+_=\-/]*)'
  match = re.match(pattern, cookie)
  key = match.group('key')
  key = key.replace('+', '=')
  value = match.group('value')
  key = urlsafe_b64decode(key)
  value = urlsafe_b64decode(value)
  #In this case, the data needed padding because it was too
  #short. Since this key is longer than 10 chars, it cannot occur
  #naturally and does not need to be escaped
  if key == 'keyForPadding':
    key = ''
  data = key + value
  return data

def pickDomain():
  """Pick a random domain from the list"""
  domains = ['live.com', 'microsoft.com', 'baidu.com', 'hao123.com']
  return choice(domains)

def pickRandomHexChar():
  """Pick a random hexadecimal character and return it"""
  characters = ['A','B','C','D','E','F']
  return characters[randint(0, 5)]

def encodeAsMarket(data):
  """Hide data inside a url commonly used for email personalization

  Parameters:
  data - the data to encode

  Returns: a dictionary with the key 'url' referencing a string
  holding the url and the key 'cookie' holding an array of 0 or more
  cookies.

  Note: Cookies will be used to store information if the data is over
  40 characters.

  """
  urlData = data
  cookies = []
  if len(data) > 40:
    urlData = data[:40]
    cookies = encodeAsCookies(data[40:])
  urlData = binascii.hexlify(urlData)
  #pad the data to 80 characters
  while len(urlData) < 80:
    urlData += pickRandomHexChar()
  domain = pickDomain()
  #Note: we cannot use urlparse here because it capitalizes our hex
  #values and we are using uppercase to distinguish padding and
  #actual text
  url = 'http://' + 'click.' + domain + '?qs=' + urlData
  retVal = {'url':url, 'cookie':cookies}
  return retVal

def isMarket(url):
  """Return true if this url matches the market pattern"""
  pattern = 'http://click[a-zA-Z0-9.]*[.]com*\?qs=[0-9a-fA-F]{80}'
  matches = re.match(pattern, url)
  if matches != None:
      return True
  return False

def decodeAsMarket(url):
  """Decode data hidden inside a url format for email personalization

  Parameters: url- the url to decode

  Returns: a string with the decoded data

  """
  
  pattern = 'click.*\?qs=(?P<hash>[0-9a-fA-F]*)'
  matches = re.search(pattern, url)
  data = matches.group('hash')
  # strip any padding
  data = data.strip('ABCDEF')
  data = binascii.unhexlify(data)
  return data

def decode(protocolUnit):
  """Decode the given data after matching the url hiding format

  Parameters: data- the url and cookies to be decoded in the form of a
  dictionary with the url stored under the key 'url' and an array of 0
  or more cookies stored under 'cookie'

  Returns: the decoded data in the form of a string

  """
  url = protocolUnit['url']
  cookies = protocolUnit['cookie']
  data = []
  if isMarket(url):
    data.append(decodeAsMarket(url))
  else:
    raise UrlEncodeError("Data does not match a known decodable type")
  for cookie in cookies:
    data.append(decodeAsCookie(cookie))
  return ''.join(data)
