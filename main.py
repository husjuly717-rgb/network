from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.core.window import Window
import re


class WaveformCanvas(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self._redraw_background, pos=self._redraw_background)

    def _redraw_background(self, *args):
        if not hasattr(self, '_bg_instr'):
            with self.canvas.before:
                Color(1, 1, 1, 1)
                self._bg_instr = Rectangle(pos=self.pos, size=self.size)
        self._bg_instr.pos = self.pos
        self._bg_instr.size = self.size

    def draw_waveform(self, x_values, y_values, bits_length):
        self.canvas.clear()
        self._redraw_background()

        if not x_values or not y_values:
            return

        # Determine ranges
        x_min, x_max = 0, max(x_values)
        y_abs_max = max(1, max(abs(v) for v in y_values))

        padding = dp(20)
        plot_x0 = self.x + padding
        plot_y0 = self.y + padding
        plot_w = max(1.0, self.width - 2 * padding)
        plot_h = max(1.0, self.height - 2 * padding)

        def to_px(x, y):
            if x_max == 0:
                sx = plot_x0
            else:
                sx = plot_x0 + (x - x_min) / (x_max - x_min) * plot_w
            sy = plot_y0 + (y + y_abs_max) / (2 * y_abs_max) * plot_h
            return sx, sy

        with self.canvas:
            # Axes/grid
            Color(0.85, 0.85, 0.85, 1)
            # Vertical bit boundaries
            for i in range(bits_length + 1):
                x1, y1 = to_px(i, -y_abs_max)
                x2, y2 = to_px(i, y_abs_max)
                Line(points=[x1, y1, x2, y2], width=1)

            # Horizontal zero line
            Color(0.2, 0.2, 0.2, 1)
            x1, y1 = to_px(0, 0)
            x2, y2 = to_px(x_max, 0)
            Line(points=[x1, y1, x2, y2], width=1)

            # Signal
            Color(0.1, 0.4, 0.9, 1)
            pts = []
            for x, y in zip(x_values, y_values):
                px, py = to_px(x, y)
                pts.extend([px, py])
            if len(pts) >= 4:
                Line(points=pts, width=2)


class EncodingLogic:
    def __init__(self):
        self.last_pulse_polarity = -1

    def reset(self):
        self.last_pulse_polarity = -1

    def get_unipolar(self, data):
        x, y = [0], [0]
        for i, bit in enumerate(data):
            level = 1 if bit == '1' else 0
            x.extend([i, i + 1])
            y.extend([level, level])
        return x, y

    def get_nrz_l(self, data):
        x, y = [0], [1]
        for i, bit in enumerate(data):
            level = -1 if bit == '1' else 1
            x.extend([i, i + 1])
            y.extend([level, level])
        return x, y

    def get_nrz_i(self, data):
        x, y = [0], [1]
        current_level = 1
        for i, bit in enumerate(data):
            if bit == '1':
                current_level *= -1
            x.extend([i, i + 1])
            y.extend([current_level, current_level])
        return x, y

    def get_rz(self, data):
        x, y = [0], [0]
        for i, bit in enumerate(data):
            if bit == '0':
                x.extend([i, i + 1])
                y.extend([0, 0])
            else:
                x.extend([i, i + 0.5, i + 0.5, i + 1])
                y.extend([1, 1, 0, 0])
        return x, y

    def get_manchester(self, data):
        x, y = [0], [1]
        for i, bit in enumerate(data):
            if bit == '0':
                x.extend([i, i + 0.5, i + 0.5, i + 1])
                y.extend([1, 1, -1, -1])
            else:
                x.extend([i, i + 0.5, i + 0.5, i + 1])
                y.extend([-1, -1, 1, 1])
        return x, y

    def get_diff_manchester(self, data):
        x, y = [0], [1]
        current_level = 1
        for i, bit in enumerate(data):
            if bit == '0':
                current_level *= -1
            x.extend([i, i + 0.5, i + 0.5, i + 1])
            y.extend([current_level, current_level, -current_level, -current_level])
            current_level *= -1
        return x, y

    def get_ami(self, data, is_scrambled=False):
        x, y = [0], [0]
        symbols = data if is_scrambled else [(bit, 'normal') for bit in data]
        for i, (symbol, typ) in enumerate(symbols):
            if symbol == '0':
                x.extend([i, i + 1])
                y.extend([0, 0])
            else:
                if typ != 'violation':
                    self.last_pulse_polarity *= -1
                x.extend([i, i + 1])
                y.extend([self.last_pulse_polarity, self.last_pulse_polarity])
        return x, y

    def get_b8zs(self, data):
        scrambled_data = []
        i = 0
        while i < len(data):
            if data[i:i+8] == '00000000':
                v_polarity = self.last_pulse_polarity
                b_polarity = -self.last_pulse_polarity
                scrambled_data.extend([('0', 'normal'), ('0', 'normal'), ('0', 'normal')])
                scrambled_data.append(('V', 'violation'))
                scrambled_data.append(('B', 'bipolar'))
                scrambled_data.extend([('0', 'normal')])
                scrambled_data.append(('V', 'violation'))
                scrambled_data.append(('B', 'bipolar'))
                self.last_pulse_polarity = b_polarity
                i += 8
            else:
                bit = data[i]
                scrambled_data.append((bit, 'normal'))
                if bit == '1':
                    self.last_pulse_polarity *= -1
                i += 1
        self.last_pulse_polarity = -1
        return self.get_ami(scrambled_data, is_scrambled=True)

    def get_hdb3(self, data):
        scrambled_data = []
        i = 0
        ones_since_last_sub = 0
        while i < len(data):
            if data[i:i+4] == '0000':
                if ones_since_last_sub % 2 == 0:
                    scrambled_data.append(('B', 'bipolar'))
                    scrambled_data.extend([('0', 'normal'), ('0', 'normal')])
                    scrambled_data.append(('V', 'violation'))
                    self.last_pulse_polarity *= -1
                else:
                    scrambled_data.extend([('0', 'normal'), ('0', 'normal'), ('0', 'normal')])
                    scrambled_data.append(('V', 'violation'))
                ones_since_last_sub = 0
                i += 4
            else:
                bit = data[i]
                scrambled_data.append((bit, 'normal'))
                if bit == '1':
                    ones_since_last_sub += 1
                    self.last_pulse_polarity *= -1
                i += 1
        self.last_pulse_polarity = -1
        return self.get_ami(scrambled_data, is_scrambled=True)


class RootUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', spacing=dp(8), padding=dp(10), **kwargs)

        # Top input row
        input_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(48), spacing=dp(8))
        input_row.add_widget(Label(text='Enter Binary String:', size_hint_x=None, width=dp(170)))
        self.binary_input = TextInput(text='0100000000110', multiline=False)
        input_row.add_widget(self.binary_input)
        self.add_widget(input_row)

        # Buttons grid
        buttons = [
            'Unipolar', 'NRZ-L', 'NRZ-I', 'RZ', 'Manchester',
            'Differential Manchester', 'AMI', 'B8ZS', 'HDB3'
        ]
        grid = GridLayout(cols=3, size_hint_y=None, spacing=dp(6), padding=(0, dp(4)))
        grid.bind(minimum_height=grid.setter('height'))
        self.buttons = {}
        for name in buttons:
            btn = Button(text=name, size_hint_y=None, height=dp(44), background_normal='', background_color=(0, 0, 0, 1), color=(1, 1, 1, 1), bold=True)
            btn.bind(on_release=lambda inst, n=name: self.on_select(n))
            grid.add_widget(btn)
            self.buttons[name] = btn
        self.add_widget(grid)

        # Plot area
        self.canvas_widget = WaveformCanvas(size_hint=(1, 1))
        self.add_widget(self.canvas_widget)

        # Logic
        self.logic = EncodingLogic()
        self.active_method = None

        # Initial plot
        self.on_select('Unipolar')

    def validate(self, s):
        if not re.match(r'^[01]+$', s):
            return False
        return True

    def on_select(self, method):
        s = self.binary_input.text.strip()
        if not self.validate(s):
            # Visual feedback for invalid input
            self.binary_input.background_color = (1, 0.8, 0.8, 1)
            return
        self.binary_input.background_color = (1, 1, 1, 1)

        # Update button styles
        if self.active_method:
            self.buttons[self.active_method].background_color = (0, 0, 0, 1)
            self.buttons[self.active_method].color = (1, 1, 1, 1)
        self.active_method = method
        self.buttons[method].background_color = (1, 0, 0, 1)
        self.buttons[method].color = (1, 1, 1, 1)

        # Reset polarity-sensitive state
        self.logic.reset()

        mapping = {
            'Unipolar': self.logic.get_unipolar,
            'NRZ-L': self.logic.get_nrz_l,
            'NRZ-I': self.logic.get_nrz_i,
            'RZ': self.logic.get_rz,
            'Manchester': self.logic.get_manchester,
            'Differential Manchester': self.logic.get_diff_manchester,
            'AMI': self.logic.get_ami,
            'B8ZS': self.logic.get_b8zs,
            'HDB3': self.logic.get_hdb3,
        }

        x_vals, y_vals = mapping[method](s)
        self.canvas_widget.draw_waveform(x_vals, y_vals, bits_length=len(s))


class EncodingAppKivy(App):
    def build(self):
        Window.size = (1000, 750)
        return RootUI()


if __name__ == '__main__':
    EncodingAppKivy().run()


