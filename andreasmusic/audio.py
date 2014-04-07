import os
import collections
import subprocess
import scipy.io.wavfile
import numpy as np

from andreasmusic import util

Audio = collections.namedtuple('Audio', ['signal', 'sample_rate'])

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
        subprocess.check_call(['ffmpeg', '-i', filename, wav_filename])
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
    
def downsample(audio, factor):
    signal = audio.signal[::factor, :]
    sample_rate = audio.sample_rate // factor
    return Audio(signal, sample_rate)

def get_channel(audio, channel_x):
    signal = audio.signal[:, channel_x][:, np.newaxis]
    return Audio(signal, audio.sample_rate)

def crop(audio, start, end):
    signal = audio.signal[start:end, :]
    return Audio(signal, audio.sample_rate)

def play(audio):
    with util.temporary_filename('.wav') as filename:
        scipy.io.wavfile.write(filename, audio.sample_rate, audio.signal)
        subprocess.check_call(['aplay', filename])

class AudioException(Exception):
    pass
