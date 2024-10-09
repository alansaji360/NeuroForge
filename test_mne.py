import os
from copy import deepcopy
import numpy as np
import mne
import keyboard

sample_data_folder = mne.datasets.sample.data_path()
sample_data_raw_file = ("data_raw.fif")
# raw = mne.io.read_raw_fif(sample_data_raw_file)

# print(raw)
# print(raw.info)

raw = mne.io.read_raw_fif(sample_data_raw_file)

print(raw.info["bads"])

# raw.compute_psd(fmax=50).plot(picks="data", exclude="bads", amplitude=False)
# raw.plot()

# picks = mne.pick_channels_regexp(raw.ch_names, regexp="EEG 05.")
# raw.plot(order=picks, n_channels=len(picks))

# picks = mne.pick_channels_regexp(raw.ch_names, regexp="EEG 05.")
# raw.plot(order=picks, n_channels=len(picks))

raw.compute_psd(fmax=50).plot(picks="data", exclude="bads", amplitude=False)
fig = raw.plot(duration=5, n_channels=4, block = True)

for ax in fig.get_axes():
    # Set axis titles and labels
    ax.set_title("Custom Raw Data Plot", fontsize=14)
    ax.set_xlabel("Time (s)", fontsize=12)
    ax.set_ylabel("Amplitude (µV)", fontsize=12)

    # Set limits on x-axis and y-axis (optional)
    # ax.set_xlim([0, 5])  # Set x-axis limits (0 to 5 seconds)
    ax.set_ylim([0, 5000])  # Set y-axis limits (-100 to 100 µV)

    # Custom ticks and grid (optional)
    ax.grid(True)  # Enable grid
    ax.tick_params(axis='both', which='major', labelsize=10)  # Customize tick size

while True:
    key = keyboard.read_key()
    if key == 'enter':
        break