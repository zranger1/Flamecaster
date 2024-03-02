import time
from multiprocessing import Process

from ArtnetRouter import ArtnetRouter
from ProjectData import ProjectData


# noinspection PyShadowingNames
def mirror_process(pd: ProjectData):
    """
    The actual Artnet router portion of our show runs in its own process,
    and communicates with the main process (and the WebUI process)
    via Queues and Events.  This function is the entry point for the
    ArtnetRouter process.
    """
    ArtnetRouter(pd)

def stopArtnetRouter(pd: ProjectData):
    pd.exit_flag.set()
    pd.routerProcess.join()

def startArtnetRouter(pd: ProjectData):
    pd.exit_flag.clear()
    pd.ui_is_active.clear()

    pd.routerProcess = Process(target=mirror_process, name="ArtnetRouter", args=(pd,))
    pd.routerProcess.daemon = True
    pd.startTime = time.time()
    pd.routerProcess.start()

def restartArtnetRouter(pd: ProjectData):
    stopArtnetRouter(pd)
    time.sleep(1)
    startArtnetRouter(pd)