from multiprocessing import Event, Queue

"""
Holds the project configuration data used by all the various processes and 
threads in the Flamecaster application. 
"""
class ProjectData:
    def __init__(self):
        self.liveConfig = None
        self.editableConfig = None
        self.projectFile = "./config/config.conf"
        self.cmdQueue = Queue()
        self.dataQueue = Queue()
        self.exit_flag = Event()
        self.ui_is_active = Event()

    def copy_live_config(self):
        """
        Copy the live configuration to the editable configuration.
        """
        self.editableConfig = self.liveConfig.copy()
