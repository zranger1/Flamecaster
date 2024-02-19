"""
Artnet protocol implementation adapted from StupidArtnet at
https://github.com/cpvalente/stupidArtnet

It's MIT licensed, and much appreciated!

ArtnetUtils.py - Provides common functions for byte objects.

2/2024 ZRanger1
"""
import time


def shift_this(number, high_first=True):
    """Utility method: extracts MSB and LSB from number.

    Args:
    number - number to shift
    high_first - MSB or LSB first (true / false)

    Returns:
    (high, low) - tuple with shifted values

    """
    low = (number & 0xFF)
    high = ((number >> 8) & 0xFF)
    if high_first:
        return high, low
    return low, high


def clamp(number, min_val, max_val):
    """Utility method: sets number in defined range.

    Args:
    number - number to use
    range_min - lowest possible number
    range_max - highest possible number

    Returns:
    number - number in correct range
    """
    return max(min_val, min(number, max_val))


def set_even(number):
    """Utility method: ensures number is even by adding.

    Args:
    number - number to make even

    Returns:
    number - even number
    """
    if number % 2 != 0:
        number += 1
    return number


def put_in_range(number, range_min, range_max, make_even=True):
    """Utility method: sets number in defined range.
    DEPRECATED: this will be removed from the library

    Args:
    number - number to use
    range_min - lowest possible number
    range_max - highest possible number
    make_even - should number be made even

    Returns:
    number - number in correct range

    """
    number = clamp(number, range_min, range_max)
    if make_even:
        number = set_even(number)
    return number


def encode_address_to_bytes(universe, sub=0, net=0):
    """Returns the address bytes for a given universe, subnet and net.

    Args:
    universe - Universe to listen
    sub - Subnet to listen
    net - Net to listen
    is_simplified - Whether to use nets and subnet or universe only,
    see User Guide page 5 (Universe Addressing)

    Returns:
    bytes - byte mask for given address

    """
    address_mask = bytearray()

    # Ensure data is in right range
    universe = clamp(universe, 0, 15)
    sub = clamp(sub, 0, 15)
    net = clamp(net, 0, 127)

    # Make mask
    address_mask.append(sub << 4 | universe)
    address_mask.append(net & 0xFF)

    return address_mask


# declare this again, requiring that parameter mask is a byte array
def decode_address_bytes(mask: bytearray):
    """Given a 16 bit encoded Artnet address, return the universe, subnet and net.

    Args:
    mask - bytearray containing the address mask to decode

    Returns:
    tuple - (net, subnet, universe)

    """
    universe = mask[0] & 0x0F
    subnet = (mask[0] & 0xF0) >> 4
    net = mask[1]

    return net, subnet, universe


# decode an integer Artnet address mask and return the universe, subnet and net
def decode_address_int(mask: int):
    """Given a 16 bit encoded Artnet address, return the universe, subnet and net.

    Args:
    mask - integer containing the address mask to decode

    Returns:
    tuple - (net, subnet, universe)

    """
    universe = mask & 0x0F
    subnet = (mask & 0xF0) >> 4
    net = mask >> 8

    return net, subnet, universe


def encode_address_bytes_to_int(mask: bytearray):
    """Given a 16 bit encoded Artnet address in a byte array,
     return the corresponding integer value.

    Args:
    mask - bytearray containing the address mask to decode

    Returns:
    int - integer value of the mask

    """
    return int.from_bytes(mask, byteorder='little')


def artnet_to_int(net, subnet, universe):
    """Given a full Artnet address, return the equivalent encoded integer value.

    Args:
    net - Artnet net number
    subnet - Artnet subnet number
    universe - Artnet universe

    Returns:
    int - integer value of the mask

    """
    return int.from_bytes(encode_address_to_bytes(universe, subnet, net), byteorder='little')


def keyExists(data, keyName):
    """
    Returns True if key exists in dictionary, False otherwise
    """
    return keyName in data


def getParam(config, keyName, defaultValue=None):
    """
    Safe value retriever. Returns the value of the
    specified key if it exists in the dictionary,
    whatever is in the defaultValue otherwise.
    """
    return config.get(keyName, defaultValue)


def time_in_millis() -> int:
    """
    Utility Method: Returns last 32 bits of the current time in milliseconds
    """
    return int(round(time.time() * 1000)) % 0xFFFFFFFF
