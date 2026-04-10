from enum import Enum
from dataclasses import dataclass
import random


class RhythmPattern(Enum):
    STRAIGHT  = "straight"
    EIGHTH    = "eighth"
    SYNCOPATO = "syncopato"
    BOSSA     = "bossa"
    SHUFFLE   = "shuffle"


PATTERNS: dict[RhythmPattern, list[bool]] = {
    RhythmPattern.STRAIGHT:  [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0],
    RhythmPattern.EIGHTH:    [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0],
    RhythmPattern.SYNCOPATO: [1,0,0,1, 0,0,1,0, 0,1,0,1, 0,0,1,0],
    RhythmPattern.BOSSA:     [1,0,0,1, 0,1,0,0, 1,0,1,0, 0,1,0,0],
    RhythmPattern.SHUFFLE:   [1,0,0,1, 1,0,0,1, 1,0,0,1, 1,0,0,1],
}

BASS_PATTERN: list[bool] = [1,0,0,0, 0,0,0,1, 1,0,0,0, 0,0,1,0]


@dataclass
class RhythmStep:
    active: bool
    velocity: float
    duration: float


def generate_rhythm(
    pattern: RhythmPattern,
    density: float = 0.75,
    vel_variance: float = 0.25,
    swing: float = 0.0,
) -> list[RhythmStep]:
    base_steps = PATTERNS[pattern]
    result = []
    for i, active in enumerate(base_steps):
        is_active = bool(active) and random.random() < density
        is_downbeat = i % 4 == 0
        base_vel = 0.85 if is_downbeat else 0.60
        velocity = min(1.0, max(0.1, base_vel + random.uniform(-vel_variance, vel_variance)))
        base_dur = 0.5
        if swing > 0 and i % 2 == 1:
            duration = base_dur * (1.0 - swing * 0.5)
        elif swing > 0 and i % 2 == 0:
            duration = base_dur * (1.0 + swing * 0.5)
        else:
            duration = base_dur
        result.append(RhythmStep(active=is_active, velocity=velocity, duration=duration))
    return result
