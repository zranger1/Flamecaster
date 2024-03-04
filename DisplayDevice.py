"""
DisplayDevice object - handles websocket connection, holds pixel buffer,
and communication with a single Pixelblaze.  Each DisplayDevice runs in its
own thread, so any I/O waits or errors will not interfere with other operations.
We expect that Pixelblaze connections may be intermittent and unreliable, so we
need to handle errors and reconnections gracefully.
"""
import logging
import threading
from threading import Thread

# import numpy as np
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
        self.sec_per_frame = 1 / self.maxFps
        # account for overhead in the frame timer
        self.sec_per_frame -= 0.05 * self.sec_per_frame

        self.sendMethod = self._send_pre_init

        # initialize output pixel buffer
        self.pixels = [0] * self.pixelCount

        # start the display device thread
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

        self.packets_in += 1
        self.pixelsReceived += count

        # copy the pixel data into the display device's pixel buffer
        index = 3 * startChannel
        pixNum: int = destPixel

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
        maintenance task will try again at intervals.
        """

        if self.pb is not None and self.pb.is_connected():
            self.sendMethod = self._send_frame

    def _send_frame(self):
        """
        Send a frame of packed pixel data to the Pixelblaze
        """

        if self.pixelsReceived > 0:
            # go to great lengths to get rid of the spaces, zeros and spurious digits python
            # *really* wants you to have.  We want to send out as few bytes of data as possible.
            self.pb.ws.send(
                "{\"setVars\":{\"pixels\":[" + ",".join(f"{x:5g}".lstrip(" ") for x in self.pixels) + "]}}")
            self.packets_out += 1

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
        inP = round(self.packets_in / et, 1)
        outF = round(self.packets_out / et, 1)
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
        # always turn off preview frames to save Pixelblaze CPU and bandwidth
        self.pb.setSendPreviewFrames(False)

        logging.debug("Pixelblaze: %s (%s) initializing." % (self.name, self.ip))
        logging.debug("Connection is %s" % ("open" if self.pb.is_connected() else "NOT open"))

        frame_timer = time.time()

        # eat incoming traffic and send data to the Pixelblaze
        while self.run_flag.is_set():
            try:
                if self.pb.is_connected():
                    ready = select.select([self.pb.ws.sock], [], [], 0)
                    if ready[0]:
                        self.pb.wsReceive()

                    # sleep 'till it's time to send a frame
                    t = time.time()
                    time.sleep(min(self.sec_per_frame, t - frame_timer))
                    frame_timer = t

                    # send any data we've received
                    self.sendMethod()
                else:
                    # sleep for a short interval. Even though pb.open will only retry every 2 seconds
                    # we can spare the CPU (and the GIL) for a bit to let other threads run.
                    time.sleep(0.25)
                    self.pb.open()
                    self.pb.setSendPreviewFrames(False)

            # minimalist exception handling: if we get an exception it is going to be a
            # connection error of some sort, and we'll need to keep trying to reconnect at intervals.
            # TODO - add an exponential backoff timer to the reconnect attempts?
            except Exception as e:
                logging.debug("Pixelblaze %s (%s) stalled or disconnected." % (self.name, self.ip))
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
