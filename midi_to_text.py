# midi_to_text.py receives a text file and a Scriabin layout and it
# produces a standard MIDI file (SMF).
#
# Usage: python2 midi_to_text.py \
#            --scriabin_layout_file=layouts/layout00.asciipb
#            --text_file=midi_to_text.py \
#            --output_midi_file='midi_to_text.mid'

from google.protobuf import text_format
import core
import gflags
import random
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

# Some MIDI constants.
NOTE_OFF = 0x80
NOTE_ON = 0x90


def _GetLayout():
    """Opens and parses the file pointed by --scriabin_layout_file, returning the Scriabin Layout as a protobuf message.
    """
    layout_file = open(FLAGS.scriabin_layout_file, 'r')
    return text_format.Parse(layout_file.read(), scriabin_pb2.Layout())


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
                continue

            keymaps = char_map[c]
            for km in keymaps:
                for note in km.notes:
                    # Generate a random velocity in the allowed range for this
                    # KeyMap.
                    random_velocity = random.randint(
                        0 if km.min_velocity <= 0 else km.min_velocity,
                        127 if km.max_velocity <= 0 else km.max_velocity)
                    notes.append(smf.Event([NOTE_ON, note, random_velocity]))
                    notes.append(smf.Event([NOTE_OFF, note, random_velocity]))
    return notes


def _GenerateSmf(notes):
    f = smf.SMF()
    f.add_track()
    second = 0.0
    for note in notes:
        f.add_event(note, 0, seconds=second)
        second += FLAGS.default_note_length
    f.save(FLAGS.output_midi_file)

if __name__ == '__main__':
    FLAGS(sys.argv)  # Initializes flags.

    layout = _GetLayout()
    notes = _ConvertTextFileToMidiNotes(layout)
    _GenerateSmf(notes)
