
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
            if self.plot is not None:
                self.plot.__del__()
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

        # self.buttons.stopGlowAnimation()
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
        
        self.COM_PORT = 'COM5'                          # Change to your COM port
        self.BAUD_RATE = 115200                         # Change to the appropriate baud rate
        self.NUM_SAMPLES = 64                           # Number of bytes to read (32 bytes = 16 samples)
        self.SAMPLE_RATE = 18000                        # Define the sampling rate (Hz)
        self.NUM_CHANNELS = n_channels                  # Number of channels to read
        self.BUFFER_SIZE = 20480                        # Buffer size
        self.Y_MIN = -1000                              # Maximum y-axis value
        self.Y_MAX = 6000                               # Maximum y-axis value

        self.fig, self.ax = plt.subplots(self.NUM_CHANNELS, figsize=(50, 20), dpi=100)
        # if self.NUM_CHANNELS == 1:
        #             self.ax = [self.ax]  # Convert to list if only one channel

        self.canvas = FigureCanvasTkAgg (self.fig, master=self.root)
        self.canvas.get_tk_widget().pack()
        
        # self.data_buffer = [np.zeros(100) for _ in range(self.NUM_CHANNELS)]  # Initialize buffers for 100 samples
        self.data_buffer = np.zeros((self.NUM_CHANNELS, self.BUFFER_SIZE))

        self.alpha_buffer = np.zeros(self.BUFFER_SIZE)
        self.beta_buffer = np.zeros(self.BUFFER_SIZE)
        self.gamma_buffer = np.zeros(self.BUFFER_SIZE)

        self.buffers = {
            ch: {
                'alpha': np.zeros(self.BUFFER_SIZE),
                'beta': np.zeros(self.BUFFER_SIZE),
                'gamma': np.zeros(self.BUFFER_SIZE)
            }
            for ch in range(self.NUM_CHANNELS)
        }

        self.enable = 1

        try:
            self.ser = serial.Serial(self.COM_PORT, self.BAUD_RATE, timeout=1)
            self.ser.set_buffer_size(rx_size=8192, tx_size=8192)
        except serial.SerialException as e:
            print(f"Error: {e}")
            tk.messagebox.showerror("Serial Error", f"Could not open serial port: {e}")
            self.ser = None
            self.enable = 0

        self.sample_index = [0] * 3
        # self.sample_index = {ch: 0 for ch in range(n_channels)}

        self.colors = {"alpha": "b", "beta": "g", "gamma": "r"}
        self.plot_alpha = False
        self.plot_beta = False
        self.plot_gamma = False
        
        self._queue = queue.Queue()

        self.data_queue = {
            ch: {
                'alpha': queue.Queue(),
                'beta': queue.Queue(),
                'gamma': queue.Queue()
            }
            for ch in range(self.NUM_CHANNELS)
        }

        self.info = mne.create_info(ch_names=['Channel 1'], sfreq=self.SAMPLE_RATE, ch_types=['eeg'])
        self.raw = mne.io.RawArray(self.data_buffer, self.info)

        self.stop_event = threading.Event()  # Event to stop the thread
        self.pause_event = threading.Event()  # Event to pause the thread

        if self.enable:
            self.startThreads()
            self.updatePlot()

    def startThreads(self):
        """Start the read and save threads"""
        self.read_thread = threading.Thread(target=self.readSerialData)
        self.save_thread = threading.Thread(target=self.saveDataToFile)
        
        self.read_thread.start()
        self.save_thread.start()

    def readSerialData(self):
        """Read data from serial in a separate thread"""

        frame_size = 36  # 3 uint16 (2 bytes each) * 6
        #frame_size = 48 # 4 uint16 (2 bytes each) * 6

        while not self.stop_event.is_set():
            if self.ser is not None:
                if self.ser.in_waiting >= frame_size:
                    frame = self.ser.read(frame_size)
        

                    data = struct.unpack('<18H', frame) 
                    #data = struct.unpack('<24H', frame)

                    header = data[0]  # First uint16 for header
                    wave_type = data[1]  # Second uint16 for wave type
                    #channel = data[2]  # Third uint16 for channel
                    data = data[2:]  # Remaining 14 uint16 for sample values
                    
                    # Print debug information
                    # print(f"Header: {header} Wave Type: {wave_type} Channel: {channel} Data: {data}")

                    # if header == 0 and channel_id in self.buffers:
                        # wave_name = self.get_wave_name(wave_type)

                        # if wave_name:
                        #     buffer = self.buffers[channel_id][wave_name]
                        #     idx = self.sample_index[channel_id]

                        #     # Update buffer with new samples
                        #     buffer[idx:idx + 14] = samples
                        #     self.sample_index[channel_id] = (idx + 14) % self.BUFFER_SIZE
                        
                    if header == 0:
                        # Update the buffers based on wave type
                        if wave_type == 1:  # Alpha wave
                            self.alpha_buffer[:-16] = self.alpha_buffer[16:]
                            self.alpha_buffer[-16:] = data

                        elif wave_type == 2:  # Beta wave
                            self.beta_buffer[:-16] = self.beta_buffer[16:]
                            self.beta_buffer[-16:] = data
                            
                        elif wave_type == 3:  # Gamma wave
                            self.gamma_buffer[:-16] = self.gamma_buffer[16:]
                            self.gamma_buffer[-16:] = data

                    # print("Current Buffers:")
                    # print(f"Alpha: {self.alpha_buffer[:10]}")  # Print first 10 values for quick check
                    # print(f"Beta: {self.beta_buffer[:10]}")
                    # print(f"Gamma: {self.gamma_buffer[:10]}")

    def get_wave_name(self, wave_type):
        """Map wave type to wave name."""
        return {1: 'alpha', 2: 'beta', 3: 'gamma'}.get(wave_type)
    
    def saveDataToFile(self):
        """Save all data to a single CSV file with clear separation."""
        with open('all_channels_data.csv', 'a') as f:
            # Write a header for the CSV file (only once)
            f.write("timestamp,channel,wave_type,samples\n")

            while not self.stop_event.is_set():
                for ch in range(self.NUM_CHANNELS):
                    for wave_type in ['alpha', 'beta', 'gamma']:
                        try:
                            # Get the samples from the queue
                            samples = self.data_queue[ch][wave_type].get(timeout=1)

                            # Format the row with channel, wave type, and sample data
                            row = (
                                f"{time.time()},{ch},{wave_type},"
                                + ','.join(map(str, samples))
                                + '\n'
                            )

                            # Write the row to the file
                            f.write(row)
                            f.flush()  # Ensure the data is saved immediately

                        except queue.Empty:
                            # If no data available, continue to the next queue
                            continue
    
    def shift_and_update(self, buffer, new_value):
        """Shift data in the buffer and add the new value."""
        buffer[:-1] = buffer[1:]
        buffer[-1] = new_value

    def updatePlot(self):
        """Update the plot with the latest data"""
        # if self.sample_index > 0:
        #     self.ax.clear()

        #     self.ax.plot(self.data_buffer[0], color='b')
        #     self.ax.set_title(f"Channel {self.NUM_CHANNELS}")
        #     self.ax.set_xlabel('Samples')
        #     self.ax.set_ylabel('Amplitude')
        #     self.ax.set_ylim(-1000, 4500)

        #     self.canvas.draw()
        # self.root.after(1, self.updatePlot)

        self.ax.clear()

        # Plot each wave type
        self.ax.plot(self.alpha_buffer, color='b', label="Alpha")
        self.ax.plot(self.beta_buffer, color='g', label="Beta")
        self.ax.plot(self.gamma_buffer, color='r', label="Gamma")

        self.ax.set_title("Alpha, Beta, and Gamma Waves")
        self.ax.set_xlabel('Samples')
        self.ax.set_ylabel('Amplitude')
        self.ax.set_ylim(self.Y_MIN, self.Y_MAX)
        self.ax.legend()

        self.canvas.draw()
        self.root.after(1, self.updatePlot)

        # self.ax.clear()  # Clear the plot

        # for ch in range(self.n_channels):
        #     alpha_data = self.buffers[ch]['alpha']
        #     beta_data = self.buffers[ch]['beta']
        #     gamma_data = self.buffers[ch]['gamma']

        #     # Plot each wave type with a different color
        #     self.ax.plot(alpha_data, label=f'Alpha (Ch {ch})', color='blue')
        #     self.ax.plot(beta_data, label=f'Beta (Ch {ch})', color='green')
        #     self.ax.plot(gamma_data, label=f'Gamma (Ch {ch})', color='red')

        # self.ax.set_ylim(-1000, 4500)  # Adjust based on signal range
        # self.ax.set_title("Real-Time EEG Data (Multi-Channel)")
        # self.ax.set_xlabel("Samples")
        # self.ax.set_ylabel("Amplitude")
        # self.ax.legend()
        # self.canvas.draw()


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