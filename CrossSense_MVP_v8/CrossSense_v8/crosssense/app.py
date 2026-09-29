from __future__ import annotations

import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk

from .controller import CrossSenseRuntime
from .deadzone import CrossDeadzoneProfile
from .settings import Settings, load_settings, save_settings


class CrossSenseApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("CrossSense v8")
        self.geometry("860x640")
        self.minsize(820, 600)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.settings = load_settings()
        self.runtime = CrossSenseRuntime()

        self.inner_var = tk.StringVar(value=str(self.settings.inner_deadzone_percent))
        self.outer_var = tk.StringVar(value=str(self.settings.outer_saturation_percent))
        self.forward_boost_var = tk.StringVar(value=str(self.settings.forward_boost_percent))
        self.auto_start_var = tk.BooleanVar(value=self.settings.auto_start)
        self.minimize_on_start_var = tk.BooleanVar(value=self.settings.minimize_on_start)

        self.status_var = tk.StringVar(value="Ready. Close DS4Windows, connect DualSense with USB, then press Start.")
        self.device_var = tk.StringVar(value="Input: none")
        self.output_var = tk.StringVar(value="Output: inactive")
        self.left_raw_var = tk.StringVar(value="Left raw: 0.0000, 0.0000")
        self.left_mapped_var = tk.StringVar(value="Left mapped: 0.0000, 0.0000")
        self.right_raw_var = tk.StringVar(value="Right raw: 0.0000, 0.0000")
        self.triggers_var = tk.StringVar(value="Triggers: LT 0 / RT 0")
        self.buttons_var = tk.StringVar(value="Buttons pressed: none")
        self.devices_var = tk.StringVar(value="Detected devices: none")

        self._style()
        self._build_ui()
        self.after(16, self._tick)

        if self.settings.auto_start:
            self.after(500, self.start)

    def _style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 30, "bold"))
        style.configure("Sub.TLabel", font=("Segoe UI", 11))
        style.configure("Section.TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("Status.TLabel", font=("Segoe UI", 10, "bold"))
        style.configure("Hint.TLabel", foreground="#555555")

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=(24, 20, 24, 16))
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.columnconfigure(1, weight=1)

        ttk.Label(root, text="CrossSense", style="Title.TLabel").grid(row=0, column=0, sticky="w", columnspan=2)
        ttk.Label(
            root,
            text="DualSense Cross Deadzone mapper with virtual Xbox output for Rocket League — v8 polished app build",
            style="Sub.TLabel",
        ).grid(row=1, column=0, sticky="w", columnspan=2, pady=(0, 16))

        profile = ttk.LabelFrame(root, text="Profile", padding=(16, 14), style="Section.TLabelframe")
        profile.grid(row=2, column=0, sticky="nsew", padx=(0, 10), pady=(0, 12))
        profile.columnconfigure(1, weight=1)

        ttk.Label(profile, text="Preset: Steam Cross 6–83", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", columnspan=3, pady=(0, 10))
        self._field(profile, 1, "Inner deadzone (%)", self.inner_var)
        self._field(profile, 2, "Outer saturation (%)", self.outer_var)
        self._field(profile, 3, "Forward boost / flip cancel assist (%)", self.forward_boost_var)
        ttk.Label(profile, text="0.0 = pure 6–83. Try 1.0 or 1.5 only if forward cancel feels weak.", style="Hint.TLabel", wraplength=380).grid(row=4, column=0, sticky="w", columnspan=3, pady=(2, 10))

        quick = ttk.Frame(profile)
        quick.grid(row=5, column=0, columnspan=3, sticky="w", pady=(0, 10))
        ttk.Button(quick, text="Pure 6–83", command=lambda: self._set_boost("0.0")).pack(side="left")
        ttk.Button(quick, text="Safe boost 1.0", command=lambda: self._set_boost("1.0")).pack(side="left", padx=(8, 0))
        ttk.Button(quick, text="Boost 1.5", command=lambda: self._set_boost("1.5")).pack(side="left", padx=(8, 0))

        ttk.Checkbutton(profile, text="Auto-start profile when app opens", variable=self.auto_start_var, command=self.save_current_settings).grid(row=6, column=0, sticky="w", columnspan=3)
        ttk.Checkbutton(profile, text="Minimize app after Start", variable=self.minimize_on_start_var, command=self.save_current_settings).grid(row=7, column=0, sticky="w", columnspan=3, pady=(4, 0))

        monitor = ttk.LabelFrame(root, text="Live monitor", padding=(16, 14), style="Section.TLabelframe")
        monitor.grid(row=2, column=1, sticky="nsew", padx=(10, 0), pady=(0, 12))
        for var in (self.device_var, self.output_var, self.left_raw_var, self.left_mapped_var, self.right_raw_var, self.triggers_var, self.buttons_var):
            ttk.Label(monitor, textvariable=var, anchor="w").pack(fill="x", pady=2)

        actions = ttk.LabelFrame(root, text="Actions", padding=(16, 14), style="Section.TLabelframe")
        actions.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        self.start_button = ttk.Button(actions, text="Start profile", command=self.start)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(actions, text="Stop", command=self.stop, state="disabled")
        self.stop_button.pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Save settings", command=self.save_current_settings).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Reset pure 6–83", command=self.reset_pure).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Open joy.cpl", command=self.open_joy_cpl).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Hide DualSense guide", command=self.show_hide_guide).pack(side="left", padx=(8, 0))

        status = ttk.Frame(root)
        status.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Label(status, textvariable=self.status_var, style="Status.TLabel", wraplength=790).pack(anchor="w")
        ttk.Label(status, textvariable=self.devices_var, style="Hint.TLabel", wraplength=790).pack(anchor="w", pady=(5, 0))

        help_text = (
            "Best Rocket League setup: keep DS4Windows closed, start CrossSense before opening Rocket League, "
            "and make Windows show one 'Controller (XBOX 360 For Windows)' from CrossSense. "
            "Hide original DualSense is still a manual HidHide step; v8 gives you the guide but does not install drivers automatically."
        )
        ttk.Label(root, text=help_text, style="Hint.TLabel", wraplength=790, justify="left").grid(row=5, column=0, columnspan=2, sticky="w")

    def _field(self, parent: ttk.Frame, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=5)
        entry = ttk.Entry(parent, textvariable=variable, width=12)
        entry.grid(row=row, column=1, sticky="w", padx=(12, 0), pady=5)
        entry.bind("<FocusOut>", lambda _e: self.save_current_settings(show_message=False))
        entry.bind("<Return>", lambda _e: self.save_current_settings(show_message=False))

    def _set_boost(self, value: str) -> None:
        self.forward_boost_var.set(value)
        self.save_current_settings(show_message=False)
        self.status_var.set(f"Forward boost set to {value}. Press Stop then Start if profile is already running.")

    def _profile_from_ui(self) -> CrossDeadzoneProfile | None:
        try:
            inner = float(self.inner_var.get().replace(",", "."))
            outer = float(self.outer_var.get().replace(",", "."))
            forward_boost = float(self.forward_boost_var.get().replace(",", "."))
            if inner < 0 or inner >= 95:
                raise ValueError("Inner deadzone must be between 0 and 95.")
            if outer <= inner or outer > 100:
                raise ValueError("Outer saturation must be greater than inner and at most 100.")
            if forward_boost < 0 or forward_boost > 15:
                raise ValueError("Forward boost must be between 0 and 15.")
            return CrossDeadzoneProfile(inner, outer, forward_boost)
        except Exception as exc:
            messagebox.showerror("Invalid profile", str(exc))
            return None

    def start(self) -> None:
        profile = self._profile_from_ui()
        if profile is None:
            return
        self.save_current_settings(show_message=False)
        self.runtime.start(profile)
        if self.runtime.running:
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            boost = profile.forward_boost_percent
            boost_text = "pure 6–83" if boost == 0 else f"6–83 + {boost:g}% forward boost"
            self.status_var.set(f"Profile active: Steam Cross {boost_text}. Virtual Xbox output is running.")
            if self.minimize_on_start_var.get():
                self.after(500, self.iconify)
        else:
            self.status_var.set(self.runtime.state.error or "Failed to start.")

    def stop(self) -> None:
        self.runtime.stop()
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.output_var.set("Output: inactive")
        self.status_var.set("Stopped. Virtual controller released.")

    def save_current_settings(self, show_message: bool = True) -> None:
        try:
            settings = Settings(
                inner_deadzone_percent=float(self.inner_var.get().replace(",", ".")),
                outer_saturation_percent=float(self.outer_var.get().replace(",", ".")),
                forward_boost_percent=float(self.forward_boost_var.get().replace(",", ".")),
                auto_start=bool(self.auto_start_var.get()),
                minimize_on_start=bool(self.minimize_on_start_var.get()),
            )
            save_settings(settings)
            self.settings = settings
            if show_message:
                self.status_var.set("Settings saved.")
        except Exception as exc:
            if show_message:
                messagebox.showerror("Could not save settings", str(exc))

    def reset_pure(self) -> None:
        self.inner_var.set("6.0")
        self.outer_var.set("83.0")
        self.forward_boost_var.set("0.0")
        self.save_current_settings(show_message=False)
        self.status_var.set("Reset to pure Steam Cross 6–83. Press Stop then Start if profile is already running.")

    def open_joy_cpl(self) -> None:
        try:
            subprocess.Popen(["control", "joy.cpl"])
        except Exception as exc:
            messagebox.showerror("Could not open joy.cpl", str(exc))

    def show_hide_guide(self) -> None:
        messagebox.showinfo(
            "Hide original DualSense",
            "To prevent double input in Rocket League:\n\n"
            "1. Close Rocket League and DS4Windows.\n"
            "2. Use HidHide Configuration Client if you already have HidHide installed.\n"
            "3. Add CrossSense/python.exe/CrossSense.exe to Applications.\n"
            "4. Tick the original DualSense Wireless Controller under Devices.\n"
            "5. Leave the virtual Xbox controller unhidden.\n"
            "6. Restart CrossSense, then open Rocket League.\n\n"
            "v8 does not install or change HidHide automatically because that can break controller input if set wrong."
        )

    def _tick(self) -> None:
        state = self.runtime.poll_and_output()
        self.device_var.set(f"Input: {state.connected_name}")
        self.output_var.set("Output: virtual Xbox active" if state.output_ready else "Output: inactive")
        self.left_raw_var.set(f"Left raw: {state.left_raw[0]:.4f}, {state.left_raw[1]:.4f}")
        self.left_mapped_var.set(f"Left mapped: {state.left_mapped[0]:.4f}, {state.left_mapped[1]:.4f}")
        self.right_raw_var.set(f"Right raw: {state.right_raw[0]:.4f}, {state.right_raw[1]:.4f}")
        self.triggers_var.set(f"Triggers: LT {state.triggers[0]} / RT {state.triggers[1]}")
        self.buttons_var.set("Buttons pressed: " + (", ".join(state.buttons_pressed) if state.buttons_pressed else "none"))
        self.devices_var.set("Detected devices: " + (", ".join(state.detected_devices) if state.detected_devices else "none"))
        if state.error:
            self.status_var.set("Error: " + state.error)
        self.after(16, self._tick)

    def on_close(self) -> None:
        self.save_current_settings(show_message=False)
        self.runtime.shutdown()
        self.destroy()


def main() -> None:
    app = CrossSenseApp()
    app.mainloop()
