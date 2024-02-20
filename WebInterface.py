import remi.gui as gui
from remi import start, App

class WebInterface(App):
    def __init__(self, *args):
        super(WebInterface, self).__init__(*args)

    def main(self):
        container = gui.VBox(width=120, height=100)
        self.lbl = gui.Label('Hello world!')
        self.bt = gui.Button('Press me!')

        # setting the listener for the onclick event of the button
        self.bt.onclick.do(self.on_button_pressed)

        # appending a widget to another, the first argument is a string key
        container.append(self.lbl)
        container.append(self.bt)

        # returning the root widget
        return container

    # listener function
    def on_button_pressed(self, widget):
        self.lbl.set_text('Button pressed!')
        self.bt.set_text('Hi!')

    def stop_server(self):
        self.server.server_starter_instance._alive = False
        self.server.server_starter_instance._sserver.shutdown()
        print("server stopped")
