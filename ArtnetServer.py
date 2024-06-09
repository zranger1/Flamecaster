"""
ArtnetServer.py - Provides a super simplified Artnet server implementation
specifically for this project.@

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
    pollReplyPacket = None

    """
    Art-Net packet header to use for validation
    Here's the full header, including the OpCode and protocol version)
    This definition is for DMX Artnet (OPCode 0x50), protocol version 15.    
    ARTDMX_HEADER = b'Art-Net\x00\x00P\x00\x0e'
    
    Because show control software does a great number of things with Art-Net, 
    we're being more lenient about header checking.  OpCode is checked at
    dispatch time, and protocol version is currently ignored.
    """
    ARTDMX_HEADER = b'Art-Net\x00\x00'

    def __init__(self, listen_ip: str, udp_port: int, pollReplyPacket, callback):
        """Initializes Art-Net server."""
        # server active flag
        self.listen = True
        self.callback = callback
        self.listen_ip = listen_ip
        self.UDP_PORT = udp_port
        self.pollReplyPacket = pollReplyPacket

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
            if data[:9] == ArtnetServer.ARTDMX_HEADER:
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
        Responds to an Art-Net Poll packet with a PollReply packet.
        :param address:
        :return:
        """
        self.socket_server.sendto(self.pollReplyPacket, address)

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
