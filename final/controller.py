from imports import *

class Controller():
    def __init__(self, root):
        """Initialize BCI Controller"""
        # Create a new frame inside the main window
        self.frame = ttk.Frame(root)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Serial configuration
        self.COM_PORT = 'COM7'                         
        self.BAUD_RATE = 115200                         
        self.SAMPLE_RATE = 18000                        
        self.NUM_CHANNELS = 1                  
        self.BUFFER_SIZE = 5000                         
        self.Y_MIN = -1000                              
        self.Y_MAX = 60000                              
        
        # Initialize control variables
        self.average = 0
        self.averagePeak = 0
        self.first_data_time = None
        self.enable = 1
        
        # Map channels and wave types to keyboard actions
        # self.key_mappings = {
        #     (0, 'alpha'): 'space',
        #     (0, 'beta'): 'space',
        #     (0, 'gamma'): 'space'
        # }
        
        # Create main feedback container
        self.feedback_container = ttk.Frame(self.frame)
        self.feedback_container.pack(fill=tk.X, padx=10, pady=5)
        
        self.create_probe_menu()

        # Create indicators frame
        self.indicators_frame = ttk.Frame(self.feedback_container)
        self.indicators_frame.pack(fill=tk.X, pady=5)
        
        # Create indicators for each wave type
        self.indicators = {}
        colors = {'alpha': 'blue', 'beta': 'green', 'gamma': 'red'}
        
        for ch in range(self.NUM_CHANNELS):
            channel_frame = ttk.Frame(self.indicators_frame)
            channel_frame.pack(side=tk.LEFT, padx=10)
            
            ttk.Label(channel_frame, text=f"Channel {ch}").pack()
            
            for wave_type in ['alpha', 'beta', 'gamma']:
                frame = ttk.Frame(channel_frame)
                frame.pack(pady=2)
                
                # Create indicator canvas
                indicator = tk.Canvas(frame, width=20, height=20)
                indicator.create_oval(2, 2, 18, 18, fill='gray', tags='indicator')
                indicator.pack(side=tk.LEFT)
                
                # Changed this part - use get_current_mapping instead of key_mappings.get
                key = self.get_current_mapping(ch, wave_type)
                label = ttk.Label(frame, text=f"{wave_type} ({key})")
                label.pack(side=tk.LEFT, padx=5)
                
                self.indicators[(ch, wave_type)] = indicator
        
        

        # Create text log frame
        self.log_frame = ttk.Frame(self.feedback_container)
        self.log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Text widget for logging
        self.log_text = tk.Text(self.log_frame, height=10, width=50)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar for text widget
        scrollbar = ttk.Scrollbar(self.log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        # Add calibration button
        self.calibrate_button = ttk.Button(self.feedback_container, 
                                         text="Start Calibration", 
                                         command=self.calibration)
        self.calibrate_button.pack(pady=5)
        
        # Initialize buffers
        self.buffers = {}
        self.sample_counters = {}  # Track samples for each channel/wave type
        self.samples_before_check = 128  # Check every 3 chunks of 32 samples
        
        for ch in range(self.NUM_CHANNELS):
            self.buffers[ch] = {
                'alpha': np.zeros(self.BUFFER_SIZE),
                'beta': np.zeros(self.BUFFER_SIZE),
                'gamma': np.zeros(self.BUFFER_SIZE)
            }
            self.sample_counters[ch] = {
                'alpha': 0,
                'beta': 0,
                'gamma': 0
            }
        
        # Style configuration for indicators
        self.indicator_colors = {
            'inactive': 'gray',
            'alpha': 'blue',
            'beta': 'green',
            'gamma': 'red'
        }
        
        # Initialize calibration variables
        self.thresholds = {}
        self.resting_values = {}
        self.impulse_values = {}
        self.calibrated = False
        
        # Timing settings
        self.last_trigger_time = {}
        self.debounce_time = 0.3  # seconds
        self.indicator_reset_time = 0.2  # seconds
        
        for ch in range(self.NUM_CHANNELS):
            self.thresholds[ch] = {
                'alpha': 0,
                'beta': 0,
                'gamma': 0
            }
            self.resting_values[ch] = {
                'alpha': [],
                'beta': [],
                'gamma': []
            }
            self.impulse_values[ch] = {
                'alpha': [],
                'beta': [],
                'gamma': []
            }
            self.last_trigger_time[(ch, 'alpha')] = 0
            self.last_trigger_time[(ch, 'beta')] = 0
            self.last_trigger_time[(ch, 'gamma')] = 0
        
        
        try:
            self.ser = serial.Serial(self.COM_PORT, self.BAUD_RATE, timeout=1)
            self.ser.set_buffer_size(rx_size=8192, tx_size=8192)
            self.log_message(f"Successfully connected to {self.COM_PORT}")  # Log to GUI
        except serial.SerialException as e:
            self.log_message(f"Serial Error: {e}")  # Log to GUI
            messagebox.showerror("Serial Error", f"Could not open serial port: {e}")
            self.ser = None
            self.enable = 0

        self.log_message(f"Enable state: {self.enable}")

        self.stop_event = threading.Event()

        self.calibration_in_progress = False

        # Start threads automatically
        if self.enable:
            self.startThreads()

    def create_probe_menu(self):
        """Create a menu for selecting probe location and mapping"""
        # Create probe menu frame
        self.probe_frame = ttk.Frame(self.feedback_container)
        self.probe_frame.pack(fill=tk.X, pady=5)
        
        probe_label = ttk.Label(self.probe_frame, text="Select Probe Location:")
        probe_label.pack(side=tk.LEFT, padx=5)
        
        self.probe_locations = {
            "C3/4 - Right/Left Hand Movement": {
                (0, 'alpha'): 'space',  # Lighter movements
                (0, 'beta'): 'enter',   # Medium movements
                (0, 'gamma'): 'esc'     # Strong movements
            },
            "O1/O2 - Visual": {
                (0, 'alpha'): 'tab',  # Eyes closed
                (0, 'beta'): 'space',     # Visual focus
                (0, 'gamma'): 'backspace'   # High visual attention
            },
            "F3/F4 - Concentration": {
                (0, 'alpha'): 'left',   # Light focus
                (0, 'beta'): 'space',   # Medium focus
                (0, 'gamma'): 'right'   # High focus
            },
            "Fp1/Fp2 - Eye Movement": {
                (0, 'alpha'): 'up',     # Light blinks
                (0, 'beta'): 'space',   # Strong blinks
                (0, 'gamma'): 'down'    # Extended blinks
            }
        }
        
        probe_selection_made = tk.BooleanVar(value=False)
        
        def on_selection(event):
            self.key_mappings = self.probe_locations[probe_dropdown.get()]
            probe_selection_made.set(True)
        
        probe_dropdown = ttk.Combobox(self.probe_frame, 
                                    values=list(self.probe_locations.keys()),
                                    state='readonly',
                                    width=30)
        probe_dropdown.pack(side=tk.LEFT, padx=5)
        probe_dropdown.bind('<<ComboboxSelected>>', on_selection)
        
        # Wait for selection
        self.frame.wait_variable(probe_selection_made)

    def get_current_mapping(self, ch, wave_type):
        """Get the current key mapping for a channel and wave type"""
        return self.key_mappings.get((ch, wave_type), 'none')

    def update_key_mappings(self):
        """Update key mappings based on selected probe location"""
        selected_location = self.probe_var.get()
        self.key_mappings = self.probe_locations[selected_location]
        
        self.log_message(f"\nUpdated mappings for {selected_location}:")
        for (ch, wave), key in self.key_mappings.items():
            self.log_message(f"Channel {ch} {wave}: mapped to '{key}'")

    def set_indicator(self, channel, wave_type, active=True):
        """Set the state of an indicator"""
        indicator = self.indicators.get((channel, wave_type))
        if indicator:
            color = self.indicator_colors[wave_type] if active else self.indicator_colors['inactive']
            indicator.itemconfig('indicator', fill=color)
            
            if active:
                # Schedule indicator reset
                self.frame.after(int(self.indicator_reset_time * 1000), 
                              lambda: self.set_indicator(channel, wave_type, False))

    def log_message(self, message):
        """Add message to log text widget and scroll to bottom"""
        self.frame.after(0, lambda: self._update_log(message))

    def _update_log(self, message):
        """Update log text widget (called from main thread)"""
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)

    def startThreads(self):
        """Start the read thread"""
        try:
            self.log_message("Creating read thread...")
            self.read_thread = threading.Thread(target=self.readSerialData)
            self.read_thread.daemon = True
            self.read_thread.start()
            self.log_message("Read thread started")
            
            # Verify thread is alive
            if self.read_thread.is_alive():
                self.log_message("Thread is alive!")
            else:
                self.log_message("Thread failed to start!")
        except Exception as e:
            self.log_message(f"Error starting thread: {e}")

    # def calibration(self):
    #     """Run calibration sequence to set thresholds"""
    #     self.calibrate_button.configure(state='disabled')
    #     self.log_message("Starting calibration sequence...")
    #     self.calibrated = False
        
    #     # Step 1: Record resting state
    #     self.log_message("Please remain relaxed for 5 seconds to record baseline...")
    #     start_time = time.time()
        
    #     while time.time() - start_time < 5:
    #         for ch in range(self.NUM_CHANNELS):
    #             for wave_type in ['alpha', 'beta', 'gamma']:
    #                 self.resting_values[ch][wave_type].extend(self.buffers[ch][wave_type][-32:])
    #         time.sleep(0.1)
        
    #     # Step 2: Record impulse state
    #     self.log_message("\nNow, please generate 3 strong impulses when prompted...")
    #     for i in range(3):
    #         self.log_message(f"\nPrepare for impulse {i+1}...")
    #         time.sleep(2)
    #         self.log_message("Generate impulse NOW!")
            
    #         start_time = time.time()
    #         while time.time() - start_time < 1:
    #             for ch in range(self.NUM_CHANNELS):
    #                 for wave_type in ['alpha', 'beta', 'gamma']:
    #                     self.impulse_values[ch][wave_type].extend(self.buffers[ch][wave_type][-32:])
    #             time.sleep(0.1)
            
    #         self.log_message("Impulse recorded.")
    #         time.sleep(1)
        
    #     self._calculate_thresholds()
    #     self.calibrated = True
    #     self.log_message("\nCalibration complete!")
        
    #     for ch in range(self.NUM_CHANNELS):
    #         for wave_type in ['alpha', 'beta', 'gamma']:
    #             self.log_message(f"Channel {ch} {wave_type} threshold: {self.thresholds[ch][wave_type]:.2f}")
        
    #     self.calibrate_button.configure(state='normal')

    def calibration(self):
        """Run calibration sequence to set thresholds"""
        if self.calibration_in_progress:
            return  # Don't start a new calibration if one is already running
            
        self.calibration_in_progress = True
        self.calibrate_button.configure(state='disabled')
        self.calibrated = False
        
        # Reset all calibration values
        for ch in range(self.NUM_CHANNELS):
            for wave_type in ['alpha', 'beta', 'gamma']:
                self.resting_values[ch][wave_type] = []
                self.impulse_values[ch][wave_type] = []
        
        # Calibration state variables
        self.cal_state = 'baseline'
        self.cal_start_time = time.time()
        self.current_impulse = 0
        self.collecting_impulse = False
        
        def calibration_step():
            current_time = time.time()
            
            if self.cal_state == 'baseline':
                if not hasattr(self, 'baseline_started'):
                    self.log_message("Starting calibration sequence...")
                    self.log_message("Please remain relaxed for 5 seconds to record baseline...")
                    self.baseline_started = True
                    
                if current_time - self.cal_start_time < 5:
                    # Collect baseline data
                    for ch in range(self.NUM_CHANNELS):
                        for wave_type in ['alpha', 'beta', 'gamma']:
                            self.resting_values[ch][wave_type].extend(self.buffers[ch][wave_type][-32:])
                    self.frame.after(100, calibration_step)
                else:
                    self.cal_state = 'impulse_prep'
                    self.cal_start_time = current_time
                    calibration_step()
                    
            elif self.cal_state == 'impulse_prep':
                self.log_message(f"\nPrepare for impulse {self.current_impulse + 1}...")
                self.cal_state = 'impulse_wait'
                self.cal_start_time = current_time
                self.frame.after(2000, calibration_step)
                
            elif self.cal_state == 'impulse_wait':
                self.log_message("Generate impulse NOW!")
                self.cal_state = 'impulse_collect'
                self.cal_start_time = current_time
                calibration_step()
                
            elif self.cal_state == 'impulse_collect':
                if current_time - self.cal_start_time < 1:
                    # Collect impulse data
                    for ch in range(self.NUM_CHANNELS):
                        for wave_type in ['alpha', 'beta', 'gamma']:
                            self.impulse_values[ch][wave_type].extend(self.buffers[ch][wave_type][-32:])
                    self.frame.after(100, calibration_step)
                else:
                    self.current_impulse += 1
                    if self.current_impulse < 3:
                        self.cal_state = 'impulse_prep'
                        self.cal_start_time = current_time
                        self.frame.after(1000, calibration_step)
                    else:
                        self.cal_state = 'complete'
                        calibration_step()
                        
            elif self.cal_state == 'complete':
                self._calculate_thresholds()
                self.calibrated = True
                self.log_message("\nCalibration complete!")
                
                for ch in range(self.NUM_CHANNELS):
                    for wave_type in ['alpha', 'beta', 'gamma']:
                        self.log_message(f"Channel {ch} {wave_type} threshold: {self.thresholds[ch][wave_type]:.2f}")
                
                self.calibrate_button.configure(state='normal')
                # Clear calibration state
                delattr(self, 'cal_state')
                delattr(self, 'baseline_started')
        
        # Start the calibration seque 
        calibration_step()

    def _calculate_thresholds(self):
        """Calculate thresholds based on calibration data"""
        for ch in range(self.NUM_CHANNELS):
            for wave_type in ['alpha', 'beta', 'gamma']:
                resting_mean = mean(self.resting_values[ch][wave_type])
                resting_std = stdev(self.resting_values[ch][wave_type])
                impulse_mean = mean(self.impulse_values[ch][wave_type])
                
                self.thresholds[ch][wave_type] = (resting_mean + impulse_mean) / 2 + (3 * resting_std)

    def check_impulses(self, channel, wave_type):
        """Check for impulses and trigger keyboard events"""
        if not self.calibrated:
            return
            
        current_time = time.time()
        
        # Get the latest readings for specific channel and wave type
        recent_values = self.buffers[channel][wave_type][-32:]
        signal_strength = max(recent_values)
        
        # Check if signal exceeds threshold and debounce time has passed
        if signal_strength > self.thresholds[channel][wave_type]:
            key = self.key_mappings.get((channel, wave_type))
            if key and (current_time - self.last_trigger_time[(channel, wave_type)]) > self.debounce_time:
                keyboard.press_and_release(key)
                self.last_trigger_time[(channel, wave_type)] = current_time
                self.log_message(f"Impulse detected on channel {channel} {wave_type} - Triggered key: {key}")
                self.frame.after(0, lambda ch=channel, wt=wave_type: self.set_indicator(ch, wt, True))

    def get_wave_name(self, wave_type):
        """Map wave type to wave name."""
        return {0: 'alpha', 1: 'beta', 2: 'gamma'}.get(wave_type)

    def readSerialData(self):
        """Read data from serial in a separate thread"""
        frame_size = 260

        # self.log_message("Read thread function entered")
        print("Read thread function entered")
        while not self.stop_event.is_set():
            # self.log_message("Checking serial port...")
            # print("fire")
            # print(f"Bytes in waiting: {self.ser.in_waiting}")
            if self.ser is not None:
                # print("testing")
                # if self.ser.in_waiting > 0:
                    # self.log_message(f"Bytes waiting: {self.ser.in_waiting}")

                if self.ser.in_waiting >= frame_size:
                    # print("fire2")
                    if self.first_data_time is None:
                        self.first_data_time = time.time()
                        self.log_message(f"First data received at: {self.first_data_time}")

                    frame = self.ser.read(frame_size)
                    data = struct.unpack('<130H', frame)

                    header = data[0]
                    id = data[1]
                    data = data[2:]

                    channel = (id // 3)
                    wave_type = id % 3

                    # print(f"Channel: {channel}, Wave Type: {wave_type}, Data: {data[0:9]}")
                    
                    if header == 0 and channel in self.buffers:
                        wave_name = self.get_wave_name(wave_type)

                        if wave_name:
                            buffer = self.buffers[channel][wave_name]
                            buffer[:-128] = buffer[128:]
                            buffer[-128:] = data
                            
                            # Increment sample counter
                            self.sample_counters[channel][wave_name] += 32
                            
                            # Check if we've collected enough samples
                            if self.sample_counters[channel][wave_name] >= self.samples_before_check:
                                self.check_impulses(channel, wave_name)
                                self.sample_counters[channel][wave_name] = 0

    def cleanup(self):
        """Safe cleanup of threads and resources"""
        self.log_message("Starting cleanup...")
        
        self.stop_event.set()
        
        if hasattr(self, 'read_thread') and self.read_thread:
            if self.read_thread.is_alive():
                self.log_message("Waiting for read thread to finish...")
                self.read_thread.join(timeout=2)
        
        if hasattr(self, 'ser') and self.ser and self.ser.is_open:
            self.log_message("Closing serial port...")
            self.ser.close()
            
        self.log_message("Cleanup complete")