import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw, ImageTk
import threading
import time
    
class ButtonStyles():
    def __init__(self, root):
        """Initialize the ButtonStyles object"""
        self.root = root
        self.stop_event = threading.Event()
        self.lbl = None
         
    def createGlowText(self, root, text, color, size=32):
        """Create glowing, animated text"""
        self.lbl = tk.Label(root, text=text, font=("OCR A Extended", size), bg="#0d0d0d", fg=color)
        self.lbl.pack(expand=True)
        
        threading.Thread(target=self.animateGlow, args=(self.lbl, color), daemon=True).start()
        # animate_glow(lbl, color)

    def animateGlow(self, widget, color):
        """Animate the widget with a glowing effect."""
        while not self.stop_event.is_set():  # Check if the stop event is set
            for alpha in range(100, 255, 5):  # Brighten
                if widget and widget.winfo_exists():  # Check if the widget still exists
                    hex_color = self.colorWithAlpha(color, alpha)
                    widget.config(fg=hex_color)
                time.sleep(0.05)
            for alpha in range(255, 100, -5):  # Dim
                if widget and widget.winfo_exists():  # Check if the widget still exists
                    hex_color = self.colorWithAlpha(color, alpha)
                    widget.config(fg=hex_color)
                time.sleep(0.05)

    def colorWithAlpha(self, color, alpha):
        """Convert a hex color to include an alpha component"""
        rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
        return f"#{''.join(f'{int(c * (alpha / 255)):02X}' for c in rgb)}"

    def stopGlowAnimation(self):
        """Stop the glow animation."""
        self.stop_event.set()
        if hasattr(self, 'animation_thread'):
            self.animation_thread.join()

    def createButton(self, root, text, command):
        """Create a custom cyberpunk-style button"""
        style = ttk.Style()
        style.configure(
            "Cyberpunk.TButton",
            font=("OCR A Extended", 14),
            foreground="#0d0d0d",
            background="#FF00FF",
            padding=10,
            relief="flat"
        )
        style.map(
            "Cyberpunk.TButton",
            background=[("active", "#00FFFF")],  # Change on hover
        )

        button = ttk.Button(root, text=text, style="Cyberpunk.TButton", command=command)
        button.pack(expand=True)

