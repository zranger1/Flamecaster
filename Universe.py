"""
Per-universe dispatcher for incoming data.  Handles setting pixels on the appropriate devices
"""


class UniverseDeviceRecord:
    """
    Data for each pixel segment on each device that cares about a given universe
    Contains:
    device - pointer to device's object
    startIndex - starting index in input pixel buffer
    destIndex  - destination index in output pixel buffer
    pixelCount - number of pixels to be copied
    """
    device = None
    startIndex = 0
    destIndex = 0
    count = 0

class Universes:
    """
    id - Universe number
    deviceList - list of records describing which pixels go where on what device...
    TODO - seriously, document this better!
    """
    id = -1
    deviceList = []

