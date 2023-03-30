"""
 sacntest.py

 Receives e1.31 packets containing pixel data from lightshowpi and sends
 them via setVars() to a Pixelblaze.
 
 Requires Python 3, websocket-client, sacn and pyblaze.py
 
 Copyright 2020 JEM (ZRanger1)

 Permission is hereby granted, free of charge, to any person obtaining a copy of this
 software and associated documentation files (the "Software"), to deal in the Software
 without restriction, including without limitation the rights to use, copy, modify, merge,
 publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons
 to whom the Software is furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included in all copies or
 substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
 BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
 AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
 CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
 ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 THE SOFTWARE.

 Version  Date         Author    Comment
 v0.0.1   11/27/2020   ZRanger1  Created
 v0.0.2   12/01/2020   ZRanger1  Update pixelblaze-client lib
 v0.1.0   12/28/2022   ZRanger1  Actually make this thing useful
"""
from pixelblaze import *
import sacn
import time
import json
import sys
import array
import ConfigParser
import DisplayDevice


class SacnProxy:
    """
    Listens for e1.31 (sACN) data and forwards it to one or more Pixelblazes.
    """
    pb = None
    receiver = None
    pixelsPerUniverse = 170
    pixelCount = 0
    dataReady = False
    notifyTimer = 0
    FrameCount = 0
    delay = 0.033333  # default to 30 fps outgoing limit
    notify_ms = 3000  # throughput check every <notify_ms> milliseconds
    show_fps = False
    configFileName = "../config/config.conf"

    config = None
    universeFragments = None
    deviceList = None
    
    pixels = []
    
    def __init__(self, bindAddr, pixelBlazeAddr):
        print("hi there!")

        ConfigParser.load(self.configFileName)

        # should use numpy for performance
        #self.pixels = [0 for x in range(512)]  # max size of a dmx universe tuple

        #self.pb = Pixelblaze(pixelBlazeAddr)   # create Pixelblaze object
        #result = self.pb.getHardwareConfig()
        #self.pixelCount = result['pixelCount']

        # bind multicast receiver to specific IP address
        #self.receiver = sacn.sACNreceiver(bind_address=bindAddr)
        #self.receiver.start()  # start receiver thread

        # set things up to listen for packets on all universes and call our dispatcher
        #self.receiver.register_listener('universe', main_dispatcher)

        """
        TODO - what we need to do here is scan our config file for universes and create
        an appropriate callback fo
        r each one, which will parse the data and fill in pixels
        on every relevant display device, then invoke that device's "send" method to 
        get the data to the Pixelblaze.
        """

        """
        # how to pack and send a packet of data to pixelblaze, in case I forget.
         @self.receiver.listen_on('universe', universe=1) 
         def callback_one(packet):  # packet is type sacn.DataPacket.
            self.pack_data(packet.dmxData, 0)
            self.dataReady = True
        """



    def debugPrintFps(self):
        self.show_fps = True
                       
    def setPixelsPerUniverse(self, pix):
        self.pixelsPerUniverse =  max(1, min(pix, 170))  # clamp to 1-170 pixels
        
    def setMaxOutputFps(self, fps):
        self.delay = 1 / fps
        
    def setThroughputCheckInterval(self, ms):
        self.notify_ms = max(500, ms)  # min interval is 1/2 second, default should be about 3 sec
    
    def time_millis(self):
        return int(round(time.time() * 1000))
    
    def calc_frame_stats(self):
        self.FrameCount += 1
        
        t = self.time_millis() - self.notifyTimer
        if (t >= self.notify_ms):
            t = 1000 * self.FrameCount / self.notify_ms
            if (self.show_fps):
                print("Incoming fps: %d"%t)
            self.FrameCount = 0                                      
          
            self.notifyTimer = self.time_millis()                  
        pass
    

        
    def run(self):
                    
        # start listening for multicasts -- joining a single universe seems to get you 
        # multicast packets for all universes, at least from lightshowpi.
        # TODO - verify that this works with other sacn providers
        self.receiver.join_multicast(1)
        self.notifyTimer = self.time_millis() 
        
        # loop forever, listening for sacn packets and forwarding the pixel data
        # to Pixelblaze
        while True:    
            time.sleep(self.delay) # limit outgoing framerate
            
            if (self.dataReady == True):
                self.send_frame(self.pb)               
                self.calc_frame_stats()                                      
                self.dataReady = False
                
    def stop(self):
        self.receiver.stop()
        self.pb.close()
        

if __name__ == "__main__":
    print("Hi from main")

    mirror = SacnProxy("127.0.0.1", "192.168.1.18")  # arguments: ip address of proxy machine, ip address of pixelblaze
    mirror.setPixelsPerUniverse(170)
    mirror.setMaxOutputFps(30)
    mirror.setThroughputCheckInterval(3000)
    mirror.debugPrintFps()

    exit(-1)

    
    try:
        pass

        #mirror.run()   # run forever (until stopped by ctrl-c or exception)
       
    except KeyboardInterrupt:
        mirror.stop()
        print("sacnProxy halted by keyboard interrupt")
    
    except Exception as blarf:
        mirror.stop()
        template = "sacnProxy halted by unexpected exception. Type: {0},  Args:\n{1!r}"
        message = template.format(type(blarf).__name__, blarf.args)
        print(message)         
        
        

    
