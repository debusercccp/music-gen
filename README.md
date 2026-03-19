# music-gen

Generatore musicale procedurale con TUI — gira sul Raspberry Pi.

## Installazione

```bash
# dipendenze sistema
sudo apt install fluidsynth fluid-soundfont-gm

# dipendenze Python
pip install -r requirements.txt --break-system-packages
```

## Avvio

```bash
python main.py
```

## Shortcut TUI

| Tasto | Azione         |
|-------|----------------|
| G     | Genera         |
| P     | Play           |
| S     | Stop           |
| E     | Esporta MIDI   |
| Q     | Esci           |

## Parametri

- **Scala** — pentatonica, maggiore, minore, dorica, blues
- **Tonalità** — C .. B
- **Progressione** — I-IV-V-I, I-V-vi-IV, ii-V-I, i-VI-III-VII, blues-12
- **Ritmo** — straight, 8th notes, sincopato, bossa nova, shuffle
- **BPM** — 60–200
- **Ottave** — 1–4
- **Battute** — 2–16
- **Densità** — quante note suona (10–100%)
- **Swing** — quanto swing (0–50%)

## Output

I file MIDI vengono salvati nella directory corrente con nome:
`output_<tonalità>_<progressione>_<bpm>bpm.mid`
