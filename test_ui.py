import tkinter as tk
from tkinter.ttk import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter import HORIZONTAL
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import mne
from PIL import Image, ImageTk, ImageDraw 
import queue
from scipy.interpolate import interp1d
import serial
import struct
import time
import threading

class App():
    def __init__(self):
        """Initialize the App object."""
        self.root = None
        self.root = tk.Tk()
        self.root.geometry("400x500")
        self.root.protocol("WM_DELETE_WINDOW", self.callback)
        self.root.configure(bg="#141414")
        self.plot = None

        self.mainMenu()

    def callback(self):
        """Callback function to handle window close event."""
        if self.plot is not None:
            self.plot.__del__()
        self.root.quit()     
    
    def clearWindow(self):
        """Clear the window of all widgets."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def toggleLivePlot(self):
        """Toggle the live plot window."""
        self.clearWindow()
        with open('waveform_data.csv', 'w') as file:
            file.truncate(0)
        print("waveform_data.csv: cleared")
        self.plot = LivePlot(self.root, n_channels=1)

    def toggleBenchmark(self):
        """Toggle the benchmark window."""
        self.clearWindow()
        self.benchmark = Benchmark(self.root)

    def createButton(self, text, command):
        """Create a circular button with a frosted glass effect."""
        frame = tk.Frame(self.root, bg="#E0E0E0")
        canvas = tk.Canvas(frame, width=100, height=100, bg="#E0E0E0", highlightthickness=0)

        # Draw the circle with Pillow (frosted effect)
        img = Image.new("RGBA", (100, 100), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse((0, 0, 100, 100), fill=(255, 255, 255, 180))  # White with transparency

        # Convert the Pillow image to a Tkinter-compatible image
        tk_img = ImageTk.PhotoImage(img)
        canvas.create_image(0, 0, anchor="nw", image=tk_img)
        canvas.image = tk_img  # Keep a reference to avoid garbage collection

        # Add the button text at the center
        canvas.create_text(50, 50, text=text, fill="#333", font=("Helvetica", 12, "bold"))

        # Bind the click event to the provided command
        canvas.bind("<Button-1>", lambda event: command())

        canvas.pack()
        return frame
    
    # def create_glowing_text(self, text, x, y, color, size=32):
    #     """Create glowing, animated text."""
    #     lbl = tk.Label(self.root, text=text, font=("OCR A Extended", size), bg="#0d0d0d", fg=color)
    #     lbl.place(x=x, y=y)

    #     # Start the glow animation in a separate thread
    #     # threading.Thread(target=self.animate_glow, args=(lbl,), daemon=True).start()

    # def animate_glow(self, label):
    #     """Animate the glow effect by cycling through colors."""
    #     colors = ["#FF00FF", "#00FFFF", "#FF4500", "#ADFF2F"]
    #     while True:
    #         for color in colors:
    #             label.config(fg=color)
    #             time.sleep(0.5)  # Delay between color changes

    def create_glowing_text(self, text, x, y, color, size=32):
        """Create glowing, animated text."""
        lbl = tk.Label(self.root, text=text, font=("OCR A Extended", size), bg="#0d0d0d", fg=color)
        lbl.place(x=x, y=y)

        threading.Thread(target=self.animate_glow, args=(lbl, color), daemon=True).start()

    def animate_glow(self, widget, color):
        """Animate the widget with a glowing effect."""
        while True:
            for alpha in range(100, 255, 5):  # Brighten
                hex_color = self.color_with_alpha(color, alpha)
                widget.config(fg=hex_color)
                time.sleep(0.05)
            for alpha in range(255, 100, -5):  # Dim
                hex_color = self.color_with_alpha(color, alpha)
                widget.config(fg=hex_color)
                time.sleep(0.05)

    def color_with_alpha(self, color, alpha):
        """Convert a hex color to include an alpha component."""
        rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
        return f"#{''.join(f'{int(c * (alpha / 255)):02X}' for c in rgb)}"

    def pulse_glow(self, label):
        """Animate pulsing glow effect."""
        colors = ["#FF00FF", "#00FFFF", "#FF4500", "#ADFF2F"]
        size = 36  # Initial font size
        while True:
            for color in colors:
                for scale in [1.0, 1.1, 1.2, 1.1, 1.0]:  # Pulsing effect scaling
                    label.config(fg=color, font=("OCR A Extended", int(size * scale)))
                    time.sleep(0.1)  # Control the speed of the pulse

    def create_cyberpunk_button(self, text, x, y, command):
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

        button = ttk.Button(self.root, text=text, style="Cyberpunk.TButton", command=command)
        button.place(x=x, y=y, width=300, height=50)

    def mainMenu(self):
        """Create the main menu."""
        # style = Style()
        # style.configure("TButton", padding=6, relief="flat", background="#20b2aa", activebackground="#20b2aa")

        # Live = Button(self.root, text ="LivePlot", command = self.toggleLivePlot, style="TButton")
        # Live.pack(expand=True)

        # Benchmark = Button(self.root, text ="Benchmark", command = self.toggleBenchmark, style="TButton")
        # Benchmark.pack(expand=True)
        
        # exit_button = Button(self.root, text = "Exit", command = exit, style="TButton") 
        # exit_button.pack(expand=True)

        # self.createButton("Live Plot", self.toggleLivePlot).pack(expand=True)
        # self.createButton("Benchmark", self.toggleBenchmark).pack(expand=True)
        # self.createButton("Exit", exit).pack(expand=True)
        
        # self.root.mainloop()

        self.create_glowing_text("NEUROFORGE", 50, 50, "#FF00FF", size=36)

        # Create two neon buttons with hover effects
        # self.create_neon_button("Start Neural Sync", "#00FFFF", self.toggleLivePlot, 150, 200)
        # self.create_neon_button("Enter Cyberspace", "#FF007F", self.toggleBenchmark, 150, 300)
        # self.create_neon_button("Exit", "#FF0000", exit, 150, 400)

        self.create_cyberpunk_button("Start Live Plot", 50, 150, self.toggleLivePlot)
        self.create_cyberpunk_button("Benchmark", 50, 250, self.toggleBenchmark)
        self.create_cyberpunk_button("Exit", 50, 350, exit)

        # Start the Tkinter main loop
        self.root.mainloop()

class LivePlot():

    def __init__(self, root, n_channels = 1):
        """Initialize Live_Plot object"""
        self.root = root
        
        self.COM_PORT = 'COM3'          # Change to your COM port
        self.BAUD_RATE = 115200         # Change to the appropriate baud rate
        self.NUM_SAMPLES = 64           # Number of bytes to read (32 bytes = 16 samples)
        self.SAMPLE_RATE = 18000        # Define the sampling rate (Hz)
        self.NUM_CHANNELS = n_channels  # Number of channels to read
        self.BUFFER_SIZE = 20480        # Buffer size
        self.Y_MIN = -1000              # Minimum y-axis value
        self.Y_MAX = 4500               # Maximum y-axis value
        
        self.fig, self.ax = plt.subplots(self.NUM_CHANNELS, figsize=(50, 20), dpi=100)
        self.canvas = FigureCanvasTkAgg (self.fig, master=self.root)
        self.canvas.get_tk_widget().pack()
        
        # self.data_buffer = [np.zeros(100) for _ in range(self.NUM_CHANNELS)]  # Initialize buffers for 100 samples
        self.data_buffer = np.zeros((self.NUM_CHANNELS, self.BUFFER_SIZE))
        
        try:
            self.ser = serial.Serial(self.COM_PORT, self.BAUD_RATE, timeout=1)
            self.ser.set_buffer_size(rx_size=8192, tx_size=8192)
        except serial.SerialException as e:
            print(f"Error: {e}")
            tk.messagebox.showerror("Serial Error", f"Could not open serial port: {e}")
            self.ser = None

        self.sample_index = 0
        self.data_queue = queue.Queue()

        self.info = mne.create_info(ch_names=['Channel 1'], sfreq=self.SAMPLE_RATE, ch_types=['eeg'])
        self.raw = mne.io.RawArray(self.data_buffer, self.info)

        self.stop_event = threading.Event()  # Event to stop the thread
        self.pause_event = threading.Event()  # Event to pause the thread

        self.read_thread = threading.Thread(target=self.readSerialData)
        self.save_thread = threading.Thread(target=self.saveDataToFile)
        self.read_thread.start()
        self.save_thread.start()
        
        self.updatePlot()

    def readSerialData(self):
        """Read data from serial in a separate thread."""
        while not self.stop_event.is_set():
            if self.ser.in_waiting >= self.NUM_SAMPLES:
                data = self.ser.read(self.NUM_SAMPLES)
                samples = struct.unpack('<32H', data)  
                
                skip = int(self.NUM_SAMPLES / 2)
                self.data_buffer[0][:-skip] = self.data_buffer[0][skip:]
                self.data_buffer[0][-skip:] = samples
                self.sample_index += skip

                self.data_queue.put(samples)

    def saveDataToFile(self):
        """Save data to file in a separate thread."""
        with open('waveform_data.csv', 'a') as f:
            while not self.stop_event.is_set() or not self.data_queue.empty():
                try:
                    samples = self.data_queue.get(timeout=1)
                    f.write(','.join(map(str, samples)) + '\n')
                    f.flush() 
                except queue.Empty:
                    pass

    def updatePlot(self):
        """Update the plot with the latest data."""
        if self.sample_index > 0:
            self.ax.clear()

            self.ax.plot(self.data_buffer[0], color='b')
            self.ax.set_title(f"Channel {self.NUM_CHANNELS}")
            self.ax.set_xlabel('Samples')
            self.ax.set_ylabel('Amplitude')
            self.ax.set_ylim(self.Y_MIN, self.Y_MAX)

            self.canvas.draw()
        self.root.after(1, self.updatePlot)

    def __del__(self):
        """Cleanup resources and stop threads."""
        self.stop_event.set()  
        if self.ser and self.ser.is_open:  
            self.ser.close()

class Benchmark():
    def __init__(self, root):
        """Initialize Benchmark object."""
        self.root = root
        self.label_file_explorer = None
        self.fig = None
        self.ax = None
        self.canvas = None
        self.scrollbar = None
        
        self.SAMPLE_RATE = 18000
        self.filename = ""

        self.benchmarkMenu()

    def browseFiles(self):
        """Browse files to load data."""
        self.filename = filedialog.askopenfilename(initialdir = "/",
                                            title = "Select a File",
                                            filetypes = (("Excel files",
                                                            "*.csv*"),
                                                        ("all files",
                                                            "*.*")))
        self.label_file_explorer.configure(text="File Opened: "+self.filename)

        self.loadFromFile(self.filename)
    
    def loadFromFile(self, filename):
        """Load data from file."""
        try:
            with open(filename, 'r') as file:
                self.data = []
                for line in file:
                    self.data.extend([float(val) for val in line.strip().split(',')])   
            self.plotData()

        except Exception as e:
            print(f"Error loading file: {e}")
            tk.messagebox.showerror("File Error", f"Could not load file: {e}")
    
    def plotData(self):
        """Plot the loaded data."""
        if self.fig is None:
            self.fig = plt.Figure(figsize=(7, 4), dpi=100)
            self.ax = self.fig.add_subplot(111)

            self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

            toolbar = NavigationToolbar2Tk(self.canvas, self.root)
            toolbar.update()
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.ax.clear()

        self.ax.plot(self.data, color='b')
        self.ax.set_title('Loaded Data from File')
        self.ax.set_xlabel('Samples')
        self.ax.set_ylabel('Amplitude')

        self.ax.set_xlim(0, len(self.data))  
        self.ax.relim()  
        self.ax.autoscale_view() 

        self.canvas.draw()

    def benchmarkMenu(self):
        """Create the benchmark menu."""
        self.label_file_explorer = Label(self.root, 
                                    text = "File Explorer using Tkinter")
        
        button_explore = Button(self.root, 
                        text = "Browse Files",
                        command = self.browseFiles)
        button_explore.pack(expand=True)

        button_exit = Button(self.root, 
                     text = "Exit",
                     command = exit) 
        button_exit.pack(expand=True)
        
        self.label_file_explorer.pack(expand=True)

if __name__ == '__main__':
    app = App()
    app.mainMenu()