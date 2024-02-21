"""
Handles loading and writing parameters from the config file
"""
import json
import sys
import logging

from DisplayDevice import DisplayDevice
from Universe import *


class ConfigParser:
    # this file holds the default configuration
    fileName = "./config/defaults.conf"

    deviceList = dict()
    universes = dict()
    systemSettings = dict()

    def parseDeviceInfo(self, config):

        # process our list of Pixelblazes
        devices = getParam(config, "devices")
        if devices is None:
            logging.error("Error: No output devices found in config file.")
            exit(-1)

            # parse device record and add to hardware device list
        for key in devices:
            dev = DisplayDevice(getParam(devices, key), self.systemSettings)
            self.deviceList[key] = dev

            self.getDeviceUniverses(dev, devices[key])

    def getDeviceUniverses(self, device, config):
        """
        :param device: DisplayDevice object for this device
        :param config: dictionary containing universe info for the given device
        """
        # get key to universe fragments for this device
        data = getParam(config, "data")
        if data is None:
            return None

        for key in data:
            fragment = UniverseFragment(device, getParam(data, key))

            if keyExists(self.universes, fragment.address_mask):
                self.universes[fragment.address_mask].append(fragment)
            else:
                self.universes[fragment.address_mask] = [fragment]

    def load(self, fileName):
        """
        read, parse and validate configuration data
        """
        # open config file
        f = open(fileName)

        # read configuration JSON blob from file
        data = json.load(f)
        f.close()

        if data is None:
            logging.error("Config.conf not found. Exiting")
            sys.exit()

        if self.systemSettings is None:
            logging.debug("System settings not found in config file. Using defaults.")

        self.systemSettings = getParam(data, "system")
        self.systemSettings["maxFps"] = getParam(self.systemSettings, "maxFps", 30)
        self.systemSettings["statusUpdateIntervalMs"] = getParam(self.systemSettings, "statusUpdateIntervalMs", 3000)
        self.systemSettings["pixelsPerUniverse"] = getParam(self.systemSettings, "pixelsPerUniverse", 170)
        self.systemSettings["listenAddress"] = getParam(self.systemSettings, "listenAddress", "127.0.0.1")

        self.parseDeviceInfo(data)

        return self.systemSettings, self.deviceList, self.universes