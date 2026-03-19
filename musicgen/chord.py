from enum import Enum
from dataclasses import dataclass
from music21 import chord as m21chord, note, pitch


class ChordType(Enum):
    MAJ  = "maj"
    MIN  = "min"
    MAJ7 = "maj7"
    MIN7 = "min7"
    DOM7 = "7"


CHORD_INTERVALS: dict[ChordType, list[int]] = {
    ChordType.MAJ:  [0, 4, 7],
    ChordType.MIN:  [0, 3, 7],
    ChordType.MAJ7: [0, 4, 7, 11],
    ChordType.MIN7: [0, 3, 7, 10],
    ChordType.DOM7: [0, 4, 7, 10],
}


@dataclass
class Chord:
    root_midi: int
    chord_type: ChordType

    @property
    def midi_notes(self) -> list[int]:
        return [self.root_midi + i for i in CHORD_INTERVALS[self.chord_type]]

    @property
    def name(self) -> str:
        p = pitch.Pitch(midi=self.root_midi)
        return f"{p.name}{self.chord_type.value}"

    def to_m21(self, duration: float = 4.0, octave_offset: int = 0) -> m21chord.Chord:
        midis = [m + octave_offset * 12 for m in self.midi_notes]
        pitches = [pitch.Pitch(midi=m) for m in midis]
        c = m21chord.Chord(pitches)
        c.quarterLength = duration
        return c

    def chord_pitch_classes(self) -> set[int]:
        return {m % 12 for m in self.midi_notes}


Progression = list[tuple[int, ChordType]]

PROGRESSIONS: dict[str, Progression] = {
    "I-IV-V-I":     [(0, ChordType.MAJ),  (5, ChordType.MAJ),  (7, ChordType.DOM7), (0, ChordType.MAJ)],
    "I-V-vi-IV":    [(0, ChordType.MAJ),  (7, ChordType.MAJ),  (9, ChordType.MIN),  (5, ChordType.MAJ)],
    "ii-V-I":       [(2, ChordType.MIN7), (7, ChordType.DOM7), (0, ChordType.MAJ7), (0, ChordType.MAJ7)],
    "i-VI-III-VII": [(0, ChordType.MIN),  (8, ChordType.MAJ),  (3, ChordType.MAJ),  (10, ChordType.DOM7)],
    "blues-12":     [(0, ChordType.DOM7)] * 4 + [(5, ChordType.DOM7)] * 2 +
                    [(0, ChordType.DOM7)] * 2 + [(7, ChordType.DOM7), (5, ChordType.DOM7),
                    (0, ChordType.DOM7), (7, ChordType.DOM7)],
}


def build_progression(root_midi: int, progression: Progression) -> list[Chord]:
    return [Chord(root_midi + semis, ctype) for semis, ctype in progression]
