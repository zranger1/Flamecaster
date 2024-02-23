import json

import remi.gui as gui
from remi import App, start
from multiprocessing import Queue
from multiprocessing import Event

cmdQueue: Queue
dataQueue: Queue
ui_is_active: Event


class RemiWrapper:
    def __init__(self, cmdQ, dataQ, ui_flag):
        global cmdQueue
        cmdQueue = cmdQ

        global dataQueue
        dataQueue = dataQ

        global ui_is_active
        ui_is_active = ui_flag

        start(WebInterface, port=8081, start_browser=False, update_interval=0.1, debug=False)


class WebInterface(App):
    table = None
    devices = {}

    def __init__(self, *args):
        super(WebInterface, self).__init__(*args)
        self.devices = dict()

    def idle(self):
        if not ui_is_active.is_set():
            ui_is_active.set()
        if not dataQueue.empty():
            # get the JSON status string from the queue
            status = json.loads(dataQueue.get())
            self.devices[status['name']] = status

            # reconfigure the table for the updated device list
            self.table.set_row_count(1+len(self.devices))
            self.fill_table()
            self.table.redraw()

    def main(self):
        container = gui.VBox(width=720, height=1480)

        self.table = gui.TableWidget(4, 3, True, False, width=500, height=700)
        # self.table.style['font-size'] = '8px'

        # appending a widget to another, the first argument is a string key
        container.append(self.table, "stats")
        # returning the root widget
        return container

    def fill_table(self):
        # add information from the devices dictionary to the table
        # print(self.devices)
        for i, key in enumerate(self.devices):
            self.table.item_at(i, 0).set_text(key)
            self.table.item_at(i, 1).set_text(str(self.devices[key]['inPps']))
            self.table.item_at(i, 2).set_text(str(self.devices[key]['outFps']))
