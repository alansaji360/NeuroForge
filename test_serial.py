import serial
import time
import struct

# Open serial port
ser = serial.Serial('COM1', 115200)  # Adjust COM port as needed

# Simulate streaming EEG data (8 channels, 250 Hz)
n_channels = 4
sfreq = 250
duration = 10  # seconds

# Simulate data for 10 seconds
for i in range(sfreq * duration):
    # Create a sample of random data for each channel
    sample = [i * 0.001 for i in range(n_channels)]
    
    # Pack data as bytes (assuming 32-bit float per channel)
    packed_sample = struct.pack('f' * n_channels, *sample)
    
    # Send the packed sample over USB
    ser.write(packed_sample)
    
    # Wait for next sample (simulate the real-time sampling rate)
    time.sleep(1 / sfreq)

# Close the connection
ser.close()