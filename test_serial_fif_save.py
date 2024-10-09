import mne

# Define the path to your .fif file
fif_file_path = 'data_raw.fif'  # Replace with your actual file path

# Load the .fif file
raw = mne.io.read_raw_fif(fif_file_path, preload=True)

# Print basic information about the data
print(raw.info)

# Show a summary of the channels
print(f"Channels: {raw.ch_names}")

# Display a plot of the data
raw.plot(duration=5, n_channels=30)