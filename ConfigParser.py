"""
Handles loading and writing parameters from the config file
"""
import json
import sys
import DisplayDevice
import Universe



class ConfigParser:
    # this file holds the default configuration
    # TODO - do we need this?  What does it need to do?
    fileName = "../config/defaults.conf"

    def buildDeviceList(self,config) :
        deviceList = []

        # process our list of Pixelblazes
        devices = self.getParam(config,"devices")
        if devices is None:
            print("Error: No output devices found in config file.")
            exit(-1)

        # parse device record and add to hardware device list
        for record in devices :
            dev = DisplayDevice(record)
            deviceList.append(dev)

            # TODO - do something about universe data here.  It needs to be added to the global
            # TODO - list of universes we're interested in, along with pointers to device and pixel data
            # TODO - read setup data, create and run thread for each pb so
            # TODO - connections can come and go without interfering with each other
            # TODO - we probably need to change the library to allow pb object creation without
            # TODO - automatic open.

        return deviceList


    def getDeviceUniverses(self,deviceConfig) :
        data = self.getParam(deviceConfig,"data")
        if data is None :
            return None;

        universeFrags = dict();

        for record in data :
            print(record)

        return universeFrags;

    def keyExists(self, data, keyName):
        """
        Returns True if key exists in dictionary, False otherwise
        """
        return keyName in data.data

    def getParam(self, config, keyName, defaultValue=None) :
        """
        Safe value retriever for config data.  Returns the value of the
        specified key if it exists in the configuration JSON blob,
        whatever is in the defaultValue otherwise.
        """
        return config.get(keyName, defaultValue)

    def load(self, fileName):
        """
        read, parse and validate configuration data
        """
        # open config file
        f = open(fileName)

        # read configuration JSON blob from file
        data = json.load(f)
        f.close()

        # TODO - if data is empty, provide appropriate defaults
        # TODO - for now, just exit
        if data is None:
            print("Config.conf not found.  Using settings in defaults.conf")
            sys.exit()

        return data


