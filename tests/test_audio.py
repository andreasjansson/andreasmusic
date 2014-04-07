import os
import unittest2 as unittest

from andreasmusic import audio

from util import rel_path

class TestRead(unittest.TestCase):

    def test_read_mono_mp3(self):
        filename = rel_path('data/audio/rate44100-bits16-channels1-freq440-duration1.mp3')
        a = audio.read(filename)
        self.assertEquals(a.signal.shape[1], 1)
        self.assertGreater(a.signal.shape[0], 42000)
        self.assertLess(a.signal.shape[0], 47000)
        self.assertEquals(a.sample_rate, 44100)

    def test_read_stereo_mp3(self):
        filename = rel_path('data/audio/rate44100-bits16-channels2-freq440-duration1.mp3')
        a = audio.read(filename)
        self.assertEquals(a.signal.shape[1], 2)
        self.assertGreater(a.signal.shape[0], 42000)
        self.assertLess(a.signal.shape[0], 47000)
        self.assertEquals(a.sample_rate, 44100)

    def test_read_mono_wav(self):
        filename = rel_path('data/audio/rate44100-bits16-channels1-freq440-duration1.wav')
        a = audio.read(filename)
        self.assertEquals(a.signal.shape[1], 1)
        self.assertGreater(a.signal.shape[0], 42000)
        self.assertLess(a.signal.shape[0], 47000)
        self.assertEquals(a.sample_rate, 44100)

    def test_read_stereo_wav(self):
        filename = rel_path('data/audio/rate44100-bits16-channels2-freq440-duration1.wav')
        a = audio.read(filename)
        self.assertEquals(a.signal.shape[1], 2)
        self.assertGreater(a.signal.shape[0], 42000)
        self.assertLess(a.signal.shape[0], 47000)
        self.assertEquals(a.sample_rate, 44100)

