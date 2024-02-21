import logging
from multiprocessing import Process
from multiprocessing import Event
from multiprocessing import Queue

from ArtnetRouter import ArtnetRouter
from WebInterface import WebInterface
from remi import start


# noinspection PyShadowingNames
def mirror_process(cmdQueue: Queue, dataQueue: Queue, exit_flag: Event):
    """
    The actual Artnet router portion of our show runs in its own process,
    and communicates with the main process (and the WebUI process)
    via Queues and Events.
    """
    dataQueue.put("ArtnetRouter: Hi There from mirror_process!")
    ArtnetRouter(cmdQueue, dataQueue, exit_flag)


# noinspection PyShadowingNames
def remi_server(cmdQueue: Queue, dataQueue: Queue, exit_flag: Event):
    """
    Start the REMI web interface server
    """
    # TODO - need to wrap this in a class so we can manage IPC and exit conditions
    start(WebInterface, port=8081, start_browser=False, commandQueue=cmdQueue, dataQueue=dataQueue, exitFlag=exit_flag)


def main():
    print("Flamethrower Artnet Router for Pixelblaze v.0.0.1")
    logging.basicConfig(level=logging.DEBUG)

    exit_flag.clear()

    # create the Artnet router process
    proc1 = Process(target=mirror_process, name="ArtnetRouter", args=(cmdQueue, dataQueue, exit_flag))
    proc1.daemon = True
    proc1.start()

    # create the REMI server process
    # TODO - we're going to need setup parameters in the config file for this
    proc2 = Process(target=remi_server, name="REMI", args=(cmdQueue, dataQueue, exit_flag))
    proc2.daemon = True
    proc2.start()

    try:
        while not exit_flag.is_set():
            data = dataQueue.get()
            print("data: " + data)

        print("Flamethrower shutting down. Thank you for playing!")

    except KeyboardInterrupt:
        exit_flag.set()
        # WebInterface.stop_server()
        proc1.join()
        proc2.join()

    except Exception as blarf:
        exit_flag.set()
        # WebInterface.stop_server()
        template = "terminated by unexpected exception. Type: {0},  Args:\n{1!r}"
        message = template.format(type(blarf).__name__, blarf.args)
        logging.error(message)

    print("Flamethrower shutting down. Thank you for playing!")


if __name__ == '__main__':
    # Queues and Events shared between processes
    cmdQueue = Queue()
    dataQueue = Queue()
    exit_flag = Event()

    main()
