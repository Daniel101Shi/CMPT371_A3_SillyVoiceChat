import tkinter as tk
from tkinter import messagebox
from network import NetworkLogic, detect_local_ip, DEFAULT_PORT
 
 
class App:
    def __init__(self, root):
        # initialize variables
        self.root = root
        self.root.title("VoiceChat")
        self.root.resizable(False, False)
        self.session = None
        self.local_ip = detect_local_ip()
        self._build_ui()
 
    def _build_ui(self):
        pad = {"padx": 16, "pady": 8}
 
        # user IP (read-only display)
        tk.Label(self.root, text="Your IP:").grid(row=0, column=0, sticky="e", **pad)
        tk.Label(self.root, text=self.local_ip, fg="gray").grid(row=0, column=1, sticky="w", **pad)
 
        # partner IP entry
        tk.Label(self.root, text="Partner IP:").grid(row=1, column=0, sticky="e", **pad)
        self.ip_entry = tk.Entry(self.root, width=20)
        self.ip_entry.grid(row=1, column=1, sticky="w", **pad)
        self.ip_entry.bind("<Return>", lambda e: self._on_connect())
        self.ip_entry.bind("<KeyRelease>", self._on_ip_changed)
        self.ip_entry.focus()
 
        # loopback checkbox (testing)
        self.loopback_var = tk.BooleanVar()
        tk.Checkbutton(
            self.root, text="Loopback test (same machine)",
            variable=self.loopback_var, command=self._on_loopback_toggle
        ).grid(row=2, column=0, columnspan=2, pady=4)
 
        # Connect / Disconnect button
        self.connect_btn = tk.Button(
            self.root, text="Connect", width=16,
            command=self._on_connect, state="disabled"
        )
        self.connect_btn.grid(row=3, column=0, columnspan=2, pady=12)
 
        # Status label
        self.status_label = tk.Label(self.root, text="Enter a partner IP to connect.", fg="gray")
        self.status_label.grid(row=4, column=0, columnspan=2, pady=4)

        # Mute button
        self.mute_btn = tk.Button(self.root, text="Mute", width=10, command=self._on_mute, state="disabled")
        self.mute_btn.grid(row=5, column=0, pady=4, padx=(30, 0))

        # Deafen button
        self.deafen_btn = tk.Button(self.root, text="Deafen", width=10, command=self._on_deafen, state="disabled")
        self.deafen_btn.grid(row=5, column=1, pady=4)

        # Volume slider
        tk.Label(self.root, text="Volume:").grid(row=6, column=0, sticky="e", padx=(56,16))
        self.volume_slider = tk.Scale(self.root, from_=0, to=100, orient="horizontal", command=self._on_volume, state="disabled")
        self.volume_slider.set(100)
        self.volume_slider.grid(row=6, column=1, sticky="w", padx=16, pady=4)

    # enable "connect" button if call is inactive
    # disable "connect" button if call is active
    def _on_ip_changed(self, event=None):
        has_ip = bool(self.ip_entry.get().strip()) or self.loopback_var.get()
        self.connect_btn.config(state="normal" if has_ip else "disabled")

    # disable IP entry in loopback (testing) mode
    def _on_loopback_toggle(self):
        if self.loopback_var.get():
            self.ip_entry.config(state="disabled")
            self.connect_btn.config(state="normal")
        else:
            self.ip_entry.config(state="normal")
            self._on_ip_changed()
 
    def _on_connect(self):
        # button should disconnect if call is active
        if self.session:
            self._disconnect()
            return
 
        # set all fields to the same for testing (can hear own mic)
        if self.loopback_var.get():
            local_ip    = "127.0.0.1"
            local_port  = DEFAULT_PORT
            target_ip   = "127.0.0.1"
            target_port = DEFAULT_PORT
        else:
            target_ip = self.ip_entry.get().strip()
            if not target_ip:
                messagebox.showwarning("Missing IP", "Please enter your partner's IP address.")
                return
            local_ip    = self.local_ip
            local_port  = DEFAULT_PORT
            target_port = DEFAULT_PORT
 
        try:
            # begin audio capture and sender threads
            self.session = NetworkLogic(local_ip, local_port, target_ip, target_port)
            self.session.start()
        except Exception as e:
            # if IP cannot be reached, terminate
            messagebox.showerror("Connection error", str(e))
            self.session = None
            return

        # disable / enable buttons as appropriate
        self.connect_btn.config(text="Disconnect")
        self.ip_entry.config(state="disabled")
        self.status_label.config(text=f"Connected → {target_ip}:{target_port}", fg="green")
        self.mute_btn.config(state="normal")
        self.deafen_btn.config(state="normal")
        self.volume_slider.config(state="normal")
        self.volume_slider.set(100)
 
    def _disconnect(self):
        # stops the current voice session
        if self.session:
            self.session.stop()
            self.session = None

        # disable / enable buttons as appropriate
        self.connect_btn.config(text="Connect")
        self.ip_entry.config(state="normal")
        self.status_label.config(text="Disconnected.", fg="gray")
        self.mute_btn.config(state="disabled", text="Mute")
        self.deafen_btn.config(state="disabled", text="Deafen")
        self.volume_slider.config(state="disabled")
        self.volume_slider.set(100)
        self._on_ip_changed()

    def _on_mute(self):
        self.session.muted = not self.session.muted
        self.mute_btn.config(text="Unmute" if self.session.muted else "Mute")

    def _on_deafen(self):
        self.session.deafened = not self.session.deafened
        self.deafen_btn.config(text="Undeafen" if self.session.deafened else "Deafen")

    def _on_volume(self, val):
        self.session.volume = int(val) / 100
 
    def on_close(self):
        # ensure the call is disconnected when the app is closed
        self._disconnect()
        self.root.destroy()
 
 
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()