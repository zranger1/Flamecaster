import logging
from ArtnetProxy import ArtnetProxy


if __name__ == '__main__':
    print("Flamethrower Artnet Router for Pixelblaze v.0.0.1")

    logging.basicConfig(level=logging.DEBUG)
    mirror = ArtnetProxy()
    try:
        mirror.run()

    except KeyboardInterrupt:
        mirror.stop()
        print("Flamethrower terminated by keyboard interrupt")

    except Exception as blarf:
        mirror.stop()
        template = "Flamethrower terminated by unexpected exception. Type: {0},  Args:\n{1!r}"
        message = template.format(type(blarf).__name__, blarf.args)
        logging.error(message)
