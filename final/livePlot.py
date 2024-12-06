from imports import *

class LivePlot():
    def __init__(self, root, n_channels=1):
        """Initialize Live_Plot object"""
        self.root = root
        
        self.COM_PORT = 'COM7'
        self.BAUD_RATE = 115200
        self.SAMPLE_RATE = 18000
        self.NUM_CHANNELS = n_channels
        self.BUFFER_SIZE = 5000
        self.Y_MIN = -1000
        self.Y_MAX = 60000
        self.FILENAME = 'waveform_data.csv'
        self.UPDATE_INTERVAL = 10  # Update interval in milliseconds

        self.first_data_time = None
        self.first_plot_time = None
        
        # Create figure and subplots
        self.fig, self.ax = plt.subplots(self.NUM_CHANNELS, figsize=(50, 20), dpi=100)
        if self.NUM_CHANNELS == 1:
            self.ax = [self.ax]

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack()
        
        # Initialize x data
        self.x_data = np.arange(self.BUFFER_SIZE)
        
        # Initialize line objects for each channel and wave type
        self.lines = {}
        for ch in range(self.NUM_CHANNELS):
            self.ax[ch].set_xlim(0, self.BUFFER_SIZE)
            self.ax[ch].set_ylim(self.Y_MIN, self.Y_MAX)
            self.ax[ch].grid(True)
            
            self.lines[ch] = {
                'alpha': self.ax[ch].plot(self.x_data, np.zeros(self.BUFFER_SIZE), 
                                        'b-', label=f'Alpha (Ch {ch})', animated=True)[0],
                'beta': self.ax[ch].plot(self.x_data, np.zeros(self.BUFFER_SIZE), 
                                       'g-', label=f'Beta (Ch {ch})', animated=True)[0],
                'gamma': self.ax[ch].plot(self.x_data, np.zeros(self.BUFFER_SIZE), 
                                        'r-', label=f'Gamma (Ch {ch})', animated=True)[0]
            }
            
            self.ax[ch].set_title(f"Channel {ch + 1} Data")
            self.ax[ch].set_xlabel("Samples")
            self.ax[ch].set_ylabel("Amplitude")
            self.ax[ch].legend(loc='upper right')

        # Draw the initial plot to set up the background
        self.fig.tight_layout()
        self.canvas.draw()
        self.backgrounds = [self.fig.canvas.copy_from_bbox(ax.bbox) for ax in self.ax]

        # Initialize buffers
        self.data_buffer = np.zeros((self.NUM_CHANNELS, self.BUFFER_SIZE))
        self.buffers = {
            ch: {
                'alpha': np.zeros(self.BUFFER_SIZE),
                'beta': np.zeros(self.BUFFER_SIZE),
                'gamma': np.zeros(self.BUFFER_SIZE)
            }
            for ch in range(self.NUM_CHANNELS)
        }

        self.enable = 1
        
        # Initialize serial connection
        try:
            self.ser = serial.Serial(self.COM_PORT, self.BAUD_RATE, timeout=1)
            self.ser.set_buffer_size(rx_size=8192, tx_size=8192)
        except serial.SerialException as e:
            print(f"Error: {e}")
            tk.messagebox.showerror("Serial Error", f"Could not open serial port: {e}")
            self.ser = None
            self.enable = 0

        # Initialize queues and events
        self._save_queue = queue.Queue(maxsize=1000)
        self.save_queues = {
            ch: {
                'alpha': queue.Queue(maxsize=1000),
                'beta': queue.Queue(maxsize=1000),
                'gamma': queue.Queue(maxsize=1000)
            }
            for ch in range(self.NUM_CHANNELS)
        }

        self.stop_event = threading.Event()
        self.pause_event = threading.Event()

        # Initialize CSV file
        self.initializeCSV()

        if self.enable:
            self.startAnimation()
            self.startThreads()

    def animate(self, frame):
        """Animation function for FuncAnimation"""
        # Restore background for each subplot
        for i, ax in enumerate(self.ax):
            self.fig.canvas.restore_region(self.backgrounds[i])
            
            # Update each line
            for wave_type in ['alpha', 'beta', 'gamma']:
            # for wave_type in ['alpha', 'beta']:
                line = self.lines[i][wave_type]
                line.set_ydata(self.buffers[i][wave_type])
                ax.draw_artist(line)
            
            # Blit the subplot
            self.fig.canvas.blit(ax.bbox)

        if self.first_data_time is not None and self.first_plot_time is None:
            self.first_plot_time = time.time()
            latency = self.first_plot_time - self.first_data_time
            print(f"First plot update at: {self.first_plot_time}")
            print(f"Data acquisition to first plot latency: {latency:.3f} seconds")

    def startAnimation(self):
        """Start the animation"""
        self.anim = animation.FuncAnimation(
            self.fig,
            self.animate,
            interval=self.UPDATE_INTERVAL,
            blit=False,  # We're handling our own blitting
            cache_frame_data=False
        )

    def startThreads(self):
        """Start the read and save threads"""
        self.read_thread = threading.Thread(target=self.readSerialData)
        self.save_thread = threading.Thread(target=self.saveDataToFile)
        
        self.read_thread.start()
        self.save_thread.start()

    def get_wave_name(self, wave_type):
        """Map wave type to wave name."""
        return {0: 'alpha', 1: 'beta', 2: 'gamma'}.get(wave_type)

    def readSerialData(self):
        """Read data from serial in a separate thread"""
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
                        
                        if wave_name == 'alpha':
                            adjusted_data = (np.array(data) * 3) - 50000
                        elif wave_name == 'beta':
                            adjusted_data = (np.array(data) * 2) 
                        elif wave_name == 'gamma':
                            adjusted_data = (np.array(data) * 1.5) 
                            
                        buffer[-128:] = adjusted_data

                        try:
                            save_data = {
                                'timestamp': time.time(),
                                'samples': list(adjusted_data)
                            }
                            self.save_queues[channel][wave_name].put_nowait(save_data)
                        except queue.Full:
                            pass

    def initializeCSV(self):
        """Initialize the CSV file with clear column headers"""
        try:
            with open(self.FILENAME, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Create descriptive headers
                headers = ['Timestamp']
                
                for ch in range(self.NUM_CHANNELS):
                    headers.extend([
                        f'Ch{ch}_Alpha',
                        f'Ch{ch}_Beta',
                        f'Ch{ch}_Gamma'
                    ])
                
                writer.writerow(headers)
                
        except Exception as e:
            print(f"Error initializing CSV: {e}")

    def saveDataToFile(self):
        """Save data to CSV file in a separate thread"""
        while not self.stop_event.is_set():
            try:
                # Create a dictionary to hold the latest data for each channel and wave type
                current_data = {
                    ch: {
                        'alpha': None,
                        'beta': None,
                        'gamma': None
                    }
                    for ch in range(self.NUM_CHANNELS)
                }
                
                # Collect the latest data from all queues
                for ch in range(self.NUM_CHANNELS):
                    for wave_type in ['alpha', 'beta', 'gamma']:
                        try:
                            if not self.save_queues[ch][wave_type].empty():
                                while True:
                                    data = self.save_queues[ch][wave_type].get_nowait()
                                    if data != 0:
                                        break
                                             
                                current_data[ch][wave_type] = data
                        except queue.Empty:
                            continue
                
                # Check if we have data to save
                has_data = any(
                    any(data is not None for data in wave_types.values())
                    for wave_types in current_data.values()
                )
                
                if has_data:
                    # Get current timestamp
                    timestamp = time.time()
                    
                    # Prepare row for CSV
                    row = [timestamp]
                    
                    # Add data for each channel and wave type
                    for ch in range(self.NUM_CHANNELS):
                        for wave_type in ['alpha', 'beta', 'gamma']:
                            data = current_data[ch][wave_type]
                            if data is not None:
                                # Calculate mean of the samples
                                mean_value = np.mean(data['samples'])
                                row.append(mean_value)
                            else:
                                row.append(None)  # or 0, depending on your preference
                    
                    # Write to CSV file
                    with open(self.FILENAME, 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(row)
                
                # Small sleep to prevent CPU overload
                time.sleep(0.01)
                
            except Exception as e:
                print(f"Error in save thread: {e}")
                time.sleep(0.1)

    def cleanup(self):
        """Safe cleanup of threads and resources"""
        print("Starting cleanup...")
        
        # Signal threads to stop
        self.stop_event.set()
        
        # Save any remaining data in queues
        try:
            self.save_remaining_data()
        except Exception as e:
            print(f"Error saving remaining data: {e}")
        
        # Safely join threads if they exist
        if hasattr(self, 'read_thread') and self.read_thread:
            if self.read_thread.is_alive():
                print("Waiting for read thread to finish...")
                self.read_thread.join(timeout=2)
                
        if hasattr(self, 'save_thread') and self.save_thread:
            if self.save_thread.is_alive():
                print("Waiting for save thread to finish...")
                self.save_thread.join(timeout=2)
        
        # Close serial port if it exists and is open
        if hasattr(self, 'ser') and self.ser and self.ser.is_open:
            print("Closing serial port...")
            self.ser.close()
            
        print("Cleanup complete")

    def save_remaining_data(self):
        """Save any remaining data in queues before shutdown"""
        remaining_data = {
            ch: {'alpha': [], 'beta': [], 'gamma': []}
            for ch in range(self.NUM_CHANNELS)
        }
        
        # Collect remaining data from queues
        for ch in range(self.NUM_CHANNELS):
            for wave_type in ['alpha', 'beta', 'gamma']:
                while True:
                    try:
                        data = self.save_queues[ch][wave_type].get_nowait()
                        remaining_data[ch][wave_type].append(data)
                    except queue.Empty:
                        break
        
        # Save remaining data
        if any(any(len(wave) > 0 for wave in waves.values()) 
            for waves in remaining_data.values()):
            current_time = time.time()
            with open(self.FILENAME, 'a', newline='') as f:
                writer = csv.writer(f)
                row = [current_time]
                for ch in range(self.NUM_CHANNELS):
                    for wave in ['alpha', 'beta', 'gamma']:
                        if remaining_data[ch][wave]:
                            row.extend(remaining_data[ch][wave][-1]['samples'])
                        else:
                            row.extend([0] * 64)  # Pad with zeros if no data
                writer.writerow(row)

    def __del__(self):
        """Safe destructor"""
        try:
            self.cleanup()
        except Exception as e:
            print(f"Error during cleanup: {e}")