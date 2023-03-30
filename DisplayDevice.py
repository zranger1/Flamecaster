"""
Per display device object - handles websocket connection, holds pixel buffer,
and sending data to a single Pixelblaze
"""
from pixelblaze import *
from enum import Enum
import ConfigParser
import Universe

class ColorFormat(Enum) :
    RGB = 0
    HSV = 1

class DisplayDevice:
    pb = None
    ip = None
    name = "<no device>"
    pixelCount = 0
    colorFormat = ColorFormat.RGB

    pixels = []

    def __init__(self, device):
        # grab generic device data from json config
        self.ip = device['ip']
        self.name = device['name']
        self.pixelCount = device['pixelCount']
        self.colorFormat = ColorFormat.HSV if device['colorFormat'] == "HSV" else ColorFormat.RGB

        # initialize output pixel array
        # TODO - numpy for performance
        self.pixels = [0 for x in range(device['pixelCount'])]

        # open Pixelblaze device
        # TODO - need to make sure this can fail and have everything
        # TODO - else still continue.
        self.pb = Pixelblaze(device['ip'])

    def pack_data(self, dmxPixels, destPixel):
        index = 0
        pixNum = destPixel

        max = destPixel + dmxPixels.length
        while(pixNum < max):
            self.pixels[pixNum] = ((dmxPixels[index] << 16) | (dmxPixels[index + 1] << 8) | dmxPixels[index + 2]) / 256.0
            if (self.pixels[pixNum] > 32767) :
                self.pixels[pixNum] = self.pixels[pixNum] - 65536
            pixNum += 1
            index += 3

    def send_frame(self, pb):
        self.pb.setVariable("pixels", self.pixels[0:self.pixelCount])
