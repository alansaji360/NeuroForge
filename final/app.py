from imports import *
from livePlot import LivePlot
from benchmark import Benchmark
from controller import Controller
from fft import Fourier

class App():
    def __init__(self):
        """Initialize the App object"""
        self.BG_COLOR = "#141414"
        
        self.root = None
        self.root = tk.Tk()
        self.root.geometry("1600x900")
        self.root.protocol("WM_DELETE_WINDOW", self.callback)
        
        self.root.configure(bg=self.BG_COLOR)

        self.plot = None
        self.benchmark = None
        self.controller = None
        self.fourier = None

        self.root.title("NeuroForge")
        self.root.iconbitmap("samurai.ico")
        self.root.resizable(True, True)
    
        self.marker = 1
        self.buttons = ButtonStyles(self.root)

        self.n_channels_slider = 1          

        self.mainMenu()

    def callback(self):
        """Callback function to handle window close event"""
        if self.marker == 0: 
            if self.plot is not None:
                self.plot.__del__()
            self.clearWindow()
            self.mainMenu();
        else:
            self.onExit()

    def clearWindow(self):
        """Clear the window of all widgets"""
        for widget in self.root.winfo_children():
            widget.destroy()

    def onExit(self):
        """Exit the application."""
        if self.plot is not None:
            self.plot.__del__()

        self.root.quit()
        exit()

    def toggleLivePlot(self):
        """Toggle the live plot window."""
        self.marker = 0
        self.buttons.stopGlowAnimation()
        n_channel = self.n_channels_slider.get()
        time.sleep(0.5)
        
        self.clearWindow()
        try:
            with open('waveform_data.csv', 'w') as file:
                file.truncate(0)
        except Exception as e:
            print(f"Error: {e}")
        print("waveform_data.csv: cleared")
        self.plot = LivePlot(self.root, n_channels=n_channel)

    def toggleBenchmark(self):
        """Toggle the benchmark window."""
        self.marker = 0
        self.buttons.stopGlowAnimation()
        time.sleep(0.5)
        self.clearWindow()
        self.benchmark = Benchmark(self.root)

    def toggleController(self):
        """Toggle the benchmark window."""
        self.marker = 0
        self.buttons.stopGlowAnimation()
        time.sleep(0.5)

        n_channel = self.n_channels_slider.get()
        self.clearWindow()
        self.controller = Controller(self.root, n_channels=self.n_channel)

    def toggleFFT(self):
        """Toggle the benchmark window."""
        self.marker = 0
        self.buttons.stopGlowAnimation()
        time.sleep(0.5)
        self.clearWindow()
        self.fourier = Fourier(self.root)

    def mainMenu(self):
        """Create the main menu."""
        # while(1):
        if self.marker == 0:
            self.marker = 1

        self.buttons.createGlowText(self.root, "NEUROFORGE", "#FF00FF", self.BG_COLOR, size=36)

        self.buttons.createButton(self.root, "NEUROVISUALIZATON",   self.toggleLivePlot)
        self.buttons.createButton(self.root, "NEUROBENCHMARK",   self.toggleBenchmark)
        self.buttons.createButton(self.root, "NEUROCONTROLLER",   self.toggleController)
        # self.buttons.createButton(self.root, "NEUROFFT",   self.toggleFFT)
        self.buttons.createButton(self.root, "NEUROEXIT",        exit)

        slider_label = tk.Label(self.root, text="SELECT NUMBER OF CHANNELS", bg=self.BG_COLOR, fg="white")
        slider_label.pack(pady=5)
        
        self.n_channels_slider = Scale(self.root, from_=1, to=4, orient=HORIZONTAL, bg=self.BG_COLOR, fg="white")
        self.n_channels_slider.set(1)  
        self.n_channels_slider.pack(pady=5)
        # print(self.n_channels_slider.get())
        
        self.root.mainloop()

if __name__ == "__main__":
    app = App()
    # app.root.mainloop()