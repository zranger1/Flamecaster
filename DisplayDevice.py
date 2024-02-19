"""
Per display device object - handles websocket connection, holds pixel buffer,
and sending data to a single Pixelblaze

TODO - respect max frame rate
"""
import threading
from threading import Thread

import numpy as np

from pixelblaze import *
from ArtnetUtils import *


class DisplayDevice:
    pb = None
    ip = None
    thread = None
    name = "<no device>"
    pixelCount = 0
    pixelsReceived = 0
    maxFps = 1000
    frame_out_timer = 0
    ms_per_frame = 0
    frames_in = 0
    frames_out = 0
    run_flag = threading.Event()

    SendMethod = None

    pixels = []

    def __init__(self, device, config):

        # set up device information record
        self.ip = getParam(device, 'ip', "")
        self.name = getParam(device, 'name', "<none>")
        self.pixelCount = getParam(device, 'pixelCount', 0)

        # take the lowest frame rate of the system config and the device
        self.maxFps = getParam(device, 'maxFps', 1000)
        self.maxFps = min(config["system"]["maxFps"], self.maxFps)
        self.ms_per_frame = 1000 / self.maxFps

        logging.debug("DisplayDevice: %s maxFps: %d (%d ms/frame)" % (self.name, self.maxFps, self.ms_per_frame))

        self.sendMethod = self.send_pre_init

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
        self.run_flag.set()
        self.frame_out_timer = 0
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
        self.frames_in += 1
        self.pixelsReceived += count

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

    def send_pre_init(self):
        if self.pb is not None:
            self.sendMethod = self.send_frame

    def send_frame(self):
        if (time_in_millis() - self.frame_out_timer) >= self.ms_per_frame:
            d = ("{\"setVars\":{\"pixels\":" +
                 np.array2string(self.pixels, precision=5, separator=',', suppress_small=True) + "}}")
            self.pb.wsSendString(d)
            self.frames_out += 1

            self.frame_out_timer = time_in_millis()

    def run_thread(self):
        # create object for Pixelblaze device and attempt to open and
        # maintain a websocket connection. Note that this can fail,
        # which means that the object will try to establish the connection on the next
        # (and subsequent) attempts to use it.
        self.pb = Pixelblaze(self.ip)
        self.pb.setSendPreviewFrames(False)

        logging.debug("DisplayDevice: %s (%s) created" % (self.name, self.ip))
        logging.debug("Connection is %s" % ("open" if self.pb.is_connected() else "not open"))

        # the thread's job here is just to maintain the websocket connection
        # and eat any incoming messages.  We're ignoring them for now, but
        # we could use them to monitor the health of the Pixelblaze later.

        updateTimer = time_in_millis()
        while self.run_flag.is_set():
            try:
                self.pb.maintain_connection()

                # display current in and out fps every 5 seconds
                elapsedTime = time_in_millis() - updateTimer
                if elapsedTime > 5000:
                    t = elapsedTime / 1000
                    logging.debug("DisplayDevice: %s in: %d out: %d" %
                                  (self.name, self.frames_in / t, self.frames_out / t))
                    self.frames_in = 0
                    self.frames_out = 0
                    updateTimer = time_in_millis()

            except Exception as e:
                logging.debug("DisplayDevice: %s (%s) exception: %s" % (self.name, self.ip, str(e)))
                pass

    def stop(self):
        logging.info("Stopping Pixelblaze: " + self.name)
        self.run_flag.clear()
        if self.pb is not None:
            self.pb.close()
        self.pb = None

    def __str__(self):
        return "DisplayDevice: name: " + self.name + " ip: " + self.ip + " pixelCount: " + str(
            self.pixelCount) + " maxFps: " + str(self.maxFps)
