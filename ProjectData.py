import time
from datetime import timedelta
from multiprocessing import Event, Queue
from typing import Union

from ConfigParser import ConfigParser


"""
Holds the project configuration data used by all the various processes and 
threads in the Flamecaster application. 
"""
class ProjectData:
    def __init__(self):
        self.liveConfig = None
        self.editableConfig = None
        self.projectFile = None
        self.routerProcess = None
        self.startTime = 0
        self.cmdQueue = Queue()
        self.dataQueue = Queue()
        self.exit_flag = Event()
        self.ui_is_active = Event()

    def copyLiveToEditable(self):
        """
        Copy the live configuration to the editable configuration.
        """
        self.editableConfig = self.liveConfig.copy()

    def loadProject(self,filePath: Union[str, None] = None):
        """
        Loads a specified project configuration file, or reloads the current project file if
        no filePath is specified.
        """
        if filePath is None:
            filePath = self.projectFile
        else:
            self.projectFile = filePath

        self.liveConfig = ConfigParser.readConfigFile(filePath)
        self.copyLiveToEditable()

    def saveProject(self, filePath: Union[str, None] = None):
        """
        Save the editable project configuration to the specified file, or to the current project file if
        no filePath is specified.
        """
        if filePath is None:
            filePath = self.projectFile
        else:
            self.projectFile = filePath

        ConfigParser.saveConfigFile(filePath, self.editableConfig)

    def revertEditableToLive(self):
        """
        Revert the editable project configuration to the current live state.
        """
        self.editableConfig = self.liveConfig.copy()

    def revertToSaved(self):
        """
        Revert the live project configuration to the last saved state.
        """
        self.loadProject()
        self.copyLiveToEditable()

    def clearEditable(self):
        """
        Clear the editable project configuration.
        """
        self.editableConfig = dict()
        ConfigParser.setSystemDefaults(self.editableConfig)

    def getUptime(self):
        """
        Returns the number of seconds since the application started in string format.
        """
        return str(timedelta(time.time() - self.startTime))
