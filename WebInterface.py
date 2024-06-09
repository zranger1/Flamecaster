import json

from remi import App
from remi.server import Server

from ArtnetUtils import clamp, artnet_to_int
from ProcessManager import restartArtnetRouter
from UIPanels import *

pd: ProjectData


def make_unique_tag(data: dict):
    """
    Given a dictionary, return a unique stringified integer tag that is not in the dictionary.
    :param data:
    :return: tag
    """
    n = len(data)
    while True:
        tag = str(n)
        if tag not in data:
            return tag
        n += 1


def str_to_int(s: str):
    """
    Convert a string to a positive integer, or return 0 if the string is not a valid number
    :param s:
    :return: int
    """
    try:
        return max(0, int(float(s)))
    except ValueError:
        return 0


class RemiWrapper:
    """
    Set up local data and run our remi-based web interface.
    """

    def __init__(self, projectData: ProjectData):
        global pd
        pd = projectData

        # get the web server configuration
        webIp = pd.liveConfig['system'].get('ipWebInterface')
        webPort = int(pd.liveConfig['system'].get('portWebInterface'))

        print("Starting Web UI at http://%s:%s" % (webIp, webPort))
        self.start(Flamecaster, address=webIp, port=webPort, start_browser=False, update_interval=0.1, debug=False)

    def start(self, main_gui_class, **kwargs):
        """Start the remi server without disturbing the app's root
        logging setup"""
        kwargs.pop('debug', False)
        kwargs.pop('standalone', False)

        logging.getLogger('remi').setLevel(level=logging.CRITICAL)

        try:
            Server(main_gui_class, start=True, **kwargs)
        except Exception as e:
            logging.error("Web UI server failed to start: " + str(e))
            logging.error("Retrying (once) on localhost:8081")
            logging.error("Please check (and save) your Web UI ip:port configuration in System Settings and try again.")
            kwargs.pop('address', None)
            kwargs.pop('port', None)

            # set up fallback Web UI configuration
            webIp = '127.0.0.1'
            webPort = 8081
            pd.liveConfig['system']['ipWebInterface'] = webIp
            pd.liveConfig['system']['portWebInterface'] = webPort
            print("Web UI did not start due to exception (probably invalid ip:port address in config file).")
            print("Attempting restart. Web UI will be available at: http://%s:%s" % (webIp, webPort))
            Server(main_gui_class, start=True, address=webIp, port=webPort, **kwargs)


# noinspection PyUnusedLocal
class Flamecaster(App):
    status_table = None
    devices = {}
    baseContainer = None
    statusPanel = None
    systemPanel = None
    devicesPanel = None
    universesPanel = None

    def __init__(self, *args):
        super(Flamecaster, self).__init__(*args)
        self.devices = dict()

    def idle(self):
        # if we're here, that means the web server is running.
        # activate the UI flag if it's not already set, so we will
        # start receiving status updates from the Artnet router
        if not pd.ui_is_active.is_set():
            pd.ui_is_active.set()
        if not pd.dataQueue.empty():
            # read the JSON status strings from the queue
            msg = json.loads(pd.dataQueue.get())
            # if top level key is "name", it's a device status message
            if 'name' in msg:
                # update the device dictionary with the new status
                self.devices[msg['name']] = msg

            # reconfigure the status table for the updated device list
            # leave the top row for labels.  The bottom row is blank
            # because it will expand to fill any remaining space in the
            #
            self.status_table.set_row_count(3 + len(self.devices))
            self.fill_status_table()
            self.status_table.redraw()

    def main(self):

        # The root Container
        baseContainer = Container()
        baseContainer.attributes['class'] = "Container  "
        baseContainer.style['position'] = "absolute"
        baseContainer.style['overflow'] = "auto"
        baseContainer.style['background-color'] = "rgb(44,44,44)"
        baseContainer.style['left'] = "0px"
        baseContainer.style['top'] = "0px"
        baseContainer.style['margin'] = "0px"
        baseContainer.style['border-style'] = "solid"
        baseContainer.style['width'] = "100%"
        baseContainer.style['display'] = "block"
        baseContainer.style['border-width'] = "1px"
        baseContainer.style['height'] = "100%"

        # The menuContainer on the left side - holds the buttons to switch between the contentWidgets
        menuContainer = Container()
        menuContainer.attributes['class'] = "Container"
        menuContainer.style['position'] = "absolute"
        menuContainer.style['overflow'] = "auto"
        menuContainer.style['left'] = "1em"
        menuContainer.style['top'] = "1em"
        menuContainer.style['margin'] = "0px"
        menuContainer.style['border-style'] = "solid"
        menuContainer.style['width'] = "12em"
        menuContainer.style['display'] = "block"
        menuContainer.style['border-width'] = "1px"
        menuContainer.style['height'] = "90%"

        # Buttons for the button menu on the left side
        btnStatus = make_menu_button("Status", 10)
        btnStatus.onclick.do(self.onclick_btnStatus)
        menuContainer.append(btnStatus, 'btnStatus')

        btnSystem = make_menu_button("System", 60)
        btnSystem.onclick.do(self.onclick_btnSystem)
        menuContainer.append(btnSystem, 'btnSystem')

        btnDevices = make_menu_button("Pixelblazes", 110)
        btnDevices.onclick.do(self.onclick_btnDevices)
        menuContainer.append(btnDevices, 'btnDevices')

        btn = make_menu_button("Save", 310)
        btn.onclick.do(self.menu_save_clicked)
        menuContainer.append(btn, 'btnSave')

        btn = make_menu_button("Reload", 360)
        btn.onclick.do(self.menu_reload_clicked)
        menuContainer.append(btn, 'btnReload')

        btn = make_menu_button("New", 410)
        btn.onclick.do(self.menu_new_clicked)
        menuContainer.append(btn, 'btnNew')

        btn = make_menu_button("Exit", 460)
        btn.onclick.do(self.menu_exit_clicked)
        menuContainer.append(btn, 'btnExit')

        # Add the menuContainer to the baseContainer and define the listeners for the menu elements
        baseContainer.append(menuContainer, 'menuContainer')

        # The contentContainer
        contentContainer = Container()
        contentContainer.attributes['class'] = "Container"
        contentContainer.style['position'] = "absolute"
        contentContainer.style['overflow'] = "auto"
        contentContainer.style['left'] = "13.75em"
        contentContainer.style['top'] = "1em"
        contentContainer.style['margin'] = "0px"
        contentContainer.style['border-style'] = "solid"
        contentContainer.style['width'] = "36em"
        contentContainer.style['display'] = "block"
        contentContainer.style['border-width'] = "1px"
        contentContainer.style['height'] = "90%"

        # Create top Level instances for the content Widgets.
        # By defining these as top Level the Widgets live even when they are not shown

        self.statusPanel = StatusContainer()
        # get a reference to the table in the screen1 Widget
        self.status_table = self.statusPanel.children['status_table']

        self.systemPanel = SystemSettingsContainer()
        self.systemPanel.set_system_text(pd.editableConfig.get('system', {}))

        self.devicesPanel = DevicesContainer()
        self.devicesPanel.set_devices_text(pd.editableConfig.get('devices', {}))

        self.universesPanel = UniversesContainer()
        self.universesPanel.set_universes_text({})

        # event handlers for the system panel
        self.systemPanel.children['maxFps'].onchange.do(self.on_system_setting_changed)
        self.systemPanel.children['updateInterval'].onchange.do(self.on_system_setting_changed)
        self.systemPanel.children['artNetIp'].onchange.do(self.on_system_setting_changed)
        self.systemPanel.children['artNetPort'].onchange.do(self.on_system_setting_changed)
        self.systemPanel.children['webIp'].onchange.do(self.on_system_setting_changed)
        self.systemPanel.children['webPort'].onchange.do(self.on_system_setting_changed)

        # event handlers for devices panel
        self.devicesPanel.children['pb_table'].ondblclick.do(self.ondblclick_pixelblaze_table)
        self.devicesPanel.children['btnEdit'].onclick.do(self.ondblclick_pixelblaze_table)
        self.devicesPanel.children['btnAdd'].onclick.do(self.onclick_btnAddDevice)
        self.devicesPanel.children['btnRemove'].onclick.do(self.onclick_btnRemoveDevice)
        self.devicesPanel.children['pb_table'].on_item_changed.do(self.on_device_setting_changed)

        # event handlers for universes table
        self.universesPanel.children['btnBack'].onclick.do(self.onclick_btnUniverseBack)
        self.universesPanel.children['btnAdd'].onclick.do(self.onclick_btnAddUniverse)
        self.universesPanel.children['btnRemove'].onclick.do(self.onclick_btnRemoveUniverse)
        self.universesPanel.children['u_table'].on_item_changed.do(self.on_universe_setting_changed)

        # Add initial content to the contentContainer - we start with the
        # status panel displayed
        contentContainer.append(self.statusPanel, 'statusPanel')

        # Add the contentContainer to the baseContainer
        baseContainer.append(contentContainer, 'contentContainer')

        # Make the local "baseContainer" a class member of the App
        self.baseContainer = baseContainer

        # return the baseContainer as root Widget
        return self.baseContainer

    def getNextAvailableUniverse(self):
        """
        Scan the editableConfig for the next available universe number
        :return:  next available (net, subnet, universe)
        """
        data = pd.editableConfig.get('devices', {})
        highestUniverse = -1
        for devTag in data:
            dev = data[devTag]
            for uTag in dev.get('data', {}):
                net = dev['data'][uTag].get('net', 0)
                subnet = dev['data'][uTag].get('subnet', 0)
                universe = dev['data'][uTag].get('universe', 0)
                mask = artnet_to_int(net, subnet, universe)
                highestUniverse = max(highestUniverse, mask)

        return decode_address_int(highestUniverse + 1)

    def on_close(self):
        # deactivate the UI flag and empty the data queue
        pd.ui_is_active.clear()
        while not pd.dataQueue.empty():
            pd.dataQueue.get()

        super(Flamecaster, self).on_close()

    def on_system_setting_changed(self, widget, newValue):
        """Event callback for system setting change.
        """
        # TODO - validate the Ip addresses and port numbers if we can
        # by the time we get here, if the system key doesn't exist, something
        # is seriously wrong and we need to know about it.
        self.systemPanel.get_system_text(pd.editableConfig['system'])

    def on_device_setting_changed(self, table: SingleRowSelectionTable, item, new_value, row, column):
        """Event callback for table item change.

        Args:
            table (TableWidget): The emitter of the event.
            item (TableItem): The TableItem instance.
            new_value (str): New text content.
            row (int): row index.
            column (int): column index.
        """
        # perform minimal validation on the new value
        if column == 2 or column == 3:
            new_value = str_to_int(new_value)

        # perform a little validation on "pixels" vs "fixture" setting
        # TODO - need better UI for this, among other things.
        elif column == 4:
            if 'p' in new_value.lower():
                new_value = "pixels"
            else:
                new_value = "fixture"
            item.set_text(new_value)

        # figure out where it belongs in the database
        devTag = table.get_row_key(row)
        key = table.get_column_key(column)
        data = pd.editableConfig.get('devices', {}).get(devTag, {})

        data[key] = new_value

    def on_universe_setting_changed(self, table: SingleRowSelectionTable, item, new_value, row, column):
        """Event callback for table item change.

        Args:
            table (TableWidget): The emitter of the event.
            item (TableItem): The TableItem instance.
            new_value (str): New text content.
            row (int): row index.
            column (int): column index.
        """
        # perform a little validation on the new value
        new_value = str_to_int(new_value)

        # make sure that address values are in roughly the correct range
        # TODO - seriously look at Art-Net universe/subnet/net validation
        # TODO - really!  This is high priority!
        if column < 3:
            new_value = clamp(new_value, 0, 255)
        # start channel can be 0-511
        elif column == 3:
            new_value = clamp(new_value, 0, 511)
        # destIndex can be up to the device's pixel count - 1
        elif column == 4:
            devTag = self.universesPanel.deviceTag
            devicePixelCount = pd.editableConfig.get('devices', {}).get(devTag, {}).get('pixelCount', 0)
            new_value = clamp(new_value, 0, devicePixelCount - 1)
        # pixel count per channel can be up to 170
        elif column == 5:
            new_value = clamp(new_value, 0, 170)

        # put the validated value in the table
        item.set_text(str(new_value))

        # figure out where it belongs in the database and put it there.
        devTag = self.universesPanel.deviceTag
        data = pd.editableConfig.get('devices', {}).get(devTag, {}).get('data', {})
        uTag = table.get_row_key(row)
        key = table.get_column_key(column)

        data[uTag][key] = new_value

    def fill_status_table(self):
        """ add information from the devices section of configDatabase to the status panel's
        main table.
        """

        lastRow = 2 + len(self.devices)
        for n in range(5):
            self.status_table.item_at(0, n).style['height'] = uiTextHeight
            self.status_table.item_at(lastRow, n).set_text("  ")

        for i, key in enumerate(self.devices):

            # the first row is reserved for the column headers
            i = i + 1
            db = self.devices[key]
            self.status_table.item_at(i, 0).set_text(key)
            self.status_table.item_at(i, 1).set_text(str(db.get('ip', '')))
            self.status_table.item_at(i, 2).set_text(str(db.get('inPps', 0)))
            self.status_table.item_at(i, 3).set_text(str(db.get('outFps', 0)))

            if db.get('connected', "false") == "true":
                self.status_table.item_at(i, 4).css_color = "rgb(0,0,0)"
                self.status_table.item_at(i, 4).set_text("Yes")
            else:
                self.status_table.item_at(i, 4).css_color = "rgb(255,0,0)"
                self.status_table.item_at(i, 4).set_text("No")

            for n in range(5):
                self.status_table.item_at(i, n).style['height'] = uiTextHeight

    def start_universe_editor(self):
        """Switch to the universes panel.  If it's already showing, do nothing."""
        if 'universesPanel' in self.baseContainer.children['contentContainer'].children.keys():
            return

        self.remove_current_content()

        # Add the status panel to the contentWidget
        self.baseContainer.children['contentContainer'].append(self.universesPanel, 'universesPanel')

    def remove_current_content(self):
        """
        Remove the current content from the contentContainer
        :param self:
        :return:
        """
        currentContent = list(self.baseContainer.children['contentContainer'].children.values())[0]
        self.baseContainer.children['contentContainer'].remove_child(currentContent)

    # switch to the status panel
    def onclick_btnStatus(self, emitter):
        """Switch to the status panel.  If it's already showing, do nothing."""

        if 'statusPanel' in self.baseContainer.children['contentContainer'].children.keys():
            return

        self.remove_current_content()

        # Add the status panel to the contentWidget
        self.baseContainer.children['contentContainer'].append(self.statusPanel, 'statusPanel')

    def onclick_btnSystem(self, emitter):
        """
        Switch to the system panel.  If it's already showing, do nothing.
        :param emitter:
        :return:
        """
        if 'systemPanel' in self.baseContainer.children['contentContainer'].children.keys():
            return

        self.remove_current_content()

        # Add the system panel to the contentWidget
        self.baseContainer.children['contentContainer'].append(self.systemPanel, 'systemPanel')

    def onclick_btnDevices(self, emitter):
        """
        Switch to the devices panel.  If it's already showing, do nothing.
        :param emitter:
        :return:
        """
        if 'devicesPanel' in self.baseContainer.children['contentContainer'].children.keys():
            return

        self.remove_current_content()

        # Add the status panel to the contentWidget
        self.baseContainer.children['contentContainer'].append(self.devicesPanel, 'devicesPanel')

    def onclick_btnAddDevice(self, emitter):
        """
        Add a new Pixelblaze to the configDatabase and redraw the devices table.
        :param emitter:
        :return:
        """
        # to add a device, we add it at the end of the configDatabase devices list,
        # rebuild the table, and redraw it
        data = pd.editableConfig.get('devices', {})

        # generate a unique tag for the new device
        devTag = make_unique_tag(data)

        # add the new device to the database
        data[devTag] = {'name': '*New*', 'ip': '0.0.0.0', 'pixelCount': 0, 'maxFps': 30, 'deviceStyle': 'pixels'}

        # append an empty "data" dictionary to the device
        data[devTag]['data'] = dict()
        self.devicesPanel.set_devices_text(data)
        self.devicesPanel.children['pb_table'].redraw()

    def onclick_btnRemoveDevice(self, emitter):
        """
        Remove the selected device from the configDatabase and redraw the table.
        :param emitter:
        :return:
        """
        # to remove a device, we remove it in configDatabase and rebuild the table
        table = self.devicesPanel.children['pb_table']
        if table.last_clicked_row is not None:
            devTag = table.get_row_key(table.last_clicked_row)
            data = pd.editableConfig.get('devices', {})
            data.pop(devTag, None)
            self.devicesPanel.set_devices_text(data)
            table.redraw()

    def onclick_btnAddUniverse(self, emitter):
        """
        Add a new universe to the device's data and redraw the table.
        :param emitter:
        :return:
        """
        table = self.universesPanel.children['u_table']
        devTag = self.universesPanel.deviceTag
        data = pd.editableConfig.get('devices', {}).get(devTag, {}).get('data', {})
        uTag = make_unique_tag(data)

        # add reasonable defaults for the new universe to the device.
        # TODO - let's be smarter about filling in universe details based on the
        # TODO - device's pixel count and the number of universes already defined
        # TODO - we should also have the option to tightly pack universes because
        # TODO - I think some programs like XLights operate that way by default.
        devicePixelCount = pd.editableConfig.get('devices', {}).get(devTag, {}).get('pixelCount', 0)

        # how many pixels have been accounted for in the device's universes?
        pixelsUsed = 0
        for u in data.values():
            pixelsUsed += u.get('pixelCount', 0)

        # how many pixels are left to be accounted for?
        pixelsLeft = max(0, devicePixelCount - pixelsUsed)
        destIndex = max(0, devicePixelCount - pixelsLeft)

        net, subnet, universe = self.getNextAvailableUniverse()

        data[uTag] = {"net": net, "subnet": subnet, "universe": universe, "startChannel": 0, "destIndex": destIndex,
                      "pixelCount": min(170, pixelsLeft)}

        self.universesPanel.set_universes_text(data)
        table.redraw()

    def onclick_btnRemoveUniverse(self, emitter):
        """
        Remove the selected universe from the device's data and redraw the table.
        :param emitter:
        :return:
        """
        table = self.universesPanel.children['u_table']
        devTag = self.universesPanel.deviceTag

        if table.last_clicked_row is not None:
            uTag = table.get_row_key(table.last_clicked_row)
            data = pd.editableConfig.get('devices', {}).get(devTag, {}).get('data', {})
            data.pop(uTag, None)

            # configDatabase['devices'][devTag]['data'] = data
            self.universesPanel.set_universes_text(data)
            table.redraw()

    def onclick_btnUniverseBack(self, emitter):
        self.onclick_btnDevices(emitter)

    def onclick_pixelblaze_table(self, table):
        pass

    def ondblclick_pixelblaze_table(self, table):
        """Called when the Widget gets double clicked by the user with the left mouse button."""
        table = self.devicesPanel.children['pb_table']

        # only react to clicks on a valid, selected data row
        if table.last_clicked_row is not None:
            devTag = table.get_row_key(table.last_clicked_row)
            data = pd.editableConfig.get('devices', {})
            data = data.get(devTag, {})
            name = data.get('name', '')
            data = data.get('data', {})

            self.universesPanel.set_universes_text(data, name, devTag)
            self.start_universe_editor()
        return

    def menu_new_clicked(self, emitter):
        pd.clearEditable()
        pass

    def menu_save_clicked(self, emitter):
        pd.saveProject()
        restartArtnetRouter(pd)
        pass

    def menu_reload_clicked(self, emitter):
        pd.revertToSaved()
        restartArtnetRouter(pd)
        pass

    def menu_exit_clicked(self, emitter):
        self.close()
        pd.exit_flag.set()
