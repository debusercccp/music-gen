"""
music-gen TUI — generatore musicale procedurale
Dipendenze: textual, music21, fluidsynth (sistema)
"""

from __future__ import annotations

import subprocess
import tempfile
import os
import threading
from pathlib import Path
from dataclasses import dataclass

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Label, Button, Select,
    Static, Log, Rule, Input,
)
from textual.reactive import reactive
from textual.binding import Binding
from textual import on, work

from musicgen.scale import ScaleType, NOTE_NAMES
from musicgen.chord import PROGRESSIONS
from musicgen.rhythm import RhythmPattern
from musicgen.generator import GenConfig, generate


# ── costanti ────────────────────────────────────────────────────────────────

SOUNDFONT_PATHS = [
    "/usr/share/sounds/sf2/FluidR3_GM.sf2",
    "/usr/share/sounds/sf2/FluidR3_GS.sf2",
    "/usr/share/sounds/sf2/TimGM6mb.sf2",
    "/usr/share/sounds/sf2/default.sf2",
    "/usr/share/soundfonts/default.sf2",
]

ROOT_NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
ROOT_MIDI  = {n: 48 + i for i, n in enumerate(ROOT_NOTES)}  # ottava 3

SCALE_LABELS = {
    ScaleType.PENTATONICA: "Pentatonica",
    ScaleType.MAGGIORE:    "Maggiore",
    ScaleType.MINORE:      "Minore nat.",
    ScaleType.DORICA:      "Dorica",
    ScaleType.BLUES:       "Blues",
}

RHYTHM_LABELS = {
    RhythmPattern.STRAIGHT:  "4/4 Straight",
    RhythmPattern.EIGHTH:    "8th Notes",
    RhythmPattern.SYNCOPATO: "Syncopato",
    RhythmPattern.BOSSA:     "Bossa Nova",
    RhythmPattern.SHUFFLE:   "Shuffle",
}

CSS = """
Screen {
    background: $surface;
}

#sidebar {
    width: 36;
    border-right: solid $primary-darken-2;
    padding: 0 1;
}

#main {
    padding: 1 2;
}

.section-title {
    color: $accent;
    text-style: bold;
    margin-top: 1;
}

.param-row {
    height: 3;
    margin-bottom: 1;
}

.param-label {
    width: 18;
    color: $text-muted;
    padding-top: 1;
}

.param-value {
    width: 6;
    color: $accent;
    text-align: right;
    padding-top: 0;
}

Select {
    width: 100%;
    margin-bottom: 1;
}

.param-input {
    width: 1fr;
}

#log-box {
    height: 12;
    border: solid $primary-darken-2;
    margin-top: 1;
}

#btn-row {
    margin-top: 1;
    height: 3;
}

Button {
    margin-right: 1;
}

#btn-generate {
    background: $accent;
    color: $background;
}

#btn-save-midi, #btn-save-wav {
    background: $success-darken-1;
    color: $background;
}

#status-bar {
    dock: bottom;
    height: 1;
    background: $primary-darken-2;
    color: $text-muted;
    padding: 0 1;
}

#seq-display {
    height: 5;
    border: solid $primary-darken-2;
    margin-top: 1;
    padding: 0 1;
}

.seq-title {
    color: $text-muted;
    text-style: bold;
}
"""


# ── widget sequencer ─────────────────────────────────────────────────────────

class SequencerDisplay(Static):
    """Visualizza i 16 step del pattern ritmico e gli accordi."""

    melody_steps: reactive[list[bool]]  = reactive([False] * 16)
    chord_steps:  reactive[list[bool]]  = reactive([False] * 4)
    chord_names:  reactive[list[str]]   = reactive(["—"] * 4)
    current_step: reactive[int]         = reactive(-1)

    def render(self) -> str:
        mel  = self.melody_steps
        cur  = self.current_step
        blocks_on  = "█"
        blocks_off = "░"
        blocks_cur = "▓"

        mel_row = ""
        for i, on in enumerate(mel):
            if i == cur:
                mel_row += f"[bold yellow]{blocks_cur}[/]"
            elif on:
                mel_row += f"[cyan]{blocks_on}[/]"
            else:
                mel_row += f"[dim]{blocks_off}[/]"
            if i % 4 == 3 and i < 15:
                mel_row += " "

        chord_row = ""
        for i, name in enumerate(self.chord_names):
            pad = 4
            cell = name[:pad].center(pad)
            if i == cur // 4 if cur >= 0 else False:
                chord_row += f"[bold yellow]{cell}[/]"
            else:
                chord_row += f"[green]{cell}[/]"
            chord_row += " "

        return f"[dim]mel [/] {mel_row}\n[dim]acc [/] {chord_row}"


# ── app principale ────────────────────────────────────────────────────────────

class MusicGenApp(App):
    TITLE   = "music-gen"
    CSS     = CSS
    BINDINGS = [
        Binding("g", "generate",    "Genera"),
        Binding("m", "export_midi", "MIDI"),
        Binding("w", "export_wav",  "WAV"),
        Binding("q", "quit",        "Esci"),
    ]

    # stato interno
    _score       = None
    _midi_path   = None
    _soundfont   = None

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal():
            # ── sidebar parametri ────────────────────────────────────────
            with Vertical(id="sidebar"):
                yield Label("SCALA", classes="section-title")
                yield Select(
                    [(n, k) for k, n in SCALE_LABELS.items()],
                    id="sel-scale",
                    value=ScaleType.PENTATONICA,
                )

                yield Label("TONALITÀ", classes="section-title")
                yield Select(
                    [(n, n) for n in ROOT_NOTES],
                    id="sel-root",
                    value="C",
                )

                yield Label("PROGRESSIONE", classes="section-title")
                yield Select(
                    [(k, k) for k in PROGRESSIONS],
                    id="sel-prog",
                    value="I-V-vi-IV",
                )

                yield Label("RITMO", classes="section-title")
                yield Select(
                    [(n, k) for k, n in RHYTHM_LABELS.items()],
                    id="sel-rhythm",
                    value=RhythmPattern.EIGHTH,
                )

                yield Rule()

                yield Label("BPM  (60–200)", classes="section-title")
                yield Input("100", id="sl-bpm", classes="param-input")

                yield Label("Ottave  (1–4)", classes="section-title")
                yield Input("2", id="sl-oct", classes="param-input")

                yield Label("Battute  (2–16)", classes="section-title")
                yield Input("4", id="sl-bars", classes="param-input")

                yield Label("Densità %  (10–100)", classes="section-title")
                yield Input("70", id="sl-den", classes="param-input")

                yield Label("Swing %  (0–50)", classes="section-title")
                yield Input("0", id="sl-swing", classes="param-input")

            # ── area principale ──────────────────────────────────────────
            with Vertical(id="main"):
                yield Label("Sequencer", classes="seq-title")
                yield SequencerDisplay(id="seq-display")

                yield Label("Log", classes="section-title")
                yield Log(id="log-box", auto_scroll=True)

                with Horizontal(id="btn-row"):
                    yield Button("⟳  Genera",        id="btn-generate", variant="primary")
                    yield Button("💾 Esporta MIDI",  id="btn-save-midi", variant="success")
                    yield Button("🔊 Esporta WAV",   id="btn-save-wav",  variant="success")

        yield Static("Pronto — premi G per generare", id="status-bar")
        yield Footer()

    # ── on mount ─────────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        self._soundfont = self._find_soundfont()
        log = self.query_one("#log-box", Log)
        if self._soundfont:
            log.write_line(f"Soundfont: {self._soundfont}")
        else:
            log.write_line("[WARN] Nessun soundfont trovato — solo esportazione MIDI")
        log.write_line("Imposta i parametri e premi G per generare.")

    def _find_soundfont(self) -> str | None:
        for p in SOUNDFONT_PATHS:
            if Path(p).exists():
                return p
        return None

    # ── helpers ───────────────────────────────────────────────────────────────

    def _get_int(self, id_: str, default: int, lo: int, hi: int) -> int:
        try:
            v = int(self.query_one(id_, Input).value)
            return max(lo, min(hi, v))
        except ValueError:
            return default

    def _build_config(self) -> GenConfig:
        scale  = self.query_one("#sel-scale",  Select).value
        root   = self.query_one("#sel-root",   Select).value
        prog   = self.query_one("#sel-prog",   Select).value
        rhythm = self.query_one("#sel-rhythm", Select).value
        bpm    = self._get_int("#sl-bpm",   100, 60,  200)
        oct_   = self._get_int("#sl-oct",   2,   1,   4)
        bars   = self._get_int("#sl-bars",  4,   2,   16)
        den    = self._get_int("#sl-den",   70,  10,  100) / 100
        swing  = self._get_int("#sl-swing", 0,   0,   50)  / 100

        return GenConfig(
            scale_type  = scale,
            progression = prog,
            rhythm      = rhythm,
            root_midi   = ROOT_MIDI[root],
            num_octaves = oct_,
            swing       = swing,
            density     = den,
            bpm         = bpm,
            num_bars    = bars,
        )

    def _set_status(self, msg: str) -> None:
        self.query_one("#status-bar", Static).update(msg)

    # ── azioni ───────────────────────────────────────────────────────────────

    @on(Button.Pressed, "#btn-generate")
    def action_generate(self) -> None:
        self._do_generate()

    @on(Button.Pressed, "#btn-save-midi")
    def action_export_midi(self) -> None:
        self._do_export_midi()

    @on(Button.Pressed, "#btn-save-wav")
    def action_export_wav(self) -> None:
        self._do_export_wav()

    # ── logica ────────────────────────────────────────────────────────────────

    @work(thread=True)
    def _do_generate(self) -> None:
        log = self.query_one("#log-box", Log)
        self.call_from_thread(self._set_status, "Generazione in corso...")
        try:
            cfg = self.call_from_thread(self._build_config)
            self.call_from_thread(log.write_line, f"Generando {cfg.num_bars} battute — {cfg.bpm} BPM…")

            score = generate(cfg)
            self._score = score

            # aggiorna sequencer display
            from musicgen.chord import build_progression, PROGRESSIONS
            prog_data  = PROGRESSIONS[cfg.progression]
            chords_seq = build_progression(cfg.root_midi, prog_data)
            chord_names = [c.name for c in chords_seq]

            from musicgen.rhythm import PATTERNS
            mel_pattern = PATTERNS[cfg.rhythm]

            seq = self.app.query_one("#seq-display", SequencerDisplay)
            self.call_from_thread(setattr, seq, "melody_steps", list(map(bool, mel_pattern)))
            self.call_from_thread(setattr, seq, "chord_names",  chord_names[:4])

            self.call_from_thread(log.write_line, "Generazione completata.")
            self.call_from_thread(self._set_status, "Pronto — M per MIDI, W per WAV")
        except Exception as ex:
            self.call_from_thread(log.write_line, f"[ERRORE] {ex}")
            self.call_from_thread(self._set_status, f"Errore: {ex}")

    @work(thread=True)
    def _do_export_wav(self) -> None:
        log = self.query_one("#log-box", Log)
        if self._score is None:
            self.call_from_thread(log.write_line, "Genera prima una composizione (G).")
            return
        if not self._soundfont:
            self.call_from_thread(log.write_line, "[ERRORE] fluidsynth o soundfont non trovato.")
            return
        try:
            # Crea MIDI temporaneo
            tmp_midi = tempfile.NamedTemporaryFile(suffix=".mid", delete=False)
            tmp_midi.close()
            self._score.write("midi", fp=tmp_midi.name)
            
            # Genera nome WAV personalizzato come per MIDI
            cfg  = self.call_from_thread(self._build_config)
            root = self.call_from_thread(
                lambda: self.query_one("#sel-root", Select).value
            )
            wav_name = f"output_{root}_{cfg.progression.replace('-','_')}_{cfg.bpm}bpm.wav"
            wav_path = Path.cwd() / wav_name
            
            self.call_from_thread(log.write_line, "Renderizzando audio WAV...")
            self.call_from_thread(self._set_status, "Generazione audio...")
            
            # fluidsynth -F output.wav soundfont.sf2 input.mid
            result = subprocess.run(
                ["fluidsynth", "-ni", "-F", str(wav_path), self._soundfont, tmp_midi.name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
            )
            
            # Rimuovi MIDI temporaneo
            Path(tmp_midi.name).unlink(missing_ok=True)
            
            if result.returncode == 0 and wav_path.exists():
                size_mb = wav_path.stat().st_size / (1024 * 1024)
                self.call_from_thread(log.write_line, f"✓ WAV salvato: {wav_name} ({size_mb:.1f} MB)")
                self.call_from_thread(self._set_status, f"Esportato: {wav_name}")
            else:
                err = result.stderr.decode() if result.stderr else "unknown error"
                self.call_from_thread(log.write_line, f"[ERRORE] Rendering fallito: {err}")
                
        except FileNotFoundError:
            self.call_from_thread(log.write_line, "[ERRORE] fluidsynth non trovato. Installa con: sudo apt install fluidsynth")
        except subprocess.TimeoutExpired:
            self.call_from_thread(log.write_line, "[ERRORE] Timeout durante il rendering")
        except Exception as ex:
            self.call_from_thread(log.write_line, f"[ERRORE] {ex}")

    @work(thread=True)
    def _do_export_midi(self) -> None:
        log = self.query_one("#log-box", Log)
        if self._score is None:
            self.call_from_thread(log.write_line, "Genera prima una composizione (G).")
            return
        try:
            cfg  = self.call_from_thread(self._build_config)
            root = self.call_from_thread(
                lambda: self.query_one("#sel-root", Select).value
            )
            name = f"output_{root}_{cfg.progression.replace('-','_')}_{cfg.bpm}bpm.mid"
            path = Path.cwd() / name
            self._score.write("midi", fp=str(path))
            self._midi_path = str(path)
            self.call_from_thread(log.write_line, f"Salvato: {path}")
            self.call_from_thread(self._set_status, f"Esportato: {name}")
        except Exception as ex:
            self.call_from_thread(log.write_line, f"[ERRORE] {ex}")


if __name__ == "__main__":
    MusicGenApp().run()
