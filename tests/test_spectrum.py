import os
import unittest2 as unittest
import numpy as np

from andreasmusic import audio
from andreasmusic import spectrum

from util import rel_path

class TestSpectrum(unittest.TestCase):

    def test_spectrogram_size_1(self):
        a = audio.Audio(np.zeros((5000, 1)), 44100)
        s = spectrum.get_spectrogram(a, 2000, 1000)
        self.assertEquals(s.shape, (1000, 4))

    def test_spectrogram_size_2(self):
        a = audio.Audio(np.zeros((5000, 1)), 44100)
        s = spectrum.get_spectrogram(a, 3000, 1000)
        self.assertEquals(s.shape, (1500, 3))

    def test_spectrogram_size_3(self):
        a = audio.Audio(np.zeros((5500, 1)), 44100)
        s = spectrum.get_spectrogram(a, 3000, 1000)
        self.assertEquals(s.shape, (1500, 3))

    def test_correct_bins(self):
        fs = 44100
        t = np.arange(0, fs)
        f = 440
        signal = np.sin(t * f * 2 * np.pi / fs)[:, np.newaxis]
        a = audio.Audio(signal, fs)
        s = spectrum.get_spectrogram(a, 4096, 1024)
        predicted_peaks = np.ones(s.shape[1]) * np.round(2048 * f / (fs / 2.0))
        actual_peaks = np.argmax(s, 0)
        self.assertTrue(np.all(actual_peaks == predicted_peaks))
