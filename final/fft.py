from imports import *

class Fourier():
    def __init__(self, root, n_channels=1):
        """Initialize FFT plotter"""
        self.root = root
        self.COM_PORT = 'COM7'
        self.BAUD_RATE = 115200
        self.SAMPLE_RATE = 18000
        self.NUM_CHANNELS = n_channels
        self.BUFFER_SIZE = 5000
        self.FFT_SIZE = 1024
        self.UPDATE_INTERVAL = 50  # milliseconds
        
        # Initialize buffers for raw data
        self.buffers = {
            ch: {
                'alpha': np.zeros(self.BUFFER_SIZE),
                'beta': np.zeros(self.BUFFER_SIZE),
                'gamma': np.zeros(self.BUFFER_SIZE)
            }
            for ch in range(self.NUM_CHANNELS)
        }
        
        self.first_data_time = None
        self.first_plot_time = None
        
        # Set up the plot
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack()
        
        # Calculate frequency bins
        # self.freq_bins = np.fft.rfftfreq(self.FFT_SIZE, d=1/self.SAMPLE_RATE)
        
        # # Initialize the line with zeros
        # self.line, = self.ax.plot(self.freq_bins, np.zeros_like(self.freq_bins))
        self.freq_bins = np.fft.rfftfreq(self.FFT_SIZE, d=1/self.SAMPLE_RATE)

        self.freq_100hz_idx = np.where(self.freq_bins <= 100)[0][-1]
        
        # Slice frequency bins to 0-100Hz
        self.freq_bins = self.freq_bins[:self.freq_100hz_idx + 1]
        
        # Initialize the line with zeros of correct size (up to 100Hz)
        self.line, = self.ax.plot(self.freq_bins, np.zeros_like(self.freq_bins))
        
        self.ax.set_xlabel('Frequency (Hz)')
        self.ax.set_ylabel('Magnitude')
        self.ax.set_title('Averaged FFT from All Channels (0-100 Hz)')
        self.ax.set_xlim(0, 100)  # Set x-axis limit to 100Hz
        self.ax.set_ylim(0, 1000)  # Adjust as needed
        self.ax.grid(True)
        
        # Draw canvas once to set up background
        self.fig.tight_layout()
        self.canvas.draw()
        
        # Initialize serial connection
        try:
            self.ser = serial.Serial(self.COM_PORT, self.BAUD_RATE, timeout=1)
            self.ser.set_buffer_size(rx_size=8192, tx_size=8192)
            self.enable = True
        except serial.SerialException as e:
            print(f"Error: {e}")
            tk.messagebox.showerror("Serial Error", f"Could not open serial port: {e}")
            self.ser = None
            self.enable = False

        self.stop_event = threading.Event()
        
        if self.enable:
            self.read_thread = threading.Thread(target=self.read_serial_data)
            self.read_thread.start()
            self.start_animation()

    def get_wave_name(self, wave_type):
        """Map wave type to wave name."""
        return {0: 'alpha', 1: 'beta', 2: 'gamma'}.get(wave_type)

    def read_serial_data(self):
        """Read and process serial data"""
        frame_size = 260

        while not self.stop_event.is_set():
            if self.ser is not None and self.ser.in_waiting >= frame_size:
                if self.first_data_time is None:
                    self.first_data_time = time.time()
                    print(f"First data received at: {self.first_data_time}")

                frame = self.ser.read(frame_size)
                data = struct.unpack('<130H', frame)

                header = data[0]
                id = data[1]
                data = data[2:]

                channel = (id // 3)
                wave_type = id % 3

                if header == 0 and channel in self.buffers:
                    wave_name = self.get_wave_name(wave_type)
                    if wave_name:
                        buffer = self.buffers[channel][wave_name]
                        buffer[:-128] = buffer[128:]
                        adjusted_data = np.array(data) * 1.5
                        buffer[-128:] = adjusted_data

    def animate(self, frame):
        """Animation function for FuncAnimation"""
        # Initialize total_fft with the full size (we'll slice it later)
        total_fft = np.zeros(self.FFT_SIZE//2 + 1)
        n_signals = 0
        
        # Loop through all channels and wave types
        for ch in range(self.NUM_CHANNELS):
            # for wave_type in ['alpha', 'beta', 'gamma']:
            buffer = self.buffers[ch]['alpha'] + self.buffers[ch]['beta'] + self.buffers[ch]['gamma']
            #     if len(buffer) >= self.FFT_SIZE:
            #         # Compute FFT for this signal
            windowed = buffer[-self.FFT_SIZE:] * signal.windows.hann(self.FFT_SIZE)
            fft_data = np.fft.rfft(windowed)
            magnitude = 2.0 * np.abs(fft_data) / self.FFT_SIZE
                    
                    # Add to total
                    # total_fft += magnitude
                    # n_signals += 1
        
        # Average the FFTs if we have data
        # if n_signals > 0:
        #     averaged_fft = total_fft / n_signals
        #     # Slice the averaged FFT to only show up to 100Hz
        #     self.line.set_ydata(averaged_fft[:self.freq_100hz_idx + 1])

        if self.first_data_time is not None and self.first_plot_time is None:
            self.first_plot_time = time.time()
            latency = self.first_plot_time - self.first_data_time
            print(f"First plot update at: {self.first_plot_time}")
            print(f"Data acquisition to first plot latency: {latency:.3f} seconds")

        return self.line,

    def start_animation(self):
        """Start the animation"""
        self.anim = FuncAnimation(
            self.fig,
            self.animate,
            interval=self.UPDATE_INTERVAL,
            blit=True,
            cache_frame_data=False
        )

    def cleanup(self):
        """Clean up resources"""
        print("Starting cleanup...")
        self.stop_event.set()
        
        self.anim.event_source.stop()
        if hasattr(self, 'read_thread'):
            self.read_thread.join(timeout=2)
            
        if self.ser and self.ser.is_open:
            self.ser.close()
            
        print("Cleanup complete")

    def __del__(self):
        """Clean up on deletion"""
        try:
            self.cleanup()
        except Exception as e:
            print(f"Error during cleanup: {e}")