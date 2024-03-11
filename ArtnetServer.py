"""
ArtnetServer.py - Provides a super simplified Artnet server implementation
specifically for this project.

Artnet protocol implementation adapted from StupidArtnet at
https://github.com/cpvalente/stupidArtnet

2/2024 ZRanger1
"""

import socket
from threading import Thread


class ArtnetServer:
    """
      ArtnetServer - Extremely simple Art-Net server implementation.

      Allows our Artnet router to listen to all Art-Net Universes.

      Since we're a router and not an endpoint, we don't do the usual
      callback-per-universe thing.  We need to listen to all the traffic
      and dispatch it to our devices as necessary.
    """
    UDP_PORT = 6454
    socket_server = None
    callback = None
    sequence = 0

    # Art-Net packet header to use for validation
    # The packet header spells Art-Net
    # The definition is for DMX Artnet (OPCode 0x50)
    # The protocol version is 15
    ARTDMX_HEADER = b'Art-Net\x00\x00P\x00\x0e'

    def __init__(self, listen_ip: str, udp_port: int, callback):
        """Initializes Art-Net server."""
        # server active flag
        self.listen = True
        self.callback = callback
        self.listen_ip = listen_ip
        self.UDP_PORT = udp_port

        self.server_thread = Thread(target=self.__init_socket, daemon=True)
        self.server_thread.start()

    def __init_socket(self):
        """Initializes server socket."""
        # Bind to UDP on the correct PORT
        self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_server.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # TODO - Eventually may need to bind more than one specific interface, which
        # might mean multiple sockets.  For now, if you need more than one interface,
        # just bind to 0.0.0.0
        self.socket_server.bind((self.listen_ip, self.UDP_PORT))  # Listen on any valid IP

        while self.listen:

            data, sender = self.socket_server.recvfrom(2048)

            # check the header -- we only support Art-Net DMX
            if data[:9] == ArtnetServer.ARTDMX_HEADER[:9]:
                if data[9] == 0x50:

                    # TODO - check packet sequence number
                    # At worst, we should track this per-universe and drop out-of-order
                    # packets, or if the sequence number is too old, indicating an episode of very high
                    # packet loss, restart the sequence.
                    # Right now, we're just going to ignore the sequence number

                    new_seq = data[12]
                    old_seq = self.sequence
                    self.sequence = new_seq

                    # pass the buffer to the callback function
                    # for distribution to interested pixelblazes
                    addr = int.from_bytes(data[14:16], byteorder='little')
                    self.callback(addr, bytearray(data)[18:])

                elif data[9] == 0x20:
                    self.send_artnet_poll_reply(sender)


    def send_artnet_poll_reply(self, address):
        """
        Send an Art-Net PollReply packet to the specified address. Most
        of this data is um... totally made up.  Seems to work though.
        :param address:
        :return:
        """
        # Art-Net header
        header = b'Art-Net\x00'

        # OpCode for ArtPollReply
        opcode = (0x2100).to_bytes(2, byteorder='little')

        # Giant yard sale of device information!
        # IP Address, Port Number, Version Info, NetSwitch, SubSwitch, OEM, Ubea Version, Status1, ESTA Manufacturer,
        # Short Name, Long Name, Node Report, NumPorts, PortTypes, GoodInput, GoodOutput, SwIn, SwOut, SwVideo,
        # SwMacro, SwRemote, Spare, Style, MAC Address, BindIP, BindIndex, Status2, Filler
        ip_address = socket.inet_aton('127.0.0.1')  # Replace with your device's IP address
        port_number = (0x1936).to_bytes(2, byteorder='big')  # Replace with your device's Port-Address
        version_info = (1).to_bytes(2, byteorder='big')  # Replace with your device's firmware version
        net_switch = (0).to_bytes(1, byteorder='big')  # Replace with your device's NetSwitch
        sub_switch = (0).to_bytes(1, byteorder='big')  # Replace with your device's SubSwitch
        oem = (0).to_bytes(2, byteorder='big')  # Replace with your device's OEM value
        ubea_version = (0).to_bytes(1, byteorder='big')  # Replace with your device's Ubea Version
        status1 = (0).to_bytes(1, byteorder='big')  # Replace with your device's Status1
        esta_manufacturer = (0).to_bytes(2, byteorder='big')  # Replace with your device's ESTA Manufacturer
        short_name = 'FC'.ljust(18, '\x00').encode()  # Replace with your device's Short Name
        long_name = 'Flamecaster'.ljust(64, '\x00').encode()  # Replace with your device's Long Name
        node_report = 'No errors'.ljust(64, '\x00').encode()  # Replace with your device's Node Report
        num_ports = (0).to_bytes(2, byteorder='big')  # Replace with your device's NumPorts
        port_types = (0).to_bytes(4, byteorder='big')  # Replace with your device's PortTypes
        good_input = (0).to_bytes(4, byteorder='big')  # Replace with your device's GoodInput
        good_output = (0).to_bytes(4, byteorder='big')  # Replace with your device's GoodOutput
        sw_in = (0).to_bytes(4, byteorder='big')  # Replace with your device's SwIn
        sw_out = (0).to_bytes(4, byteorder='big')  # Replace with your device's SwOut
        sw_video = (0).to_bytes(1, byteorder='big')  # Replace with your device's SwVideo
        sw_macro = (0).to_bytes(1, byteorder='big')  # Replace with your device's SwMacro
        sw_remote = (0).to_bytes(1, byteorder='big')  # Replace with your device's SwRemote
        spare = (0).to_bytes(4, byteorder='big')  # Replace with your device's Spare
        style = (0).to_bytes(1, byteorder='big')  # Replace with your device's Style
        mac_address = b'\x00\x00\x00\x00\x00\x00'  # Replace with your device's MAC Address
        bind_ip = socket.inet_aton('127.0.0.1')  # Replace with your device's BindIP
        bind_index = (0).to_bytes(1, byteorder='big')  # Replace with your device's BindIndex
        status2 = (0).to_bytes(1, byteorder='big')  # Replace with your device's Status2
        filler = (0).to_bytes(26, byteorder='big')  # Replace with your device's Filler

        # Combine to form the Art-Net PollReply packet
        artnet_poll_reply_packet = (header + opcode + ip_address + port_number + version_info + net_switch +
                                    sub_switch + oem + ubea_version + status1 + esta_manufacturer + short_name +
                                    long_name + node_report + num_ports + port_types + good_input + good_output +
                                    sw_in + sw_out + sw_video + sw_macro + sw_remote + spare + style + mac_address +
                                    bind_ip + bind_index + status2 + filler)

        # Send the packet
        self.socket_server.sendto(artnet_poll_reply_packet, address)


    def __del__(self):
        """Graceful shutdown."""
        self.close()

    def __str__(self):
        """Printable object state."""
        state = "===================================\n"
        state += "ArtnetServer Listening\n"
        return state

    def close(self):
        """Close UDP socket."""
        self.listen = False  # Set flag
        self.server_thread.join()  # Terminate thread once jobs are complete

