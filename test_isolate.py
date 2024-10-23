import tkinter as tk
from tkinter.ttk import *
from tkinter import messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import serial
import struct
import time
import threading

class App():
    def __init__(self):
        self.root = None
        self.root = tk.Tk()
        self.root.geometry("200x200")
        self.root.protocol("WM_DELETE_WINDOW", self.callback)

    def callback(self):
        if self.plot is not None:
            self.plot.__del__()
            self.plot.ser.close()
        self.root.quit()     

    def clearWindow(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def toggleLivePlot(self):
        self.clearWindow()
        time.sleep(0.5)
        self.plot = Live_Plot(self.root, n_channels=1)

    def start(self):
        style = Style()
        style.configure("TButton", padding=6, relief="flat", background="#20b2aa", activebackground="#20b2aa")

        A = Button(self.root, text ="LivePlot", command=self.toggleLivePlot, style="TButton")
        A.pack(expand=True)
        
        self.root.mainloop()

class Live_Plot():
    def __init__(self, root, n_channels=1):
        """Initialize Live_Plot object"""
        self.root = root
        
        self.COM_PORT = 'COM3'          # Change to your COM port
        self.BAUD_RATE = 115200         # Change to the appropriate baud rate
        self.NUM_SAMPLES = 128          # Number of bytes to read (32 bytes = 16 samples)
        self.SAMPLE_RATE = 18000        # Define the sampling rate (Hz)
        self.NUM_CHANNELS = n_channels  # Number of channels to read
        self.BUFFER_SIZE = 20480        # Buffer size

        self.fig, self.ax = plt.subplots(self.NUM_CHANNELS, figsize=(10, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack()
        self.indicator = ToggleLight(self.root)
        
        self.data_buffer = np.zeros((self.NUM_CHANNELS, self.BUFFER_SIZE))

        try:
            self.ser = serial.Serial(self.COM_PORT, self.BAUD_RATE, timeout=1)
            self.ser.set_buffer_size(rx_size=8192, tx_size=8192)
        except serial.SerialException as e:
            print(f"Error: {e}")
            tk.messagebox.showerror("Serial Error", f"Could not open serial port: {e}")
            self.ser = None

        self.sample_index = 0
        self.stop_event = threading.Event()  # Event to stop the thread
        self.pause_event = threading.Event()  # Event to pause the thread

        self.read_thread = threading.Thread(target=self.read_serial_data)
        self.read_thread.start()
        
        self.light_thread = threading.Thread(target=self.indicator.toggle_light)

    
        self.update_plot() 

    def read_serial_data(self):
        """Read data from serial in a separate thread."""
        while not self.stop_event.is_set():
            if self.ser.in_waiting >= self.NUM_SAMPLES:
                data = self.ser.read(self.NUM_SAMPLES)
                samples = struct.unpack('<64H', data)  # Unpack the data (adjust format according to your device)

                # Shift the buffer and add new samples
                self.data_buffer[0][:-64] = self.data_buffer[0][64:]
                self.data_buffer[0][-64:] = samples
                self.sample_index += 64

    def detect_blinks(self, data, threshold=1500, min_distance=50):
        """Detect blinks based on amplitude threshold crossing."""
        blink_indices = []
        last_blink_index = -min_distance  # Initialize to a negative value
        for i in range(1, len(data)):
            # Detect if the amplitude crosses the threshold (blink detection)
            if data[i] > threshold and (i - last_blink_index) > min_distance:
                blink_indices.append(i)
                last_blink_index = i
        return blink_indices

    def update_plot(self):
        """Update the plot with the latest data and highlight detected blinks."""
        if self.sample_index > 0:
            self.ax.clear()

            # Plot raw data
            self.ax.plot(self.data_buffer[0], color='b', label='Raw EEG')

            # Detect and highlight blinks
            blinks = self.detect_blinks(self.data_buffer[0], 2400)
            for blink in blinks:
                # print("blink")
                # self.indicator.toggle_light()
                self.ax.axvline(x=blink, color='r', linestyle='--', label='Blink Detected' if blink == blinks[0] else "")

            self.ax.legend()
            self.ax.set_title("Real-Time Blink Detection")
            self.ax.set_xlabel('Samples')
            self.ax.set_ylabel('Amplitude')
            self.ax.set_ylim(-1000, 4500)

            self.canvas.draw()

        # Schedule the next update after a short interval (e.g., 50 ms)
        self.root.after(1, self.update_plot)

    def __del__(self):
        """Cleanup resources and stop threads."""
        self.stop_event.set()  # Signal the thread to stop
        if self.ser:
            self.ser.close()

class ToggleLight:
    def __init__(self, root):
        self.root = root
        self.root.title("Toggleable Light")

        # Create a canvas to draw the light
        self.canvas = tk.Canvas(self.root, width=200, height=200)
        self.canvas.pack()

        # Draw a circle to represent the light (initially off)
        self.light = self.canvas.create_oval(50, 50, 150, 150, fill="gray")

        # Create a button to toggle the light
        self.toggle_button = tk.Button(self.root, text="Toggle Light", command=self.toggle_light)
        self.toggle_button.pack()

        # Track light state (initially off)
        self.is_on = False

    def toggle_light(self):
        """Toggle the light on or off."""
        # self.canvas.itemconfig(self.light, fill="yellow")
        # time.sleep(0.1)
        # self.canvas.itemconfig(self.light, fill="gray")
        # if self.is_on:
        #     self.canvas.itemconfig(self.light, fill="gray")  # Turn off (gray color)
        #     self.is_on = False
        # else:
        #     self.canvas.itemconfig(self.light, fill="yellow")  # Turn on (yellow color)
        #     self.is_on = True

if __name__ == '__main__':
    app = App()
    app.start()