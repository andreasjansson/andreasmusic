# TODO: make it row-order instead of column order

import numpy as np
import scipy
import subprocess
from scipy.signal import argrelmax, medfilt, medfilt2d
from scipy.cluster.vq import kmeans, vq

from andreasmusic import util
from andreasmusic import harmonic_midi
from andreasmusic import pitches as apitches

def get_spectrogram(audio, window_size, hop_size, window_function=np.hanning, return_angles=False):
    if audio.signal.shape[1] != 1:
        raise NotImplementedError('Only single-channel audio is supported for now')

    signal = audio.signal[:, 0]

    window = window_function(window_size)
    length = (len(signal) - window_size) // int(hop_size) + 1
    if return_angles:
        spectrogram = np.zeros((length, window_size), dtype=np.complex)
    else:
        spectrogram = np.zeros((length, window_size // 2))

    for i in xrange(0, length):
        start = int(round(i * hop_size))

        windowed = signal[start:start + window_size] * window
        if len(windowed) < window_size:
            print len(windowed), window_size
            windowed = np.append(windowed, np.zeros(window_size - len(windowed)))

        fft = scipy.fft(windowed)
        if return_angles:
            spectrogram[i, :] = fft
        else:
            spectrogram[i, :] = np.abs(fft[:len(fft) / 2])

    return spectrogram

def get_variable_spectra(a, split_points):
    if a.signal.shape[1] != 1:
        raise NotImplementedError('Only single-channel audio is supported for now')

    signal = a.signal[:, 0]

    spectra = []
    split_points = np.append(split_points, len(a.signal))
    for t0, t1 in zip(split_points[:-1], split_points[1:]):
        spectra.append(scipy.fft(signal[int(t0):int(t1)]))
    return spectra

def filter_peaks(spectrogram):
    coords = argrelmax(spectrogram, order=20, axis=1)
    maxes = np.zeros(spectrogram.shape)
    maxes[coords] = spectrogram[coords]
    return maxes

def median_filter(s_or_a, order=11, p=2):

    if hasattr(s_or_a, 'signal'):
        a = s_or_a
        s = get_spectrogram(a, a.sample_rate / 10, a.sample_rate / 20, return_angles=True)
    else:
        a = None
        s = s_or_a

    harmonic = medfilt2d(np.abs(s), (abs(order), 1))
    percussive = medfilt2d(np.abs(s), (1, abs(order)))
    if order > 0:
        mask = harmonic ** p / (harmonic ** p + percussive ** p)
    else:
        mask = percussive ** p / (harmonic ** p + percussive ** p)
    masked = s * mask
    masked[np.isnan(masked)] = 0

    if a:
        masked_audio = get_audio(masked, a.sample_rate, a.sample_rate / 10, a.sample_rate / 20)
        return masked_audio
    else:
        return masked
    
def get_audio(spectrogram, sample_rate, window_size, hop_size):
    from andreasmusic import audio

    #spectrogram = np.hstack((spectrogram, spectrogram[:, ::-1]))

    window = 1 #np.hanning(window_size)
    signal = np.zeros(len(spectrogram) * hop_size + (window_size - hop_size))
    for i, t in enumerate(xrange(0, len(spectrogram) * hop_size, hop_size)):
        signal[t:t + window_size] += np.real(scipy.ifft(spectrogram[i])) * window

    return audio.Audio(signal[np.newaxis].T.astype(np.float32), sample_rate)



def overtones_to_spectrogram(overtones, sample_rate, window_size, gaussian_width=1.0/24):
    halfwin = window_size / 2.0
    length, n_pitches, n_harmonics = overtones.shape

    def f(x):
        return np.exp(-(np.linspace(-x, 1-x, halfwin) / (x * gaussian_width)) ** 2)

    spectrogram = np.zeros((len(overtones), int(halfwin)))

    for i in xrange(n_pitches):
        pitch = i + harmonic_midi.MIN_PITCH
        freq = apitches.C0.fq * 2 ** (pitch / 12.0)
        index = np.round(halfwin * freq / (sample_rate / 2))

        filterbank = np.array([
            f(x) for x in np.arange(index, index * (n_harmonics + 1), index) / halfwin
        ])
        #filterbank = (filterbank.T / np.sum(filterbank, 1)).T

        spectrogram += overtones[:, i, :].dot(filterbank)

    return spectrogram

def spectrogram_to_overtones(spectrogram, sample_rate, window_size, harmonics=16, gaussian_width=1.0/24):
    halfwin = window_size / 2.0

    def f(x):
        return np.exp(-(np.linspace(-x, 1-x, halfwin) / (x * gaussian_width)) ** 2)

    pitches = range(harmonic_midi.MIN_PITCH, harmonic_midi.MAX_PITCH)

    overtones = np.zeros((len(spectrogram), len(pitches), harmonics))

    for i, pitch in enumerate(pitches):
        freq = apitches.C0.fq * 2 ** (pitch / 12.0)
        index = np.round(halfwin * freq / (sample_rate / 2))

        filterbank = np.array([
            f(x) for x in np.arange(index, index * (harmonics + 1), index) / halfwin
        ])
        filterbank = (filterbank.T / np.sum(filterbank, 1)).T

        for t, s in enumerate(spectrogram):
            overtones[t, i, :] = np.sum(filterbank * s, 1)


    return overtones

def _get_centroid_mask(overtones):
    flat = overtones.reshape((len(overtones) * 48, overtones.shape[2]))
    f0flat = flat[np.argmax(flat, 1) == 0]
    f0flat = f0flat[np.max(f0flat, 1) > 0]
    f0flat = (f0flat.T / np.max(f0flat, 1)).T

    centroids, distortion = kmeans(f0flat, 24)
    codes, dists = vq(f0flat, centroids)
    #centroids = centroids[np.bincount(codes) > np.median(np.bincount(codes))]    
    flat_norm = (flat.T / np.max(flat, 1)).T
    codes, dists = vq(flat_norm, centroids)

    flat_filtered = np.copy(flat)

    for i, (s, c) in enumerate(zip(flat, codes)):
        if c < 0 or c > len(centroids):
            continue

        centroid = centroids[c]
        centroid_denorm = centroid * np.max(s)
        flat_filtered[i, 1:] -= centroid_denorm[1:]
        flat_filtered[i, 1:] = np.maximum(flat_filtered[i, 1:], 0)

    overtones_filtered = flat_filtered.reshape(overtones.shape)

    return overtones_filtered

def get_filterbank(i, halfwin=2048, gaussian_width=1.0/50, harmonics=50):
    i = float(i)

    def f(x):
        return np.exp(-(np.linspace(-x, 1-x, halfwin) / (x * gaussian_width)) ** 2)

    fb = np.array([
        f(x) for x in np.arange(i, i * (harmonics + 1), i) / halfwin
    ])

    #fb = (fb.T * np.linspace(1, 0, len(fb))).T
    fb[0, :] = 0

    fb = np.min(1 - fb, 0)
    
    return fb
    

def filter_overtones_static(sg):

    filtered = np.copy(sg)

    halfwin = sg.shape[1]

    mx = np.max(sg)

    for i in xrange(halfwin / 4 - 1, 0, -1):
        fb = get_filterbank(i, halfwin)
        if i % 100 == 0:
            print i
        for t, s in enumerate(filtered):
            fb1 = (1 - (1 - fb) * (min(s[i] * 5 / mx, 1)))
            filtered[t] *= fb1

    return filtered

def add_angles(sg, orig):
    sg = np.hstack((sg, sg[:, ::-1]))
    return sg * np.exp(1j * np.angle(orig))
