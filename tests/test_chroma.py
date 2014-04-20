import unittest2 as unittest
import numpy as np

from andreasmusic import chroma
from andreasmusic import pitches

class TestChroma(unittest.TestCase):

    def test_untuned_chromagram(self):
        sr = 11025
        window_size = 2000
        spectrogram = np.zeros((window_size / 2, 3))
        a4_bin = ((window_size / 2) / (sr / 2.0)) * pitches.A4.fq
        b4_bin = ((window_size / 2) / (sr / 2.0)) * pitches.B4.fq
        c5_bin = ((window_size / 2) / (sr / 2.0)) * pitches.C5.fq
        b5_bin = ((window_size / 2) / (sr / 2.0)) * pitches.B5.fq
        spectrogram[a4_bin, 0] = 1
        spectrogram[b4_bin, 1] = .5
        spectrogram[b5_bin, 1] = .4
        spectrogram[a4_bin, 2] = .1
        spectrogram[c5_bin, 2] = .2

        chromagram = chroma.get_chromagram(spectrogram, sample_rate=sr)

        expected = np.zeros((12, 3))
        expected[9, 0] = 1
        expected[11, 1] = .9
        expected[9, 2] = .1
        expected[0, 2] = .2

        self.assertTrue(np.all(chromagram == expected))

    def test_tune_chromagram(self):
        tuning_bins = 5
        chromagram = np.zeros((12 * tuning_bins, 2))

        chromagram[0, 0] = .5
        chromagram[1, 0] = 1
        chromagram[2, 0] = .4
        chromagram[3, 0] = .2
        chromagram[4, 0] = .3
        chromagram[58, 0] = .1
        chromagram[59, 0] = .4
        chromagram[2, 1] = .4

        self.assertEquals(chroma._max_tuning_bin(chromagram, tuning_bins), 1)

        tuned = chroma.tune_chromagram(chromagram, tuning_bins)

        expected = np.zeros((12, 2))
        expected[0, 0] = (chromagram[59, 0] +
                          chromagram[0, 0] +
                          chromagram[1, 0] +
                          chromagram[2, 0] +
                          chromagram[3, 0])
        expected[1, 0] = chromagram[4, 0]
        expected[11, 0] = chromagram[58, 0]
        expected[0, 1] = chromagram[2, 1]

        self.assertTrue(np.all(tuned == expected))

    def test_tuning_indices(self):
        self.assertTrue(np.all(chroma._get_tuning_indices(2, 3, 0)
                               == np.array([0, 0, 1, 1, 1, 0])))
        self.assertTrue(np.all(chroma._get_tuning_indices(2, 3, 1)
                               == np.array([0, 0, 0, 1, 1, 1])))
        self.assertTrue(np.all(chroma._get_tuning_indices(2, 3, 2)
                               == np.array([0, 1, 1, 1, 0, 0])))
