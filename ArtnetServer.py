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

    def __init__(self, udp_port, callback):
        """Initializes Art-Net server."""
        # server active flag
        self.listen = True
        self.callback = callback
        self.UDP_PORT = udp_port

        self.server_thread = Thread(target=self.__init_socket, daemon=True)
        self.server_thread.start()

    def __init_socket(self):
        """Initializes server socket."""
        # Bind to UDP on the correct PORT
        self.socket_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_server.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # TODO - Eventually may need to bind to a specific IP address
        self.socket_server.bind(('', self.UDP_PORT))  # Listen on any valid IP

        while self.listen:

            data, unused_address = self.socket_server.recvfrom(2048)

            # check the header -- we only support Art-Net DMX
            if data[:12] == ArtnetServer.ARTDMX_HEADER:

                # check sequence numbers to see if we've missed a packet
                # if there's a >50% packet loss it's not our problem
                new_seq = data[12]
                old_seq = self.sequence

                if new_seq == 0x00 or new_seq > old_seq or old_seq - new_seq > 0x80:
                    self.sequence = new_seq

                    # make an array from the buffer and pass it on
                    # for distribution to the pixelblazes
                    addr = int.from_bytes(data[14:16], byteorder='little')
                    self.callback(addr, bytearray(data)[18:])

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

