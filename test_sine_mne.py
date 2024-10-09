import serial
import struct
import numpy as np
import mne
import matplotlib.pyplot as plt

# Define constants
COM_PORT = 'COM3'  # Change to your COM port
BAUD_RATE = 115200  # Change to the appropriate baud rate
NUM_SAMPLES = 32  # Number of bytes to read (32 bytes = 16 samples)
SAMPLE_RATE = 1000  # Define the sampling rate (Hz)
NUM_CHANNELS = 1  # Number of channels to read

# Initialize serial connection
ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)

# Create a buffer to store data
data_buffer = np.zeros((NUM_CHANNELS, 100))  # Buffer for 100 samples for 1 channel
sample_index = 0

# Prepare the MNE raw object
info = mne.create_info(ch_names=['Channel 1'], sfreq=SAMPLE_RATE, ch_types=['eeg'])
raw = mne.io.RawArray(data_buffer, info)

# Initialize a figure for plotting
plt.ion()  # Turn on interactive mode

# Function to read from COM port and update MNE plot
def read_and_plot():
    global sample_index

    fig, ax = plt.subplots()  # Create a new figure and axis

    while True:
        if ser.in_waiting >= NUM_SAMPLES:  # Check if enough data is available
            data = ser.read(NUM_SAMPLES)  # Read 32 bytes (enough for 16 samples)

            # Unpack the 32 bytes into 16 little-endian unsigned integers (uint16)
            samples = struct.unpack('<16H', data)  # Adjust to unpack 16 uint16 samples
            print(f"Received Samples: {samples}")

            # Update the data buffer
            data_buffer[0][:-16] = data_buffer[0][16:]  # Shift left to make room
            data_buffer[0][-16:] = samples  # Add new samples

            # Update MNE RawArray data
            # Ensure that we're only updating up to the buffer size
            start_index = sample_index % 100  # Wrap around if over the size of the buffer
            end_index = start_index + 16
            if end_index <= 100:
                raw._data[0, start_index:end_index] = samples  # Update raw data
            else:
                raw._data[0, start_index:100] = samples[:100 - start_index]  # Fill the end of the buffer
                raw._data[0, :end_index - 100] = samples[100 - start_index:]  # Fill the start of the buffer

            sample_index += 16
            
            # Clear the axis and plot the updated data
            ax.clear()
            ax.plot(raw._data[0], color='b')
            ax.set_xlabel('Samples')
            ax.set_ylabel('Amplitude')
            ax.set_ylim(0, 3000)  # Adjust y-limits as needed

            plt.pause(0.01)  # Pause to allow for the plot to update

# Start reading from the COM port and updating the plot
read_and_plot()