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
"""
import argparse
import logging
from ProcessManager import startArtnetRouter
from ProjectData import ProjectData
from WebInterface import RemiWrapper

def main():
    print("Flamecaster Artnet Router for Pixelblaze v.0.5.4")
    print("Copyright 2024 ZRanger1 - Apache 2.0 License")

    # configure logging
    logging.basicConfig(
        format='%(asctime)s %(levelname)-6s: %(message)s',
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S')

    # use argparse to manage our lone (for now) command line argument -  the project configuration file name,
    # specified by # --file.  If it's not there, we'll use the default.
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=False, default="./config/config.conf",
                        help="Path to project configuration file to use.  Default is ./config/config.conf")
    # Parse the command line.
    args = parser.parse_args()

    # read the project configuration file and create an editable copy for
    # the WebUI to work with.
    pd = ProjectData()
    pd.loadProject(args.file)
    pd.copyLiveToEditable()

    # create and start the Artnet router in its own process
    startArtnetRouter(pd)

    # now, run the WebUI in the current process, where it will live 'till the app is closed.
    try:
        RemiWrapper(pd)

    except KeyboardInterrupt:
        pd.exit_flag.set()

    except Exception as e:
        pd.exit_flag.set()
        message = "Terminated by unexpected exception: " + str(e)
        logging.error(message)

    pd.routerProcess.join()
    print("Flamecaster shutting down. Thank you for playing!")

if __name__ == '__main__':
    main()
