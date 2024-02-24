from ArtnetUtils import *


class UniverseFragment:
    """
    Data for each pixel segment on each device that cares about a given universe
    Contains:
    device - pointer to device's object
    startIndex - starting index in input pixel buffer
    destIndex  - destination index in output pixel buffer
    pixelCount - number of pixels to be copied
    """
    device = None
    address_mask = 0
    startChannel = 0
    destIndex = 0
    pixelCount = 0

    def __init__(self, device, record):
        self.device = device
        self.net = getParam(record, "net", 0)
        self.subnet = getParam(record, "subnet", 0)
        self.universe = getParam(record, "universe", 0)
        self.address_mask = artnet_to_int(self.net, self.subnet, self.universe)
        self.startChannel = getParam(record, "startChannel", 0)
        self.destIndex = getParam(record, "destIndex", 0)
        self.pixelCount = getParam(record, "pixelCount", 0)

    def __str__(self):
        # format the device name and the universe fragment data into a JSON string and return it.
        # instead of address_mask, use net, subnet, universe.
        return ('{"device": "' + self.device.name + '", "net": ' + str(self.net) +
                ', "subnet": ' + str(self.subnet) + ', "universe": ' + str(self.universe) +
                ', "startChannel": ' + str(self.startChannel) + ', "destIndex": ' + str(self.destIndex) +
                ', "pixelCount": ' + str(self.pixelCount) + '}')





