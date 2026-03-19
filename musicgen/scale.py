from enum import Enum
from music21 import pitch


class ScaleType(Enum):
    PENTATONICA = "pentatonica"
    MAGGIORE    = "maggiore"
    MINORE      = "minore"
    DORICA      = "dorica"
    BLUES       = "blues"


SCALE_INTERVALS: dict[ScaleType, list[int]] = {
    ScaleType.PENTATONICA: [0, 2, 4, 7, 9],
    ScaleType.MAGGIORE:    [0, 2, 4, 5, 7, 9, 11],
    ScaleType.MINORE:      [0, 2, 3, 5, 7, 8, 10],
    ScaleType.DORICA:      [0, 2, 3, 5, 7, 9, 10],
    ScaleType.BLUES:       [0, 3, 5, 6, 7, 10],
}


def build_scale(root_midi: int, scale_type: ScaleType, num_octaves: int = 2) -> list[int]:
    intervals = SCALE_INTERVALS[scale_type]
    notes = []
    for octave in range(num_octaves):
        for interval in intervals:
            notes.append(root_midi + octave * 12 + interval)
    return notes


def midi_to_name(midi: int) -> str:
    return pitch.Pitch(midi=midi).name


NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
