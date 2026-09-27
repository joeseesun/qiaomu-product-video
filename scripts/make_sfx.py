#!/usr/bin/env python3
"""Synthesize an original UI sound-effect kit (48 kHz mono WAV, peak -3 dBFS).

    python3 make_sfx.py --out assets/sfx [--only click,pop] [--seed 3] [--bright 1.0]

Sounds: click, click-alt, pop, toggle, typing, ding-dong, success, error, whoosh, riser, impact.
Peaks are normalized to -3 dBFS so gains behave like recorded libraries. Tweak --bright
(0.6 warmer … 1.5 brighter) to match the product's character. Stdlib only.

Copyright (c) 向阳乔木 — MIT License.
"""
from __future__ import annotations

import argparse
import array
import json
import math
import random
import sys
import wave
from pathlib import Path

SR = 48000
TAU = 2 * math.pi


def buf(seconds: float) -> list[float]:
    return [0.0] * int(SR * seconds)


def add_tone(out, start, dur, freq, amp=1.0, decay=20.0, attack=0.002, sweep_to=None, harmonics=((1, 1.0),)):
    n0, n = int(start * SR), int(dur * SR)
    phase = [0.0] * len(harmonics)
    for i in range(n):
        if n0 + i >= len(out):
            break
        t = i / SR
        f = freq if sweep_to is None else freq * (sweep_to / freq) ** (t / dur)
        env = (min(1.0, t / attack) if attack > 0 else 1.0) * math.exp(-decay * t)
        s = 0.0
        for k, (mult, a) in enumerate(harmonics):
            phase[k] += TAU * f * mult / SR
            s += a * math.sin(phase[k])
        out[n0 + i] += amp * env * s


def add_noise(out, start, dur, amp=1.0, decay=40.0, attack=0.0005, rng=None, lp=0.5, hp=0.0, shape=None):
    """Filtered noise burst. lp/hp are one-pole coefficients (0..1). shape(t)->gain overrides envelope."""
    rng = rng or random.Random(1)
    n0, n = int(start * SR), int(dur * SR)
    low = high_prev_in = high_prev_out = 0.0
    for i in range(n):
        if n0 + i >= len(out):
            break
        t = i / SR
        x = rng.uniform(-1, 1)
        c = lp(t / dur) if callable(lp) else lp
        low += c * (x - low)
        y = low
        if hp:
            hy = hp * (high_prev_out + y - high_prev_in)
            high_prev_in, high_prev_out = y, hy
            y = hy
        env = shape(t / dur) if shape else (min(1.0, t / attack) if attack else 1.0) * math.exp(-decay * t)
        out[n0 + i] += amp * env * y


def normalize(out, peak_db=-3.0):
    peak = max(1e-9, max(abs(v) for v in out))
    g = 10 ** (peak_db / 20) / peak
    # 3 ms fade-out to avoid clicks at the tail
    tail = int(0.003 * SR)
    for i in range(len(out)):
        out[i] *= g
        if i >= len(out) - tail:
            out[i] *= (len(out) - i) / tail
    return out


def write(path: Path, out):
    data = array.array("h", (max(-32767, min(32767, int(v * 32767))) for v in out))
    if sys.byteorder == "big":
        data.byteswap()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def make(name: str, rng: random.Random, bright: float):
    b = bright
    if name in ("click", "click-alt"):
        f = (3200 if name == "click" else 2500) * b
        o = buf(0.06)
        add_noise(o, 0, 0.012, amp=0.8, decay=400, lp=0.6, hp=0.7, rng=rng)
        add_tone(o, 0, 0.05, f, amp=0.5, decay=120, attack=0.0005)
        add_tone(o, 0, 0.05, f * 0.5, amp=0.3, decay=90, attack=0.0005)
        return o
    if name == "pop":
        o = buf(0.12)
        add_tone(o, 0, 0.1, 380 * b, sweep_to=980 * b, amp=1.0, decay=38, attack=0.001)
        return o
    if name == "toggle":
        o = buf(0.12)
        add_tone(o, 0, 0.04, 1800 * b, amp=0.8, decay=150, attack=0.0005)
        add_tone(o, 0.035, 0.05, 2600 * b, amp=0.7, decay=140, attack=0.0005)
        return o
    if name == "typing":
        o = buf(0.75)
        t = 0.0
        while t < 0.62:
            add_noise(o, t, 0.02, amp=rng.uniform(0.55, 0.9), decay=320, lp=rng.uniform(0.35, 0.6), hp=0.6, rng=rng)
            add_tone(o, t, 0.03, rng.uniform(1400, 2200) * b, amp=0.25, decay=200, attack=0.0005)
            t += rng.uniform(0.06, 0.11)
        return o
    bell = ((1, 1.0), (2.0, 0.35), (3.01, 0.12), (4.2, 0.06))
    if name == "ding-dong":
        o = buf(1.2)
        add_tone(o, 0, 1.0, 1318.5 * b, amp=0.8, decay=4.5, attack=0.003, harmonics=bell)  # E6
        add_tone(o, 0.22, 0.95, 1046.5 * b, amp=0.8, decay=4.0, attack=0.003, harmonics=bell)  # C6
        return o
    if name == "success":
        o = buf(0.9)
        for k, f in enumerate((1046.5, 1318.5, 1568.0)):  # C6 E6 G6
            add_tone(o, k * 0.075, 0.7, f * b, amp=0.6, decay=6.5, attack=0.002, harmonics=bell)
        return o
    if name == "error":
        o = buf(0.45)
        sq = ((1, 1.0), (3, 0.3), (5, 0.15))
        add_tone(o, 0, 0.16, 330, amp=0.6, decay=10, attack=0.002, harmonics=sq)
        add_tone(o, 0.17, 0.22, 262, amp=0.6, decay=9, attack=0.002, harmonics=sq)
        return o
    if name == "whoosh":
        o = buf(0.8)
        # band sweeps up then settles; loudest ~0.45 s — align the PEAK to the cut
        add_noise(o, 0, 0.8, amp=1.0, rng=rng, lp=lambda x: 0.05 + 0.5 * math.sin(math.pi * min(1, x * 1.1)) * b,
                  hp=0.3, shape=lambda x: math.sin(math.pi * min(1.0, x / 0.56)) ** 2 if x < 0.56 else math.exp(-9 * (x - 0.56)))
        return o
    if name == "riser":
        o = buf(1.6)
        add_noise(o, 0, 1.6, amp=0.7, rng=rng, lp=lambda x: 0.03 + 0.6 * x * b, hp=0.2, shape=lambda x: x ** 2.2)
        add_tone(o, 0, 1.6, 180, sweep_to=1400 * b, amp=0.35, decay=0, attack=1.2)
        return o
    if name == "impact":
        o = buf(1.4)
        add_tone(o, 0, 1.3, 90, sweep_to=38, amp=1.0, decay=3.2, attack=0.002, harmonics=((1, 1.0), (2, 0.2)))
        add_noise(o, 0, 0.25, amp=0.6, decay=28, lp=0.25, rng=rng)
        return o
    raise ValueError(name)


ALL = ["click", "click-alt", "pop", "toggle", "typing", "ding-dong", "success", "error", "whoosh", "riser", "impact"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="assets/sfx")
    ap.add_argument("--only", help="comma-separated subset")
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--bright", type=float, default=1.0)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    names = args.only.split(",") if args.only else ALL
    written = []
    for n in names:
        rng = random.Random(f"{args.seed}-{n}")
        write(out / f"{n}.wav", normalize(make(n, rng, args.bright)))
        written.append(str(out / f"{n}.wav"))
    (out / "SOURCE.json").write_text(json.dumps({
        "generator": "qiaomu-product-video/scripts/make_sfx.py", "seed": args.seed, "bright": args.bright,
        "license": "original synthesis, MIT", "files": [Path(w).name for w in written],
    }, indent=2), encoding="utf-8")
    print(json.dumps(written, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
