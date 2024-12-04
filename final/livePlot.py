from imports import *

class LivePlot():
    def __init__(self, root, n_channels = 1):
        """Initialize Live_Plot object"""
        self.root = root
        
        self.COM_PORT = 'COM6'                          # Change to your COM port
        self.BAUD_RATE = 115200                         # Change to the appropriate baud rate
        self.SAMPLE_RATE = 18000                        # Define the sampling rate (Hz)
        self.NUM_CHANNELS = n_channels                  # Number of channels to read
        self.BUFFER_SIZE = 5000                         # Buffer size
        self.Y_MIN = -1000                              # Maximum y-axis value
        self.Y_MAX = 60000                              # Maximum y-axis value
        self.FILENAME = 'waveform_data.csv'             # Filename to save data

        self.first_data_time = None
        self.first_plot_time = None
        
        self.fig, self.ax = plt.subplots(self.NUM_CHANNELS, figsize=(50, 20), dpi=100)
        if self.NUM_CHANNELS == 1:
                    self.ax = [self.ax]  # Convert to list if only one channel

        self.canvas = FigureCanvasTkAgg (self.fig, master=self.root)
        self.canvas.get_tk_widget().pack()
        
        # self.data_buffer = [np.zeros(100) for _ in range(self.NUM_CHANNELS)]  # Initialize buffers for 100 samples
        self.data_buffer = np.zeros((self.NUM_CHANNELS, self.BUFFER_SIZE))

        self.alpha_buffer = np.zeros(self.BUFFER_SIZE)
        self.beta_buffer = np.zeros(self.BUFFER_SIZE)
        self.gamma_buffer = np.zeros(self.BUFFER_SIZE)

        # self.buffers = {
        #     ch: {
        #         'alpha': np.zeros(self.BUFFER_SIZE),
        #         'beta': np.zeros(self.BUFFER_SIZE),
        #         'gamma': np.zeros(self.BUFFER_SIZE)
        #     }
        #     for ch in range(1 ,self.NUM_CHANNELS)
        # }

        self.buffers = {}

        for ch in range(self.NUM_CHANNELS):
            self.buffers[ch] = {
                'alpha': np.zeros(self.BUFFER_SIZE),
                'beta': np.zeros(self.BUFFER_SIZE),
                'gamma': np.zeros(self.BUFFER_SIZE)
            }

        self.enable = 1

        try:
            self.ser = serial.Serial(self.COM_PORT, self.BAUD_RATE, timeout=1)
            self.ser.set_buffer_size(rx_size=8192, tx_size=8192)
        except serial.SerialException as e:
            print(f"Error: {e}")
            tk.messagebox.showerror("Serial Error", f"Could not open serial port: {e}")
            self.ser = None
            self.enable = 0

        self.sample_index = [0] * 3
        # self.sample_index = {ch: 0 for ch in range(n_channels)}

        self.colors = {"alpha": "b", "beta": "g", "gamma": "r"}
        self.plot_alpha = False
        self.plot_beta = False
        self.plot_gamma = False

        self._save_queue = queue.Queue(maxsize=1000)
        self._latest_data = None

        self.file_handle = None
        self.csv_writer = None

        self.initializeCSV()

        self._queue = queue.Queue()

        self.save_queues = {
            ch: {
                'alpha': queue.Queue(maxsize=1000),
                'beta': queue.Queue(maxsize=1000),
                'gamma': queue.Queue(maxsize=1000)
            }
            for ch in range(self.NUM_CHANNELS)
        }
        # self.info = mne.create_info(ch_names=['Channel 1'], sfreq=self.SAMPLE_RATE, ch_types=['eeg'])
        # self.raw = mne.io.RawArray(self.data_buffer, self.info)

        self.stop_event = threading.Event()  # Event to stop the thread
        self.pause_event = threading.Event()  # Event to pause the thread

        if self.enable:
            self.updatePlot()
            self.startThreads()
            # time.sleep(1000) 
            

    def startThreads(self):
        """Start the read and save threads"""
        self.read_thread = threading.Thread(target=self.readSerialData)
        self.save_thread = threading.Thread(target=self.saveDataToFile)
        
        self.read_thread.start()
        # self.save_thread.start()

    def initializeCSV(self):
        """Initialize the CSV file with appropriate headers"""
        with open(self.FILENAME, 'w', newline='') as f:
            writer = csv.writer(f)
            # Write header row
            header = ['timestamp']
            for ch in range(self.NUM_CHANNELS):
                for wave in ['alpha', 'beta', 'gamma']:
                    header.extend([f'ch{ch}_{wave}_sample{i}' for i in range(64)])
            writer.writerow(header)

    def readSerialData(self):
        """Read data from serial in a separate thread"""
        frame_size = 68  # 66 uint16 (2 bytes each) 5

        while not self.stop_event.is_set():
            if self.ser is not None:
                if self.ser.in_waiting >= frame_size:
                    

                    #add the current time to queue
                    if self.first_data_time is None:
                        self.first_data_time = time.time()
                        print(f"First data received at: {self.first_data_time}")

                    frame = self.ser.read(frame_size)
                    data = struct.unpack('<34H', frame) 

                    header = data[0]        # 1st uint16 for header
                    id = data[1]            # 2nd uint16 0-12 channel/wave type 
                    data = data[2:]         # Remaining uint16 for sample values

                    channel = (id // 3)
                    wave_type = id % 3
                    
                    #  debug 
                    # print(f"Header: {id} Wave Type: {wave_type} Channel: {channel} Data: {data}")

                    if header == 0 and channel in self.buffers:
                        wave_name = self.get_wave_name(wave_type)

                        if wave_name:
                            buffer = self.buffers[channel][wave_name]

                            buffer[:-32] = buffer[32:]
                            buffer[-32:] = data

                            try:
                                save_data = {
                                    'timestamp': time.time(),
                                    'samples': list(data)  # Convert to list to ensure serializability
                                }
                                self.save_queues[channel][wave_name].put_nowait(save_data)
                            except queue.Full:
                                pass
                                # print(f"Queue full for channel {channel} {wave_name}")

    def get_wave_name(self, wave_type):
        """Map wave type to wave name."""
        return {0: 'alpha', 1: 'beta', 2: 'gamma'}.get(wave_type)
    
    def saveDataToFile(self):
        """Save data to CSV file in a separate thread"""
        last_save_time = None
        data_buffer = {}  # Temporary buffer to collect complete sets of data
        
        while not self.stop_event.is_set():
            try:
                current_time = time.time()
                
                # Initialize new timestamp in buffer if needed
                if last_save_time is None or current_time - last_save_time >= 0.1:  # Save every 100ms
                    last_save_time = current_time
                    data_buffer[current_time] = {
                        ch: {'alpha': None, 'beta': None, 'gamma': None}
                        for ch in range(self.NUM_CHANNELS)
                    }
                
                # Try to get data from all queues
                for ch in range(self.NUM_CHANNELS):
                    for wave_type in ['alpha', 'beta', 'gamma']:
                        try:
                            if self.save_queues[ch][wave_type].qsize() > 0:
                                data = self.save_queues[ch][wave_type].get_nowait()
                                # Store in the current time slot
                                data_buffer[current_time][ch][wave_type] = data['samples']
                        except queue.Empty:
                            continue
                
                # Check if we have complete data for any timestamp
                times_to_save = []
                for timestamp in data_buffer:
                    all_data_present = True
                    for ch in range(self.NUM_CHANNELS):
                        for wave_type in ['alpha', 'beta', 'gamma']:
                            if data_buffer[timestamp][ch][wave_type] is None:
                                all_data_present = False
                                break
                        if not all_data_present:
                            break
                            
                    if all_data_present:
                        times_to_save.append(timestamp)
                    elif current_time - timestamp > 5:  # Clean up old incomplete data
                        times_to_save.append(timestamp)
                
                # Save complete data sets
                for timestamp in times_to_save:
                    if all(all(data_buffer[timestamp][ch][wave] is not None 
                            for wave in ['alpha', 'beta', 'gamma'])
                        for ch in range(self.NUM_CHANNELS)):
                        with open(self.FILENAME, 'a', newline='') as f:
                            writer = csv.writer(f)
                            row = [timestamp]
                            for ch in range(self.NUM_CHANNELS):
                                for wave in ['alpha', 'beta', 'gamma']:
                                    row.extend(data_buffer[timestamp][ch][wave])
                            writer.writerow(row)
                    
                    del data_buffer[timestamp]
                
                # Small sleep to prevent high CPU usage
                time.sleep(0.001)
                
            except Exception as e:
                pass
                # print(f"Error saving data: {e}")/

    def updatePlot(self):
        """Update the plot with the latest data"""
        try:
            for ch, ax in enumerate(self.ax):
                # print(f"Channel {ch}")
                ax.clear()  # Clear the individual subplot
                
                alpha_data = self.buffers[ch]['alpha']
                beta_data = self.buffers[ch]['beta']
                gamma_data = self.buffers[ch]['gamma']

                # print(f"Alpha data (Ch {ch}): {self.buffers[ch]['alpha'][:10]}")
                # print(f"Beta data (Ch {ch}): {self.buffers[ch]['beta'][:10]}")
                # print(f"Gamma data (Ch {ch}): {self.buffers[ch]['gamma'][:10]}")

                # Plot each wave type
                ax.plot(alpha_data, label=f'Alpha (Ch {ch})', color='blue')
                ax.plot(beta_data, label=f'Beta (Ch {ch})', color='green')
                ax.plot(gamma_data, label=f'Gamma (Ch {ch})', color='red')

                ax.set_ylim(self.Y_MIN, self.Y_MAX)
                ax.set_title(f"Channel {ch + 1} Data")
                ax.set_xlabel("Samples")
                ax.set_ylabel("Amplitude")
                ax.legend(loc='upper right')

                if self.first_data_time is not None and self.first_plot_time is None:
                    self.first_plot_time = time.time()
                    latency = self.first_plot_time - self.first_data_time
                    print(f"First plot update at: {self.first_plot_time}")
                    print(f"Data acquisition to first plot latency: {latency:.3f} seconds")

            self.canvas.draw()
            self.root.after(10, self.updatePlot)
        except Exception as e:
            print(f"Error updating plot: {e}")

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