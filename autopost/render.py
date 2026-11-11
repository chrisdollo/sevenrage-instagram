"""Bone & Ink post renderer: 1080x1350 feed images and 1080x1920 Reels.

Fonts are free (OFL) stand-ins so this runs on any machine:
Inter for the tweet style (Helvetica-like), Gelasio for the quote style (Georgia-like).
"""
import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

from content import ROOT, attribution
import music

FONTS = Path(__file__).resolve().parent / "fonts"
BG, INK, MUTED, ACCENT = (0xEF, 0xEA, 0xE0), (0x14, 0x14, 0x14), (0x7A, 0x72, 0x68), (0xB4, 0x46, 0x2B)
NAME, HANDLE = "7rage", "@sevenrage7"
W, H = 1080, 1350
RW, RH, FPS, SECONDS = 1080, 1920, 30, 7

_cache = {}


def font(name, size, weight=400):
    key = (name, size, weight)
    if key not in _cache:
        f = ImageFont.truetype(str(FONTS / name), size)
        axes = [a["name"] for a in f.get_variation_axes()]
        f.set_variation_by_axes([min(32, max(14, size)) if a == b"Optical size" else weight for a in axes])
        _cache[key] = f
    return _cache[key]


def wrap(text, f, width):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if f.getlength(trial) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit(text, name, weight, width, max_h, start, minimum, line_h):
    size = start
    while True:
        f = font(name, size, weight)
        lines = wrap(text, f, width)
        if len(lines) * size * line_h <= max_h or size <= minimum:
            return f, lines, size
        size -= 2


def draw_lines(d, lines, f, size, x, y, color, line_h):
    for i, ln in enumerate(lines):
        d.text((x, y + i * size * line_h), ln, font=f, fill=color)


def spaced(d, xy, text, f, color, tracking):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=color)
        x += f.getlength(ch) + tracking
    return x


def avatar(size):
    logo = Image.open(ROOT / "logo.png").convert("RGB").resize((size * 4, size * 4), Image.LANCZOS)
    mask = Image.new("L", logo.size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, *logo.size), fill=255)
    logo.putalpha(mask)
    return logo.resize((size, size), Image.LANCZOS)


def tweet(text):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    x, tw, lh = 90, W - 180, 1.32
    f, lines, size = fit(text, "Inter.ttf", 400, tw, 620, 62, 40, lh)
    body_h = len(lines) * size * lh
    top = int((H - (180 + body_h)) / 2)
    img.paste(av := avatar(130), (x, top), av)
    d.ellipse((x, top, x + 130, top + 130), outline=(0xCF, 0xC8, 0xBC), width=2)
    d.text((x + 160, top + 14), NAME, font=font("Inter.ttf", 48, 700), fill=INK)
    d.text((x + 160, top + 74), HANDLE, font=font("Inter.ttf", 42, 400), fill=MUTED)
    draw_lines(d, lines, f, size, x, top + 180, INK, lh)
    return img


def quote(text, source):
    author, work = attribution(source)
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    x, tw, lh = 130, W - 260, 1.3
    f, lines, size = fit(text, "Gelasio-Italic.ttf", 400, tw, 600, 70, 42, lh)
    body_h = len(lines) * size * lh
    work_h = 50 if work else 0
    top = int((H - (170 + body_h + 70 + 40 + work_h)) / 2)
    d.text((x - 8, top - 70), "“", font=font("Gelasio.ttf", 300, 700), fill=ACCENT)
    draw_lines(d, lines, f, size, x, top + 170, INK, lh)
    ay = int(top + 170 + body_h + 60)
    d.rectangle((x, ay + 20, x + 70, ay + 25), fill=ACCENT)
    spaced(d, (x + 95, ay), author, font("Inter.ttf", 32, 600), INK, 5)
    if work:
        d.text((x + 95, ay + 50), work, font=font("Gelasio-Italic.ttf", 32, 400), fill=MUTED)
    hf = font("Inter.ttf", 28, 500)
    hw = sum(hf.getlength(c) + 2 for c in HANDLE)
    spaced(d, ((W - hw) / 2, H - 105), HANDLE, hf, MUTED, 2)
    return img


def reel(post, out_path, mood=None, rng=None):
    """7-second 9:16 video: the post on bone with a slow push-in. mood=None means a silent track
    (Instagram is happier with an audio stream present, even a silent one)."""
    import numpy as np
    audio = music.generate(mood, SECONDS, rng) if mood else music.silence(SECONDS)
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "a.wav"
        music.write_wav(wav, audio)
        cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{RW}x{RH}", "-r", str(FPS), "-i", "-",
               "-i", str(wav), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high",
               "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
               "-shortest", "-movflags", "+faststart", str(out_path)]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        frames = FPS * SECONDS
        canvas = Image.new("RGB", (RW, RH), BG)
        for i in range(frames):
            t = i / (frames - 1)
            s = 1 + 0.04 * (t * t * (3 - 2 * t))
            w, h = round(W * s), round(H * s)
            frame = canvas.copy()
            frame.paste(post.resize((w, h), Image.BICUBIC), ((RW - w) // 2, (RH - h) // 2))
            p.stdin.write(np.asarray(frame).tobytes())
        p.stdin.close()
        if p.wait() != 0:
            raise RuntimeError("ffmpeg failed")
