import tkinter as tk
from tkinter.ttk import *
from tkinter import messagebox
from tkinter import filedialog
from tkinter import HORIZONTAL
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import mne
import queue
from scipy.interpolate import interp1d
import serial
import struct
import threading

class App():
    def __init__(self):
        self.root = None
        self.root = tk.Tk()
        self.root.geometry("200x200")
        self.root.protocol("WM_DELETE_WINDOW", self.callback)
        self.plot = None

    def callback(self):
        if self.plot is not None:
            self.plot.__del__()
        self.root.quit()     
    
    def clearWindow(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def toggleLivePlot(self):
        self.clearWindow()
        with open('waveform_data.csv', 'w') as file:
            file.truncate(0)
        print("waveform_data.csv: cleared")
        self.plot = Live_Plot(self.root, n_channels=1)

    def toggleBenchmark(self):
        self.clearWindow()
        self.benchmark = Benchmark(self.root)
        self.benchmark.benchmark()

    def start(self):
        style = Style()
        style.configure("TButton", padding=6, relief="flat", background="#20b2aa", activebackground="#20b2aa")

        Live = Button(self.root, text ="LivePlot", command = self.toggleLivePlot, style="TButton")
        Live.pack(expand=True)

        Benchmark = Button(self.root, text ="Benchmark", command = self.toggleBenchmark, style="TButton")
        Benchmark.pack(expand=True)
        
        exit_button = Button(self.root, text = "Exit", command = exit, style="TButton") 
        exit_button.pack(expand=True)



        self.root.mainloop()

class Live_Plot():
    def __init__(self, root, n_channels = 1):
        """Initialize Live_Plot object"""
        self.root = root
        
        self.COM_PORT = 'COM3'          # Change to your COM port
        self.BAUD_RATE = 115200         # Change to the appropriate baud rate
        self.NUM_SAMPLES = 64          # Number of bytes to read (32 bytes = 16 samples)
        self.SAMPLE_RATE = 18000        # Define the sampling rate (Hz)
        self.NUM_CHANNELS = n_channels  # Number of channels to read
        self.BUFFER_SIZE = 10240        # Buffer size

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

        self.read_thread = threading.Thread(target=self.read_serial_data)
        self.save_thread = threading.Thread(target=self.save_data_to_file)
        self.read_thread.start()
        self.save_thread.start()
        
        self.update_plot() 

    def read_serial_data(self):
        """Read data from serial in a separate thread."""
        while not self.stop_event.is_set():
            if self.ser.in_waiting >= self.NUM_SAMPLES:
                data = self.ser.read(self.NUM_SAMPLES)
                samples = struct.unpack('<32H', data)  # Unpack the data

                # Shift the buffer and add new samples
                skip = int(self.NUM_SAMPLES / 2)
                self.data_buffer[0][:-skip] = self.data_buffer[0][skip:]
                self.data_buffer[0][-skip:] = samples
                self.sample_index += skip

                self.data_queue.put(samples)

    def save_data_to_file(self):
        """Save data to file in a separate thread."""
        with open('waveform_data.csv', 'a') as f:
            while not self.stop_event.is_set() or not self.data_queue.empty():
                try:
                    # Get a batch of samples from the queue
                    samples = self.data_queue.get(timeout=1)
                    # Save the samples to the file
                    f.write(','.join(map(str, samples)) + '\n')
                    f.flush()  # Flush to ensure data is written immediately
                except queue.Empty:
                    # Timeout reached, no data to save, keep the loop running
                    pass

    def update_plot(self):
        """Update the plot with the latest data."""
        if self.sample_index > 0:
            # Clear and plot the updated data
            self.ax.clear()
            # self.ax.plot(self.x_new, self.y_new, color='b')
            self.ax.plot(self.data_buffer[0], color='b')
            self.ax.set_title(f"Channel {self.NUM_CHANNELS}")
            self.ax.set_xlabel('Samples')
            self.ax.set_ylabel('Amplitude')
            self.ax.set_ylim(-1000, 4500)

            self.canvas.draw()

        # Schedule the next update after a short interval (e.g., 50 ms)
        self.root.after(1, self.update_plot)

    def __del__(self):
        """Cleanup resources and stop threads."""
        self.stop_event.set()  
        if self.ser and self.ser.is_open:  
            self.ser.close()

class Benchmark():
    def __init__(self, root):
        self.root = root
        self.label_file_explorer = None
        self.fig = None
        self.ax = None
        self.canvas = None
        self.scrollbar = None
        
        self.SAMPLE_RATE = 18000
        self.filename = ""
        
        # self.canvas = tk.Canvas(root, width=300, height=300)
        # self.canvas.get_tk_widget().pack()

    def browseFiles(self):
        self.filename = filedialog.askopenfilename(initialdir = "/",
                                            title = "Select a File",
                                            filetypes = (("Excel files",
                                                            "*.csv*"),
                                                        ("all files",
                                                            "*.*")))
        
        # Change label contents
        self.label_file_explorer.configure(text="File Opened: "+self.filename)

        self.loadFromFile(self.filename)
    
    def loadFromFile(self, filename):
        try:
            with open(filename, 'r') as file:
                self.data = []
                for line in file:
                    self.data.extend([float(val) for val in line.strip().split(',')])   
            self.plot_data()

        except Exception as e:
            print(f"Error loading file: {e}")
            tk.messagebox.showerror("File Error", f"Could not load file: {e}")
    
    def plot_data(self):
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

    def benchmark(self):
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
    app.start()