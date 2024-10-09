import serial
import struct
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

# Define constants
COM_PORT = 'COM3'  # Change to your COM port
BAUD_RATE = 115200  # Change to the appropriate baud rate
NUM_SAMPLES = 32  # Number of bytes to read (32 bytes = 8 samples)
NUM_CHANNELS = 1  # Number of channels to read

# Initialize serial connection
ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)

# Create a buffer to store data
data_buffer = np.zeros((NUM_CHANNELS, 4096))  # Buffer for 100 samples for 1 channel
sample_index = 0

# Function to read from COM port and update the plot
def read_and_plot():
    global sample_index
    while True:
        if ser.in_waiting >= NUM_SAMPLES:  # Check if enough data is available
            data = ser.read(NUM_SAMPLES)  # Read 32 bytes (enough for 8 samples)

            # Unpack the 32 bytes into 8 little-endian signed integers
            samples = struct.unpack('<8i', data)
            # print(f"Received Samples: {samples}")

            # Shift the buffer contents to the left by 8 positions to make room for the new samples
            data_buffer[0][:-8] = data_buffer[0][8:]

            # Add the 8 new samples to the end of the buffer
            data_buffer[0][-8:] = samples

            # Prepare data for plotting
            x = np.arange(len(data_buffer[0]))  # Original sample indices
            y = data_buffer[0]  # Sampled sine wave values

            # Create an interpolation function
            f_interp = interp1d(x, y, kind='cubic')  # Cubic interpolation

            # Generate new x values for a smoother curve
            x_new = np.linspace(0, len(y) - 1, num=len(y) * 10)  # 10x more points
            y_new = f_interp(x_new)

            # Plot the interpolated data
            plt.clf()  # Clear the previous plot
            plt.plot(x, y, 'o', label='Original Samples')  # Original samples
            plt.plot(x_new, y_new, '-', label='Interpolated Curve')  # Interpolated curve
            plt.title('Sine Wave')
            plt.xlabel('Samples')
            plt.ylabel('Amplitude')
            plt.legend()
            plt.pause(0.01)  # Pause to update the plot

# Initialize the plot
plt.ion()  # Turn on interactive mode
plt.figure()

# Start reading from the COM port and updating the plot
read_and_plot()