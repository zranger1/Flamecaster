import json
import logging
import time
from multiprocessing import Queue
from multiprocessing import Event

from ArtnetServer import ArtnetServer
from ConfigParser import ConfigParser
from ArtnetUtils import time_in_millis


class ArtnetRouter:
    """
    Listens for data and forwards it to one or more Pixelblazes.  Designed to run in its own
    process, and communicate with the main process via Queues.
    """
    receiver = None
    pixelsPerUniverse = 170
    pixelCount = 0
    dataReady = False
    notifyTimer = 0
    FrameCount = 0
    delay = 0.033333  # default to 30 fps outgoing limit
    notify_ms = 3000  # status update to UI/log every 3 seconds by default
    configFileName = "./config/config.conf"

    config = None
    universes = []
    deviceList = None

    pixels = []

    def __init__(self, configDatabase: dict, cmdQueue: Queue, dataQueue: Queue, ui_is_active: Event, exit_flag: Event):
        logging.basicConfig(
            format='%(asctime)s %(levelname)-6s: %(message)s',
            level=logging.DEBUG,
            datefmt='%Y-%m-%d %H:%M:%S')

        self.cmdQueue = cmdQueue
        self.dataQueue = dataQueue
        self.ui_is_active = ui_is_active
        self.exit_flag = exit_flag

        jim = ConfigParser()
        self.config, self.deviceList, self.universes = jim.parse(configDatabase)

        # TODO - bind multicast receiver to specific IP address
        # TODO - the way it is now, we can still only handle 256 universes
        # TODO - regardless of the number of incoming interfaces.  This is
        # TODO - almost certainly ok, but just for the sake of completeness...
        # logging.debug("Listening for Art-Net on %s:%s" % self.config['ipArtnet'], self.config['portArtnet'])
        logging.debug("Listening for Art-Net on all interfaces at port %s" % self.config['portArtnet'])
        self.notifyTimer = time_in_millis()

        # loop 'till we're done, listening for packets and forwarding the pixel data
        # to Pixelblazes
        self.receiver = ArtnetServer(self.config["portArtnet"], self.main_dispatcher)
        sleep_time = self.config['statusUpdateIntervalMs'] / 1000

        # Periodically send updated status information to the UI queue, where
        # the WebUI can display it if anybody's watching.  We try to keep
        # this thread asleep as much as possible so the other threads in
        # this process can deal with moving the data around.
        while True:
            try:
                if self.exit_flag.is_set():
                    break

                time.sleep(sleep_time)
                elapsedTime = time_in_millis() - self.notifyTimer

                for key in self.deviceList:
                    dd = self.deviceList[key]
                    if ui_is_active.is_set():
                        self.dataQueue.put(dd.getStatusString(elapsedTime / 1000))
                    dd.resetCounters()

                self.notifyTimer = time_in_millis()

            except KeyboardInterrupt:
                # this throws us out of the loop and into the shutdown sequence
                break

            except Exception as e:
                logging.error("ArtnetRouter thread run loop: " + str(e))


        self.exit_flag.set()
        self.shutdown()

    def setPixelsPerUniverse(self, pix):
        self.pixelsPerUniverse = max(1, min(pix, 170))  # clamp to 1-170 pixels

    def setThroughputCheckInterval(self, ms):
        self.notify_ms = max(500, ms)  # min interval is 1/2 second, default should be about 3 sec

    def shutdown(self):
        # stop all devices in DeviceList
        for key in self.deviceList:
            logging.debug("Stopping device: " + self.deviceList[key].name)
            self.deviceList[key].stop()

        # stop listening for Artnet packets
        logging.debug("Stopping Artnet Receiver")
        del self.receiver

    def main_dispatcher(self, addr, data):
        """Test function, receives data from server callback."""
        # universe, subnet, net = decode_address_int(addr)
        # print("%d, subnet %d, net %d" % (universe, subnet, net))

        # test against the universe fragments in universes and print any matches
        for key in self.universes:
            u = self.universes[key]
            for k in u:
                if k.address_mask == addr:
                    k.device.process_pixel_data(data, k.startChannel, k.destIndex, k.pixelCount)

    # use each universe's str() method to convert the printable data in self.universes into a JSON string
    # by calling the __str__ method of each UniverseFragment in the list, and concatenating the results
    def getUniverseData(self):
        n = 0
        result = "{\"universes\":{"
        for key in self.universes:
            u = self.universes[key]
            for k in u:
                result += "\"" + n.__str__() + "\":" + k.__str__() + ","
                n += 1
        # drop the trailing comma
        result = result[:-1]
        result += "}}"
        return result


    # convert the printable data in self.deviceList to a JSON string and return it,
    # by calling each device's getStatusString method and concatenating the results
    def getDeviceData(self, et):
        n = 0
        result = "{\"devices\":{"
        for key in self.deviceList:
            result += "\"" + n.__str__() + "\":" + self.deviceList[key].getStatusString(et) + ","
            n += 1

        # drop the trailing comma
        result = result[:-1]
        result += "}}"
        return result


