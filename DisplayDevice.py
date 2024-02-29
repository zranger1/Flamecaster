"""
Per display device object - handles websocket connection, holds pixel buffer,
and sending data to a single Pixelblaze

TODO - respect max frame rate
"""
import threading
from threading import Thread
import logging
import numpy as np
import select

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
    sendFlag = False
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

    def process_pixel_data(self, dmxPixels: bytearray, startChannel: int, destPixel: int, count: int):
        """
        Pack RGB color data into a single 32-bit fixed point float for
        compact transmission to a Pixelblaze
        :param dmxPixels: byte array of RGB pixels received from Artnet source
        :param startChannel: starting channel in the Artnet packet
        :param destPixel: index of first pixel in destination array
        :param count: number of pixels to process
        """

        # logging.debug("  packet for " + self.name + " with " + str(count) + " pixels.")
        self.packets_in += 1
        self.pixelsReceived += count

        # copy the pixel data into the display device's pixel buffer
        index = 3 * startChannel
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
        Idle send function - runs until a Pixelblaze is connected.  Keeps track
        of incoming traffic, but doesn't try to send anything or connect the
        pixelblaze.  If the initial connection attempt failed, the connection
        maintenance task will keep trying.
        """
        if self.pb is not None and self.pb.is_connected():
            self.sendMethod = self._send_frame

    def _send_frame(self):
        """
        Send a frame of packed pixel data to the Pixelblaze
        """
        t = time_in_millis()
        if (t - self.frame_timer) >= self.ms_per_frame:
            if self.pixelsReceived > 0:
                d = ("{\"setVars\":{\"pixels\":" +
                     np.array2string(self.pixels, precision=5, separator=',', suppress_small=True) + "}}")
                self.pb.wsSendString(d)
                self.packets_out += 1
            self.frame_timer = t

    def getStatusString(self, et):
        """
        Return a JSON-ized status string for the display device
        :param et: elapsed time in seconds
        :return: status string
        """
        if self.pb is None:
            is_connected = "false"
        else:
            is_connected = "true" if self.pb.is_connected() else "false"
        inP = round(self.packets_in / et, 2)
        outF = round(self.packets_out / et, 2)
        return json.dumps({"name": self.name, "inPps": inP, "outFps": outF,
                           "ip": self.ip, "maxFps": self.maxFps, "connected": is_connected})

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

        logging.debug("Pixelblaze: %s (%s) initializing." % (self.name, self.ip))
        logging.debug("Connection is %s" % ("open" if self.pb.is_connected() else "NOT open"))

        # eat incoming traffic and send data to the Pixelblaze
        while self.run_flag.is_set():
            try:
                if self.pb.is_connected():
                    ready = select.select([self.pb.ws.sock], [], [], 0)
                    if ready[0]:
                        self.pb.wsReceive()

                    self.sendMethod()
                else:
                    self.pb.open()
                    self.pb.setSendPreviewFrames(False)

            # minimalist exception handling: if we get an exception it is going to be a
            # connection error, and we need to keep trying to reconnect at intervals.
            except Exception as e:
                logging.debug("Pixelblaze %s (%s) stall or disconnect." % (self.name, self.ip))
                logging.debug("Exception: %s" % str(e))
                self.pb.close()
                pass

    def stop(self):
        self.run_flag.clear()
        if self.pb is not None:
            self.pb.close()
        self.pb = None

    def __str__(self):
        return ("DisplayDevice: name: " + self.name + " ip: " + self.ip + " pixelCount: " +
                str(self.pixelCount) + " maxFps: " + str(self.maxFps) + " pixelsReceived: " +
                str(self.pixelsReceived) + " packets_in: " + str(self.packets_in) + " packets_out: " +
                str(self.packets_out) + " run_flag: " + str(self.run_flag.is_set()))
