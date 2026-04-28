# music-gen - Generatore Musicale Procedurale

Generatore di musica procedurale con interfaccia TUI (Textual) che crea composizioni MIDI e audio WAV.

##  Caratteristiche

- **Interfaccia TUI** interattiva con Textual
- **Generazione procedurale** di melodie, accordi e linee di basso
- **Visualizzazione sequencer** in tempo reale
- **Esportazione MIDI** per ulteriore editing
- **Rendering audio WAV** con fluidsynth
- **Parametri configurabili**:
  - Scale: Pentatonica, Maggiore, Minore, Dorica, Blues
  - Progressioni: I-IV-V-I, I-V-vi-IV, ii-V-I, blues-12, etc.
  - Ritmi: Straight, Eighth, Syncopato, Bossa Nova, Shuffle
  - BPM, swing, densità, numero battute

##  Installazione

### Dipendenze di sistema
```bash
sudo apt update
sudo apt install python3 python3-pip fluidsynth
```

### Dipendenze Python
```bash
pip install textual music21 --break-system-packages
```

### Soundfont (opzionale per audio)
Se non hai già un soundfont, installa FluidR3:
```bash
sudo apt install fluid-soundfont-gm
```

##  Utilizzo

```bash
python3 main.py
```

### Comandi tastiera

- **G** - Genera nuova composizione
- **M** - Esporta MIDI (salva file con nome personalizzato)
- **W** - Esporta WAV (renderizza audio con fluidsynth)
- **Q** - Esci

### Comandi mouse

- Modifica parametri nelle select box e input fields
- Clicca sui bottoni per le azioni

##  Struttura File

```
music-gen/
├── main.py              # Applicazione TUI principale
└── musicgen/            # Modulo generatore
    ├── __init__.py      # Exports del modulo
    ├── scale.py         # Definizione scale musicali
    ├── chord.py         # Costruzione accordi e progressioni
    ├── rhythm.py        # Pattern ritmici
    └── generator.py     # Engine principale di generazione
```

##  Output

### MIDI (tasto E)
File MIDI multi-traccia:
- Traccia 1: Melodia (Vibraphone)
- Traccia 2: Accordi (Piano)
- Traccia 3: Basso (Acoustic Bass)

Nome file: `output_{tonalità}_{progressione}_{bpm}bpm.mid`

### Audio WAV (tasto W)
File audio renderizzato con fluidsynth:
- Nome: `output_{tonalità}_{progressione}_{bpm}bpm.wav`
- Formato: WAV stereo
- Sample rate: 44.1 kHz (default fluidsynth)

## Parametri

### Scale
- **Pentatonica**: [0,2,4,7,9] - suono orientale/modale
- **Maggiore**: scala diatonica maggiore
- **Minore**: scala minore naturale
- **Dorica**: modo dorico (minor con 6ª maggiore)
- **Blues**: scala blues con blue notes

### Progressioni
- **I-IV-V-I**: progressione classica
- **I-V-vi-IV**: pop/rock (es. "Let It Be")
- **ii-V-I**: jazz standard
- **i-VI-III-VII**: progressione andalusa
- **blues-12**: 12-bar blues

### Ritmi
- **Straight**: semiminime (4/4)
- **Eighth**: crome costanti
- **Syncopato**: ritmo sincopato
- **Bossa Nova**: pattern bossa
- **Shuffle**: swing shuffle

### Altri parametri
- **BPM**: 60-200 (default 100)
- **Ottave**: 1-4 range melodico (default 2)
- **Battute**: 2-16 lunghezza pezzo (default 4)
- **Densità**: 10-100% probabilità note (default 70%)
- **Swing**: 0-50% swing amount (default 0%)

##  Troubleshooting

### Audio non funziona
1. Verifica che fluidsynth sia installato: `which fluidsynth`
2. Verifica soundfont disponibili: `ls /usr/share/sounds/sf2/`
3. Controlla il log nella TUI per errori specifici

### Import error
Se vedi `ModuleNotFoundError: No module named 'musicgen'`:
```bash
# Assicurati di essere nella directory corretta
cd /path/to/music-gen
python3 main.py
```

### Textual non si avvia
```bash
# Reinstalla textual
pip install --upgrade textual --break-system-packages
```

##  Esempi d'uso

### Generare bossa nova in D minore
1. Scala: Minore
2. Tonalità: D
3. Progressione: i-VI-III-VII
4. Ritmo: Bossa Nova
5. BPM: 120
6. Swing: 20%
7. Premi **G** per generare
8. Premi **W** per esportare WAV

### Jazz ii-V-I swing
1. Scala: Maggiore
2. Tonalità: C
3. Progressione: ii-V-I
4. Ritmo: Shuffle
5. BPM: 140
6. Swing: 40%
7. Densità: 60%
8. Premi **G** poi **M** per MIDI

##  Sviluppo

### Aggiungere nuove scale
Modifica `musicgen/scale.py`:
```python
class ScaleType(Enum):
    NUOVA_SCALA = "nuova"

SCALE_INTERVALS = {
    ScaleType.NUOVA_SCALA: [0, 2, 4, 6, 8, 10],  # intervalli in semitoni
}
```

### Aggiungere progressioni
Modifica `musicgen/chord.py`:
```python
PROGRESSIONS = {
    "custom": [(0, ChordType.MAJ), (5, ChordType.MIN7), ...],
}
```

### Aggiungere pattern ritmici
Modifica `musicgen/rhythm.py`:
```python
PATTERNS = {
    RhythmPattern.CUSTOM: [1,0,1,1, 0,1,0,1, ...],  # 16 step (1=attivo)
}
```

##  Licenza

Progetto personale - uso libero

##  Autore

Rocco (noya/debusercccp)
- Portfolio: progetti bioinformatica, ML, audio DSP
- Raspberry Pi cluster: rasp, video
- PC Linux: Orion

## Dipendenze

- [textual](https://github.com/Textualize/textual) - Framework TUI
- [music21](https://github.com/cuthbertLab/music21) - Libreria musicale
- [fluidsynth](https://www.fluidsynth.org/) - Sintetizzatore audio

---

**Note**: Il rendering WAV richiede qualche secondo. I file vengono salvati nella directory corrente.
