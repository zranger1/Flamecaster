import logging
import time
import socket

from ArtnetServer import ArtnetServer
from ArtnetUtils import time_in_millis
from ConfigParser import ConfigParser
from ProjectData import ProjectData


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

    config = None
    universes = []
    deviceList = None
    pollReplyPacket = None

    pixels = []

    def __init__(self, pd: ProjectData):
        logging.basicConfig(
            format='%(asctime)s %(levelname)-6s: %(message)s',
            level=logging.DEBUG,
            datefmt='%Y-%m-%d %H:%M:%S')

        self.pd = pd
        self.dataQueue = pd.dataQueue
        self.ui_is_active = pd.ui_is_active
        self.exit_flag = pd.exit_flag

        jim = ConfigParser()
        self.config, self.deviceList, self.universes = jim.parse(pd.liveConfig)

        if self.config['ipArtnet'] == "0.0.0.0":
            print("Listening for Art-Net on all interfaces at port %s" % self.config['portArtnet'])
        else:
            print("Listening for Art-Net on %s:%s" % (self.config['ipArtnet'], self.config['portArtnet']))
        self.notifyTimer = time_in_millis()

        # loop 'till we're done, listening for packets and forwarding the pixel data
        # to Pixelblazes
        self.pollReplyPacket = self.createPollReplyPacket(self.config['ipArtnet'], self.config['portArtnet'])
        self.receiver = ArtnetServer(self.config["ipArtnet"], self.config["portArtnet"], self.pollReplyPacket,
                                     self.main_dispatcher)
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
                    if self.ui_is_active.is_set():
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
            logging.info("Stopping device: " + self.deviceList[key].name)
            self.deviceList[key].stop()

        # stop listening for Artnet packets
        logging.debug("Stopping Artnet receiver thread")
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
                    # Art-Net datagram size - 512 bytes of data plus 60 bytes of header
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

    def createPollReplyPacket(self, listen_ip: str, udp_port: int):
        """
        Create an Art-Net PollReply packet that we can send to controllers, so
        automatic detection and connection monitoring will work.
        :param address:
        :return:
        """
        # Art-Net header
        header = b'Art-Net\x00'

        # OpCode for ArtPollReply packet
        opcode = (0x2100).to_bytes(2, byteorder='little')

        # Giant yard sale of device information!  Most of this doesn't apply to us.
        ip_address = socket.inet_aton(listen_ip)  # Flamecaster's listen IP address
        port_number = udp_port.to_bytes(2, byteorder='big')  # Flamecaster's listen port number
        version_info = (1).to_bytes(2, byteorder='big')  # firmware version
        net_switch = (0).to_bytes(1, byteorder='big')  # NetSwitch
        sub_switch = (0).to_bytes(1, byteorder='big')  # SubSwitch
        oem = (0).to_bytes(2, byteorder='big')  # OEM value?
        ubea_version = (0).to_bytes(1, byteorder='big')  # Ubea Version?
        status1 = (0).to_bytes(1, byteorder='big')  # device Status1
        esta_manufacturer = (0).to_bytes(2, byteorder='big')  # ESTA Manufacturer code?
        short_name = 'FC'.ljust(18, '\x00').encode()  # Short Name
        long_name = 'Flamecaster'.ljust(64, '\x00').encode()  # Long Name
        node_report = 'No errors'.ljust(64, '\x00').encode()  # Node Report
        num_ports = (0).to_bytes(2, byteorder='big')  # NumPorts
        port_types = (0).to_bytes(4, byteorder='big')  # PortTypes
        good_input = (0).to_bytes(4, byteorder='big')  # GoodInput
        good_output = (0).to_bytes(4, byteorder='big')  # GoodOutput
        sw_in = (0).to_bytes(4, byteorder='big')  # SwIn
        sw_out = (0).to_bytes(4, byteorder='big')  # SwOut
        sw_video = (0).to_bytes(1, byteorder='big')  # SwVideo
        sw_macro = (0).to_bytes(1, byteorder='big')  # SwMacro
        sw_remote = (0).to_bytes(1, byteorder='big')  # SwRemote
        spare = (0).to_bytes(4, byteorder='big')  # Spare
        style = (0).to_bytes(1, byteorder='big')  # Style
        mac_address = b'\x00\x00\x00\x00\x00\x00'  # MAC Address
        bind_ip = socket.inet_aton(listen_ip)  # Flamecaster's BindIP
        bind_index = (0).to_bytes(1, byteorder='big')  # BindIndex
        status2 = (0).to_bytes(1, byteorder='big')  # Status2
        filler = (0).to_bytes(26, byteorder='big')  # Filler

        # Combine to form the Art-Net PollReply packet
        return (header + opcode + ip_address + port_number + version_info + net_switch +
                sub_switch + oem + ubea_version + status1 + esta_manufacturer + short_name +
                long_name + node_report + num_ports + port_types + good_input + good_output +
                sw_in + sw_out + sw_video + sw_macro + sw_remote + spare + style + mac_address +
                bind_ip + bind_index + status2 + filler)
