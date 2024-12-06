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
        self.data = None

        self.benchmarkMenu()

    def browseFiles(self):
        """Browse files to load data"""
        self.filename = filedialog.askopenfilename(
            initialdir = "/",
            title = "Select a File",
            filetypes = (("CSV files", "*.csv*"), ("all files", "*.*"))
        )
        self.label_file_explorer.configure(text="File Opened: "+self.filename)
        self.loadFromFile(self.filename)
    
    def loadFromFile(self, filename):
        """Load data from file"""
        try:
            self.data = {
                'timestamps': [],
                'channels': {}
            }
            
            with open(filename, 'r') as file:
                reader = csv.reader(file)
                header = next(reader)  # Skip header row
                
                # Initialize data structure
                num_channels = (len(header) - 1) // 3  # Subtract timestamp column and divide by 3 wave types
                for ch in range(num_channels):
                    self.data['channels'][f'ch{ch}'] = {
                        'alpha': [],
                        'beta': [],
                        'gamma': []
                    }
                
                past_alpha = 0
                past_beta = 0
                past_gamma = 0

                # Process each row
                for row in reader:
                    if not row or len(row) < 2:  # Skip empty rows
                        continue
                    
                    try:
                        # Get timestamp
                        timestamp = float(row[0])
                        self.data['timestamps'].append(timestamp)
                        
                        # Process each channel's data
                        for ch in range(num_channels):
                            base_idx = 1 + (ch * 3)  # Start after timestamp, 3 values per channel
                            if base_idx + 2 < len(row):  # Ensure we have all three values
                                try:
                                    alpha = float(row[base_idx]) if row[base_idx] and row[base_idx].lower() != 'none' else past_alpha
                                    beta = float(row[base_idx + 1]) if row[base_idx + 1] and row[base_idx + 1].lower() != 'none' else past_beta
                                    gamma = float(row[base_idx + 2]) if row[base_idx + 2] and row[base_idx + 2].lower() != 'none' else past_gamma

                                    if alpha:
                                        past_alpha = alpha
                                    if beta:
                                        past_beta = beta
                                    if gamma:
                                        past_gamma = gamma
                                    
                                    self.data['channels'][f'ch{ch}']['alpha'].append(alpha)
                                    self.data['channels'][f'ch{ch}']['beta'].append(beta)
                                    self.data['channels'][f'ch{ch}']['gamma'].append(gamma)
                                except ValueError as ve:
                                    print(f"Value error in row {len(self.data['timestamps'])}, channel {ch}: {ve}")
                                    # Append zeros for invalid values
                                    self.data['channels'][f'ch{ch}']['alpha'].append(0)
                                    self.data['channels'][f'ch{ch}']['beta'].append(0)
                                    self.data['channels'][f'ch{ch}']['gamma'].append(0)
                    except Exception as row_error:
                        print(f"Error processing row: {row_error}")
                        continue
            
            self.plotData()

        except Exception as e:
            print(f"Error loading file: {e}")
            traceback.print_exc()
            tk.messagebox.showerror("File Error", f"Could not load file: {e}")
    
    def plotData(self):
        """Plot the loaded data"""
        if not self.data:
            print("No data to plot")
            return

        try:
            if self.fig is None:
                num_channels = len(self.data['channels'])
                self.fig = plt.Figure(figsize=(50, 20), dpi=100, facecolor='#141414')
                self.ax = [self.fig.add_subplot(num_channels, 1, i+1) for i in range(num_channels)]

                self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
                self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

                toolbar = NavigationToolbar2Tk(self.canvas, self.root)
                toolbar.update()
                self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

            # Plot data for each channel
            colors = {'alpha': 'cyan', 'beta': 'magenta', 'gamma': 'yellow'}
            
            for i, (channel, waves) in enumerate(sorted(self.data['channels'].items())):
                ax = self.ax[i]
                ax.clear()
                ax.set_facecolor('#141414')
                
                # Convert timestamps to seconds for x-axis
                time_seconds = [t - self.data['timestamps'][0] for t in self.data['timestamps']]
                
                # Plot each wave type
                for wave_type, wave_data in waves.items():
                    ax.plot(time_seconds, wave_data,
                           color=colors[wave_type],     
                           label=f'{wave_type.capitalize()}',
                           alpha=0.8,
                           linewidth=1)
                
                ax.set_title(f'Channel {channel[-1]} Data', color='white', pad=20)
                ax.set_xlabel('Time (seconds)', color='white')
                ax.set_ylabel('Amplitude', color='white')
                
                ax.tick_params(axis='both', colors='white')
                ax.grid(True, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)
                ax.legend(loc='upper right')
                
                # Set reasonable y-axis limits
                ax.set_ylim(-1000, 40000)

            self.fig.tight_layout()
            self.canvas.draw()

        except Exception as e:
            print(f"Error plotting data: {e}")
            traceback.print_exc()

    def benchmarkMenu(self):
        """Create the benchmark menu"""
        self.label_file_explorer = Label(self.root, text="File Explorer using Tkinter")
        self.buttons.createButton(self.root, "Explore", self.browseFiles)