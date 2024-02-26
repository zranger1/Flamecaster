from remi.gui import *


class StatusContainer(Container):
    def __init__(self, **kwargs):
        super(StatusContainer, self).__init__(**kwargs)
        self.style['position'] = "absolute"
        self.style['overflow'] = "auto"
        self.style['background-color'] = "#ffff80"
        self.style['left'] = "10px"
        self.style['top'] = "10px"
        self.style['margin'] = "0px"
        self.style['width'] = "427px"
        self.style['display'] = "block"
        self.style['height'] = "480px"
        title = Label("Status")
        table = TableWidget(4, 5, True, False, width=427, height=480)

        for n in range(5):
            table.item_at(0, n).style['height'] = "30px"

        table.item_at(0, 0).set_text("Name")
        table.item_at(0, 1).set_text("IP Address")
        table.item_at(0, 2).set_text("PPS in")
        table.item_at(0, 3).set_text("FPS out")
        table.item_at(0, 4).set_text("Connected")
        self.append(title, 'title')
        self.append(table, 'status_table')


class SystemSettingsContainer(Container):
    def __init__(self, **kwargs):
        super(SystemSettingsContainer, self).__init__(**kwargs)
        self.style['position'] = "absolute"
        self.style['overflow'] = "auto"
        # self.style['background-color'] = "#80ff9c"
        self.style['left'] = "10px"
        self.style['top'] = "10px"
        self.style['margin'] = "0px"
        self.style['width'] = "427px"
        self.style['display'] = "block"
        self.style['height'] = "480px"
        title = Label("System Settings")
        title.style['background-color'] = "#80ff9c"
        self.append(title, 'title')

        rowHeight = 30
        tx = 30
        self.make_control_row("Max FPS", "maxFps", tx)
        tx += rowHeight
        self.make_control_row("Update Interval", "updateInterval", tx)
        tx += rowHeight
        self.make_control_row("Art-Net IP", "artNetIp", tx)
        tx += rowHeight
        self.make_control_row("Web IP", "webIp", tx)

    def make_control_row(self, label, tag, y):
        topPos = str(y) + 'px'
        title = Label(label)
        title.css_position = "absolute"
        title.style['left'] = "10px"
        title.style['top'] = topPos
        title.style['width'] = "100px"
        self.append(title, 'l_' + tag)

        txt = TextInput()
        txt.css_position = "absolute"
        txt.attr_maxlength = 15
        txt.style['left'] = "120px"
        txt.style['top'] = topPos
        txt.style['width'] = "130px"
        txt.style['height'] = "20px"
        self.append(txt, tag)

    def set_system_text(self, data: dict):
        self.get_child('maxFps').set_text(str(data['maxFps']))
        self.get_child('updateInterval').set_text(str(data['statusUpdateIntervalMs']))
        self.get_child('artNetIp').set_text(data['ipArtnet'])
        self.get_child('webIp').set_text(data['ipWebInterface'])

    def get_system_text(self, data: dict):
        data['maxFps'] = int(self.get_child('maxFps').get_text())
        data['statusUpdateIntervalMs'] = int(self.get_child('updateInterval').get_text())
        data['ipArtnet'] = self.get_child('artNetIp').get_text()
        data['ipWebInterface'] = self.get_child('webIp').get_text()


class DevicesContainer(Container):
    def __init__(self, **kwargs):
        super(DevicesContainer, self).__init__(**kwargs)
        self.style['position'] = "absolute"
        self.style['overflow'] = "auto"
        self.style['background-color'] = "#80f7ff"
        self.style['left'] = "10px"
        self.style['top'] = "10px"
        self.style['margin'] = "0px"
        self.style['width'] = "427px"
        self.style['display'] = "block"
        self.style['height'] = "200px"
        title = Label("Pixelblazes")

        table = TableWidget(2, 5, True, False, width=427, height=200)

        table.item_at(0, 0).set_text("#")
        table.item_at(0, 1).set_text("Name")
        table.item_at(0, 2).set_text("IP Address")
        table.item_at(0, 3).set_text("Pixels")
        table.item_at(0, 4).set_text("Pattern")

        self.append(title, 'title')
        self.append(table, 'pb_table')

    def set_devices_text(self, data: dict):
        # get number of keys in the dictionary
        num_keys = len(data)
        table = self.get_child('pb_table')
        table.set_row_count(num_keys + 3)

        # fix the header height, which keeps getting reset
        for n in range(5):
            table.item_at(0, n).style['height'] = "30px"

        row = 1
        # for each key in the dictionary
        for key in data:
            for n in range(5):
                table.item_at(row, n).style['height'] = "30px"

            # set the row number
            table.item_at(row, 0).set_text(str(row))
            table.item_at(row, 1).set_text(data[key]['name'])
            table.item_at(row, 2).set_text(data[key]['ip'])
            table.item_at(row, 3).set_text(str(data[key]['pixelCount']))
            table.item_at(row, 4).set_text(data[key]['renderPattern'])
            row += 1


class RoutingContainer(Container):
    def __init__(self, **kwargs):
        super(RoutingContainer, self).__init__(**kwargs)
        self.style['position'] = "absolute"
        self.style['overflow'] = "auto"
        self.style['background-color'] = "#e380ff"
        self.style['left'] = "10px"
        self.style['top'] = "10px"
        self.style['margin'] = "0px"
        self.style['width'] = "427px"
        self.style['display'] = "block"
        self.style['height'] = "480px"
        title = Label("Routing")
        self.append(title, 'title')
