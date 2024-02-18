"""
Per display device object - handles websocket connection, holds pixel buffer,
and sending data to a single Pixelblaze
"""
import logging
from threading import Thread
import numpy as np
from pixelblaze import *
from utilities import *


class DisplayDevice:
    pb = None
    ip = None
    thread = None
    name = "<no device>"
    pixelCount = 0
    pixelsReceived = 0
    colorFormat = ColorFormat.RGB
    send_flag = threading.Event()

    pixels = []

    def __init__(self, device):

        # set up device information record
        self.ip = getParam(device, 'ip', "")
        self.name = getParam(device, 'name', "<none>")
        self.pixelCount = getParam(device, 'pixelCount', 0)
        cf = getParam(device, 'colorFormat', "RGB")
        self.colorFormat = ColorFormat.HSV if cf == "HSV" else ColorFormat.RGB

        # initialize output pixel array
        self.pixels = np.zeros(self.pixelCount, dtype=np.float32)

        # start the display device thread
        # each display device runs in its own thread, so any I/O waits
        # will not interfere with other operations.
        # We fully expect Pixelblazes to come and go at odd and inconvenient
        # times, so we need to be able to handle that gracefully.
        # TODO - is a thread smooth enough for this or do we need a process?
        thread = Thread(target=self.run_thread)
        thread.daemon = True
        thread.start()

    def process_pixel_data(self, dmxPixels: bytearray, destPixel: int, count: int):
        """
        Pack RGB color data into a single 32-bit fixed point float for
        compact transmission to a Pixelblaze
        :param dmxPixels: byte array of RGB pixels received from Artnet source
        :param destPixel: index of first pixel in destination array
        :param count: number of pixels to process
        """

        # return immediately if send_flag is true, so we don't stomp on the
        # outgoing frame of data
        if self.send_flag.is_set():
            return

        # copy the pixel data into the display device's pixel buffer
        index = 0
        pixNum = destPixel

        maxIndex = min(self.pixelCount, destPixel + count)
        while pixNum < maxIndex:
            self.pixels[pixNum] = ((dmxPixels[index] << 16) | (dmxPixels[index + 1] << 8) | dmxPixels[
                index + 2]) / 256.0
            if self.pixels[pixNum] > 32767:
                self.pixels[pixNum] = self.pixels[pixNum] - 65536
            pixNum += 1
            index += 3

        # print number of pixels received
        self.pixelsReceived += count
        # print("Pixels received: " + str(self.pixelsReceived) + " of " + str(self.pixelCount) + " for " + self.name)

        # if we have pixels to send, do so
        if self.pixelsReceived >= self.pixelCount:
            # print("Requesting send for " + self.name)
            self.send_flag.set()

    def send_frame(self):
        if self.pb is not None:
            d = "{\"setVars\":{\"pixels\":"+np.array2string(self.pixels, precision=5, separator=',', suppress_small=True)+"}}"
            self.pb.wsSendString(d)

    def run_thread(self):
        # create object for Pixelblaze device and attempt to open and
        # maintain a websocket connection. Note that this can fail,
        # which means that the object will try to establish the connection on the next
        # (and subsequent) attempts to use it.
        self.pb = Pixelblaze(self.ip, ignoreOpenFailure=True)
        self.pb.ws.settimeout(0)
        self.send_flag.clear()

        logging.debug("DisplayDevice: %s (%s) created" % (self.name, self.ip))
        logging.debug("Connection is %s" % ("open" if self.pb.is_connected() else "not open"))

        # loop until the thread gets a kill signal
        while True:
            # if we have pixels to send, do so
            if self.send_flag.is_set():
                # print("Sending frame for " + self.name + " with " + str(self.pixelsReceived) + " pixels.")
                self.send_frame()
                self.pixelsReceived = 0
                self.send_flag.clear()
                # print("Done sending frame for " + self.name)
            # otherwise, devour all incoming messages
            else:
                self.pb.maintain_connection(False)


    def __str__(self):
        return "DisplayDevice: name: " + self.name + " ip: " + self.ip + " pixelCount: " + str(
            self.pixelCount) + " colorFormat: " + str(self.colorFormat)
