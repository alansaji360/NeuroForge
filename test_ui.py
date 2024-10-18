
from button_styles import ButtonStyles
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
import threading
import time
import tkinter as tk
from tkinter.ttk import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter import HORIZONTAL
from tkinter import ttk

class App():
    def __init__(self):
        """Initialize the App object"""
        self.BG_COLOR = "#141414"

        self.root = None
        self.root = tk.Tk()
        self.root.geometry("400x500")
        self.root.protocol("WM_DELETE_WINDOW", self.callback)
        self.root.configure(bg=self.BG_COLOR)
        self.plot = None
        self.root.title("NeuroForge")
        self.root.iconbitmap("samurai.ico")
        self.root.resizable(True, True)

        self.marker = 1

        self.buttons = ButtonStyles(self.root)

        self.mainMenu()

    def callback(self):
        """Callback function to handle window close event"""
        if self.marker == 0: 
            self.clearWindow()
            self.mainMenu();
        else:
            self.onExit()

    def clearWindow(self):
        """Clear the window of all widgets"""
        for widget in self.root.winfo_children():
            widget.destroy()

    def onExit(self):
        """Exit the application."""
        if self.plot is not None:
            self.plot.__del__()

        self.buttons.stopGlowAnimation()
        self.root.quit()
        exit()

    def toggleLivePlot(self):
        """Toggle the live plot window."""
        self.marker = 0
        self.buttons.stopGlowAnimation()
        time.sleep(0.5)
        self.clearWindow()
        with open('waveform_data.csv', 'w') as file:
            file.truncate(0)
        print("waveform_data.csv: cleared")
        self.plot = LivePlot(self.root, n_channels=1)

    def toggleBenchmark(self):
        """Toggle the benchmark window."""
        self.marker = 0
        self.buttons.stopGlowAnimation()
        time.sleep(0.5)
        self.clearWindow()
        self.benchmark = Benchmark(self.root)

    def mainMenu(self):
        """Create the main menu."""
        if self.marker == 0:
            self.marker = 1

        self.buttons.createGlowText(self.root, "NEUROFORGE", "#FF00FF", self.BG_COLOR, size=36)

        self.buttons.createButton(self.root, "Live Plot",   self.toggleLivePlot)
        self.buttons.createButton(self.root, "Benchmark",   self.toggleBenchmark)
        self.buttons.createButton(self.root, "Exit",        exit)

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
        
        self.updatePlot()

    def startThreads(self):
        """Start the read and save threads"""
        self.read_thread.start()
        self.save_thread.start()

    def readSerialData(self):
        """Read data from serial in a separate thread"""
        while not self.stop_event.is_set():
            if self.ser is not None:    
                if self.ser.in_waiting >= self.NUM_SAMPLES:
                    data = self.ser.read(self.NUM_SAMPLES)
                    samples = struct.unpack('<32H', data)  
                    
                    skip = int(self.NUM_SAMPLES / 2)
                    self.data_buffer[0][:-skip] = self.data_buffer[0][skip:]
                    self.data_buffer[0][-skip:] = samples
                    self.sample_index += skip

                    self.data_queue.put(samples)
            else:
                self.stop_event.set()

    def saveDataToFile(self):
        """Save data to file in a separate thread"""
        with open('cache.csv', 'a') as f:
            while not self.stop_event.is_set() or not self.data_queue.empty():
                try:
                    samples = self.data_queue.get(timeout=1)
                    f.write(','.join(map(str, samples)) + '\n')
                    f.flush() 
                except queue.Empty:
                    pass

    def updatePlot(self):
        """Update the plot with the latest data"""
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
        """Cleanup resources and stop threads"""
        self.stop_event.set()  
        if self.ser and self.ser.is_open:  
            self.ser.close()

class Benchmark():
    def __init__(self, root):
        """Initialize Benchmark object"""
        self.root = root
        self.label_file_explorer = None
        self.fig = None
        self.ax = None
        self.canvas = None
        self.scrollbar = None
        
        self.SAMPLE_RATE = 18000
        self.filename = ""

        self.buttons = ButtonStyles(self.root)

        self.benchmarkMenu()

    def browseFiles(self):
        """Browse files to load data"""
        self.filename = filedialog.askopenfilename(initialdir = "/",
                                            title = "Select a File",
                                            filetypes = (("Excel files",
                                                            "*.csv*"),
                                                        ("all files",
                                                            "*.*")))
        self.label_file_explorer.configure(text="File Opened: "+self.filename)

        self.loadFromFile(self.filename)
    
    def loadFromFile(self, filename):
        """Load data from file"""
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
        """Plot the loaded data"""
        if self.fig is None:
            self.fig = plt.Figure(figsize=(7, 4), dpi=100, facecolor='#141414')
            self.ax = self.fig.add_subplot(111)

            self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

            toolbar = NavigationToolbar2Tk(self.canvas, self.root)
            toolbar.update()
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        # self.ax.clear()

        # self.ax.plot(self.data, color='b')
        # self.ax.set_title('Loaded Data from File')
        # self.ax.set_xlabel('Samples')
        # self.ax.set_ylabel('Amplitude')

        # self.ax.set_xlim(0, len(self.data))  
        # self.ax.relim()  
        # self.ax.autoscale_view() 

        # self.canvas.draw()

        self.ax.clear()
        self.ax.set_facecolor('#141414') 

        self.ax.plot(self.data, color='cyan') 
        self.ax.set_title('Loaded Data from File', color='white')  
        self.ax.set_xlabel('Samples', color='white') 
        self.ax.set_ylabel('Amplitude', color='white') 

        self.ax.set_xlim(0, len(self.data) if len(self.data) > 0 else 1)
        self.ax.relim()
        self.ax.autoscale_view()

        self.ax.tick_params(axis='both', colors='white') 
        self.ax.grid(color='gray', linestyle='--', linewidth=0.5)  

        self.canvas.draw()

    def benchmarkMenu(self):
        """Create the benchmark menu."""
        self.label_file_explorer = Label(self.root, 
                                    text = "File Explorer using Tkinter")

        self.buttons.createButton(self.root, "Explore", self.browseFiles)

if __name__ == '__main__':
    app = App()