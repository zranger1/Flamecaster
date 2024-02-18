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
