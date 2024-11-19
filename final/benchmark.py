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
    
    def plotData(self):
        """Plot the loaded data"""
        if self.fig is None:
            self.fig = plt.Figure(figsize=(7, 4), dpi=100, facecolor='#141414')
            self.ax = self.fig.add_subplot(111)

            self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

            toolbar = NavigationToolbar2Tk(self.canvas, self.root)
            toolbar.update()
            self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        # self.ax.clear()

        # self.ax.plot(self.data, color='b')
        # self.ax.set_title('Loaded Data from File')
        # self.ax.set_xlabel('Samples')
        # self.ax.set_ylabel('Amplitude')

        # self.ax.set_xlim(0, len(self.data))  
        # self.ax.relim()  
        # self.ax.autoscale_view() 

        # self.canvas.draw()

        self.ax.clear()
        self.ax.set_facecolor('#141414') 

        self.ax.plot(self.data, color='cyan') 
        self.ax.set_title('Loaded Data from File', color='white')  
        self.ax.set_xlabel('Samples', color='white') 
        self.ax.set_ylabel('Amplitude', color='white') 

        self.ax.set_xlim(0, len(self.data) if len(self.data) > 0 else 1)
        self.ax.relim()
        self.ax.autoscale_view()

        self.ax.tick_params(axis='both', colors='white') 
        self.ax.grid(color='gray', linestyle='--', linewidth=0.5)  

        self.canvas.draw()

    def benchmarkMenu(self):
        """Create the benchmark menu."""
        self.label_file_explorer = Label(self.root, 
                                    text = "File Explorer using Tkinter")

        self.buttons.createButton(self.root, "Explore", self.browseFiles)