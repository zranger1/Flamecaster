from remi.gui import *
from UIConstants import uiTextHeight

class SingleRowSelectionTable(TableWidget):
    """ A subclass of gui.Table that has the feature
        that the last selected row is highlighted.
    """

    def __init__(self, *arg, **kwargs):
        super(SingleRowSelectionTable, self).__init__(*arg, **kwargs)
        self.last_clicked_row = None
        self.last_item_clicked = None

    @decorate_event
    def on_table_row_click(self, row, item):
        """ Highlight selected row, return the row and item clicked."""
        if self.last_clicked_row is not None:
            del self.last_clicked_row.style['outline']

        if row != self.children['0']:
            self.last_clicked_row = row
            self.last_item_clicked = item
            self.last_clicked_row.style['outline'] = "2px dotted blue"

        else:
            self.last_clicked_row = None
            self.last_item_clicked = None

        return row, item


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
            table.item_at(0, n).style['height'] = uiTextHeight

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
        table = SingleRowSelectionTable(2, 5, True, False, width=427, height=200)

        table.item_at(0, 0).set_text("#")
        table.item_at(0, 1).set_text("Name")
        table.item_at(0, 2).set_text("IP Address")
        table.item_at(0, 3).set_text("Pixels")
        table.item_at(0, 4).set_text("Pattern")
        self.append(table, 'pb_table')

        # create table for universe editing
        title = Label("Art-Net Data")
        title.style['height'] = "20px"
        self.append(title, 'u_title')
        table = SingleRowSelectionTable(2, 7, True, False, width=427, height=200)

        table.style.css_top = "220px"
        table.style.css_left = "50px"
        table.item_at(0, 0).set_text("#")
        table.item_at(0,1).set_text("Net")
        table.item_at(0,2).set_text("Subnet")
        table.item_at(0, 3).set_text("Universe")
        table.item_at(0, 4).set_text("Start Ch")
        table.item_at(0, 5).set_text("Dest Index")
        table.item_at(0, 6).set_text("Pixels")
        self.append(table, 'u_table')

    def set_devices_text(self, data: dict):
        # get number of keys in the dictionary
        num_keys = len(data)
        table = self.get_child('pb_table')
        table.set_row_count(num_keys + 3)

        # fix the header height, which keeps getting reset
        for n in range(5):
            table.item_at(0, n).style['height'] = uiTextHeight

        row = 1
        # for each key in the dictionary
        for key in data:
            for n in range(5):
                table.item_at(row, n).style['height'] = uiTextHeight

            db = data[key]
            # set the row number
            table.item_at(row, 0).set_text(str(row))
            table.item_at(row, 1).set_text(db.get('name', ''))
            table.item_at(row, 2).set_text(db.get('ip', ''))
            table.item_at(row, 3).set_text(str(db.get('pixelCount',0)))
            table.item_at(row, 4).set_text(db.get('renderPattern','@preset'))
            row += 1

    def set_universes_text(self, data: dict):
        # get number of keys in the dictionary
        num_keys = len(data)
        table = self.get_child('u_table')
        # clear everything but headers out of the table, then
        # set the new size.
        table.set_row_count(1)
        table.set_row_count(num_keys + 3)

        # fix the header height, which keeps getting reset
        for n in range(7):
            table.item_at(0, n).css_height = uiTextHeight

        row = 1
        # for each key in the dictionary
        for key in data:
            for n in range(7):
                table.item_at(row, n).css_height = uiTextHeight

            # set the row number
            table.item_at(row, 0).set_text(str(row))
            table.item_at(row, 1).set_text(str(data.get(key).get('net',0)))
            table.item_at(row, 2).set_text(str(data.get(key).get('subnet',0)))
            table.item_at(row, 3).set_text(str(data.get(key).get('universe',0)))
            table.item_at(row, 4).set_text(str(data.get(key).get('startChannel',0)))
            table.item_at(row, 5).set_text(str(data.get(key).get('destIndex',0)))
            table.item_at(row, 6).set_text(str(data.get(key).get('pixelCount',0)))
            row += 1
