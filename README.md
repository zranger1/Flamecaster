## FlameCaster Art-Net Router for Pixelblaze
Extremely(!) early pre-alpha version.  

Receives data packets over Art-Net and distributes them via websockets to one
or more Pixelblazes

This is very much a work in progress.  You are welcome to try it out, and I would love to hear your feedback,
but please check back frequently for updates, and be aware that it is not yet ready for production use. 

### State of the Project - 2/23/2024
- **Art-Net -> Pixelblaze routing is working.** You can send Art-Net data from your lighting application
to FlameCaster, and it will distribute it to your Pixelblazes.  But...
- **Configuration tools are... not baked yet.**  To configure the system, you need to hand-edit the JSON in the config.conf
file.  If you understand how Art-Net works, it's mostly self-explanatory, but it requires a fair amount of patience - it's very easy to misplace a comma or bracket in the JSON.
- **The web UI was carved from mammoth bones with stone tools!**  Right now, it just gives a crude status display. Lots more to be done here.


### Requirements
Requires Python 3.10+, and the following libraries from pypl:
- pixelblaze-client
- numpy
- websocket-client
- remi

Flamecaster is pure Python, and should run on any platform that supports Python 3.10+.  It is reasonably efficient, and 
will be optimized further as we go, but if you're going to run a significant number of pixels, I'd suggest a Raspberry
Pi 4 or better. 

If you're running your show from a laptop or desktop, it can also happily run there along with your
lighting software.  (This has the added advantage of keeping your Art-Net traffic off the network.)

### Notes
- Art-Net DMX is currently the only supported protocol.  Yes, you'll have to divide your universe into 170-pixel chunks!
- X-Lights users:  X-Lights doesn't really get the whole routing thing.  It wants each Artnet controller to
have its own IP address.   I'm not sure how to best work around this yet.

### Acknowledgements
Uses the REMI library to create its web interface.
More information about REMI can be found at: https://github.com/dddomodossola/remi

Uses a very highly modified version of the pixelblaze-client library to communicate with Pixelblazes.
More information about pixelblaze-client can be found at: https://github.com/zranger1/pixelblaze-client

### Version History
```
v0.5.0   02/23/2024 Initial pre-alpha release
```
