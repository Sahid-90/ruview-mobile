"""
RuView Mobile - WiFi Spatial Intelligence & Vital Signs Dashboard
Inspired by π RuView (https://github.com/ruvnet/RuView)
Built with Kivy for Android
"""

import math
import time
import random
import threading
import json
import requests

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.graphics import Color, Line, Ellipse, Rectangle
from kivy.metrics import dp
from kivy.utils import get_color_from_hex


# ─── Radar / Spatial View Widget ──────────────────────────────────────────────

class RadarWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.angle = 0
        self.targets = []
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def set_targets(self, targets):
        self.targets = targets
        self.update_canvas()

    def update_sweep(self, dt):
        self.angle = (self.angle + 3) % 360
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            cx = self.center_x
            cy = self.center_y
            radius = min(self.width, self.height) * 0.45

            if radius <= 0:
                return

            # Background radar circle
            Color(0.05, 0.1, 0.15, 0.9)
            Ellipse(pos=(cx - radius, cy - radius), size=(radius * 2, radius * 2))

            # Range rings (1m, 2m, 3m, 4m)
            for r_ratio in [0.25, 0.5, 0.75, 1.0]:
                r = radius * r_ratio
                Color(0.0, 0.8, 0.6, 0.25)
                Line(circle=(cx, cy, r), width=1.2)

            # Crosshairs
            Color(0.0, 0.8, 0.6, 0.2)
            Line(points=[cx - radius, cy, cx + radius, cy], width=1)
            Line(points=[cx, cy - radius, cx, cy + radius], width=1)

            # Rotating Radar Beam / Sweep
            rad = math.radians(self.angle)
            sweep_x = cx + radius * math.cos(rad)
            sweep_y = cy + radius * math.sin(rad)
            Color(0.0, 1.0, 0.7, 0.6)
            Line(points=[cx, cy, sweep_x, sweep_y], width=2)

            # Beam trailing glow
            for trail in range(1, 8):
                trad = math.radians((self.angle - trail * 2) % 360)
                tx = cx + radius * math.cos(trad)
                ty = cy + radius * math.sin(trad)
                alpha = max(0.0, 0.3 - (trail * 0.04))
                Color(0.0, 0.9, 0.6, alpha)
                Line(points=[cx, cy, tx, ty], width=1.5)

            # Center sensor node (ESP32)
            Color(0.2, 0.6, 1.0, 1.0)
            Ellipse(pos=(cx - dp(6), cy - dp(6)), size=(dp(12), dp(12)))

            # Detected People / Targets (Spatial Intelligence)
            for t in self.targets:
                tx = cx + t["x"] * radius
                ty = cy + t["y"] * radius

                # Pulsating outer aura
                Color(1.0, 0.3, 0.4, 0.35)
                Ellipse(pos=(tx - dp(14), ty - dp(14)), size=(dp(28), dp(28)))

                # Target blip
                Color(1.0, 0.2, 0.3, 0.95)
                Ellipse(pos=(tx - dp(6), ty - dp(6)), size=(dp(12), dp(12)))


# ─── Vital Sign Waveform Widget ───────────────────────────────────────────────

class WaveformWidget(Widget):
    def __init__(self, color_hex="#00E676", **kwargs):
        super().__init__(**kwargs)
        self.wave_color = get_color_from_hex(color_hex)
        self.points = []
        self.phase = 0
        self.bpm = 72
        self.bind(pos=self.redraw, size=self.redraw)

    def update_wave(self, phase_speed=0.15, bpm=72):
        self.phase = (self.phase + phase_speed) % (2 * math.pi)
        self.bpm = bpm
        self.redraw()

    def redraw(self, *args):
        self.canvas.clear()
        with self.canvas:
            if self.width <= 0 or self.height <= 0:
                return

            # Background grid box
            Color(0.08, 0.12, 0.16, 0.7)
            Rectangle(pos=self.pos, size=self.size)

            mid_y = self.y + self.height * 0.5
            pts = []
            steps = 40
            dx = self.width / float(steps)

            for i in range(steps + 1):
                x = self.x + i * dx
                # ECG / Respiration wave approximation
                t = (i * 0.3) - self.phase
                wave = math.sin(t) * 0.4

                # Simulated ECG spike
                norm_t = (t % (2 * math.pi))
                if 1.0 < norm_t < 1.4:
                    wave += math.sin((norm_t - 1.0) * math.pi / 0.4) * 0.8
                elif 1.4 <= norm_t < 1.6:
                    wave -= 0.3

                y = mid_y + wave * (self.height * 0.38)
                pts.extend([x, y])

            Color(*self.wave_color)
            Line(points=pts, width=1.8)


# ─── Main RuView Dashboard Layout ────────────────────────────────────────────

class RuViewDashboard(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(10)
        self.spacing = dp(8)

        self.demo_mode = True
        self.server_ip = "192.168.1.100:8080"
        self.connected = False

        # Target simulation state
        self.sim_targets = [
            {"id": "Person 1", "x": 0.35, "y": 0.4, "vx": 0.005, "vy": -0.003, "bpm": 74, "rpm": 16},
            {"id": "Person 2", "x": -0.45, "y": -0.2, "vx": -0.003, "vy": 0.004, "bpm": 68, "rpm": 14}
        ]

        self.setup_ui()
        Clock.schedule_interval(self.tick_update, 0.05)

    def setup_ui(self):
        # ── 1. Header Bar ──────────────────────────────────────────────────
        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(46), spacing=dp(8))

        title = Label(
            text="π [b]RuView[/b] [size=13sp][color=00e5ff]WiFi Sensing[/color][/size]",
            markup=True,
            font_size="20sp",
            size_hint_x=0.6,
            halign="left",
            valign="middle",
            color=get_color_from_hex("#FFFFFF")
        )
        title.bind(size=title.setter("text_size"))

        self.mode_btn = Button(
            text="🟢 DEMO",
            size_hint_x=0.22,
            background_color=get_color_from_hex("#00B0FF"),
            font_size="11sp"
        )
        self.mode_btn.bind(on_release=self.toggle_mode)

        settings_btn = Button(
            text="⚙️",
            size_hint_x=0.18,
            background_color=get_color_from_hex("#37474F"),
            font_size="16sp"
        )
        settings_btn.bind(on_release=self.show_settings_popup)

        header.add_widget(title)
        header.add_widget(self.mode_btn)
        header.add_widget(settings_btn)
        self.add_widget(header)

        # ── 2. Status Banner ───────────────────────────────────────────────
        self.status_box = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(30),
            padding=[dp(8), 0]
        )
        self.csi_status = Label(
            text="📡 WiFi CSI: [color=00E676]Online (-48 dBm)[/color]",
            markup=True,
            font_size="12sp",
            size_hint_x=0.5,
            halign="left",
            valign="middle"
        )
        self.csi_status.bind(size=self.csi_status.setter("text_size"))

        self.presence_status = Label(
            text="👥 People: [b][color=FF5252]2 Detected[/color][/b]",
            markup=True,
            font_size="12sp",
            size_hint_x=0.5,
            halign="right",
            valign="middle"
        )
        self.presence_status.bind(size=self.presence_status.setter("text_size"))

        self.status_box.add_widget(self.csi_status)
        self.status_box.add_widget(self.presence_status)
        self.add_widget(self.status_box)

        # ── 3. Interactive Spatial Radar ───────────────────────────────────
        self.radar = RadarWidget(size_hint_y=0.48)
        self.add_widget(self.radar)

        # ── 4. Vital Signs Panel (ECG + Respiration) ───────────────────────
        vitals_title = Label(
            text="🫀 [b]Real-time Biometrics (Through-Wall)[/b]",
            markup=True,
            font_size="13sp",
            size_hint_y=None,
            height=dp(24),
            color=get_color_from_hex("#B0BEC5"),
            halign="left",
            valign="middle"
        )
        vitals_title.bind(size=vitals_title.setter("text_size"))
        self.add_widget(vitals_title)

        vitals_row = GridLayout(cols=2, spacing=dp(8), size_hint_y=0.38)

        # Card 1: Heart Rate
        hr_card = BoxLayout(orientation="vertical", padding=dp(6), spacing=dp(4))
        self.hr_label = Label(
            text="Heart Rate: [b][color=FF5252]72 BPM[/color][/b]",
            markup=True,
            font_size="13sp",
            size_hint_y=None,
            height=dp(22)
        )
        self.ecg_wave = WaveformWidget(color_hex="#FF5252")
        hr_card.add_widget(self.hr_label)
        hr_card.add_widget(self.ecg_wave)

        # Card 2: Respiration Rate
        resp_card = BoxLayout(orientation="vertical", padding=dp(6), spacing=dp(4))
        self.resp_label = Label(
            text="Breathing: [b][color=00E676]16 RPM[/color][/b]",
            markup=True,
            font_size="13sp",
            size_hint_y=None,
            height=dp(22)
        )
        self.resp_wave = WaveformWidget(color_hex="#00E676")
        resp_card.add_widget(self.resp_label)
        resp_card.add_widget(self.resp_wave)

        vitals_row.add_widget(hr_card)
        vitals_row.add_widget(resp_card)
        self.add_widget(vitals_row)

    # ── Logic & Updates ───────────────────────────────────────────────────────

    def tick_update(self, dt):
        self.radar.update_sweep(dt)

        if self.demo_mode:
            # Simulate realistic movement of targets in 2D space
            for t in self.sim_targets:
                t["x"] += t["vx"]
                t["y"] += t["vy"]

                dist = math.hypot(t["x"], t["y"])
                if dist > 0.85:
                    t["vx"] *= -1
                    t["vy"] *= -1

                # Natural heartbeat variations
                if random.random() < 0.1:
                    t["bpm"] = max(60, min(100, t["bpm"] + random.randint(-1, 1)))
                if random.random() < 0.05:
                    t["rpm"] = max(12, min(22, t["rpm"] + random.randint(-1, 1)))

            primary = self.sim_targets[0]
            self.hr_label.text = f"Heart Rate: [b][color=FF5252]{primary['bpm']} BPM[/color][/b]"
            self.resp_label.text = f"Breathing: [b][color=00E676]{primary['rpm']} RPM[/color][/b]"

            self.ecg_wave.update_wave(phase_speed=0.22, bpm=primary["bpm"])
            self.resp_wave.update_wave(phase_speed=0.08, bpm=primary["rpm"])

            self.radar.set_targets(self.sim_targets)

    def toggle_mode(self, *args):
        self.demo_mode = not self.demo_mode
        if self.demo_mode:
            self.mode_btn.text = "🟢 DEMO"
            self.mode_btn.background_color = get_color_from_hex("#00B0FF")
            self.csi_status.text = "📡 WiFi CSI: [color=00E676]Online (Simulated)[/color]"
        else:
            self.mode_btn.text = "🟡 LIVE"
            self.mode_btn.background_color = get_color_from_hex("#FF9100")
            self.csi_status.text = f"📡 RuView Node: [color=FFD54F]{self.server_ip}[/color]"

    def show_settings_popup(self, *args):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))

        info_lbl = Label(
            text="Enter RuView Server / ESP32 Node IP:",
            size_hint_y=None,
            height=dp(30),
            font_size="13sp"
        )
        ip_input = TextInput(
            text=self.server_ip,
            multiline=False,
            size_hint_y=None,
            height=dp(44),
            font_size="15sp",
            background_color=get_color_from_hex("#263238"),
            foreground_color=get_color_from_hex("#ECEFF1")
        )

        btn_row = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(44))
        save_btn = Button(text="Save & Connect", background_color=get_color_from_hex("#1565C0"))
        close_btn = Button(text="Cancel", background_color=get_color_from_hex("#37474F"))

        btn_row.add_widget(save_btn)
        btn_row.add_widget(close_btn)

        content.add_widget(info_lbl)
        content.add_widget(ip_input)
        content.add_widget(btn_row)

        popup = Popup(
            title="RuView Node Configuration",
            content=content,
            size_hint=(0.88, 0.42)
        )

        def save_and_close(*a):
            self.server_ip = ip_input.text.strip()
            popup.dismiss()

        save_btn.bind(on_release=save_and_close)
        close_btn.bind(on_release=popup.dismiss)
        popup.open()


# ─── App Entry Point ──────────────────────────────────────────────────────────

class RuViewApp(App):
    def build(self):
        from kivy.core.window import Window
        Window.clearcolor = get_color_from_hex("#0A0E14")
        return RuViewDashboard()


if __name__ == "__main__":
    RuViewApp().run()
