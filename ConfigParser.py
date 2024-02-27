"""
Handles loading and writing parameters from the config file, as well as
parsing and validating the configuration data.
"""
import json
import logging
import sys

from DisplayDevice import DisplayDevice
from Universe import *


class ConfigParser:
    deviceList = dict()
    universes = dict()
    systemSettings = dict()

    def parseDeviceInfo(self, config):
        """
        Extract device and universe data from the configuration dictionary and
        create DisplayDevice objects for each device.
        """

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
        Extract universe data for a given device from the configuration dictionary
        and add it to the device's universe list
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

    @staticmethod
    def readConfigFile(fileName):
        """
        read JSON blob of configuration data from the specified file
        """
        try:
            # open config file
            f = open(fileName)

            # read configuration JSON blob from file
            data = json.load(f)
            f.close()

            if data is None:
                logging.error("%s is not a valid Flamecaster configuration file." % fileName)

            return data

        except Exception as e:
            logging.error("Error reading config file %s: %s" % (fileName, str(e)))
            return None

    @staticmethod
    def saveConfigFile(fileName, configDatabase):
        """
        Write configuration data to file
        """
        try:
            with open(fileName, 'w') as f:
                json.dump(configDatabase, f, indent=4)
                f.close()

        except Exception as e:
            logging.error("Error writing config file %s: %s" % (fileName, str(e)))

    def parse(self, data: dict):
        """
        Parse and validate configuration data from a loaded JSON blob
        """

        if data is None:
            sys.exit()

        if self.systemSettings is None:
            logging.debug("System settings not found in config file. Using defaults.")

        self.systemSettings = getParam(data, "system")
        self.systemSettings["maxFps"] = getParam(self.systemSettings, "maxFps", 30)
        self.systemSettings["statusUpdateIntervalMs"] = getParam(self.systemSettings, "statusUpdateIntervalMs", 3000)
        self.systemSettings["pixelsPerUniverse"] = getParam(self.systemSettings, "pixelsPerUniverse", 170)
        self.systemSettings["ipArtnet"] = getParam(self.systemSettings, "ipArtnet", "127.0.0.1")
        self.systemSettings["portArtnet"] = getParam(self.systemSettings, "portArtnet", 6454)
        self.systemSettings["ipWebInterface"] = getParam(self.systemSettings, "ipWebInterface", "127.0.0.1")
        self.systemSettings["portWebInterface"] = getParam(self.systemSettings, "portWebInterface", 8081)

        self.parseDeviceInfo(data)

        return self.systemSettings, self.deviceList, self.universes
