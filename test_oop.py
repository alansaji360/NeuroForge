import tkinter as tk
from tkinter.ttk import *
from tkinter import messagebox
from tkinter import filedialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mne
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
        if self.plot != None:
            self.plot.__del__
            self.plot.ser.close()
        self.root.quit()     
    
    def clearWindow(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def toggleLivePlot(self):
        self.clearWindow()
        self.plot = Live_Plot(self.root, n_channels=1)
        # self.plot.read_and_plot()
        # self.plot.create_plot()
        # self.plot.start_timer(interval=100)

    def toggleBenchmark(self):
        self.clearWindow()
        self.benchmark = Benchmark(self.root)
        self.benchmark.benchmark()

    def start(self):
        style = Style()
        style.configure("TButton", padding=6, relief="flat", background="#20b2aa", activebackground="#20b2aa")

        A = Button(self.root, text ="LivePlot", command = self.toggleLivePlot, style="TButton")
        A.pack(expand=True)

        B = Button(self.root, text ="Benchmark", command = self.toggleBenchmark, style="TButton")
        B.pack(expand=True)
        
        self.root.mainloop()

class Live_Plot():
    def __init__(self, root, n_channels = 1):
        """Initialize Live_Plot object"""
        self.root = root
        
        self.COM_PORT = 'COM3'          # Change to your COM port
        self.BAUD_RATE = 115200         # Change to the appropriate baud rate
        self.NUM_SAMPLES = 128          # Number of bytes to read (32 bytes = 16 samples)
        self.SAMPLE_RATE = 18000        # Define the sampling rate (Hz)
        self.NUM_CHANNELS = n_channels  # Number of channels to read
        self.BUFFER_SIZE = 5120         # Buffer size

        self.fig, self.ax = plt.subplots(self.NUM_CHANNELS, figsize=(50, 20), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
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
        self.info = mne.create_info(ch_names=['Channel 1'], sfreq=self.SAMPLE_RATE, ch_types=['eeg'])
        self.raw = mne.io.RawArray(self.data_buffer, self.info)

        self.stop_event = threading.Event()  # Event to stop the thread
        self.read_thread = threading.Thread(target=self.read_serial_data)
        self.read_thread.start()

        self.update_plot() 

    def read_serial_data(self):
        """Read data from serial in a separate thread."""
        while not self.stop_event.is_set():
            if self.ser.in_waiting >= self.NUM_SAMPLES:
                data = self.ser.read(self.NUM_SAMPLES)
                samples = struct.unpack('<64H', data)  # Unpack the data

                # Shift the buffer and add new samples
                self.data_buffer[0][:-64] = self.data_buffer[0][64:]
                self.data_buffer[0][-64:] = samples
                self.sample_index += 64

    def update_plot(self):
        """Update the plot with the latest data."""
        if self.sample_index > 0:
            # Clear and plot the updated data
            self.ax.clear()
            self.ax.plot(self.data_buffer[0], color='b')
            self.ax.set_title(f"Channel {self.NUM_CHANNELS}")
            self.ax.set_xlabel('Samples')
            self.ax.set_ylabel('Amplitude')
            self.ax.set_ylim(0, 3000)

            self.canvas.draw()

        # Schedule the next update after a short interval (e.g., 50 ms)
        self.root.after(1, self.update_plot)

    def __del__(self):
        """Cleanup resources and stop threads."""
        self.stop_event.set()  # Signal the thread to stop
        if self.ser:
            self.ser.close()

class Benchmark():
    def __init__(self, root):
        self.root = root
        self.label_file_explorer = None
        # self.canvas = tk.Canvas(root, width=300, height=300)
        # self.canvas.get_tk_widget().pack()

    def browseFiles(self):
        filename = filedialog.askopenfilename(initialdir = "/",
                                            title = "Select a File",
                                            filetypes = (("Text files",
                                                            "*.txt*"),
                                                        ("all files",
                                                            "*.*")))
        
        # Change label contents
        self.label_file_explorer.configure(text="File Opened: "+filename)

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
        #button_explore.grid(column = 1, row = 2)
        #button_exit.grid(column = 1,row = 3)



if __name__ == '__main__':
    app = App()
    app.start()