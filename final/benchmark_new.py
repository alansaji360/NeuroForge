from imports import *

class Benchmark():
    def __init__(self, root):
        """Initialize Benchmark object"""
        self.root = root
        self.label_file_explorer = None
        self.fig = None
        self.axes = None
        self.canvas = None
        self.scrollbar = None
        
        self.SAMPLE_RATE = 18000
        self.NUM_CHANNELS = 4
        self.filename = ""
        
        # Dictionary to store data for each channel
        self.channel_data = {
            channel: {
                'alpha': [],
                'beta': [],
                'gamma': []
            } for channel in range(self.NUM_CHANNELS)
        }

        self.buttons = ButtonStyles(self.root)
        self.benchmarkMenu()

    def browseFiles(self):
        """Browse files to load data"""
        self.filename = filedialog.askopenfilename(
            initialdir="/",
            title="Select a File",
            filetypes=(
                ("CSV files", "*.csv*"),
                ("all files", "*.*")
            )
        )
        self.label_file_explorer.configure(text="File Opened: "+self.filename)
        self.loadFromFile(self.filename)
    
    def loadFromFile(self, filename):
        """Load data from file"""
        try:
            # Reset channel data
            self.channel_data = {
                channel: {
                    'alpha': [],
                    'beta': [],
                    'gamma': []
                } for channel in range(self.NUM_CHANNELS)
            }
            
            with open(filename, 'r') as file:
                # Skip header row
                header = next(file)
                
                for line in file:
                    values = line.strip().split(',')
                    timestamp = float(values[0])
                    
                    # Process each channel's data
                    data_index = 1  # Start after timestamp
                    for channel in range(self.NUM_CHANNELS):
                        for wave_type in ['alpha', 'beta', 'gamma']:
                            # Get the next 16 samples for this channel and wave type
                            samples = [float(val) for val in values[data_index:data_index + 16]]
                            self.channel_data[channel][wave_type].extend(samples)
                            data_index += 16
            
            self.plotData()

        except Exception as e:
            print(f"Error loading file: {e}")
            tk.messagebox.showerror("File Error", f"Could not load file: {e}")
    
    def plotData(self):
        """Plot the loaded data for all channels"""
        if self.fig is None:
            self.fig = plt.Figure(figsize=(12, 8), dpi=100, facecolor='#141414')
            self.axes = []
            
            # Create subplot for each channel
            for i in range(self.NUM_CHANNELS):
                ax = self.fig.add_subplot(self.NUM_CHANNELS, 1, i+1)
                self.axes.append(ax)
            
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

            toolbar = NavigationToolbar2Tk(self.canvas, self.root)
            toolbar.update()
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Plot data for each channel
        wave_colors = {'alpha': 'blue', 'beta': 'green', 'gamma': 'red'}
        
        for channel, ax in enumerate(self.axes):
            ax.clear()
            ax.set_facecolor('#141414')
            
            # Plot each wave type
            for wave_type, color in wave_colors.items():
                data = self.channel_data[channel][wave_type]
                if data:  # Only plot if we have data
                    ax.plot(data, color=color, label=wave_type, alpha=0.7)
            
            ax.set_title(f'Channel {channel + 1}', color='white')
            ax.set_xlabel('Samples', color='white')
            ax.set_ylabel('Amplitude', color='white')
            
            ax.tick_params(axis='both', colors='white')
            ax.grid(color='gray', linestyle='--', linewidth=0.5)
            ax.legend(loc='upper right')
            
            # Set reasonable limits
            ax.set_xlim(0, len(data) if data else 1)
            ax.relim()
            ax.autoscale_view()

        self.fig.tight_layout()  # Adjust subplot spacing
        self.canvas.draw()

    def benchmarkMenu(self):
        """Create the benchmark menu."""
        self.label_file_explorer = Label(
            self.root,
            text="File Explorer using Tkinter",
            fg='white',
            bg='#141414'
        )
        self.label_file_explorer.pack()

        self.buttons.createButton(self.root, "Explore", self.browseFiles)