import os
import collections
import subprocess
import scipy.io.wavfile
import numpy as np

from andreasmusic import util

class Audio(object):
    def __init__(self, signal, sample_rate):
        self.signal = signal
        self.sample_rate = sample_rate

    def write(self, filename):
        filename = os.path.expanduser(filename)
        _, extension = os.path.splitext(filename)
        if extension in ['.mp3']:
            return self._write_mp3(filename)
        elif extension == '.wav':
            return self._write_wav(filename)
        else:
            raise NotImplementedError('Unknown file extension: %s (%s)' %
                                      (extension, filename))

    def _write_mp3(self, filename):
        with util.temporary_filename('.wav') as wav_filename:
            self._write_wav(wav_filename)
            subprocess.check_output(['ffmpeg', '-y', '-i', wav_filename, filename], stderr=subprocess.STDOUT)

    def _write_wav(self, filename):
        scipy.io.wavfile.write(filename, self.sample_rate, self.signal)

    def downsample(self, factor):
        signal = self.signal[::factor, :]
        sample_rate = self.sample_rate // factor
        return Audio(signal, sample_rate)

    def get_channel(self, channel_x):
        signal = self.signal[:, channel_x][:, np.newaxis]
        return Audio(signal, self.sample_rate)

    def find_zero_crossing(self, t, max_t=1000):
        for i in xrange(max_t):
            cur = self.signal[t + i]
            prev = self.signal[t + i - 1]
            if np.sign(cur) != np.sign(prev):
                if np.abs(prev) < np.abs(cur):
                    return t + i - 1
                else:
                    return t + i
        return t

    def crop(self, start=None, end=None, zero_crossing=False):
        if start is None:
            start = 0
        if end is None:
            end = len(self.signal)
        if zero_crossing:
            start = self.find_zero_crossing(start)
            end = self.find_zero_crossing(end)
        signal = self.signal[start:end]
        signal = signal.astype('float32')
        return Audio(signal, self.sample_rate)

    def crop_seconds(self, start, end=None):
        start *= int(self.sample_rate)
        if end is not None:
            end *= int(self.sample_rate)
        return self.crop(start, end)

    def add_at(self, other, t):
        assert self.sample_rate == other.sample_rate
        s1 = self.signal
        s2 = other.signal
        assert s1.shape[1] == s2.shape[1]

        if t + len(s2) > len(s1):
            signal = np.vstack((s1, np.zeros((t + len(s2) - len(s1), s1.shape[1]))))
        else:
            signal = s1.copy()

        signal[t:t + len(s2), :] += s2
        signal = signal.astype('float32')

        return Audio(signal, self.sample_rate)

    def add_after(self, other):
        return self.add_at(other, len(self.signal))

    def normalise(self, peak=1.0):
        factor = peak / np.max(np.abs(self.signal))
        return Audio(self.signal * factor, self.sample_rate)

    def clip(self, peak=1.0):
        signal = np.maximum(np.minimum(self.signal, 1), -1)
        return Audio(signal, self.sample_rate)

    def play(self):
        with util.temporary_filename('.wav') as filename:
            self.write(filename)
            subprocess.check_call(['aplay', filename])

    def copy(self):
        return Audio(self.signal, self.sample_rate)

def read(filename):
    filename = os.path.expanduser(filename)
    _, extension = os.path.splitext(filename)
    if extension in ['.mp3', '.mp4']:
        return _read_mpX(filename)
    elif extension == '.wav':
        return _read_wav(filename)
    else:
        raise NotImplementedError('Unknown file extension: %s (%s)' %
                                  (extension, filename))

def _read_mpX(filename):
    with util.temporary_filename('.wav') as wav_filename:
        subprocess.check_output(['ffmpeg', '-y', '-i', filename, wav_filename], stderr=subprocess.STDOUT)
        return _read_wav(wav_filename)

def _read_wav(filename):
    sample_rate, signal = scipy.io.wavfile.read(filename)
    if signal.dtype == 'int16':
        signal = signal.astype(float) / (2**15)
    elif signal.dtype == 'int32':
        signal = signal.astype(float) / (2**31)

    if np.max(signal) > 1 or np.min(signal) < -1:
        raise AudioException('Unknown data type')

    if len(signal.shape) == 1:
        signal = signal[:,np.newaxis]

    signal = signal.astype('float32')

    return Audio(signal, sample_rate)
    
class AudioException(Exception):
    pass
