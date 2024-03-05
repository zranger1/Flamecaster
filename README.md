## FlameCaster Art-Net Router for Pixelblaze
Receives data packets over Art-Net and distributes them via websockets to one
or more Pixelblazes

This is a work in progress.  You are welcome to try it out, and I would love to hear your feedback,
but please check back frequently for updates, and be aware that it is not yet ready for production use. 

### State of the Project
##### *Art-Net -> Pixelblaze Routing works!*
You can send Art-Net data from your lighting application to FlameCaster, and on to your Pixelblazes!
At this point, routing is quite reliable, even as Pixelblazes and Art-Net sources come and go at random. There is still
work to be done to see if we can improve frame rates for Pixelblazes with large (>500) numbers of pixels. This appears
to be a function of both wi-fi signal quality and the size of the websockets messages that must be sent for
each frame.  

##### *Web UI (There's a Web UI!)* 
You can view and configure Flamecaster from your tablet, phone, etc.  All the basics are working, and refinements are in progress.
By default, the web UI is available at http://localhost:8081.  You can change the address and port from the settings panel.

##### *Documentation*
There will be actual documentation someday.  I promise.  If you're familiar with Pixelblaze and Art-Net, it's mostly
self-explanatory though.

The basics are:
- When editing, press the "+" button to add a thing, and the "-" button to remove one.
- The left-hand panel is the main menu.
- To see the list of Pixelblazes, where you can add, edit or remove devices, press the "Pixelblazes" button in the left-hand panel.
- To add, edit or remove Art-Net sources, select a Pixelblaze and press the "Art-Net" button in the
left-hand panel, or double click the Pixelblaze you want to edit.  
- After you've edited things to your liking, **press "Save" in the left-hand panel to save your changes and 
restart the server with your new settings.**  (This will momentarily disconnect all Pixelblazes, so don't do it
during a show!)
- Changes to WebUI address:port won't be active until the next time you start Flamecaster.


### Requirements
Requires Python 3.10+, and the following libraries from pypl:
- numpy
- websocket-client
- remi

Flamecaster is pure Python, and should run on any platform that supports Python 3.10+.  It is reasonably efficient, and 
will be optimized further as we go, but if you're going to run a significant number of pixels, I'd suggest a Raspberry
Pi 4 or better. If you're running your show from a laptop or desktop, it can also happily run there along with your
lighting software.  (This has the added advantage of keeping your Art-Net traffic off the network.)


### Installation and Usage
1. Clone or download this repository to your system.
2. Install and load the included 'Artnet Receiver' pattern on your Pixelblazes.
3. Install Python 3.10 or later on your system according to your OS's instructions.
4. Install the required Python libraries using pip:
```
pip install numpy websocket-client remi
```
5. Run Flamecaster from the command line:
```
python -m Flamecaster
```

### Notes
- Art-Net DMX is currently the only supported protocol.  Yes, you'll have to divide your project into 170-pixel chunks!
Artsync is currently not supported.
- Automatic Pixelblaze detection is not yet implemented.  It's coming, but you'll need to use static IP addresses for
now.  This means you'll need a router that can act as a DHCP server. (Most can, but be sure before you invest in one.)
In any case, I strongly recommend against using the Pixelblaze's built-in wireless AP in an Artnet-driven project.
It is not designed for the high traffic level and may result in both slow network and slow Pixelblaze LED rendering
performance.
- Pixelblaze v3 hardware is **highly** recommended.  You can use a Pixelblaze 2, but you'll need to restrict outgoing frame rate to
10fps or less to avoid saturating the Pixelblaze's websocket connection. 
- How shall I say this?   Wi-Fi: It's way twitchier than anyone would like.  Before you take a wireless LED project live in
an adverse environment (pretty much anywhere in public, really), be prepared to spend time optimizing router setup, channel selection, antenna positioning, and
anything and everything else that might improve the signal.  
- Don't try to send your Art-Net traffic to Flamecaster over Wi-Fi.  Especially not the same Wi-Fi network
you're using for your Pixelblazes.  S...l...o...w...  Slow and cranky.   

### Acknowledgements
Uses the REMI library to create its web interface.
More information about REMI can be found at: https://github.com/dddomodossola/remi

Uses a highly modified version of the StupidArtnet library to receive Art-Net data.
More information about StupidArtnet can be found at: https://github.com/cpvalente/stupidArtnet

Uses a radically modified version of the pixelblaze-client library to communicate with Pixelblazes.
More information about pixelblaze-client can be found at: https://github.com/zranger1/pixelblaze-client

### Version History
```
v0.5.0   03/03/2024 Initial pre-alpha release
v0.5.1   03/04/2024 Update to packet handling to make Xlights happier
```

### Donation
If this project saves you time and effort, please consider donating to help support my Open Source work.  Every donut or cup of coffee is a wonderful help!  :-)

[![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/donate/?hosted_button_id=YM9DKUT5V34G8)
