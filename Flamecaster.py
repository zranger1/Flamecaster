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
from multiprocessing import Process, Event, Queue

from ArtnetRouter import ArtnetRouter
from ConfigParser import ConfigParser
from WebInterface import RemiWrapper

cmdQueue = Queue()
dataQueue = Queue()
exit_flag = Event()
ui_is_active = Event()
configDatabase = None


# noinspection PyShadowingNames
def mirror_process(configDatabase: dict, cmdQueue: Queue, dataQueue: Queue, ui_is_active: Event, exit_flag: Event):
    """
    The actual Artnet router portion of our show runs in its own process,
    and communicates with the main process (and the WebUI process)
    via Queues and Events.
    """
    ArtnetRouter(configDatabase, cmdQueue, dataQueue, ui_is_active, exit_flag)


def main():
    print("Flamecaster Artnet Router for Pixelblaze v.0.5.0")
    print("Copyright 2024 ZRanger1 - Apache 2.0 License")

    # configure logging
    logging.basicConfig(
        format='%(asctime)s %(levelname)-6s: %(message)s',
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S')

    global configDatabase
    configDatabase = ConfigParser.readConfigFile("./config/config.conf")

    # create the Artnet router process
    exit_flag.clear()
    ui_is_active.clear()

    proc1 = Process(target=mirror_process, name="ArtnetRouter",
                    args=(configDatabase, cmdQueue, dataQueue, ui_is_active, exit_flag))
    proc1.daemon = True
    proc1.start()

    # now, run the WebUI in this process, where it will live 'till the app is closed.
    try:
        RemiWrapper(configDatabase, cmdQueue, dataQueue, ui_is_active)

    except KeyboardInterrupt:
        exit_flag.set()

    except Exception as e:
        exit_flag.set()
        message = "Terminated by unexpected exception: " + str(e)
        logging.error(message)

    proc1.join()
    print("Flamecaster shutting down. Thank you for playing!")


if __name__ == '__main__':
    main()
