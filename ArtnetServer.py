"""
Artnet protocol implementation adapted from StupidArtnet at
https://github.com/cpvalente/stupidArtnet

It's MIT licensed, and much appreciated!

ArtnetServer.py - Provides a simple Artnet server implementation.

2/2024 ZRanger1
"""

import socket
from threading import Thread

from ArtnetUtils import encode_address_to_bytes


class ArtnetServer:
    UDP_PORT = 6454
    socket_server = None
    ARTDMX_HEADER = b'Art-Net\x00\x00P\x00\x0e'
    listeners = []

    def __init__(self):
        """Initializes Art-Net server."""
        # server active flag
        self.listen = True

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

            # only dealing with Art-Net DMX
            if self.validate_header(data):

                # see if we've got a listener for this packet
                for listener in self.listeners:

                    # check if the packet we've received is old
                    new_seq = data[12]
                    old_seq = listener['sequence']
                    # if there's a >50% packet loss it's not our problem
                    if new_seq == 0x00 or new_seq > old_seq or old_seq - new_seq > 0x80:
                        listener['sequence'] = new_seq
                        listener['buffer'] = bytearray(data)[18:]
                        # make an integer array from the buffer
                        addr = int.from_bytes(data[14:16], byteorder='little')
                        callback = listener['callback']
                        callback(addr, listener['buffer'])

    def __del__(self):
        """Graceful shutdown."""
        self.listeners.clear()
        self.close()

    def __str__(self):
        """Printable object state."""
        state = "===================================\n"
        state += "ArtnetServer Listening\n"
        return state

    def register_listener(self, callback_function=None):
        """
        Adds a listener to all Art-Net Universes.
        Since we're a proxy and not an endpoint, we don't do the usual
        callback-per-universe thing.  We need to listen to all incoming
        Artnet traffic and dispatch it ourselves as necessary. So the
        listener callback gets an Artnet universe specifier along with
        the data buffer, and is responsible for ignoring any packets
        it isn't specifically interested in.

        Args:
        callback_function - Function to call when new packet is received

        Returns:
        id - id of listener, used to delete listener if required
        """
        listener_id = len(self.listeners)
        new_listener = {
            'id': listener_id,
            'callback': callback_function,
            'buffer': [],
            'sequence': 0
        }

        self.listeners.append(new_listener)

        return listener_id

    def delete_listener(self, listener_id):
        """Deletes a registered listener.

        Args:
        listener_id - Id of listener to delete

        Returns:
        None
        """
        self.listeners = [
            i for i in self.listeners if not i['id'] == listener_id]

    def delete_all_listener(self):
        """Deletes all registered listeners.

        Returns:
        None
        """
        self.listeners = []

    def see_buffer(self, listener_id):
        """Show buffer values."""
        for listener in self.listeners:
            if listener.get('id') == listener_id:
                return listener.get('buffer')

        return "Listener not found"

    def get_buffer(self, listener_id):
        """Return buffer values."""
        for listener in self.listeners:
            if listener.get('id') == listener_id:
                return listener.get('buffer')
        print("Buffer object not found")
        return []

    def clear_buffer(self, listener_id):
        """Clear buffer in listener."""
        for listener in self.listeners:
            if listener.get('id') == listener_id:
                listener['buffer'] = []

    def set_callback(self, listener_id, callback_function):
        """Add / change callback to a given listener."""
        for listener in self.listeners:
            if listener.get('id') == listener_id:
                listener['callback'] = callback_function

    def set_address_filter(self, listener_id, universe, sub=0, net=0,
                           is_simplified=True):
        """Add / change filter to existing listener."""
        # make mask bytes
        address_mask = encode_address_to_bytes(universe, sub, net)

        # find listener
        for listener in self.listeners:
            if listener.get('id') == listener_id:
                listener['simplified'] = is_simplified
                listener['address_mask'] = address_mask
                listener['buffer'] = []

    def close(self):
        """Close UDP socket."""
        self.listen = False  # Set flag
        self.server_thread.join()  # Terminate thread once jobs are complete

    @staticmethod
    def validate_header(header):
        """Validates packet header as Art-Net packet.

        - The packet header spells Art-Net
        - The definition is for DMX Artnet (OPCode 0x50)
        - The protocol version is 15

        Args:
        header - Packet header as bytearray

        Returns:
        boolean - comparison value

        """
        return header[:12] == ArtnetServer.ARTDMX_HEADER


def test_callback(addr, data):
    """Test function, receives data from server callback."""
    print("Received new data on UVerse %d \n" % addr, data)
