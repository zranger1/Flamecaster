import socket
import struct
import time
import threading
from ArtnetUtils import time_in_millis


class PixelblazeEnumerator:
    """
    Listens on a network to detect available Pixelblazes, which the user can then list
    or open as Pixelblaze objects.  Also provides time synchronization services for
    running synchronized patterns on a network of Pixelblazes.
    """
    PORT = 1889
    SYNC_ID = 890
    BEACON_PACKET = 42
    TIMESYNC_PACKET = 43
    DEVICE_TIMEOUT = 30000
    LIST_CHECK_INTERVAL = 5000

    listTimeoutCheck = 0
    isRunning = False
    threadObj = None
    listener = None
    devices = dict()
    autoSync = False

    def __init__(self, hostIP="0.0.0.0"):
        """
        Create an object that listens continuously for Pixelblaze beacon
        packets, maintains a list of Pixelblazes and supports synchronizing time
        on multiple Pixelblazes to allows them to run patterns simultaneously.
        Takes the IPv4 address of the interface to use for listening on the calling computer.
        Listens on all available interfaces if hostIP is not specified.
        """
        self.start(hostIP)

    def __del__(self):
        self.stop()

    @staticmethod
    def _unpack_beacon(data):
        """
        Utility Method: Unpacks data from a Pixelblaze beacon
        packet, returning a 3 element list which contains
        (packet_type, sender_id, sender_time)
        """
        return struct.unpack("<LLL", data)

    def _pack_timesync(self, now, sender_id, sender_time):
        """
        Utility Method: Builds a Pixelblaze timesync packet from
        supplied data.
        """
        return struct.pack("<LLLLL", self.TIMESYNC_PACKET, self.SYNC_ID, now, sender_id, sender_time)

    def _set_timesync_id(self, sync_id):
        """Utility Method:  Sets the PixelblazeEnumerator object's network
           id for time synchronization. At the moment, any 32 bit value will
           do, and calling this method does (almost) nothing.  In the
           future, the ID might be used to determine priority among multiple time sources.
        """
        self.SYNC_ID = sync_id

    def setDeviceTimeout(self, ms):
        """
        Sets the interval in milliseconds which the enumerator will wait without
        hearing from a device before removing it from the active devices list.

        The default timeout is 30000 (30 seconds).
        """
        self.DEVICE_TIMEOUT = ms

    def enableTimesync(self):
        """
        Instructs the PixelblazeEnumerator object to automatically synchronize
        time on all Pixelblazes. (Note that time synchronization
        is off by default when a new PixelblazeEnumerator is created.)
        """
        self.autoSync = True

    def disableTimesync(self):
        """
        Turns off the time synchronization -- the PixelblazeEnumerator will not
        automatically synchronize Pixelblazes.
        """
        self.autoSync = False

    def start(self, hostIP):
        """
        Open socket for listening to Pixelblaze datagram traffic,
        set appropriate options and bind to specified interface and
        start listener thread.
        """
        try:
            self.listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.listener.bind((hostIP, self.PORT))

            self.threadObj = threading.Thread(target=self._listen)
            self.isRunning = True
            self.listTimeoutCheck = 0
            self.threadObj.start()

            return True
        except socket.error as e:
            print(e)
            self.stop()
            return False

    def stop(self):
        """
        Stop listening for datagrams, terminate listener thread and close socket.
        """
        if self.listener is None:
            return
        else:
            self.isRunning = False
            self.threadObj.join()
            time.sleep(0.5)
            self.listener.close()
            self.threadObj = None
            self.listener = None

    def _send_timesync(self, now, sender_id, sender_time, addr):
        """
        Utility Method: Composes and sends a timesync packet to a single Pixelblaze
        """
        try:
            self.listener.sendto(self._pack_timesync(now, sender_id, sender_time), addr)

        except socket.error as e:
            print(e)
            self.stop()

    def _listen(self):
        """
        Internal Method: Datagram listener thread handler -- loop and listen.
        """

        while self.isRunning:
            data, addr = self.listener.recvfrom(1024)
            now = time_in_millis()

            # check the list periodically,and remove devices we haven't seen in a while
            if (now - self.listTimeoutCheck) >= self.LIST_CHECK_INTERVAL:
                newlist = dict()

                for dev, record in self.devices.items():
                    if (now - record["timestamp"]) <= self.DEVICE_TIMEOUT:
                        newlist[dev] = record

                self.devices = newlist
                self.listTimeoutCheck = now

            # when we receive a beacon packet from a Pixelblaze,
            # update device record and timestamp in our device list
            pkt = self._unpack_beacon(data)
            if pkt[0] == self.BEACON_PACKET:
                # add pixelblaze to list of devices
                self.devices[pkt[1]] = {"address": addr, "timestamp": now, "sender_id": pkt[1], "sender_time": pkt[2]}

                # immediately send timesync if enabled
                if self.autoSync:  # send
                    self._send_timesync(now, pkt[1], pkt[2], addr)

            elif pkt[0] == self.TIMESYNC_PACKET:  # always defer to other time sources
                if self.autoSync:
                    self.disableTimesync()

    def getPixelblazeList(self):
        dev = []
        for record in self.devices.values():
            dev.append(record["address"][0])  # just the ip
        return dev
