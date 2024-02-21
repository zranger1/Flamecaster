"""
Per display device object - handles websocket connection, holds pixel buffer,
and sending data to a single Pixelblaze

TODO - respect max frame rate
"""
import threading
from threading import Thread

import numpy as np

from ArtnetUtils import *
from pixelblaze import *


class DisplayDevice:
    parent = None
    pb = None
    ip = None
    thread = None
    name = "<no device>"
    pixelCount = 0
    pixelsReceived = 0
    maxFps = 1000
    frame_timer = 0
    ms_per_frame = 0
    packets_in = 0
    packets_out = 0
    run_flag = threading.Event()

    sendFrame = None

    pixels = []

    def __init__(self, device, config):

        # set up device information record
        self.ip = getParam(device, 'ip', "")
        self.name = getParam(device, 'name', "<none>")
        self.pixelCount = getParam(device, 'pixelCount', 0)

        # both the device and the system configuration can specify a maxFps.
        # We take the lowest of the two.
        self.maxFps = getParam(device, 'maxFps', 1000)
        self.maxFps = min(config["maxFps"], self.maxFps)
        self.ms_per_frame = 1000 / self.maxFps

        logging.debug("DisplayDevice: %s maxFps: %d (%d ms/frame)" % (self.name, self.maxFps, self.ms_per_frame))

        self.sendMethod = self._send_pre_init

        # initialize output pixel array
        self.pixels = np.zeros(self.pixelCount, dtype=np.float32)

        # start the display device thread
        # each display device runs in its own thread, so any I/O waits
        # will not interfere with other operations.
        # We fully expect Pixelblazes to come and go at odd and inconvenient
        # times, so we need to be able to handle that gracefully.
        thread = Thread(target=self.run_thread)
        thread.daemon = True
        self.run_flag.set()
        self.frame_timer = 0
        thread.start()

    def process_pixel_data(self, dmxPixels: bytearray, destPixel: int, count: int):
        """
        Pack RGB color data into a single 32-bit fixed point float for
        compact transmission to a Pixelblaze
        :param dmxPixels: byte array of RGB pixels received from Artnet source
        :param destPixel: index of first pixel in destination array
        :param count: number of pixels to process
        """

        # logging.debug("  packet for " + self.name + " with " + str(count) + " pixels.")
        self.packets_in += 1
        self.pixelsReceived += count

        # copy the pixel data into the display device's pixel buffer
        index = 0
        pixNum = destPixel

        # Pack the RGB color data into a single 32-bit fixed point float for compact transmission to a Pixelblaze.
        # This is done by shifting red, green and blue values into a 32-bit integer and dividing
        # the result by 256 to produce a float.
        maxIndex = min(self.pixelCount, destPixel + count)
        while pixNum < maxIndex:
            self.pixels[pixNum] = ((dmxPixels[index] << 16) | (dmxPixels[index + 1] << 8) | dmxPixels[
                index + 2]) / 256.0

            # The Pixelblaze uses a 16.16 fixed point, two's complement representation for pixel data.
            # If the value is greater than 32767, we need to subtract 65536 to convert it to a negative number
            # to keep it in a range the Pixelblaze can understand.
            if self.pixels[pixNum] > 32767:
                self.pixels[pixNum] = self.pixels[pixNum] - 65536
            pixNum += 1
            index += 3

    def _send_pre_init(self):
        """
        Idle send function - runs while the Pixelblaze objects are initializing and
        connecting, which may take a few seconds.
        """

        if self.pb is not None:
            self.sendMethod = self._send_frame

    def _send_frame(self):
        """
        Send a frame of packed pixel data to the Pixelblaze
        """
        if (time_in_millis() - self.frame_timer) >= self.ms_per_frame:
            if self.pixelsReceived > 0:
                # logging.debug("Sending frame to " + self.name + " with " + str(self.pixelsReceived) + " pixels."
                d = ("{\"setVars\":{\"pixels\":" +
                     np.array2string(self.pixels, precision=5, separator=',', suppress_small=True) + "}}")
                self.pb.wsSendString(d)
                self.packets_out += 1

            self.frame_timer = time_in_millis()

    def getStatusString(self, et):
        """
        Return a status string for the display device
        :param et: elapsed time in seconds
        :return: status string
        """
        return "X%s in: %d out: %d" % (self.name, self.packets_in / et, self.packets_out / et)

    def resetCounters(self):
        """
        Reset the packet counters for this display device
        """
        self.packets_in = 0
        self.packets_out = 0
        self.pixelsReceived = 0

    def run_thread(self):
        """
        Create Pixelblaze device object, and attempt to open it and
        maintain a websocket connection. Note that this can fail,
        which means that the object will try to establish the connection on the next
        (and subsequent) attempts to use it.
        """
        self.pb = Pixelblaze(self.ip)
        self.pb.setSendPreviewFrames(False)

        logging.debug("DisplayDevice: %s (%s) created" % (self.name, self.ip))
        logging.debug("Connection is %s" % ("open" if self.pb.is_connected() else "not open"))

        # the thread's job here is just to maintain the websocket connection
        # and eat any incoming messages.  We're ignoring them for now, but
        # we could use them to monitor the health of the Pixelblaze later.
        while self.run_flag.is_set():
            try:
                self.pb.maintain_connection()

            except Exception as e:
                logging.debug("DisplayDevice: %s (%s) exception: %s" % (self.name, self.ip, str(e)))
                pass

    def stop(self):
        # logging.debug("Stopping Pixelblaze: " + self.name)
        self.run_flag.clear()
        if self.pb is not None:
            self.pb.close()
        self.pb = None

    def __str__(self):
        return ("DisplayDevice: name: " + self.name + " ip: " + self.ip + " pixelCount: " +
                str(self.pixelCount) + " maxFps: " + str(self.maxFps) + " pixelsReceived: " +
                str(self.pixelsReceived) + " packets_in: " + str(self.packets_in) + " packets_out: " +
                str(self.packets_out) + " run_flag: " + str(self.run_flag.is_set()))
