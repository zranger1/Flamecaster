import logging
import time
from multiprocessing import Process
from multiprocessing import Queue
from multiprocessing import Event

from ArtnetProxy import ArtnetProxy
from WebInterface import WebInterface
from remi import start, App


def mirror_process(cmd: Queue, data: Queue, run: Event):
    """
    The actual Artnet router portion of our show runs in its own process,
    and communicates with the main process (and the WebUI process)
    via Queues and Events.
    """
    mirror = ArtnetProxy(cmd, data, run)
    mirror.run()


if __name__ == '__main__':
    print("Flamethrower Artnet Router for Pixelblaze v.0.0.1")

    logging.basicConfig(level=logging.DEBUG)
    cmdQueue = Queue()
    dataQueue = Queue()
    exit_flag = Event()

    exit_flag.clear()

    procs = []
    proc = Process(target=mirror_process, name="ArtnetRouter", args=(cmdQueue, dataQueue, exit_flag))
    proc.daemon = True
    procs.append(proc)
    proc.start()

    # fire up the web interface
    # TODO - we're going to need setup parameters in the config file for this
    start(WebInterface, port=8081, start_browser=False)

    try:
        # wait for the exit flag to be set
        exit_flag.wait()
        print("Flamethrower shutting down. Thank you for playing!")

    except KeyboardInterrupt:
        exit_flag.set()
        WebInterface.stop_server()
        print("(  terminated by keyboard interrupt)")

    except Exception as blarf:
        exit_flag.set()
        WebInterface.stop_server()
        template = "terminated by unexpected exception. Type: {0},  Args:\n{1!r}"
        message = template.format(type(blarf).__name__, blarf.args)
        logging.error(message)
