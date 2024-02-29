from remi.gui import *

from UIConstants import uiTextHeight
from remi_extensions import SingleRowSelectionTable


def make_action_button(text, offset, left):
    btn = Button(text)
    btn.attributes['class'] = "Button"
    btn.style['position'] = "absolute"
    btn.style['overflow'] = "auto"
    btn.style['left'] = str(offset + left) + "px"
    btn.style['top'] = "24px"
    btn.style['margin'] = "0px"
    btn.style['width'] = "50px"
    btn.style['display'] = "block"
    btn.style['height'] = "20px"
    return btn


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
        self.append(title, 'title')

        table = TableWidget(4, 5, True, False, width="427px", height="100%")

        for n in range(5):
            table.item_at(0, n).style['height'] = uiTextHeight

        table.item_at(0, 0).set_text("Name")
        table.item_at(0, 1).set_text("IP Address")
        table.item_at(0, 2).set_text("PPS in")
        table.item_at(0, 3).set_text("FPS out")
        table.item_at(0, 4).set_text("Connected")

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

        rowHeight = 22
        tx = 30
        self.make_control_row("Max FPS", "maxFps", tx)
        tx += rowHeight
        self.make_control_row("Update Interval", "updateInterval", tx)
        tx += rowHeight
        self.make_control_row("Art-Net IP", "artNetIp", tx)
        tx += rowHeight
        self.make_control_row("Art-Net Port", "artNetPort", tx)
        tx += rowHeight
        self.make_control_row("Web IP", "webIp", tx)
        tx += rowHeight
        self.make_control_row("Web Port", "webPort", tx)

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
        self.get_child('maxFps').set_text(str(data.get('maxFps', 0)))
        self.get_child('updateInterval').set_text(str(data.get('statusUpdateIntervalMs', 0)))
        self.get_child('artNetIp').set_text(data.get('ipArtnet', '127.0.0.1'))
        self.get_child('artNetPort').set_text(str(data.get('portArtnet', '6454')))
        self.get_child('webIp').set_text(data.get('ipWebInterface', '127.0.0.1'))
        self.get_child('webPort').set_text(str(data.get('portWebInterface', '8081')))

    def get_system_text(self, data: dict):
        data['maxFps'] = int(self.get_child('maxFps').get_text())
        data['statusUpdateIntervalMs'] = int(self.get_child('updateInterval').get_text())
        data['ipArtnet'] = self.get_child('artNetIp').get_text()
        data['portArtnet'] = int(self.get_child('artNetPort').get_text())
        data['ipWebInterface'] = self.get_child('webIp').get_text()
        data['portWebInterface'] = int(self.get_child('webPort').get_text())


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
        self.style['height'] = "480px"

        # create table for devices
        title = Label("Pixelblazes")
        self.append(title, 'pb_title')

        btn = make_action_button("+", 200, 10)
        self.append(btn, 'btnAdd')
        btn = make_action_button("-", 200, 80)
        self.append(btn, 'btnRemove')
        btn = make_action_button("Art-Net", 200, 150)
        self.append(btn, 'btnEdit')

        table = SingleRowSelectionTable(2, 5, True, True, width="427px", height="100%")
        table.set_column_keys(['name', 'ip', 'pixelCount', 'maxFps', 'renderPattern'])
        table.style['position'] = "absolute"
        table.style['overflow'] = "auto"
        table.style['left'] = "0px"
        table.style['top'] = "50px"

        table.item_at(0, 0).set_text("Name")
        table.item_at(0, 1).set_text("IP Address")
        table.item_at(0, 2).set_text("Pixels")
        table.item_at(0, 3).set_text("Max FPS")
        table.item_at(0, 4).set_text("Pattern")
        self.append(table, 'pb_table')

    def set_devices_text(self, data: dict):
        # get number of keys in the dictionary
        num_keys = len(data)
        table = self.get_child('pb_table')
        table.set_row_count(1)
        table.clear_row_keys()
        table.set_row_count(num_keys + 2)

        # fix the header height, which keeps getting reset
        for n in range(5):
            table.item_at(0, n).style['height'] = uiTextHeight

        row = 1
        # for each key in the dictionary
        for key in data:
            for n in range(5):
                table.item_at(row, n).style['height'] = uiTextHeight

            db = data[key]
            table.set_row_key(row, key)
            table.item_at(row, 0).set_text(db.get('name', ''))
            table.item_at(row, 1).set_text(db.get('ip', ''))
            table.item_at(row, 2).set_text(str(db.get('pixelCount', 0)))
            table.item_at(row, 3).set_text(str(db.get('maxFps', 30)))
            table.item_at(row, 4).set_text(db.get('renderPattern', '@preset'))
            row += 1


class UniversesContainer(Container):
    def __init__(self, **kwargs):
        super(UniversesContainer, self).__init__(**kwargs)
        self.style['position'] = "absolute"
        self.style['overflow'] = "auto"
        self.style['background-color'] = "#80f7ff"
        self.style['left'] = "10px"
        self.style['top'] = "10px"
        self.style['margin'] = "0px"
        self.style['width'] = "427px"
        self.style['display'] = "block"
        self.style['height'] = "480px"

        self.deviceTag = None
        self.deviceName = ''

        # create table for universe editing
        title = Label("Universe Data")
        self.append(title, 'u_title')

        btn = make_action_button("Back", 0, 10)
        self.append(btn, 'btnBack')
        btn = make_action_button("+", 200, 10)
        self.append(btn, 'btnAdd')
        btn = make_action_button("-", 200, 80)
        self.append(btn, 'btnRemove')

        table = SingleRowSelectionTable(2, 6, True, True, width=427, height="100%")
        table.set_column_keys(['net', 'subnet', 'universe', 'startChannel', 'destIndex', 'pixelCount'])
        table.style['position'] = "absolute"
        table.style['overflow'] = "auto"
        table.style['left'] = "0px"
        table.style['top'] = "50px"

        table.item_at(0, 0).set_text("Net")
        table.item_at(0, 1).set_text("Subnet")
        table.item_at(0, 2).set_text("Universe")
        table.item_at(0, 3).set_text("Start Ch")
        table.item_at(0, 4).set_text("Dest Index")
        table.item_at(0, 5).set_text("Pixels")
        self.append(table, 'u_table')

    def set_universes_text(self, data: dict, name: str = None, devTag=None):
        # if a new device tag isn't specified, leave it alone.
        if devTag is not None:
            self.deviceTag = devTag

        if name is not None:
            self.deviceName = name

        label = self.get_child('u_title')
        label.set_text("Universe Data for " + self.deviceName)

        # get number of keys in the dictionary
        num_keys = len(data)
        table = self.get_child('u_table')
        # clear everything but headers out of the table, then
        # set the new size.
        table.set_row_count(1)
        table.clear_row_keys()
        table.set_row_count(num_keys + 2)

        # fix the header height, which keeps getting reset
        for n in range(6):
            table.item_at(0, n).css_height = uiTextHeight

        row = 1
        # for each key in the dictionary
        for key in data:
            for n in range(6):
                table.item_at(row, n).css_height = uiTextHeight

            table.set_row_key(row, key)
            table.item_at(row, 0).set_text(str(data.get(key).get('net', 0)))
            table.item_at(row, 1).set_text(str(data.get(key).get('subnet', 0)))
            table.item_at(row, 2).set_text(str(data.get(key).get('universe', 0)))
            table.item_at(row, 3).set_text(str(data.get(key).get('startChannel', 0)))
            table.item_at(row, 4).set_text(str(data.get(key).get('destIndex', 0)))
            table.item_at(row, 5).set_text(str(data.get(key).get('pixelCount', 0)))
            row += 1
