import sys
import numpy as np
from collections import namedtuple

Note = namedtuple('Note', ['name', 'fq', 'midi_pitch'])

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

ENHARMONIC_EQUIVALENTS = {
    'C#': 'Db',
    'Db': 'C#',
    'D#': 'Eb',
    'Eb': 'D#',
    'E' : 'Fb',
    'Fb': 'E',
    'E#': 'F',
    'F' : 'E#',
    'F#': 'Gb',
    'Gb': 'F#',
    'G#': 'Ab',
    'Ab': 'G#',
    'A#': 'Bb',
    'Bb': 'A#',
    'B' : 'Cb',
    'Cb': 'B',
    'B#': 'C',
    'C' : 'B#',
}

MIDI_FREQS = {}

def _setup():
    for octave in range(0, 7):
        for i, note_name in enumerate(NOTE_NAMES):
            dist_from_a = (octave - 3) * 12 + i - 9
            fq = 440 * np.power(2, dist_from_a / 12.0)
            midi_pitch = (octave + 1) * 12 + i

            MIDI_FREQS[midi_pitch] = fq

            note_names = [note_name]
            if note_name in ENHARMONIC_EQUIVALENTS:
                note_names.append(ENHARMONIC_EQUIVALENTS[note_name])

            for n in [note_name] + ([ENHARMONIC_EQUIVALENTS[note_name]]
                                    if note_name in ENHARMONIC_EQUIVALENTS else []):
                name = '%s%d' % (n, octave)
                note = Note(name, fq, midi_pitch)
                setattr(sys.modules[__name__], name.replace('#', '_'), note)
_setup()


class UnknownNote(Exception): pass

def note_number(note_name):
    if note_name in NOTE_NAMES:
        return NOTE_NAMES.index(note_name)
    elif note_name in ENHARMONIC_EQUIVALENTS:
        return NOTE_NAMES.index(ENHARMONIC_EQUIVALENTS[note_name])
    raise UnknownNote(note_name)

def note_name(note_number):
    if note_number < 0:
        raise UnknownNote(note_number)
    name = NOTE_NAMES[note_number % 12]
    octave = int(note_number / 12)
    return '%s%d' % (name, octave)

def pitch_to_freq(pitch):
    return MIDI_FREQS[pitch]
