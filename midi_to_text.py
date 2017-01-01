from google.protobuf import text_format
from pynput.keyboard import Key, Controller
import gflags
import rtmidi_python as rtmidi
import scriabin_pb2
import sys
import time

FLAGS = gflags.FLAGS

gflags.DEFINE_string('scriabin_layout_file', None,
										 'Path to ASCII Protocol buffer file containing the layout file')

# Some MIDI constants.
CONTROL = 0xB0;
NOTE_ON = 0x90;
SUSTAIN_CC = 0x40;

# Global variables.
keyboard = Controller()
sustain_value = 0

# Opens and parses the file pointed by --scriabin_layout_file, returning
# the Scriabin Layout as a protobuf message.
def _GetLayout():
  layout_file = open(FLAGS.scriabin_layout_file, 'r')
  return text_format.Parse(layout_file.read(), scriabin_pb2.Layout())

# Returns the character code that can be used with keyboard.press() and
# keyboard.release().
def _GetCode(char):
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
    print('Could not understand key ', char, '. Will replace it with nothing')
    return None
  return char

# Returns True if the key_map satisfies the current conditions (velocity,
# sustain_value etc).
def _SatisfiesConditions(key_map, velocity, sustain_value):
  if velocity < key_map.min_velocity:
    return False
  if key_map.max_velocity > 0 and velocity >= key_map.max_velocity:
    return False
  if sustain_value < key_map.min_sustain:
    return False
  if key_map.max_sustain > 0 and sustain_value >= key_map.max_sustain:
    return False
  return True

# Presses the characters in key_map.characters simulating a real keyboard
# press.
def _PressChars(key_map):
  for char in key_map.chars:
    code = _GetCode(char)
    if code is not None:
      keyboard.press(code)

# Releases the characters in key_map.characters simulating a real keyboard
# release.
def _ReleaseChars(key_map):
  for char in key_map.chars:
    code = _GetCode(char)
    if code is not None:
      keyboard.release(code)

# Main handler for each Note On message.
def HandleNote(note_map, note, velocity, sustain_value):
  if note not in note_map:
    print('note not found in note_map')
    return

  key_maps = note_map[note]
  for key_map in key_maps:
    # Most controllers don't actually send a Note Off but instead send a
    # note with velocity == 0.
    if velocity <= 0:
      _ReleaseChars(key_map)
      continue

    if _SatisfiesConditions(key_map, velocity, sustain_value):
      _PressChars(key_map)

# Returns a MIDI note to [KeyMap] dictionary from the given Layout
# message.
def _CreateNoteMap(layout):
  note_map = {}
  for km in layout.keymaps:
    for note in km.notes:
      if note not in note_map:
        note_map[note] = []
      note_map[note].append(km)
  return note_map

# Creates a closure which wraps the given layout.
#
# The result should be ready for RTMidi's callback system.
def _CreateMidiCallback(layout):
  note_map = _CreateNoteMap(layout)

  def _MidiCallback(message, time_stamp):
    global sustain_value

    msg_type = message[0] & 0xf0
    if msg_type == NOTE_ON:
      note = message[1]
      velocity = message[2]
      HandleNote(note_map, note, velocity, sustain_value)
    elif msg_type == CONTROL:
      cc_number = message[1]
      if cc_number == SUSTAIN_CC:
        cc_value = message[2]
        sustain_value = cc_value

  return _MidiCallback

if __name__ == '__main__':
  FLAGS(sys.argv)  # Initializes flags.

  layout = _GetLayout()

  midi_in = rtmidi.MidiIn()
  midi_in.callback = _CreateMidiCallback(layout)
  # TODO(kenjitoyama): Do virtual ports always exist? Do we need to use
  #                    midi_in.open_port(1)?
  midi_in.open_virtual_port('Scriabin')
  
  # Cannot exit so sleep for a long, long time.
  # TODO(kenjitoyama): Try with signal.pause() instead of sleep().
  time.sleep(1000000)
