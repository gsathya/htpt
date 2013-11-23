# Ben Jones
# Georgia Tech
# Fall 2013
# basicServer.py: this is a very basic web server to test the client
# portion of the htpt.py code

import select
import socket

from flask import Flask, request, make_response
app = Flask(__name__)

import frame
import urlEncode
import imageEncode

def callback(data):
    print data

#constants
disassembler = frame.Disassemble(callback)
assembler = frame.Assemble()
assembler.seqNum = frame.SeqNumber(-1)

@app.route('/')
def retImages():
    print request.url
    print request.cookies
    encoded = {'url':request.url, 'cookie':[]}
    decoded = urlEncode.decode(encoded)
    disassembler.disassemble(decoded)
    data = assembler.assemble('return message')
    image = imageEncode.encode(data, 'png')
    response = make_response(image)
    response.headers['Content-Type'] = 'image/png'
    response.headers['Content-Disposition'] = 'attachment; filename=img.png'
    return response

if __name__ == "__main__":
    app.run(debug=True)
