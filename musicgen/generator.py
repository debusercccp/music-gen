from dataclasses import dataclass
from music21 import stream, note, instrument, tempo, pitch
import random

from .scale import ScaleType, build_scale
from .chord import ChordType, Chord, Progression, build_progression, PROGRESSIONS
from .rhythm import RhythmPattern, BASS_PATTERN, generate_rhythm


@dataclass
class GenConfig:
    scale_type:   ScaleType     = ScaleType.PENTATONICA
    progression:  str           = "I-V-vi-IV"
    rhythm:       RhythmPattern = RhythmPattern.EIGHTH
    root_midi:    int           = 60
    num_octaves:  int           = 2
    swing:        float         = 0.0
    density:      float         = 0.75
    vel_variance: float         = 0.25
    bpm:          int           = 100
    num_bars:     int           = 4


def _pick_melody_note(
    scale_notes: list[int],
    chord: Chord,
    prev_midi: int | None,
) -> int:
    chord_pcs = chord.chord_pitch_classes()
    in_chord = [m for m in scale_notes if m % 12 in chord_pcs]
    pool = in_chord if in_chord else scale_notes
    if prev_midi is None:
        return random.choice(pool)
    weights = [1.0 / (abs(m - prev_midi) + 1) for m in pool]
    total = sum(weights)
    weights = [w / total for w in weights]
    return random.choices(pool, weights=weights, k=1)[0]


def generate_bar(
    cfg: GenConfig,
    chord: Chord,
    scale_notes: list[int],
    prev_melody_midi: int | None,
) -> tuple[stream.Part, stream.Part, stream.Part, int | None]:
    mel_part   = stream.Part()
    chord_part = stream.Part()
    bass_part  = stream.Part()

    rhythm_steps = generate_rhythm(
        cfg.rhythm,
        density=cfg.density,
        vel_variance=cfg.vel_variance,
        swing=cfg.swing,
    )

    last_midi = prev_melody_midi

    for step in rhythm_steps:
        if step.active:
            midi = _pick_melody_note(scale_notes, chord, last_midi)
            n = note.Note(midi=midi)
            n.quarterLength = step.duration
            n.volume.velocity = int(step.velocity * 127)
            mel_part.append(n)
            last_midi = midi
        else:
            r = note.Rest()
            r.quarterLength = step.duration
            mel_part.append(r)

    c = chord.to_m21(duration=4.0, octave_offset=-1)
    c.volume.velocity = 55
    chord_part.append(c)

    root_bass  = chord.root_midi - 24
    fifth_bass = root_bass + 7
    for i, active in enumerate(BASS_PATTERN):
        if active:
            midi = root_bass if i % 8 < 4 else fifth_bass
            n = note.Note(midi=midi)
            n.quarterLength = 0.5
            n.volume.velocity = int(random.uniform(70, 90))
            bass_part.append(n)
        else:
            bass_part.append(note.Rest(quarterLength=0.5))

    return mel_part, chord_part, bass_part, last_midi


def generate(cfg: GenConfig) -> stream.Score:
    prog   = PROGRESSIONS[cfg.progression]
    chords = build_progression(cfg.root_midi, prog)
    scale_notes = build_scale(cfg.root_midi, cfg.scale_type, cfg.num_octaves)
    chord_seq   = [chords[i % len(chords)] for i in range(cfg.num_bars)]

    mel_score   = stream.Part(id="melody")
    chord_score = stream.Part(id="chords")
    bass_score  = stream.Part(id="bass")

    mel_score.insert(0, instrument.Vibraphone())
    chord_score.insert(0, instrument.Piano())
    bass_score.insert(0, instrument.AcousticBass())

    prev_midi = None
    for chord in chord_seq:
        mel_bar, chord_bar, bass_bar, prev_midi = generate_bar(cfg, chord, scale_notes, prev_midi)
        for part, bar in [(mel_score, mel_bar), (chord_score, chord_bar), (bass_score, bass_bar)]:
            for elem in bar:
                part.append(elem)

    score = stream.Score()
    score.insert(0, tempo.MetronomeMark(number=cfg.bpm))
    score.append(mel_score)
    score.append(chord_score)
    score.append(bass_score)
    return score
