import numpy as np
import scipy

def get_spectrogram(audio, window_size, hop_size, window_function=np.hanning):
    if audio.signal.shape[1] != 1:
        raise NotImplementedError('Only single-channel audio is supported for now')

    signal = audio.signal[:, 0]

    window = window_function(window_size)
    width = (len(signal) - window_size) // hop_size + 1
    spectrogram = np.zeros((window_size // 2, width))

    for i in xrange(0, width):
        windowed = signal[(i * hop_size) : (i * hop_size + window_size)] * window
        spectrum = abs(scipy.fft(windowed))
        spectrum = spectrum[0:len(spectrum) / 2]
        spectrogram[:, i] = spectrum

    return spectrogram
