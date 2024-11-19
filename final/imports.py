# imports.py
from button_styles import ButtonStyles
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import mne
from PIL import Image, ImageTk, ImageDraw 
import queue
from scipy.interpolate import interp1d
import serial
import struct
import threading
import time
import tkinter as tk
from tkinter.ttk import *
from tkinter import messagebox, filedialog, HORIZONTAL, ttk, Scale