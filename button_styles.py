import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw, ImageTk
import threading
import time
    
def createGlowText(root, text, x, y, color, size=32):
    """Create glowing, animated text."""
    lbl = tk.Label(root, text=text, font=("OCR A Extended", size), bg="#0d0d0d", fg=color)
    lbl.place(x=x, y=y)

    threading.Thread(target=animate_glow, args=(lbl, color), daemon=True).start()
    # animate_glow(lbl, color)

def animate_glow(widget, color):
    """Animate the widget with a glowing effect."""
    while True:
        for alpha in range(100, 255, 5):  # Brighten
            hex_color = color_with_alpha(color, alpha)
            widget.config(fg=hex_color)
            time.sleep(0.05)
        for alpha in range(255, 100, -5):  # Dim
            hex_color = color_with_alpha(color, alpha)
            widget.config(fg=hex_color)
            time.sleep(0.05)

def color_with_alpha(color, alpha):
    """Convert a hex color to include an alpha component."""
    rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
    return f"#{''.join(f'{int(c * (alpha / 255)):02X}' for c in rgb)}"

def createButton(root, text, x, y, command):
    """Create a custom cyberpunk-style button."""
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
    button.place(x=x, y=y, width=300, height=50)