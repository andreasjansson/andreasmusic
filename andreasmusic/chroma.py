import numpy as np
from andreasmusic import pitches

def get_chromagram(spectrogram, sample_rate, tuned=False, tuning_bins=5,
                   bins=12, base=pitches.C4.fq):
    window_size = spectrogram.shape[0] * 2
    length = spectrogram.shape[1]

    if tuned:
        bins *= tuning_bins

    chromagram = np.zeros((bins, length))

    # create an index array, mapping each spectrogram bin index
    # to a chromagram bin index
    indices = np.mod(
        np.round(bins *
                 np.log2(
                     (sample_rate / 2.0) *
                     np.arange(1, window_size / 2) /
                     (window_size / 2) / base
                 )
             ), bins).astype(int)
             
    indices = np.insert(indices, 0, 0) # arbitrarily set fq 0 to c

    for i in xrange(length):
        chromagram[:,i] = np.bincount(indices, weights=spectrogram[:,i])
        
    if tuned:
        chromagram = tune_chromagram(chromagram, tuning_bins)

    return chromagram

def tune_chromagram(chromagram, tuning_bins=5):
    assert chromagram.shape[0] % tuning_bins == 0

    tuning = _max_tuning_bin(chromagram, tuning_bins)

    actual_bins = chromagram.shape[0] / tuning_bins
    indices = _get_tuning_indices(actual_bins, tuning_bins, tuning)

    tuned = np.zeros((actual_bins, chromagram.shape[1]))
    for i in xrange(chromagram.shape[1]):
        tuned[:, i] = np.bincount(indices, weights=chromagram[:, i])

    return tuned

def _get_tuning_indices(actual_bins, tuning_bins, tuning):
    indices = np.repeat(np.arange(actual_bins), tuning_bins)
    roll = -((tuning_bins // 2 - tuning) % tuning_bins)
    indices = np.roll(indices, roll)
    return indices

def _max_tuning_bin(chromagram, tuning_bins):
    indices = np.tile(np.arange(tuning_bins), chromagram.shape[0] / tuning_bins)
    bin_sums = np.sum(chromagram, 1)
    tuning_sums = np.bincount(indices, weights=bin_sums)
    tuning = np.argmax(tuning_sums)
    return tuning
