import numpy as np

def get_chromagram(spectrogram, sample_rate, tuning_bins=5):
    window_size = spectrogram.shape[0]

