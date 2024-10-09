import serial
import struct
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# Function to read data from COM port
def read_data_from_com(port, baud_rate):
    ser = serial.Serial(port, baud_rate, timeout=1)
    return ser

# Function to update the plot
def update_plot(frame, ser, lines, data_buffers):
    if ser.in_waiting >= 32:  # Check if enough data is available
        data = ser.read(32)  # Read 32 bytes (8 channels * 4 bytes)
        sample = struct.unpack('f' * 8, data)  # Unpack the data
        print(f"Received Sample: {sample}")  # Debugging statement

        # Update data buffers for each channel
        for i, buffer in enumerate(data_buffers):
            buffer[:-1] = buffer[1:]  # Shift data down
            buffer[-1] = sample[i]  # Append new data

        # Update the lines with new data
        for i, line in enumerate(lines):
            line.set_ydata(data_buffers[i])  # Update y-data for each line

    return lines

# Main function
def main():
    com_port = 'COM2'  # Change to your desired COM port
    baud_rate = 115200  # Must match the sending script

    # Set up the serial connection
    ser = read_data_from_com(com_port, baud_rate)

    # Set up the plotting
    plt.figure(figsize=(10, 6))
    ax = plt.axes(xlim=(0, 100), ylim=(-1, 1))  # Adjust limits as necessary
    ax.set_title("Live EEG Data from COM2")
    ax.set_xlabel("Samples")
    ax.set_ylabel("Amplitude")

    # Initialize lines for each channel and data buffers
    lines = [ax.plot([], [])[0] for _ in range(8)]
    colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k', 'purple']  # Colors for each channel
    data_buffers = [np.zeros(100) for _ in range(8)]  # Initialize buffers for 100 samples

    for i, line in enumerate(lines):
        line.set_color(colors[i])
        line.set_label(f'Channel {i + 1}')
        line.set_data(np.arange(100), data_buffers[i])  # Set initial data

    ax.legend()

    # Create an animation
    ani = animation.FuncAnimation(
        plt.gcf(),
        update_plot,
        fargs=(ser, lines, data_buffers),
        interval=100  # Update every 100 ms
    )

    plt.show()

if __name__ == '__main__':
    main()