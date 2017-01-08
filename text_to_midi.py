# midi_to_text.py receives a text file and a Scriabin layout and it
# produces a standard MIDI file (SMF).
#
# Usage: python2 text_to_midi.py \
#            --scriabin_layout_file=layouts/layout00.asciipb
#            --text_file=text_to_midi.py \
#            --output_midi_file='text_to_midi.mid'

from google.protobuf import text_format
import core
import gflags
import numpy as np
import scriabin_pb2
import smf
import sys

FLAGS = gflags.FLAGS

gflags.DEFINE_string('scriabin_layout_file', None,
                     'Path to ASCII Protocol buffer file containing the layout file')

gflags.DEFINE_string('text_file', None,
                     'Path to text file which will be used to generate a song')

gflags.DEFINE_string('output_midi_file', None,
                     'Path to output .mid file which will contain the generated song')

gflags.DEFINE_float('default_note_length', 0.1,
                    'Each note produced will have this length in seconds')

gflags.DEFINE_bool('want_duration_variation', False,
                   'Whether note durations will have varying values.')

gflags.DEFINE_integer('num_tracks', 1,
                      'Number of tracks in the output MIDI file.')

# Some MIDI constants.
NOTE_OFF = 0x80
NOTE_ON = 0x90


def _GetLayout():
    """Opens and parses the file pointed by --scriabin_layout_file, returning the Scriabin Layout as a protobuf message.
    """
    layout_file = open(FLAGS.scriabin_layout_file, 'r')
    return text_format.Parse(layout_file.read(), scriabin_pb2.Layout())


def _GetNoteDuration():
    """Returns the note length according to FLAGS.default_note_length and
    FLAGS.want_duration_variation.

    When using multiple output tracks (FLAGS.num_tracks > 1), it's often
    desirable to "synchronize" events so that NOTE ONs start at the same
    time. For this to happen, FLAGS.want_duration_variation must be
    False.
    """
    return (np.random.normal(FLAGS.default_note_length,
                             FLAGS.default_note_length / 3.0)
            if FLAGS.want_duration_variation
            else FLAGS.default_note_length)


def _ConvertTextFileToMidiNotes(layout):
    """Opens and parses the file pointed by --text_file, returning MIDI
    events corresponding to the layout.
    """
    char_map = core.CreateCharMap(layout)
    notes = []
    with open(FLAGS.text_file, 'r') as f:
        while True:
            c = f.read(1)
            if not c:  # EOF
                break

            # If the character is not present in the map, ignore it.
            if c not in char_map:
                print('Char \'{}\' not in the given map'.format(c))
                continue

            keymaps = char_map[c]
            for km in keymaps:
                for note in km.notes:
                    # Generate a random velocity in the allowed range for this
                    # KeyMap.
                    random_velocity = np.random.randint(
                        0 if km.min_velocity <= 0 else km.min_velocity,
                        127 if km.max_velocity <= 0 else km.max_velocity)
                    notes.append(smf.Event([NOTE_ON, note, random_velocity]))
                    notes.append(smf.Event([NOTE_OFF, note, random_velocity]))
    # Create a list of pairs of Note ONs and Note OFFs.
    return zip(notes[::2], notes[1::2])


def _GenerateSmf(notes):
    f = smf.SMF()

    # cursors will hold a cursor for each track which indicates at which
    # point in time events will be inserted.
    cursors = {}

    # Add FLAGS.num_tracks tracks and create cursors for each of them.
    for i in range(FLAGS.num_tracks):
        f.add_track()
        cursors[i] = 0.0

    current_track = 0
    for note in notes:
        note_on = note[0]
        note_off = note[1]
        f.add_event(note_on, current_track, seconds=cursors[current_track])
        duration = _GetNoteDuration()
        cursors[current_track] += duration
        f.add_event(note_off, current_track, seconds=cursors[current_track])
        duration = _GetNoteDuration()
        cursors[current_track] += duration

        current_track = (current_track + 1) % FLAGS.num_tracks
    f.save(FLAGS.output_midi_file)

if __name__ == '__main__':
    FLAGS(sys.argv)  # Initializes flags.

    layout = _GetLayout()
    notes = _ConvertTextFileToMidiNotes(layout)
    _GenerateSmf(notes)
