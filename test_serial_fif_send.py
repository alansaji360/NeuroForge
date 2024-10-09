import mne
import serial
import struct
import numpy as np
import time

# Function to send data to a COM port
def send_data_to_com(data, ser):
    # Convert numpy array to bytes (assuming 32-bit float for each sample)
    packed_data = struct.pack('f' * len(data), *data)
    ser.write(packed_data)

# Main function
def main():
    # Load data from the FIF file
    fif_file_path = 'C:/Users/alans/mne_data/MNE-sample-data/MEG/sample/sample_audvis_filt-0-40_raw.fif'  # Replace with your FIF file path
    raw = mne.io.read_raw_fif(fif_file_path, preload=True)

    # Configure the serial port
    com_port = 'COM1'  # Change to your desired COM port
    baud_rate = 115200
    ser = serial.Serial(com_port, baud_rate, timeout=1)

    # Send data over the COM port
    for i in range(len(raw.times)):
        # Get the next sample (assuming 8 channels)
        sample = raw[:, i][0]  # Extract data for all channels at time i

        # Send the sample to the COM port
        send_data_to_com(sample, ser)

        # Simulate sampling rate (adjust according to your actual sampling rate)
        time.sleep(1 / raw.info['sfreq'])

    # Close the serial connection
    ser.close()

if __name__ == '__main__':
    main()