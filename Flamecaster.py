"""
 FlameCaster Art-Net Router for Pixelblaze

 Receives LED data packets over Art-Net and distributes them via websockets to one
 or more Pixelblazes

 Uses the REMI library to create its web interface.
 More information about REMI can be found at: https://github.com/dddomodossola/remi

 Uses a highly modified version of the pixelblaze-client library to communicate with Pixelblazes.
 More information about pixelblaze-client can be found at: https://github.com/zranger1/pixelblaze-client

 Requires Python 3.10+, and the following libraries from pypl:
     numpy
     websocket-client
     remi

 Copyright 2024 ZRanger1
 Apache 2.0 License - see the github repository for details.

 Version  Date         Author    Comment
 v0.5.0   02/23/2024   ZRanger1  Initial pre-alpha release
"""
import logging
from multiprocessing import Process

from ArtnetRouter import ArtnetRouter
from ConfigParser import ConfigParser
from ProjectData import ProjectData
from WebInterface import RemiWrapper


# noinspection PyShadowingNames
def mirror_process(pd: ProjectData):
    """
    The actual Artnet router portion of our show runs in its own process,
    and communicates with the main process (and the WebUI process)
    via Queues and Events.
    """
    ArtnetRouter(pd.liveConfig, pd.cmdQueue, pd.dataQueue, pd.ui_is_active, pd.exit_flag)


def main():
    print("Flamecaster Artnet Router for Pixelblaze v.0.5.0")
    print("Copyright 2024 ZRanger1 - Apache 2.0 License")

    # configure logging
    logging.basicConfig(
        format='%(asctime)s %(levelname)-6s: %(message)s',
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S')

    pd = ProjectData()

    # read the project configuration file and create an editable copy for
    # the WebUI to work with.
    pd.liveConfig = ConfigParser.readConfigFile(pd.projectFile)
    pd.copy_live_config()

    # create the Artnet router process
    pd.exit_flag.clear()
    pd.ui_is_active.clear()

    proc1 = Process(target=mirror_process, name="ArtnetRouter", args=(pd,))
    proc1.daemon = True
    proc1.start()

    # now, run the WebUI in this process, where it will live 'till the app is closed.
    try:
        RemiWrapper(pd)

    except KeyboardInterrupt:
        pd.exit_flag.set()

    except Exception as e:
        pd.exit_flag.set()
        message = "Terminated by unexpected exception: " + str(e)
        logging.error(message)

    proc1.join()
    print("Flamecaster shutting down. Thank you for playing!")


if __name__ == '__main__':
    main()
