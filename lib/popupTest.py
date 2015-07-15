from kivy._event import partial
from kivy.app import App
from kivy.core.clipboard import Clipboard
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button



Builder.load_string("""
<RootWidget>
    BoxLayout:
        padding: 30, 30, 30, 30
        orientation: "vertical"
        Label:
            size_hint: 1, 0.2
            text: "Double click buttons to copy tx id"
        ScrollView:
            id: tx_scroller
            size_hint: 1, 0.8
            GridLayout:
                cols: 1
                spacing: 7
                size_hint_y: None
                id: tx_list
""")

tx_list = [
    ['asdf', 1.234, False],
    ['fghj', 2.234, False],
    ['xvbb', 3.234, False],
    ['wetw', 4.234, False],
    ['hjkl', 5.234, False],
    ['wret', 6.234, False],
    ['bvnm', 7.234, False],
    ['zzzz', 8.234, False]
    ]


class RootWidget(BoxLayout):
    """Root Kivy accordion widget class"""
    tx_dict = {}
    def __init__(self, **kwargs):
        super(RootWidget, self).__init__(**kwargs)
        for idx, val in enumerate(tx_list):
            self.tx_dict[idx] = Button(text="tx_id: {0} | amount: {1:.4f}".format(val[0], val[1]),
                                       size_hint_y=None, height=15, font_size=9)
            self.tx_dict[idx].bind(on_press=self._create_button_callback(val[0]))
            self.ids.tx_list.add_widget(self.tx_dict[idx])

    def _create_button_callback(self, val):
        def callback(button):
            Clipboard.put(val)
        return callback

class lightWalletApp(App):
    def build(self):
        root = RootWidget()
        return root


if __name__ == '__main__':
    lightWalletApp().run()

