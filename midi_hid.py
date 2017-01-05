# midi_hid.py gets MIDI input and simulates keystrokes in a normal qwerty
# keyboard. It can be used to control your OS and for typing.

from google.protobuf import text_format
from pynput.keyboard import Key, Controller
import core
import gflags
import rtmidi_python as rtmidi
import scriabin_pb2
import sys
import time

FLAGS = gflags.FLAGS

gflags.DEFINE_string('scriabin_layout_file', None,
                     'Path to ASCII Protocol buffer file containing the layout file')

# Some MIDI constants.
CONTROL = 0xB0
NOTE_ON = 0x90
SUSTAIN_CC = 0x40


def _GetLayout():
    """Opens and parses the file pointed by --scriabin_layout_file, returning the Scriabin Layout as a protobuf message.
    """
    layout_file = open(FLAGS.scriabin_layout_file, 'r')
    return text_format.Parse(layout_file.read(), scriabin_pb2.Layout())


class ScriabinHandler(object):

    def __init__(self, layout):
        self.layout = layout
        self.sustain_value = 0
        self.keyboard = Controller()

    def _PressChars(self, key_map):
        """Presses the characters in key_map.characters simulating a real
        keyboard press.
        """
        for char in key_map.chars:
            code = self._GetCode(char)
            if code is not None:
                self.keyboard.press(code)

    def _ReleaseChars(self, key_map):
        """Releases the characters in key_map.characters simulating a real
        keyboard release.
        """
        for char in key_map.chars:
            code = self._GetCode(char)
            if code is not None:
                self.keyboard.release(code)

    def _HandleNote(self, note_map, note, velocity, sustain_value):
        """Main handler for each Note On message.
        """
        if note not in note_map:
            print('note not found in note_map')
            return

        key_maps = note_map[note]
        for key_map in key_maps:
            # Most controllers don't actually send a Note Off but instead send
            # a note with velocity == 0.
            if velocity <= 0:
                self._ReleaseChars(key_map)
                continue

            if core.SatisfiesConditions(key_map, velocity, sustain_value):
                self._PressChars(key_map)

    def CreateMidiCallback(self):
        """Creates a closure which wraps the given layout.

        The result should be ready for RTMidi's callback system.
        """
        note_map = core.CreateNoteMap(self.layout)

        def _MidiCallback(message, time_stamp):
            msg_type = message[0] & 0xf0
            if msg_type == NOTE_ON:
                note = message[1]
                velocity = message[2]
                self._HandleNote(note_map, note, velocity, self.sustain_value)
            elif msg_type == CONTROL:
                cc_number = message[1]
                if cc_number == SUSTAIN_CC:
                    cc_value = message[2]
                    self.sustain_value = cc_value

        return _MidiCallback

    def _GetCode(self, char):
        """Returns the character code that can be used with keyboard.press()
        and keyboard.release().
        """
        if char == 'escape':
            return Key.esc
        elif char == 'tab':
            return Key.tab
        elif char == 'super':
            return Key.cmd
        elif char == 'ctrl':
            return Key.ctrl
        elif char == 'shift':
            return Key.shift
        elif char == 'alt':
            return Key.alt
        elif char == 'backspace':
            return Key.backspace
        elif char == 'delete':
            return Key.delete
        elif char == 'enter':
            return Key.enter
        elif char == 'left':
            return Key.left
        elif char == 'right':
            return Key.right
        elif char == 'up':
            return Key.up
        elif char == 'down':
            return Key.down
        elif not isinstance(char, basestring):
            print('Could not understand key ',
                  char, '. Will replace it with nothing')
            return None
        return char

if __name__ == '__main__':
    FLAGS(sys.argv)  # Initializes flags.

    layout = _GetLayout()
    scriabin_handler = ScriabinHandler(layout)

    midi_in = rtmidi.MidiIn()
    midi_in.callback = scriabin_handler.CreateMidiCallback()
    # TODO(kenjitoyama): Do virtual ports always exist? Do we need to use
    #                    midi_in.open_port(1)?
    midi_in.open_virtual_port('Scriabin')

    # Cannot exit so sleep for a long, long time.
    # TODO(kenjitoyama): Try with signal.pause() instead of sleep().
    time.sleep(1000000)
