from enum import Enum


class ColorFormat(Enum):
    """
    Enum for the color types that we can send to the Pixelblaze
    Note that if HSV is specified, Flamethrower must do the conversion
    on the fly, which requires a little more CPU power.
    """
    RGB = 0
    HSV = 1


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
