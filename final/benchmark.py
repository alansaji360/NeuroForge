from imports import *
class Benchmark():
    def __init__(self, root):
        """Initialize Benchmark object"""
        self.root = root
        self.label_file_explorer = None
        self.fig = None
        self.ax = None
        self.canvas = None
        self.scrollbar = None
        
        self.SAMPLE_RATE = 18000
        self.filename = ""

        self.buttons = ButtonStyles(self.root)

        self.benchmarkMenu()

    def browseFiles(self):
        """Browse files to load data"""
        self.filename = filedialog.askopenfilename(initialdir = "/",
                                            title = "Select a File",
                                            filetypes = (("Excel files",
                                                            "*.csv*"),
                                                        ("all files",
                                                            "*.*")))
        self.label_file_explorer.configure(text="File Opened: "+self.filename)

        self.loadFromFile(self.filename)
    
    def loadFromFile(self, filename):
        """Load data from file"""
        try:
            with open(filename, 'r') as file:
                self.data = []
                for line in file:
                    self.data.extend([float(val) for val in line.strip().split(',')])   
            self.plotData()

        except Exception as e:
            print(f"Error loading file: {e}")
            tk.messagebox.showerror("File Error", f"Could not load file: {e}")
    
    def loadFromFile(self, filename):
        """Load data from file"""
        try:
            self.data = {
                'timestamps': [],
                'channels': {}
            }
            
            with open(filename, 'r') as file:
                # Read header first
                header = next(csv.reader(file))
                
                # Parse header to determine number of channels and waves
                # First column is timestamp
                channel_wave_columns = header[1:]
                
                # Initialize data structure based on header
                for col in channel_wave_columns:
                    # Parse column name (format: ch0_alpha_sample0, ch0_beta_sample0, etc.)
                    parts = col.split('_')
                    if len(parts) >= 2:
                        channel = parts[0]  # ch0, ch1, etc.
                        wave_type = parts[1]  # alpha, beta, gamma
                        
                        if channel not in self.data['channels']:
                            self.data['channels'][channel] = {}
                        
                        if wave_type not in self.data['channels'][channel]:
                            self.data['channels'][channel][wave_type] = []
                
                # Read data
                for row in csv.reader(file):
                    if not row:  # Skip empty rows
                        continue
                    
                    # First column is timestamp
                    self.data['timestamps'].append(float(row[0]))
                    
                    # Process each channel and wave type
                    current_col = 1
                    for channel in sorted(self.data['channels'].keys()):
                        for wave_type in ['alpha', 'beta', 'gamma']:
                            # Each wave type has 64 samples
                            wave_data = [float(x) for x in row[current_col:current_col + 64]]
                            self.data['channels'][channel][wave_type].extend(wave_data)
                            current_col += 64
            
            self.plotData()

        except Exception as e:
            print(f"Error loading file: {e}")
            tk.messagebox.showerror("File Error", f"Could not load file: {e}")
    
    def plotData(self):
        """Plot the loaded data"""
        if self.fig is None:
            # Create figure with subplots for each channel
            num_channels = len(self.data['channels'])
            self.fig = plt.Figure(figsize=(12, 4 * num_channels), dpi=100, facecolor='#141414')
            self.ax = [self.fig.add_subplot(num_channels, 1, i+1) for i in range(num_channels)]

            self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

            toolbar = NavigationToolbar2Tk(self.canvas, self.root)
            toolbar.update()
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Clear all subplots
        for axis in self.ax:
            axis.clear()
            axis.set_facecolor('#141414')

        # Plot data for each channel
        colors = {'alpha': 'cyan', 'beta': 'magenta', 'gamma': 'yellow'}
        
        for i, (channel, waves) in enumerate(sorted(self.data['channels'].items())):
            for wave_type, wave_data in waves.items():
                self.ax[i].plot(wave_data, 
                               color=colors[wave_type], 
                               label=f'{wave_type.capitalize()}',
                               alpha=0.8)
            
            self.ax[i].set_title(f'Channel {channel} Data', color='white')
            self.ax[i].set_xlabel('Samples', color='white')
            self.ax[i].set_ylabel('Amplitude', color='white')
            
            self.ax[i].tick_params(axis='both', colors='white')
            self.ax[i].grid(color='gray', linestyle='--', linewidth=0.5, alpha=0.5)
            self.ax[i].legend()

            # Set reasonable y-axis limits
            self.ax[i].set_ylim(-1000, 40000)  # Adjust these values based on your data range

        self.fig.tight_layout()
        self.canvas.draw()

    def benchmarkMenu(self):
        """Create the benchmark menu."""
        self.label_file_explorer = Label(self.root, 
                                    text = "File Explorer using Tkinter")

        self.buttons.createButton(self.root, "Explore", self.browseFiles)