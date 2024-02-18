"""
 Flamethrower for Pixelblaze

 sACN/Artnet router:  Receives LED data packets and distributes
 them via websockets to one or more Pixelblazes
 
 Requires Python 3.10+, pixelblaze-client and sacn
 
 Copyright 2023 ZRanger1

 Permission is hereby granted, free of charge, to any person obtaining a copy of this
 software and associated documentation files (the "Software"), to deal in the Software
 without restriction, including without limitation the rights to use, copy, modify, merge,
 publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons
 to whom the Software is furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included in all copies or
 substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
 BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
 AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
 CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
 ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 THE SOFTWARE.

 Version  Date         Author    Comment
 v0.5.0   03/30/2023   ZRanger1  Initial version
"""
import json
import logging
import time

from ArtnetServer import ArtnetServer
from ConfigParser import ConfigParser


class ArtnetProxy:
    """
    Listens for data and forwards it to one or more Pixelblazes.
    """
    receiver = None
    isRunning = False
    pixelsPerUniverse = 170
    pixelCount = 0
    dataReady = False
    notifyTimer = 0
    FrameCount = 0
    delay = 0.033333  # default to 30 fps outgoing limit
    notify_ms = 3000  # throughput check every <notify_ms> milliseconds
    show_fps = False
    configFileName = "./config/config.conf"

    config = None
    universes = []
    deviceList = None

    pixels = []

    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)

        jim = ConfigParser()
        self.config, self.deviceList, self.universes = jim.load(self.configFileName)
        print(json.dumps(self.config, indent=4))

        # print the value for each key in deviceList
        for key in self.deviceList:
            print(key + " : " + str(self.deviceList[key]))

        # print the value for each key in universes
        for key in self.universes:
            u = self.universes[key]
            # print each key and value
            for k in u:
                print(k)

    def debugPrintFps(self):
        self.show_fps = True

    def setPixelsPerUniverse(self, pix):
        self.pixelsPerUniverse = max(1, min(pix, 170))  # clamp to 1-170 pixels

    def setMaxOutputFps(self, fps):
        self.delay = 1 / fps

    def setThroughputCheckInterval(self, ms):
        self.notify_ms = max(500, ms)  # min interval is 1/2 second, default should be about 3 sec

    @staticmethod
    def time_millis():
        return int(round(time.time() * 1000))

    def calc_frame_stats(self):
        self.FrameCount += 1

        t = self.time_millis() - self.notifyTimer
        if t >= self.notify_ms:
            t = 1000 * self.FrameCount / self.notify_ms
            if self.show_fps:
                logging.info("Incoming fps: %d" % t)
            self.FrameCount = 0

            self.notifyTimer = self.time_millis()
        pass

    def run(self):
        # bind multicast receiver to specific IP address
        logging.debug("Binding to %s" % self.config['listenAddress'])
        self.isRunning = True
        self.notifyTimer = self.time_millis()

        # loop 'till we're done, listening for packets and forwarding the pixel data
        # to Pixelblazes

        self.receiver = ArtnetServer()
        self.receiver.register_listener(self.main_dispatcher)

        while self.isRunning:
            # TODO - add UI loop in here somewhere...
            # sleep between UI updates (if the UI existed)

            try:
                time.sleep(0.5)
            except KeyboardInterrupt:
                break

        self.stop()

    def stop(self):
        # stop all devices in DeviceList
        for key in self.deviceList:
            self.deviceList[key].stop()

        # stop listening for Artnet packets
        logging.info("Stopping Artnet receiver")
        del self.receiver

    def main_dispatcher(self, addr, data):
        """Test function, receives data from server callback."""
        # universe, subnet, net = decode_address_int(addr)
        # print("Received data on universe %d, subnet %d, net %d" % (universe, subnet, net))

        # test against the universe fragments in universes and print any matches
        for key in self.universes:
            u = self.universes[key]
            for k in u:
                if k.address_mask == addr:
                    k.device.process_pixel_data(data, k.destIndex, k.pixelCount)
