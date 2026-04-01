#!/usr/bin/env python3
"""
generate_soundtrack.py — Synthesise an 8-bit / chiptune parody recreation
of the iconic "Never Gonna Give You Up" intro riff.

Pure waveform synthesis (no samples, no copyrighted material).
Outputs embed/audio/agi_theme.wav  (and .m4a via ffmpeg if available).

Notes extracted from a MIDI transcription of the original (Db major, 113 BPM).
The STRINGS track carries the iconic synth hook; SYN BASS 2 carries the bass.
"""

import math
import struct
import wave
import os
import subprocess

SAMPLE_RATE = 44100
BPM = 113
BEAT = 60.0 / BPM
MASTER_VOL = 0.45

# ── Waveform generators ──────────────────────────────────────────

def square_wave(freq, t, duty=0.5):
    if freq == 0:
        return 0.0
    phase = (t * freq) % 1.0
    return 1.0 if phase < duty else -1.0

def saw_wave(freq, t):
    if freq == 0:
        return 0.0
    phase = (t * freq) % 1.0
    return 2.0 * phase - 1.0

def triangle_wave(freq, t):
    if freq == 0:
        return 0.0
    phase = (t * freq) % 1.0
    return 4.0 * abs(phase - 0.5) - 1.0

def noise(t):
    x = int(t * SAMPLE_RATE) & 0xFFFF
    x ^= x << 7 & 0xFFFF
    x ^= x >> 9
    x ^= x << 8 & 0xFFFF
    return (x / 32768.0) - 1.0

def sine_wave(freq, t):
    if freq == 0:
        return 0.0
    return math.sin(2.0 * math.pi * freq * t)

# ── Envelopes ─────────────────────────────────────────────────────

def adsr(t, dur, a=0.01, d=0.05, s=0.7, r=0.08):
    if t < 0:
        return 0.0
    if t < a:
        return t / a
    t2 = t - a
    if t2 < d:
        return 1.0 - (1.0 - s) * (t2 / d)
    t3 = t - a - d
    sustain_dur = dur - a - d - r
    if sustain_dur < 0:
        sustain_dur = 0
    if t3 < sustain_dur:
        return s
    t4 = t3 - sustain_dur
    if t4 < r:
        return s * (1.0 - t4 / r)
    return 0.0

def exp_decay(t, dur, tau=0.15):
    if t < 0 or t > dur:
        return 0.0
    return math.exp(-t / tau)

# ── Note helpers ──────────────────────────────────────────────────

NOTE_FREQS = {}
_note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
for _oct in range(0, 9):
    for _i, _n in enumerate(_note_names):
        midi = (_oct + 1) * 12 + _i
        NOTE_FREQS[f"{_n}{_oct}"] = 440.0 * (2.0 ** ((midi - 69) / 12.0))

_flat_map = {'Db': 'C#', 'Eb': 'D#', 'Fb': 'E', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#', 'Cb': 'B'}
for _oct in range(0, 9):
    for _flat, _sharp in _flat_map.items():
        NOTE_FREQS[f"{_flat}{_oct}"] = NOTE_FREQS[f"{_sharp}{_oct}"]

def note_freq(name):
    if name in ('R', 'rest', '-', ''):
        return 0.0
    return NOTE_FREQS[name]

def midi_to_name(n):
    octave = (n // 12) - 1
    name = _note_names[n % 12]
    return f"{name}{octave}"

def freq_from_midi(n):
    return note_freq(midi_to_name(n))

# ── Instrument renderers ─────────────────────────────────────────

def render_bass(freq, t, dur):
    env = adsr(t, dur, a=0.005, d=0.06, s=0.55, r=0.03)
    s = 0.65 * saw_wave(freq, t) + 0.35 * square_wave(freq, t, 0.25)
    return s * env * 0.60

def render_lead(freq, t, dur):
    env = adsr(t, dur, a=0.008, d=0.08, s=0.7, r=0.12)
    s = 0.6 * square_wave(freq, t, 0.5) + 0.25 * square_wave(freq * 1.004, t, 0.45) + 0.15 * saw_wave(freq, t)
    return s * env * 0.38

def render_pad(freq, t, dur):
    env = adsr(t, dur, a=0.12, d=0.15, s=0.45, r=0.25)
    s = 0.7 * triangle_wave(freq, t) + 0.3 * sine_wave(freq, t)
    return s * env * 0.18

def render_epiano(freq, t, dur):
    env = adsr(t, dur, a=0.005, d=0.15, s=0.35, r=0.15)
    s = 0.5 * sine_wave(freq, t) + 0.3 * sine_wave(freq * 2, t) + 0.2 * triangle_wave(freq, t)
    return s * env * 0.25

def render_kick(t, dur):
    env = exp_decay(t, dur, tau=0.12)
    pitch = 150 * math.exp(-t * 30) + 50
    return sine_wave(pitch, t) * env * 0.65

def render_snare(t, dur):
    env = exp_decay(t, dur, tau=0.07)
    body_env = exp_decay(t, dur, tau=0.04)
    return (0.6 * noise(t) * env + 0.4 * sine_wave(200, t) * body_env) * 0.45

def render_hihat(t, dur):
    env = exp_decay(t, dur, tau=0.025)
    return noise(t) * env * 0.22

# ── Silly sound effect renderers ─────────────────────────────────

def load_anime_wow():
    """Load the real anime wow sample from embed/audio/anime_wow.mp3."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    mp3_path = os.path.join(repo_root, "embed", "audio", "anime_wow.mp3")
    raw_path = os.path.join("/tmp", "anime_wow_mono.raw")
    subprocess.run(
        ["ffmpeg", "-y", "-i", mp3_path, "-ac", "1", "-ar", str(SAMPLE_RATE),
         "-f", "s16le", "-acodec", "pcm_s16le", raw_path],
        check=True, capture_output=True,
    )
    data = open(raw_path, "rb").read()
    n = len(data) // 2
    samples = struct.unpack(f"<{n}h", data)
    peak = max(abs(s) for s in samples) or 1
    return [s / peak for s in samples]

def render_vinyl_scratch(t, dur):
    """Record scratch: sweeping noise burst."""
    freq = 800 + 3000 * (1.0 - t / dur) if t < dur else 800
    env = exp_decay(t, dur, tau=0.08)
    n = noise(t + 0.1)
    tone = sine_wave(freq, t) * 0.3
    return (n * 0.7 + tone) * env * 0.50

def render_airhorn(t, dur):
    """MLG airhorn: stacked square waves with slight vibrato."""
    vib = 1.0 + 0.008 * math.sin(2 * math.pi * 6 * t)
    base = 540 * vib
    env = adsr(t, dur, a=0.01, d=0.05, s=0.85, r=0.15)
    s = (0.5 * square_wave(base, t, 0.5) +
         0.3 * square_wave(base * 1.5, t, 0.4) +
         0.2 * saw_wave(base * 2, t))
    return s * env * 0.30

def render_fart(t, dur):
    """Low rumble + noise = classic comedy sound."""
    freq = 60 + 20 * math.sin(2 * math.pi * 8 * t)
    env = adsr(t, dur, a=0.02, d=0.1, s=0.6, r=0.15)
    body = saw_wave(freq, t) * 0.5 + square_wave(freq * 0.5, t, 0.3) * 0.3
    n = noise(t) * 0.4
    return (body + n) * env * 0.35

# SFX placement (time in seconds relative to music start, duration, renderer)
sfx_events_spec = [
    # Vinyl scratch right before the bass drops
    (-0.3, 0.25, render_vinyl_scratch),
    # Airhorn right after second descending run (~8s in)
    (8.0, 0.7, render_airhorn),
    # Fart tucked in at the quiet gap before 3rd descending run
    (11.5, 0.35, render_fart),
    # Final airhorn at the very end
    (14.8, 0.9, render_airhorn),
]

# Anime wow sample placement: (start_time_sec, volume_scale)
# Placed at the very beginning (before music) and at the end
WOW_LEAD_TIME = 4.5  # wow is ~4.2s; start it this much before the music
WOW_END_OFFSET = 13.0  # seconds into the music for the ending wow

def render_sfx(total_samples):
    """Render all silly synth sound effects."""
    events = []
    for t_start, dur, renderer in sfx_events_spec:
        n_samp = int(dur * SAMPLE_RATE)
        start_samp = int(t_start * SAMPLE_RATE)
        if start_samp < 0:
            skip = -start_samp
            buf = [renderer((i + skip) / SAMPLE_RATE, dur) for i in range(max(0, n_samp - skip))]
            events.append((0, buf))
        else:
            buf = [renderer(i / SAMPLE_RATE, dur) for i in range(n_samp)]
            events.append((start_samp, buf))
    return events

def render_wow_events(wow_samples, music_offset):
    """Place the real anime wow sample at beginning and end."""
    events = []
    vol = 0.55
    scaled = [s * vol for s in wow_samples]
    # Beginning: starts before the music, so at sample 0 of the final buffer
    # (the music is shifted forward by music_offset)
    events.append((0, scaled[:]))
    # End: over the last part of the music
    end_start = int((music_offset + WOW_END_OFFSET) * SAMPLE_RATE)
    events.append((end_start, scaled[:]))
    return events

# ── Song data from MIDI ──────────────────────────────────────────
# Extracted from actual MIDI transcription. Key: Db major, 113 BPM.
# Times converted to beat positions (time_sec / BEAT).
#
# Format: list of (note_name, start_beat, duration_beats)
# This is more accurate than sequential note lists since the MIDI
# has precise timing.

def time_to_beat(sec):
    return sec / BEAT

# SYN BASS 2 (Track 2) — the iconic bass riff
# First ~17 seconds = first 4 bars repeated twice
# MIDI notes: D#1=27, F1=29, G#1=32, A#1=34, C2=36, C#2=37
bass_midi = [
    # Bar 1: D#1 hits then C2-A#1 descending
    (27, 6.37), (27, 6.63), (27, 6.77),
    (36, 7.03), (34, 7.16),
    (32, 7.43), (32, 7.69),
    # Bar 2: D#1-G#1 then F1 repeated, C2-A#1
    (27, 8.22), (32, 8.36),
    (29, 8.50), (29, 8.76), (29, 8.89),
    (36, 9.16), (34, 9.30),
    # Bar 3: A#1 repeated, C2, A#1
    (34, 9.83), (34, 9.96), (34, 10.09),
    (36, 10.23), (34, 10.49),
    # Bar 4: D#1 hits, C2-A#1, G#1
    (27, 10.62), (27, 10.88), (27, 11.02),
    (36, 11.29), (34, 11.42),
    (32, 11.68), (32, 11.95),
    # Bar 5: G#1 repeated, F1 repeated, C2-A#1
    (32, 12.48), (32, 12.61),
    (29, 12.74), (29, 13.00), (29, 13.14),
    (36, 13.41), (34, 13.55),
    # Bar 6: G#1 repeated, C#2, D#1 start of next repeat
    (32, 14.08), (32, 14.34), (32, 14.47),
    (37, 14.73),
]

# Offset: bass starts at ~6.37s. We zero-base it.
BASS_OFFSET = 6.37

# STRINGS (Track 11) — the iconic synth melody hook
# C#5=73, C#6=85, D#5=75, D#6=87, F5=77, F6=89, F#5=78, F#6=90,
# G#4=68, G#5=80, G#6=92
strings_midi = [
    # Bar 1: C#5/C#6
    (85, 6.39), (73, 6.39),
    # D#5/D#6
    (87, 7.15), (75, 7.15),
    # G#4/G#5 (brief)
    (80, 7.94), (68, 7.94),
    # Bar 2: D#5/D#6
    (87, 8.45), (75, 8.45),
    # F5/F6
    (89, 9.30), (77, 9.30),
    # Bar 3: G#5/G#6 - F#5/F#6 - F5/F6 - C#5/C#6 (the descending run!)
    (92, 10.06), (80, 10.06),
    (90, 10.18), (78, 10.18),
    (89, 10.30), (77, 10.30),
    (85, 10.45), (73, 10.45),
    # Bar 4: D#5/D#6
    (87, 11.40), (75, 11.40),
    # G#4/G#5
    (80, 12.21), (68, 12.21),
    # (gap — bars 5-6 strings are sparse, then repeat)
    # Bar 7: descending run again
    (92, 14.34), (80, 14.34),
    (90, 14.46), (78, 14.46),
    (89, 14.59), (77, 14.59),
    (85, 14.73), (73, 14.73),
    # D#5/D#6
    (87, 15.65), (75, 15.65),
    # G#4/G#5
    (80, 16.43), (68, 16.43),
    # D#5/D#6
    (87, 16.98), (75, 16.98),
    # F5/F6
    (89, 17.79), (77, 17.79),
    # Descending run (3rd time)
    (92, 18.61), (80, 18.61),
    (90, 18.72), (78, 18.72),
    (89, 18.84), (77, 18.84),
    (85, 18.99), (73, 18.99),
    # D#5/D#6
    (87, 19.88), (75, 19.88),
    # G#4/G#5
    (80, 20.68), (68, 20.68),
]

STRINGS_OFFSET = 6.39

# E.PIANO 2 (Track 1) — chord stabs
# These are clusters: F#3/A#3/C#4/F4, G#3/A#3/C4/D#4, G#3/C4/D#4, F3/G#3/C#4
epiano_chords = [
    # Chord 1: F#3(54) A#3(58) C#4(61) F4(65) at ~6.41s
    ([54, 58, 61, 65], 6.41, 0.7),
    # Chord 2: G#3(56) A#3(58) C4(60) D#4(63) at ~7.18s
    ([56, 58, 60, 63], 7.18, 1.2),
    # Chord 3: G#3(56) C4(60) D#4(63) at ~8.48s
    ([56, 60, 63], 8.48, 0.75),
    # Chord 4: F3(53) G#3(56) C#4(61) at ~9.30s
    ([53, 56, 61], 9.30, 1.2),
    # Repeat pattern
    ([54, 58, 61, 65], 10.64, 0.7),
    ([56, 58, 60, 63], 11.42, 1.2),
    ([56, 60, 63], 12.73, 0.75),
    ([53, 56, 61], 13.55, 1.2),
    # 3rd repeat
    ([54, 58, 61, 65], 14.85, 0.7),
    ([56, 58, 60, 63], 15.67, 1.2),
    ([56, 60, 63], 16.99, 0.75),
    ([53, 56, 61], 17.79, 1.2),
    # 4th repeat
    ([54, 58, 61, 65], 19.12, 0.7),
    ([56, 58, 60, 63], 19.93, 0.95),
    ([56, 60, 63], 20.97, 0.45),
    ([53, 56, 61, 65], 21.50, 1.7),
]

EPIANO_OFFSET = 6.41

# ── Drum pattern from MIDI ──
# Kick (B1=35), Snare (E2=40 + D#2=39), HH closed (G#2=44), HH open (A#2=46)
# The pattern repeats every 2 beats roughly.
# Simplified to a grid: K on 1 and 3, S on 2 and 4, HH on 8ths
drum_pattern = "K.H.S.H.K.HHS.HH"

# How long the intro runs before we'd loop
INTRO_END = 21.5   # seconds from absolute MIDI time
TOTAL_TIME = INTRO_END - BASS_OFFSET + 1.0  # ~16s of music
TOTAL_BARS = int(TOTAL_TIME / (4 * BEAT)) + 1

# ── Render from timed events ─────────────────────────────────────

def render_timed_bass(offset, midi_events, total_samples):
    """Render bass from (midi_note, abs_time) pairs."""
    events = []
    for i, (note, abs_t) in enumerate(midi_events):
        t_local = abs_t - offset
        if t_local < 0:
            continue
        # Duration: until next note or 0.2s
        if i + 1 < len(midi_events):
            dur = midi_events[i + 1][1] - abs_t
            dur = min(dur, 0.4)
        else:
            dur = 0.2
        dur = max(dur, 0.05)
        freq = freq_from_midi(note)
        n_samp = int(dur * SAMPLE_RATE)
        start_samp = int(t_local * SAMPLE_RATE)
        buf = [render_bass(freq, j / SAMPLE_RATE, dur) for j in range(n_samp)]
        events.append((start_samp, buf))
    return events

def render_timed_strings(offset, midi_events, total_samples):
    """Render strings melody from (midi_note, abs_time) pairs."""
    events = []
    # Group simultaneous notes (octave doubles)
    groups = {}
    for note, abs_t in midi_events:
        key = round(abs_t, 2)
        if key not in groups:
            groups[key] = []
        groups[key].append(note)

    sorted_times = sorted(groups.keys())
    for idx, t_abs in enumerate(sorted_times):
        t_local = t_abs - offset
        if t_local < 0:
            continue
        notes = groups[t_abs]
        if idx + 1 < len(sorted_times):
            dur = sorted_times[idx + 1] - t_abs
            dur = min(dur, 1.5)
        else:
            dur = 0.8
        dur = max(dur, 0.1)
        n_samp = int(dur * SAMPLE_RATE)
        start_samp = int(t_local * SAMPLE_RATE)
        buf = [0.0] * n_samp
        for note in notes:
            freq = freq_from_midi(note)
            for j in range(n_samp):
                buf[j] += render_lead(freq, j / SAMPLE_RATE, dur)
        n = len(notes)
        if n > 1:
            buf = [x / (n * 0.7) for x in buf]
        events.append((start_samp, buf))
    return events

def render_timed_epiano(offset, chord_events, total_samples):
    """Render e-piano chord stabs."""
    events = []
    for midi_notes, abs_t, dur in chord_events:
        t_local = abs_t - offset
        if t_local < 0:
            continue
        n_samp = int(dur * SAMPLE_RATE)
        start_samp = int(t_local * SAMPLE_RATE)
        buf = [0.0] * n_samp
        for note in midi_notes:
            freq = freq_from_midi(note)
            for j in range(n_samp):
                buf[j] += render_epiano(freq, j / SAMPLE_RATE, dur)
        n = len(midi_notes)
        if n > 1:
            buf = [x / (n * 0.6) for x in buf]
        events.append((start_samp, buf))
    return events

def render_drums(total_time):
    events = []
    sixteenth = BEAT / 4
    total_bars = int(total_time / (4 * BEAT)) + 1
    for bar in range(total_bars):
        for slot, ch in enumerate(drum_pattern):
            t = (bar * 4 + slot * 0.25) * BEAT
            if t > total_time:
                break
            dur = sixteenth * 0.9
            n_samp = int(dur * SAMPLE_RATE)
            start_samp = int(t * SAMPLE_RATE)
            if ch == 'K':
                buf = [render_kick(i / SAMPLE_RATE, dur) for i in range(n_samp)]
                events.append((start_samp, buf))
            elif ch == 'S':
                buf = [render_snare(i / SAMPLE_RATE, dur) for i in range(n_samp)]
                events.append((start_samp, buf))
            elif ch == 'H':
                buf = [render_hihat(i / SAMPLE_RATE, dur) for i in range(n_samp)]
                events.append((start_samp, buf))
    return events

def mix_events(all_events, total_samples):
    buf = [0.0] * total_samples
    for events in all_events:
        for start, samples in events:
            for i, s in enumerate(samples):
                idx = start + i
                if 0 <= idx < total_samples:
                    buf[idx] += s
    return buf

def soft_clip(x, threshold=0.8):
    if x > threshold:
        return threshold + (1.0 - threshold) * math.tanh((x - threshold) / (1.0 - threshold))
    elif x < -threshold:
        return -(threshold + (1.0 - threshold) * math.tanh((-x - threshold) / (1.0 - threshold)))
    return x

def write_wav(filename, buf):
    peak = max(abs(x) for x in buf) or 1.0
    scale = MASTER_VOL / peak
    with wave.open(filename, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        frames = b''
        for x in buf:
            x = soft_clip(x * scale)
            sample = max(-32767, min(32767, int(x * 32767)))
            frames += struct.pack('<h', sample)
        wf.writeframes(frames)

def main():
    print("🎵 Generating AGI theme (chiptune parody from MIDI data)...")

    print("  Loading anime wow sample...")
    wow_samples = load_anime_wow()
    wow_dur = len(wow_samples) / SAMPLE_RATE
    print(f"    wow duration: {wow_dur:.2f}s")

    # The wow plays first, then music kicks in 1s later (big overlap)
    music_offset = 1.0
    final_duration = music_offset + TOTAL_TIME + wow_dur + 1.0
    total_samples = int(final_duration * SAMPLE_RATE)

    # Shift all music events forward by music_offset
    music_shift = int(music_offset * SAMPLE_RATE)

    def shift_events(events):
        return [(start + music_shift, buf) for start, buf in events]

    print("  Rendering bass (SYN BASS 2)...")
    bass_events = shift_events(render_timed_bass(BASS_OFFSET, bass_midi, total_samples))

    print("  Rendering strings melody...")
    strings_events = shift_events(render_timed_strings(STRINGS_OFFSET, strings_midi, total_samples))

    print("  Rendering e-piano chords...")
    epiano_events = shift_events(render_timed_epiano(EPIANO_OFFSET, epiano_chords, total_samples))

    print("  Rendering drums...")
    drum_events = shift_events(render_drums(TOTAL_TIME))

    print("  Rendering SFX (vinyl scratch, airhorn, fart)...")
    sfx_raw = render_sfx(total_samples)
    sfx = shift_events(sfx_raw)

    print("  Placing anime wow (beginning + end)...")
    wow_events = render_wow_events(wow_samples, music_offset)

    print("  Mixing...")
    mixed = mix_events([bass_events, strings_events, epiano_events, drum_events, sfx, wow_events], total_samples)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    audio_dir = os.path.join(repo_root, "embed", "audio")
    os.makedirs(audio_dir, exist_ok=True)

    wav_path = os.path.join(audio_dir, "agi_theme.wav")
    write_wav(wav_path, mixed)
    print(f"  ✓ WAV: {wav_path}")

    m4a_path = os.path.join(audio_dir, "agi_theme.m4a")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", wav_path, "-c:a", "aac", "-b:a", "128k", m4a_path],
            check=True, capture_output=True,
        )
        print(f"  ✓ M4A: {m4a_path}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  ⚠ ffmpeg not available — skipping m4a conversion")

    print(f"\nDone! ~{final_duration:.1f}s of chiptune rickroll with wow.")
    print(f"\nTo use with agi-cli:")
    print(f"  AGI_AUDIO={wav_path} ./agi")
    print(f"  — or copy to ~/.config/agi-cli/audio.wav")

if __name__ == "__main__":
    main()
