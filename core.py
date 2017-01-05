def SatisfiesConditions(key_map, velocity, sustain_value):
  """Returns True if the key_map satisfies the current conditions
  (velocity, sustain_value etc).
  """
  if velocity < key_map.min_velocity:
    return False
  if key_map.max_velocity > 0 and velocity >= key_map.max_velocity:
    return False
  if sustain_value < key_map.min_sustain:
    return False
  if key_map.max_sustain > 0 and sustain_value >= key_map.max_sustain:
    return False
  return True

def CreateNoteMap(layout):
  """Returns a MIDI note to [KeyMap] dictionary from the given Layout
  message.
  """
  note_map = {}
  for km in layout.keymaps:
    for note in km.notes:
      if note not in note_map:
        note_map[note] = []
      note_map[note].append(km)
  return note_map
