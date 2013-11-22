# Karim Habak
# Georgia Tech Fall 2013
# image-encode.py: Hide data in images
import struct, random, math, os, time
from PIL import Image
import numpy as np

AVAILABLE_TYPES=['bmp', 'png', 'llj']

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
  if imageType =='png':
    return encodeAsPNG(data)
  if imageType =='llj':
    return encodeAsLLJ(data)

    
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
  if imageType =='png':
    return decodeAsPNG(Im)
  if imageType =='llj':
    return decodeAsLLJ(Im)    
        
    
def appendBytes (byteArray, appendedPart):
    for i in range(0, len(appendedPart)):
        byteArray.append(appendedPart[i])    
    return byteArray

def encodeAsBMP(data):
    """
    Encode data in BMP Image
    
    First, Build the header then append 
    the data and return the image bytestream
    """
    gridSize = math.ceil((4+len(data))/3.0)
    
    dimension = max(int(math.ceil(math.sqrt(gridSize))), 101)
    dimension += (4 - dimension%4)
    
    bitmapImage = bytearray()
    #This header matchs Windows paint.
        
    header = {
        'mn1':66,
        'mn2':77,
        'filesize':54+ 3*dimension*dimension,
        'undef1':0,
        'undef2':0,
        'offset':54,
        'headerlength':40,
        'width':dimension, #Based on the data. The minimum BMB size is width is 20
        'height':dimension, #Based on the data. The minimum BMB size is width is 20
        'colorplanes':1, #It is the only legal value
        'colordepth':24,
        'compression':0,
        'imagesize':3*dimension*dimension,
        'res_hor':1,
        'res_vert':1,
        'palette':0,
        'importantcolors':0
        }

    bitmapImage = appendBytes(bitmapImage, struct.pack('<B',header['mn1'])) #index 0
    bitmapImage = appendBytes(bitmapImage, struct.pack('<B',header['mn2'])) #index 1
    bitmapImage = appendBytes(bitmapImage, struct.pack('<L',header['filesize'])) #index 2
    bitmapImage = appendBytes(bitmapImage, struct.pack('<H',header['undef1'])) #index 6
    bitmapImage = appendBytes(bitmapImage, struct.pack('<H',header['undef2'])) #index 8
    bitmapImage = appendBytes(bitmapImage, struct.pack('<L',header['offset'])) #index 10
    bitmapImage = appendBytes(bitmapImage, struct.pack('<L',header['headerlength'])) #index 14
    bitmapImage = appendBytes(bitmapImage, struct.pack('<L',header['width'])) #index 18
    bitmapImage = appendBytes(bitmapImage, struct.pack('<L',header['height'])) #index 22
    bitmapImage = appendBytes(bitmapImage, struct.pack('<H',header['colorplanes'])) #index 26
    bitmapImage = appendBytes(bitmapImage, struct.pack('<H',header['colordepth'])) #index 28
    bitmapImage = appendBytes(bitmapImage, struct.pack('<L',header['compression'])) #index 30
    bitmapImage = appendBytes(bitmapImage, struct.pack('<L',header['imagesize'])) #index 34
    bitmapImage = appendBytes(bitmapImage, struct.pack('<L',header['res_hor'])) #index 38
    bitmapImage = appendBytes(bitmapImage, struct.pack('<L',header['res_vert'])) ##index 42
    bitmapImage = appendBytes(bitmapImage, struct.pack('<L',header['palette'])) #index 46
    bitmapImage = appendBytes(bitmapImage, struct.pack('<L',header['importantcolors'])) #index 50
    bitmapImage = appendBytes(bitmapImage, struct.pack('<L',len(data))) #index 54
    bitmapImage = appendBytes(bitmapImage, data)
    
    "Padding due to data-dimentions missmatching"
    #I add 4 in since I added the size of the data directly after the header.
    for i in range(len(data) +4, 3 * int(header['width']* header['height'])):
        b = getRandomByte()
        bitmapImage = appendBytes(bitmapImage, struct.pack('<B',b))
    
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
    bitmapImage = appendBytes(bitmapImage, padbytes)
    return bitmapImage

def decodeAsBMP(bitmapImage):
    dataOffset = struct.unpack('<L', bitmapImage[10:14])[0]
    dataLength = struct.unpack('<L', bitmapImage[dataOffset:dataOffset + 4])[0]
    data = bitmapImage[dataOffset + 4:dataOffset + 4 + dataLength]
    return data

def getRandomByte():
    x = random.randint(0,255)
    return x

def encodeAsPNG(data):
    bitmapImage = encodeAsBMP(data)
    outfile = open('myImage.bmp','w')
    outfile.write(bitmapImage)
    outfile.close()
    
    img = Image.open('myImage.bmp')
    img.save('myImage.png', 'PNG')
    
    file = open('myImage.png', 'r')
    PNGImage = file.read()
    return PNGImage
    
def decodeAsPNG(PNGImage):
    outfile = open('myImage.png','w')
    outfile.write(PNGImage)
    outfile.close()
    
    img = Image.open('myImage.png')
    img.save('myImage.bmp', 'BMP')
    
    file = open('myImage.bmp', 'r')
    bitmapImage = file.read()
    return decodeAsBMP(bitmapImage)
    
    
def encodeAsLLJ(data):
    bitmapImage = encodeAsBMP(data)
    outfile = open('myImage.bmp','w')
    outfile.write(bitmapImage)
    outfile.close()
    
    os.system('convert myImage.bmp -quality 100 -compress Lossless myImage.llj')
    
    file = open('myImage.llj', 'r')
    LLJImage = file.read()
    return LLJImage
    
def decodeAsLLJ(LLJImage):
    outfile = open('myImage.llj','w')
    outfile.write(LLJImage)
    outfile.close()
    
    os.system('convert myImage.llj -quality 100 -compress Lossless myImage.bmp')
    
    file = open('myImage.bmp', 'r')
    bitmapImage = file.read()
    return decodeAsBMP(bitmapImage)
    
    
if __name__ == '__main__':
    file = open('Test.zip', 'r')
    MyData = file.read()
    
    outfile = open('Test2.zip','w')
    start = time.time()
    result = decode(encode(MyData , 'llj'), 'llj')
    end = time.time()
    print end - start
    outfile.write(result)
    outfile.close()
    
    print "Done"
    
    #encode('Karim Ahmed Ahmed Ibrahim Habak 122343254354365 That is it!', 'llj')