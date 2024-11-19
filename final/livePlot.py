from imports import *

class LivePlot():
    def __init__(self, root, n_channels = 1):
        """Initialize Live_Plot object"""
        self.root = root
        
        self.COM_PORT = 'COM5'                          # Change to your COM port
        self.BAUD_RATE = 115200                         # Change to the appropriate baud rate
        self.NUM_SAMPLES = 64                           # Number of bytes to read (32 bytes = 16 samples)
        self.SAMPLE_RATE = 18000                        # Define the sampling rate (Hz)
        self.NUM_CHANNELS = n_channels                  # Number of channels to read
        self.BUFFER_SIZE = 20480                        # Buffer size
        self.Y_MIN = -1000                              # Maximum y-axis value
        self.Y_MAX = 16000                               # Maximum y-axis value

        self.fig, self.ax = plt.subplots(self.NUM_CHANNELS, figsize=(50, 20), dpi=100)
        # if self.NUM_CHANNELS == 1:
        #             self.ax = [self.ax]  # Convert to list if only one channel

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
            self.buffers[ch] = {'alpha': [], 'beta': [], 'gamma': []} 

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
        
        self._queue = queue.Queue()

        self.data_queue = {
            ch: {
                'alpha': queue.Queue(),
                'beta': queue.Queue(),
                'gamma': queue.Queue()
            }
            for ch in range(self.NUM_CHANNELS)
        }
        # self.info = mne.create_info(ch_names=['Channel 1'], sfreq=self.SAMPLE_RATE, ch_types=['eeg'])
        # self.raw = mne.io.RawArray(self.data_buffer, self.info)

        self.stop_event = threading.Event()  # Event to stop the thread
        self.pause_event = threading.Event()  # Event to pause the thread

        if self.enable:
            self.startThreads()
            self.updatePlot()

    def startThreads(self):
        """Start the read and save threads"""
        self.read_thread = threading.Thread(target=self.readSerialData)
        self.save_thread = threading.Thread(target=self.saveDataToFile)
        
        self.read_thread.start()
        self.save_thread.start()

    def readSerialData(self):
        """Read data from serial in a separate thread"""
        print("ddsf")
        frame_size = 36  # 3 uint16 (2 bytes each) * 6
        # frame_size = 48 # 4 uint16 (2 bytes each) * 6

        while not self.stop_event.is_set():
            # print("in while")
            if self.ser is not None:
                # print("in if")
                if self.ser.in_waiting >= frame_size:
                    # print('ds')
                    frame = self.ser.read(frame_size)
        

                    data = struct.unpack('<18H', frame) 
                    #data = struct.unpack('<24H', frame)

                    header = data[0]        # 1st uint16 for header
                    id = data[1]             # 2nd uint16 0-12 channel/wave type 
                    data = data[2:]         # Remaining 16 uint16 for sample values
                    
                    channel = (id // 3)
                    wave_type = id % 3
                    # Print debug information
                    # print("ds")
                    # print(f"Header: {id} Wave Type: {wave_type} Channel: {channel} Data: {data[0]}")

                    if header == 0 and channel in self.buffers:
                        wave_name = self.get_wave_name(wave_type)

                        if wave_name:
                            buffer = self.buffers[channel][wave_name]
                            # idx = self.sample_index[channel]

                            buffer[:-16] = buffer[16:]
                            buffer[-16:] = data
                            # buffer[idx:idx + 14] = samples
                            # self.sample_index[channel_id] = (idx + 14) % self.BUFFER_SIZE
                    # print(f"Buffers: {self.buffers[0]['alpha'][:10]}")
                        
                    # if header == 0:
                    #     # Update the buffers based on wave type
                    #     if wave_type == 1:  # Alpha wave
                    #         self.alpha_buffer[:-16] = self.alpha_buffer[16:]
                    #         self.alpha_buffer[-16:] = data

                    #     elif wave_type == 2:  # Beta wave
                    #         self.beta_buffer[:-16] = self.beta_buffer[16:]
                    #         self.beta_buffer[-16:] = data
                            
                    #     elif wave_type == 3:  # Gamma wave
                    #         self.gamma_buffer[:-16] = self.gamma_buffer[16:]
                    #         self.gamma_buffer[-16:] = data

                    # print("Current Buffers:")
                    # print(f"Alpha: {self.alpha_buffer[:10]}")  # Print first 10 values for quick check
                    # print(f"Beta: {self.beta_buffer[:10]}")
                    # print(f"Gamma: {self.gamma_buffer[:10]}")

    def get_wave_name(self, wave_type):
        """Map wave type to wave name."""
        return {0: 'alpha', 1: 'beta', 2: 'gamma'}.get(wave_type)
    
    def saveDataToFile(self):
        """Save all data to a single CSV file with clear separation."""
        with open('all_channels_data.csv', 'a') as f:
            # Write a header for the CSV file (only once)
            f.write("timestamp,channel,wave_type,samples\n")

            while not self.stop_event.is_set():
                for ch in range(self.NUM_CHANNELS):
                    for wave_type in ['alpha', 'beta', 'gamma']:
                        try:
                            # Get the samples from the queue
                            samples = self.data_queue[ch][wave_type].get(timeout=1)

                            # Format the row with channel, wave type, and sample data
                            row = (
                                f"{time.time()},{ch},{wave_type},"
                                + ','.join(map(str, samples))
                                + '\n'
                            )

                            f.write(row)
                            f.flush()

                        except queue.Empty:
                            continue
    
    def shift_and_update(self, buffer, new_value):
        """Shift data in the buffer and add the new value."""
        buffer[:-1] = buffer[1:]
        buffer[-1] = new_value

    def updatePlot(self):
        """Update the plot with the latest data"""
        # if self.sample_index > 0:
        #     self.ax.clear()

        #     self.ax.plot(self.data_buffer[0], color='b')
        #     self.ax.set_title(f"Channel {self.NUM_CHANNELS}")
        #     self.ax.set_xlabel('Samples')
        #     self.ax.set_ylabel('Amplitude')
        #     self.ax.set_ylim(-1000, 4500)

        #     self.canvas.draw()
        # self.root.after(1, self.updatePlot)

        # self.ax.clear()

        # # Plot each wave type
        # self.ax.plot(self.alpha_buffer, color='b', label="Alpha")
        # self.ax.plot(self.beta_buffer, color='g', label="Beta")
        # self.ax.plot(self.gamma_buffer, color='r', label="Gamma")

        # self.ax.set_title("Alpha, Beta, and Gamma Waves")
        # self.ax.set_xlabel('Samples')
        # self.ax.set_ylabel('Amplitude')
        # self.ax.set_ylim(self.Y_MIN, self.Y_MAX)
        # self.ax.legend()

        # self.canvas.draw()
        # self.root.after(1, self.updatePlot)

        # self.ax.clear()  # Clear the plot
        # if self.NUM_CHANNELS > 1:
        #     for ax in self.ax:
        #         ax.clear()  # Clear each subplot
        # else:
        #     self.ax.clear()  # Single channel case, self.ax is not an array


        # for ch in range(self.NUM_CHANNELS):
        #     alpha_data = self.buffers[ch]['alpha']
        #     beta_data = self.buffers[ch]['beta']
        #     gamma_data = self.buffers[ch]['gamma']

        #     # Plot each wave type with a different color
        #     self.ax.plot(alpha_data, label=f'Alpha (Ch {ch})', color='blue')
        #     self.ax.plot(beta_data, label=f'Beta (Ch {ch})', color='green')
        #     self.ax.plot(gamma_data, label=f'Gamma (Ch {ch})', color='red')

        # self.ax.set_ylim(-1000, 4500)  # Adjust based on signal range
        # self.ax.set_title("Real-Time EEG Data (Multi-Channel)")
        # self.ax.set_xlabel("Samples")
        # self.ax.set_ylabel("Amplitude")
        # self.ax.legend()
        # self.canvas.draw()

        # self.root.after(1, self.updatePlot)

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

        self.canvas.draw()
        self.root.after(1, self.updatePlot)

    def __del__(self):
        """Cleanup resources and stop threads"""
        self.stop_event.set()  
        if self.ser and self.ser.is_open:  
            self.ser.close()