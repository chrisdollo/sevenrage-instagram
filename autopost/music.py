"""Generated background music for Reels. Synthesised from scratch, so it is ours: no licence needed.

Three moods, matched to the tweet categories:
  calm     (A, going through it)  slow minor pads
  hopeful  (B, get back up)       major pads + soft arpeggio
  bounce   (C, laugh at it)       plucky arpeggio + light kick and hats
Each call varies key, voicing and tempo, so no two Reels sound identical.
"""
import numpy as np

SR = 44100


def _note(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def _env(n, attack, release):
    e = np.ones(n)
    a, r = int(attack * SR), int(release * SR)
    if a:
        e[:a] = np.linspace(0, 1, a)
    if r:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def _pad(freq, dur, bright=0.35):
    t = np.arange(int(dur * SR)) / SR
    wave = np.zeros_like(t)
    for h in range(1, 7):  # soft saw: decaying harmonics, slight detune for width
        amp = bright ** (h - 1) / h
        wave += amp * (np.sin(2 * np.pi * freq * h * t) + np.sin(2 * np.pi * freq * h * 1.003 * t)) / 2
    return wave * _env(len(t), dur * 0.35, dur * 0.4)


def _pluck(freq, dur=0.9, decay=5.0):
    t = np.arange(int(dur * SR)) / SR
    wave = sum(np.sin(2 * np.pi * freq * h * t) / h ** 1.6 for h in range(1, 5))
    return wave * np.exp(-decay * t) * _env(len(t), 0.004, 0.05)


def _kick(dur=0.35):
    t = np.arange(int(dur * SR)) / SR
    f = 50 + 70 * np.exp(-25 * t)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-9 * t)


def _hat(rng, dur=0.06):
    n = int(dur * SR)
    noise = rng.standard_normal(n)
    noise = np.diff(noise, prepend=0)  # crude high-pass
    return noise * np.exp(-60 * np.arange(n) / SR) * 0.25


def _add(buf, sig, start):
    i = int(start * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i]


def _echo(x, delay=0.27, fb=0.35, mix=0.3):
    d = int(delay * SR)
    y = x.copy()
    for k in range(1, 5):
        if d * k >= len(x):
            break
        y[d * k:] += x[: len(x) - d * k] * (fb ** k) * mix
    return y


PROGS = {
    "calm": [[0, 3, 7], [-4, 0, 3], [-9, -5, 0], [-2, 2, 5]],      # i - VI - III - VII (minor)
    "hopeful": [[0, 4, 7], [7, 11, 14], [9, 12, 16], [5, 9, 12]],   # I - V - vi - IV
    "bounce": [[0, 4, 7], [5, 9, 12], [7, 11, 14], [0, 4, 7]],      # I - IV - V - I
}


def generate(mood, seconds, rng):
    """Return stereo float32 audio (n, 2) for the given mood. rng is a random.Random."""
    rng = np.random.default_rng(rng.randrange(2 ** 32))
    n = int(seconds * SR)
    buf = np.zeros(n)
    root = 57 + int(rng.integers(-3, 4))  # around A3
    prog = PROGS[mood]
    chord_len = seconds / len(prog)

    for ci, chord in enumerate(prog):
        start = ci * chord_len
        for iv in chord:
            buf_part = _pad(_note(root + iv), chord_len + 0.6, bright=0.25 if mood == "calm" else 0.35)
            _add(buf, buf_part * (0.16 if mood == "calm" else 0.11), start)
        _add(buf, _pad(_note(root + chord[0] - 12), chord_len + 0.6, 0.2) * 0.12, start)  # bass

        if mood in ("hopeful", "bounce"):
            bpm = float(rng.integers(84, 96) if mood == "hopeful" else rng.integers(100, 112))
            step = 60 / bpm / 2
            pattern = chord + [chord[1] + 12, chord[2], chord[0] + 12]
            k = 0
            while k * step < chord_len - 0.05:
                note = pattern[k % len(pattern)] + 12
                _add(buf, _pluck(_note(root + note), decay=6 if mood == "bounce" else 3.5) *
                     (0.13 if mood == "bounce" else 0.09), start + k * step)
                k += 1

    if mood == "bounce":
        bpm = 104
        beat = 60 / bpm
        b = 0
        while b * beat < seconds - 0.2:
            if b % 2 == 0:
                _add(buf, _kick() * 0.5, b * beat)
            _add(buf, _hat(rng), b * beat + beat / 2)
            b += 1

    buf = _echo(buf, mix=0.35 if mood == "calm" else 0.22)
    buf *= _env(n, 0.3, 0.9)
    peak = np.max(np.abs(buf)) or 1.0
    buf = buf / peak * 0.5
    right = np.roll(buf, int(0.012 * SR)) * 0.95 + buf * 0.05  # small stereo spread
    return np.stack([buf, right], axis=1).astype(np.float32)


def silence(seconds):
    return np.zeros((int(seconds * SR), 2), dtype=np.float32)


def write_wav(path, audio):
    import wave
    pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
