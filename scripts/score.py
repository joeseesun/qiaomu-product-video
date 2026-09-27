#!/usr/bin/env python3
"""Compose an original, film-specific score from plan.json (stdlib only, deterministic).

    python3 score.py plan.json --mood warm --key D --out assets/music.wav [--seed 7]

The arrangement is derived from the shot list, not a loop:
  * tempo from plan.audio.beatGrid.bpm; one chord per bar;
  * each shot sets an intensity (hook 1 → features 2 → montage 3 → end cadence);
  * a downbeat hit lands on shots with role "brand"; reading-heavy shots thin out;
  * the last shot resolves IV–V–I and lets the final chord ring out by plan.duration.
Moods pick the palette: warm (felt keys, pad, brushes), bright (plucky keys, claps),
tech (supersaw-ish pad, pluck arps, tight kick), ambient (pad + bells, no drums),
punchy (bass pulse, kick/snare). This is a starting score: listen, then edit the
ARRANGEMENT section or pass --dry to print the plan it derived.

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
NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
MAJOR = [0, 2, 4, 5, 7, 9, 11]
MINOR = [0, 2, 3, 5, 7, 8, 10]
MOODS = {
    "warm": {"prog": [0, 5, 3, 4], "keys": "felt", "drums": "brush", "pad": 0.16, "bright": 0.7, "bass": 0.12, "kick": 0.09},
    "bright": {"prog": [0, 4, 5, 3], "keys": "pluck", "drums": "clap", "pad": 0.12, "bright": 1.0},
    "tech": {"prog": [0, 5, 3, 4], "keys": "pluck", "drums": "tight", "pad": 0.2, "bright": 1.2},
    "ambient": {"prog": [0, 3, 5, 4], "keys": "bell", "drums": None, "pad": 0.22, "bright": 0.6},
    "punchy": {"prog": [0, 6, 5, 4], "keys": "pluck", "drums": "punch", "pad": 0.12, "bright": 1.1},
}


def midi_hz(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


class Bus:
    def __init__(self, seconds: float):
        n = int(seconds * SR) + SR
        self.l = array.array("f", bytes(4 * n))
        self.r = array.array("f", bytes(4 * n))

    def add(self, start: float, samples, pan: float = 0.0, gain: float = 1.0):
        i0 = int(start * SR)
        gl, gr = gain * math.cos((pan + 1) * math.pi / 4), gain * math.sin((pan + 1) * math.pi / 4)
        L, R = self.l, self.r
        n = min(len(samples), len(L) - i0)
        for k in range(max(0, -i0), n):
            s = samples[k]
            L[i0 + k] += s * gl
            R[i0 + k] += s * gr


def tone(freq, dur, partials, decay, attack=0.005, release=0.08, detune=0.0):
    n = int(dur * SR)
    out = array.array("f", bytes(4 * n))
    rel0 = n - int(release * SR)
    for mult, amp in partials:
        w = TAU * freq * mult * (1 + detune) / SR
        d = decay * (1 + 0.35 * (mult - 1))
        ph = 0.0
        for i in range(n):
            t = i / SR
            env = (t / attack if t < attack else 1.0) * math.exp(-d * t)
            if i > rel0:
                env *= (n - i) / (n - rel0)
            out[i] += amp * env * math.sin(ph)
            ph += w
    return out


def pad_voice(freq, dur, bright, attack=0.7):
    n = int(dur * SR)
    out = array.array("f", bytes(4 * n))
    harmonics = [(h, 1.0 / h) for h in range(1, 7 if bright > 0.9 else 5)]
    for det in (-0.004, 0.004):
        for h, a in harmonics:
            w = TAU * freq * h * (1 + det) / SR
            ph = random.random() * TAU
            for i in range(n):
                t = i / SR
                env = min(1.0, t / attack) * min(1.0, (dur - t) / 0.6)
                out[i] += a * 0.5 * env * math.sin(ph)
                ph += w
    return out


def noise_hit(dur, decay, hp=0.85, rng=None):
    rng = rng or random.Random(1)
    n = int(dur * SR)
    out = array.array("f", bytes(4 * n))
    prev_x = prev_y = 0.0
    for i in range(n):
        x = rng.uniform(-1, 1)
        y = hp * (prev_y + x - prev_x)
        prev_x, prev_y = x, y
        out[i] = y * math.exp(-decay * i / SR)
    return out


def kick(tight=False):
    n = int(0.35 * SR)
    out = array.array("f", bytes(4 * n))
    ph = 0.0
    for i in range(n):
        t = i / SR
        f = 45 + (110 if tight else 80) * math.exp(-t * 28)
        ph += TAU * f / SR
        out[i] = math.sin(ph) * math.exp(-t * (14 if tight else 9))
    return out


def chord_degrees(root_degree: int, scale):
    """Triad + 7th as scale-degree indexes → semitone offsets from key root."""
    return [scale[(root_degree + k) % 7] + 12 * ((root_degree + k) // 7) for k in (0, 2, 4, 6)]


def derive(plan: dict, mood: str):
    bpm = float((plan.get("audio") or {}).get("beatGrid", {}).get("bpm") or 96)
    beat = 60 / bpm
    bar = beat * 4
    dur = float(plan["duration"])
    bars = int(math.ceil(dur / bar))
    shots = plan["shots"]
    sections = []
    for i, s in enumerate(shots):
        roles = set(s.get("role") or [])
        kind = s.get("type", "")
        if i == len(shots) - 1:
            level = "end"
        elif i == 0 or "hook" in roles:
            level = 1
        elif kind == "montage":
            level = 3
        elif kind == "brand":
            level = 1
        else:
            level = 2
        sections.append({"id": s["id"], "start": s["start"], "end": s["end"], "level": level,
                         "hit": "brand" in roles and i > 0 or kind == "brand" or i == len(shots) - 1})
    return {"bpm": bpm, "beat": beat, "bar": bar, "bars": bars, "duration": dur, "sections": sections, "mood": mood}


def level_at(arr, t):
    for s in arr["sections"]:
        if s["start"] <= t < s["end"]:
            return s["level"]
    return arr["sections"][-1]["level"]


def compose(plan: dict, mood: str, key: str, minor: bool, seed: int):
    random.seed(seed)
    m = MOODS[mood]
    scale = MINOR if minor else MAJOR
    root = 50 + NOTE[key]  # around D3
    arr = derive(plan, mood)
    beat, bar, dur = arr["beat"], arr["bar"], arr["duration"]
    bus = {k: Bus(dur + 2) for k in ("pad", "keys", "bass", "drums", "fx")}
    end_sec = arr["sections"][-1]
    end_bar0 = int(end_sec["start"] // bar)
    prog = m["prog"]

    for b in range(arr["bars"]):
        t0 = b * bar
        if t0 >= dur:
            break
        lvl = level_at(arr, t0 + 0.01)
        # final section: IV → V → I and hold
        if lvl == "end":
            k = b - end_bar0
            degree = [3, 4, 0, 0][min(k, 3)]
        else:
            degree = prog[b % len(prog)]
        chord = chord_degrees(degree, scale)
        length = min(bar, dur - t0)
        last_bar = lvl == "end" and t0 + bar >= dur - 0.01
        # pad: always, quieter while reading-heavy
        pad_len = (dur - t0 + 0.2) if last_bar else length + 0.35
        # open voicing: root an octave up so the pad never sits in the bass register
        voicing = [chord[0] + 12, chord[1], chord[2]] + ([chord[3]] if lvl in (2, 3) else [])
        for j, off in enumerate(voicing):
            bus["pad"].add(t0, pad_voice(midi_hz(root + off), pad_len, m["bright"]), pan=(-0.4 + 0.4 * j), gain=m["pad"] / 3)
        # bass
        if lvl != 1 or b % 2 == 0:
            bass_note = midi_hz(root - 12 + chord[0])
            steps = 1 if lvl in (1, "end") else 2
            for q in range(steps):
                bus["bass"].add(t0 + q * bar / steps, tone(bass_note, (bar / steps) * 0.95 if not last_bar else dur - t0, [(1, 1.0), (2, 0.35)], 1.6, attack=0.01, release=0.2), gain=m.get("bass", 0.3))
        # keys: broken chords; density by level
        pattern = {1: [0, 3, 6], 2: [0, 2, 3, 5, 6], 3: [0, 1, 2, 3, 4, 5, 6, 7], "end": [0, 2, 4]}[lvl]
        if last_bar:
            pattern = [0]
        notes = [chord[0] + 12, chord[1] + 12, chord[2] + 12, chord[1] + 24, chord[2] + 12, chord[0] + 24, chord[1] + 12, chord[3] + 12]
        for p in pattern:
            nt = t0 + p * beat / 2
            if nt >= dur:
                continue
            f = midi_hz(root + notes[p % len(notes)])
            if m["keys"] == "felt":
                sound = tone(f, 1.6 if not last_bar else dur - nt, [(1, 1.0), (2, 0.35), (3, 0.12), (4.02, 0.05)], 2.2 + f / 900, attack=0.006)
            elif m["keys"] == "bell":
                sound = tone(f * 2, 2.4, [(1, 1.0), (2.76, 0.3), (5.4, 0.1)], 1.4)
            else:
                sound = tone(f, 0.5, [(1, 1.0), (2, 0.5), (3, 0.3), (4, 0.15)], 9 * m["bright"], attack=0.002)
            vel = 0.8 + 0.2 * random.random()
            bus["keys"].add(nt, sound, pan=random.uniform(-0.35, 0.35), gain=0.11 * vel)
        # drums
        if m["drums"] and lvl in (2, 3):
            for q in range(4):
                bt = t0 + q * beat
                if q in (0, 2):
                    bus["drums"].add(bt, kick(m["drums"] == "tight"), gain=m.get("kick", 0.3))
                hat_steps = 2 if lvl == 2 else 4
                for h in range(hat_steps):
                    ht = bt + h * beat / hat_steps
                    if h or q % 2:
                        bus["drums"].add(ht, noise_hit(0.08, 55 if m["drums"] == "brush" else 90, rng=random.Random(int(ht * 1000))), pan=0.3, gain=0.05 if m["drums"] == "brush" else 0.07)
                if q in (1, 3) and m["drums"] in ("clap", "punch"):
                    bus["drums"].add(bt, noise_hit(0.2, 22, hp=0.6, rng=random.Random(int(bt * 999))), gain=0.12)
    # downbeat hits on brand shots and the final landing
    for s in arr["sections"]:
        if s["hit"]:
            t = s["start"]
            bus["fx"].add(t, tone(midi_hz(root - 12), 2.4, [(1, 1.0), (2, 0.4)], 1.3, attack=0.004), gain=0.16)
            bus["fx"].add(t, noise_hit(1.6, 3.5, hp=0.95, rng=random.Random(9)), gain=0.035)
    return bus, arr


def highpass(buf, n, cutoff):
    """One-pole high-pass in place (keeps pads/keys out of the bass register)."""
    rc = 1 / (TAU * cutoff)
    a = rc / (rc + 1 / SR)
    px = py = 0.0
    for i in range(n):
        x = buf[i]
        y = a * (py + x - px)
        buf[i] = y
        px, py = x, y


HP = {"pad": 160, "keys": 140, "fx": 40, "drums": 45, "bass": 30}


def mixdown(bus, dur, out: Path):
    n = int(dur * SR)
    L = array.array("f", bytes(4 * n))
    R = array.array("f", bytes(4 * n))
    for name, b in bus.items():
        highpass(b.l, n, HP.get(name, 30))
        highpass(b.r, n, HP.get(name, 30))
        for i in range(n):
            L[i] += b.l[i]
            R[i] += b.r[i]
    peak = max(1e-9, max(max(abs(x) for x in L), max(abs(x) for x in R)))
    g = 10 ** (-1.0 / 20) / peak
    fade = int(1.2 * SR)
    pcm = array.array("h", bytes(4 * n))
    for i in range(n):
        e = g * (min(1.0, (n - i) / fade) if i > n - fade else 1.0) * min(1.0, i / 240)
        pcm[2 * i] = int(max(-1, min(1, L[i] * e)) * 32767)
        pcm[2 * i + 1] = int(max(-1, min(1, R[i] * e)) * 32767)
    if sys.byteorder == "big":
        pcm.byteswap()
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan")
    ap.add_argument("--mood", choices=sorted(MOODS), default="warm")
    ap.add_argument("--key", default="D")
    ap.add_argument("--minor", action="store_true")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="assets/music.wav")
    ap.add_argument("--dry", action="store_true", help="print the derived arrangement and exit")
    args = ap.parse_args()
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    if args.dry:
        print(json.dumps(derive(plan, args.mood), ensure_ascii=False, indent=2))
        return 0
    bus, arr = compose(plan, args.mood, args.key, args.minor, args.seed)
    out = Path(args.out)
    if not out.is_absolute():
        out = Path(args.plan).resolve().parent / out
    mixdown(bus, arr["duration"], out)
    info = {"file": str(out), "source": "code-original", "generator": "qiaomu-product-video/scripts/score.py",
            "mood": args.mood, "key": args.key + (" minor" if args.minor else " major"), "bpm": arr["bpm"],
            "seed": args.seed, "duration": arr["duration"],
            "sections": [{k: s[k] for k in ("id", "start", "end", "level")} for s in arr["sections"]]}
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
