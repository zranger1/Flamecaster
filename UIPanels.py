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
        table.item_at(0, 2).set_text("Packets/Sec in")
        table.item_at(0, 3).set_text("FPS out")
        table.item_at(0, 4).set_text("Connected")
        self.append(title, 'title')
        self.append(table, 'status_table')


class SystemSettingsContainer(Container):
    def __init__(self, **kwargs):
        super(SystemSettingsContainer, self).__init__(**kwargs)
        self.style['position'] = "absolute"
        self.style['overflow'] = "auto"
        self.style['background-color'] = "#80ff9c"
        self.style['left'] = "10px"
        self.style['top'] = "10px"
        self.style['margin'] = "0px"
        self.style['width'] = "427px"
        self.style['display'] = "block"
        self.style['height'] = "480px"
        title = Label("System Settings")
        self.append(title, 'title')
        
        
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
        title = Label("Pixelblazes")
        self.append(title, 'title')


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
