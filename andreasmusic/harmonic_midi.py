# emphasis on the harmony, more than anything else

import midi
import numpy as np
import collections
import subprocess

from andreasmusic import util

MIN_PITCH = 12 * 2
MAX_PITCH = 12 * 7
RANGE = MAX_PITCH - MIN_PITCH

# some people never NoteOff these instruments
TRANSIENT_PROGRAMS = {
    None, # assuming piano here, naively
    0,	# Tone_000/000_Acoustic_Grand_Piano.pat amp=120 pan=center
    1,	# Tone_000/001_Acoustic_Brite_Piano.pat 
    2,	# Tone_000/002_Electric_Grand_Piano.pat 
    4,	# Tone_000/004_Electric_Piano_1_Rhodes.pat 
    5,	# Tone_000/005_Electric_Piano_2_Chorused_Yamaha_DX.pat 
    6,	# Tone_000/006_Harpsichord.pat 
    7,	# Tone_000/007_Clavinet.pat 
    8,	# Tone_000/008_Celesta.pat 
    9,	# Tone_000/009_Glockenspiel.pat 
    13,	# Tone_000/013_Xylophone.pat 
    14,	# Tone_000/014_Tubular_Bells.pat 
    15,	# Tone_000/015_Dulcimer.pat 
    24,	# Tone_000/024_Nylon_Guitar.pat 
    25,	# Tone_000/025_Steel_Guitar.pat 
    26,	# Tone_000/026_Jazz_Guitar.pat 
    27,	# Tone_000/027_Clean_Electric_Guitar.pat 
    28,	# Tone_000/028_Muted_Electric_Guitar.pat 
    29,	# Tone_000/029_Overdriven_Guitar.pat 
    30,	# Tone_000/030_Distortion_Guitar.pat 
    32,	# Tone_000/032_Acoustic_Bass.pat 
    33,	# Tone_000/033_Finger_Bass.pat 
    34,	# Tone_000/034_Pick_Bass.pat 
    35,	# Tone_000/035_Fretless_Bass.pat 
    36,	# Tone_000/036_Slap_Bass_1.pat 
    37,	# Tone_000/037_Slap_Bass_2.pat 
    38,	# Tone_000/038_Synth_Bass_1.pat 
    45,	# Tone_000/045_Pizzicato_Strings.pat 
    46,	# Tone_000/046_Harp.pat 
    47,	# Tone_000/047_Timpani.pat 
    98,	# Tone_000/098_Crystal.pat 
    101,# Tone_000/101_Goblins--Unicorn.pat 
    104,# Tone_000/104_Sitar.pat 
}

CONTROL_VOLUME = 7
CONTROL_BANK_SELECT = 0

def read(filename, oversampling=1):
    raw = midi.read_midifile(filename)
    raw.make_ticks_abs()

    length, resolution = get_length(raw)
    resolution /= oversampling
    length *= oversampling

    tempos = []

    pitches = np.zeros((length, MAX_PITCH - MIN_PITCH), dtype=np.float32)

    for track_number, track in enumerate(raw):
        tick = 0
        programs = {}
        channel_active_pitches = collections.defaultdict(set)

        for event in track:
            prev_t = (tick / resolution)
            tick = event.tick
            t = int(tick / resolution)

            if isinstance(event, midi.NoteOnEvent):
                if not is_percussion(programs, event.channel):
                    pitch, velocity = event.data
                    if velocity == 0:
                        channel_active_pitches[event.channel].discard(pitch)
                    else:
                        channel_active_pitches[event.channel].add(pitch)

            elif isinstance(event, midi.NoteOffEvent):
                pitch, _ = event.data
                channel_active_pitches[event.channel].discard(pitch)

            elif isinstance(event, midi.ProgramChangeEvent):
                programs[event.channel] = event.data[0]

            elif isinstance(event, midi.SetTempoEvent):
                tempos.append((tick, event.get_bpm()))

            active_pitches = set()
            for channel, ap in channel_active_pitches.items():
                active_pitches |= ap

            for p in active_pitches:
                if MIN_PITCH <= p < MAX_PITCH:
                    pitches[t, p - MIN_PITCH] = min(1, pitches[t, p - MIN_PITCH] + 1)

            # for channel, active_pitches in channel_active_pitches.items():
            #     # TODO: decide whether or not to keep this. i'm leaning towards
            #     # only counting note on messages since people never write note off...
            #     if False and ( channel in programs and programs[channel] in TRANSIENT_PROGRAMS and t != prev_t):
            #         channel_active_pitches[channel] = set()

    pitches = lower_resolution(pitches, oversampling)

    return pitches, tempos

def lower_resolution(pitchgram, factor):
    return np.array([
        x.sum(0) for x in np.split(pitchgram, range(factor, len(pitchgram), factor))
    ])

def pitch_to_int(p):
    return np.dot(np.power(2, np.arange(len(p) - 1, -1, -1)), p)

def get_length(raw):
    max_length = 0
    resolution = raw.resolution
    metronome = None
    for track in raw:
        t = 0
        for event in track:
            t = event.tick
            if isinstance(event, midi.TimeSignatureEvent):
                if metronome is None:
                    metronome = event.metronome
                elif metronome != event.metronome:
                    raise MultipleMetronomesError
        if t > max_length:
            max_length = t

    if metronome is None:
        metronome = 24

    if metronome != 24:
        print '--------- metronome %d != 24' % metronome
        metronome = 24 #####

    resolution = resolution * (metronome / 24.0)
 
    return int(max_length / resolution) + 1, resolution

class MultipleMetronomesError(Exception): pass

def is_percussion(programs, channel):
    return programs.get(channel, 0) >= 112 or channel == 9
        
def play(pitchgram, transpose=0, tempo=120, instrument=41):
    with util.temporary_filename() as filename:
        write_pitchgram(pitchgram, filename, transpose, tempo=tempo, instrument=instrument)
        subprocess.check_output(['timidity', filename])

def synthesize_audio(pitchgram, transpose=0, tempo=120, instrument=41):
    from andreasmusic import audio

    with util.temporary_filename('.mid') as midi_filename:
        with util.temporary_filename('.wav') as wav_filename:
            write_pitchgram(pitchgram, midi_filename, transpose, tempo, instrument)
            subprocess.check_output(['timidity', '-Ow', '-o', wav_filename, midi_filename])
            return audio.read(wav_filename)

def write_pitchgram(pitchgram, filename, transpose=0, tempo=120, instrument=41):
    pattern = midi.Pattern()
    pattern.resolution = 96

    track = midi.Track()
    pattern.append(track)

    track.append(midi.ProgramChangeEvent(data=[instrument]))

    track.append(midi.SetTempoEvent(bpm=tempo))

    diffs = pitchgram - np.vstack((np.zeros((1, pitchgram.shape[1])), pitchgram[:-1]))

    tick = 0
    tick_increment = 24 * 4
    #tick_increment = 12
    for diff in diffs:
        pitches_on = np.where(diff == 1)[0]
        pitches_off = np.where(diff == -1)[0]

        for pitch in pitches_on:
            on = midi.NoteOnEvent(tick=tick, velocity=100, pitch=MIN_PITCH + transpose + pitch)
            track.append(on)
            tick = 0

        for pitch in pitches_off:
            off = midi.NoteOffEvent(tick=tick, pitch=MIN_PITCH + transpose + pitch)
            track.append(off)
            tick = 0

        tick += tick_increment

    tick += tick_increment

    eot = midi.EndOfTrackEvent(tick=tick)
    track.append(eot)
    midi.write_midifile(filename, pattern)

    return pattern
