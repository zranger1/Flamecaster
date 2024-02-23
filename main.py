import logging
import time
from multiprocessing import Process, Queue
from multiprocessing import Event
from multiprocessing import Queue
from typing import Any

from ArtnetRouter import ArtnetRouter

from remi import start
from WebInterface import RemiWrapper

cmdQueue = Queue()
dataQueue = Queue()
exit_flag = Event()
ui_is_active = Event()


# noinspection PyShadowingNames
def mirror_process(cmdQueue: Queue, dataQueue: Queue, ui_is_active: Event, exit_flag: Event):
    """
    The actual Artnet router portion of our show runs in its own process,
    and communicates with the main process (and the WebUI process)
    via Queues and Events.
    """
    ArtnetRouter(cmdQueue, dataQueue, ui_is_active, exit_flag)


def main():
    print("Flamethrower Artnet Router for Pixelblaze v.0.0.1")
    logging.basicConfig(level=logging.DEBUG)

    exit_flag.clear()
    ui_is_active.clear()

    # create the Artnet router process
    proc1 = Process(target=mirror_process, name="ArtnetRouter", args=(cmdQueue, dataQueue, ui_is_active, exit_flag))
    proc1.daemon = True
    proc1.start()

    # now, run the WebUI in the main process
    try:
        RemiWrapper(cmdQueue, dataQueue, ui_is_active)

    except KeyboardInterrupt:
        exit_flag.set()

    except Exception as e:
        exit_flag.set()
        message = "Terminated by unexpected exception: " + str(e)
        logging.error(message)

    proc1.join()
    print("Flamethrower shutting down. Thank you for playing!")


if __name__ == '__main__':
    main()
