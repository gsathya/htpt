# Karim Habak
# Georgia Tech Fall 2013
# image-encode.py: Hide data in images
import struct, random, math
from PIL import Image
import numpy as np

AVAILABLE_TYPES=['bmp', 'jpg']

class ImageEncodeError(Exception):
  pass
  
def encode(data, imageType):
  """
  Encode data as a image

  Parameters:
  data - a string holding the data to be encoded
  imageType - an string indicating what type of expression to hide
  the data in

  Returns: a data stream of image

  """
  if imageType not in AVAILABLE_TYPES:
      raise(ImageEncodeError("Non-supported or invalid image type."))

  if imageType == 'bmp':
    return encodeAsBMP(data)
  if imageType =='jpg':
    return encodeAsJPEG(data)
    
    
def decode(Im, imageType):
  """
  Encode data as a image

  Parameters:
  data - a string holding the data to be encoded
  imageType - an string indicating what type of expression to hide
  the data in

  Returns: a data stream of image

  """
  if imageType not in AVAILABLE_TYPES:
      raise(ImageEncodeError("Non-supported or invalid image type."))

  if imageType == 'bmp':
    return decodeAsBMP(Im)
  if imageType =='jpg':
    return decodeAsJPEG(Im)

def encodeAsBMP(data):
    """
    Encode data in BMP Image
    
    First, Build the header then append 
    the data and return the image bytestream
    """
    gridSize = math.ceil((4+len(data))/3.0)
    
    bitmapImage = []
    header = {
        'mn1':66,
        'mn2':77,
        'filesize':0,
        'undef1':0,
        'undef2':0,
        'offset':54,
        'headerlength':40,
        'width':math.ceil(math.sqrt(gridSize)),
        'height':math.ceil(math.sqrt(gridSize)),
        'colorplanes':0,
        'colordepth':24,
        'compression':0,
        'imagesize':
        0,
        'res_hor':0,
        'res_vert':0,
        'palette':0,
        'importantcolors':0
        }
    bitmapImage.append(struct.pack('<B',header['mn1']))
    bitmapImage.append(struct.pack('<B',header['mn2']))
    bitmapImage.append(struct.pack('<L',header['filesize']))
    bitmapImage.append(struct.pack('<H',header['undef1']))
    bitmapImage.append(struct.pack('<H',header['undef2']))
    bitmapImage.append(struct.pack('<L',header['offset']))
    bitmapImage.append(struct.pack('<L',header['headerlength']))
    bitmapImage.append(struct.pack('<L',header['width']))
    bitmapImage.append(struct.pack('<L',header['height']))
    bitmapImage.append(struct.pack('<H',header['colorplanes']))
    bitmapImage.append(struct.pack('<H',header['colordepth']))
    bitmapImage.append(struct.pack('<L',header['compression']))
    bitmapImage.append(struct.pack('<L',header['imagesize']))
    bitmapImage.append(struct.pack('<L',header['res_hor']))
    bitmapImage.append(struct.pack('<L',header['res_vert']))
    bitmapImage.append(struct.pack('<L',header['palette']))
    bitmapImage.append(struct.pack('<L',header['importantcolors']))
    bitmapImage.append(struct.pack('<L',len(data)))
    bitmapImage.append(data)
    
    "Padding due to data-dimentions missmatching"
    for i in range(len(data) +4, 3 * int(header['width']* header['height'])):
        b = getRandomByte()
        bitmapImage.append(struct.pack('<B',b))
    
    "Extra Padding due to colordepth"
    rowMod = (header['width']*header['colordepth']/8) % 4
    if rowMod == 0:
        padding = 0
    else:
        padding = (4 - rowMod)
    padbytes = ''
    for i in range(int(padding)):
        x = struct.pack('<B',0)
        padbytes = padbytes + x
    bitmapImage.append(padbytes)
    print bitmapImage
    print bytearray(bitmapImage)
    return bitmapImage

def decodeAsBMP(bitmapImage):
    dataOffset = struct.unpack('<L', bitmapImage[10:14])
    dataLength = struct.unpack('<L', bitmapImage[dataOffset:dataOffset + 4])
    data = bitmapImage[dataOffset + 4:dataOffset + 4 + dataLength]
    return data

def getRandomByte():
    x = random.randint(0,255)
    return x

def encodeAsJPEG(data):
    bitmapImage = encodeAsBMP(data)
    outfile = open('myImage.bmp','wb')
    outfile.write(bytearray(bitmapImage))
    outfile.close()
    img = Image.open('myImage.bmp')
    img.save('myImage.jpg', 'JPEG')
    
    file = open('myImage.jpg', 'r')
    JPEGImage = file.read()
    return JPEGImage
    
def decodeAsJPEG(JPEGImage):
    outfile = open('myImage.jpg','wb')
    outfile.write(JPEGImage)
    outfile.close()
    
    img = Image.open('myImage.jpg')
    img.save('myImage.bmp', 'BMP')
    
    file = open('myImage.bmp', 'r')
    bitmapImage = file.read()
    return decodeAsBMP(bitmapImage)
    
    
if __name__ == '__main__':
    decode(encode('Karim Ahmed Ahmed Ibrahim Habak 122343254354365 That is it', 'jpg'), 'jpg')