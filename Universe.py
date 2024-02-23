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
        net = getParam(record, "net", 0)
        subnet = getParam(record, "subnet", 0)
        universe = getParam(record, "universe", 0)
        self.address_mask = artnet_to_int(net, subnet, universe)
        self.startChannel = getParam(record, "startChannel", 0)
        self.destIndex = getParam(record, "destIndex", 0)
        self.pixelCount = getParam(record, "pixelCount", 0)

    def __str__(self):
        return ("UniverseFragment: device: " + str(self.device.name) +
                " address_mask: " + str(self.address_mask) + " Start channel: " +
                str(self.startChannel) + " destIndex: " + str(self.destIndex) +
                " pixelCount: " + str(self.pixelCount))
