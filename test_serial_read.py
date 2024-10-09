import serial
import numpy as np
import mne

# Initialize serial connection (replace 'COM3' with the correct port for your device)
ser = serial.Serial('COM2', baudrate=115200, timeout=1)  # Adjust baud rate as necessary

# Define variables
n_channels = 4  # Number of EEG channels
sfreq = 250  # Sampling frequency (Hz)
ch_names = ['Fp1', 'Fp2', 'C3', 'C4', 'P7', 'P8', 'O1', 'O2']  # Replace with actual channel names
data_buffer = []  # Buffer to store incoming data

# Create MNE info structure
info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')

# Function to process the incoming data
def process_eeg_data(sample):
    global data_buffer
    # Convert the sample to the right format (e.g., a list of floats)
    data_buffer.append(sample)

# Read from the USB serial port
print("Starting data stream...")

while True:
    if ser.in_waiting > 0:
        # Read data from serial (replace 32 with the actual packet size)
        raw_data = ser.read(32)
        
        # Convert raw data (e.g., bytes) into actual EEG values
        # Assuming each channel's data is sent as a float32 (4 bytes)
        sample = np.frombuffer(raw_data, dtype=np.float32)
        
        # Make sure the sample contains data from all channels
        if len(sample) == n_channels:
            process_eeg_data(sample)
        
        # Stop reading after a certain time for demo purposes (e.g., 10 seconds)
        # Replace this with a real-time condition in your application
        
        print(len(data_buffer))
        if len(data_buffer) >= sfreq * 10:  # 10 seconds of data
            break

# Convert buffer to a NumPy array and transpose for MNE (channels x time)
eeg_data = np.array(data_buffer).T

# Create MNE RawArray object for further analysis
raw = mne.io.RawArray(eeg_data, info)

# Visualize the EEG data
raw.plot()