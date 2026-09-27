#!/usr/bin/env python3
"""Measure the beat grid of a user-supplied song so cuts and UI hits land on real beats.

Copyright (c) 向阳乔木 — MIT License. Standard library + ffmpeg only.

    python3 beat_grid.py song.mp3                       # print tempo, first downbeat, bars, drop
    python3 beat_grid.py song.mp3 --plan plan.json      # also report how far each shot start is from a downbeat
    python3 beat_grid.py song.mp3 --plan plan.json --write   # store audio.beatGrid (+ drop) in plan.json

Method: decode to mono 11025 Hz → frame energy (full band + kick band) → half-wave rectified log-energy
flux as the onset envelope → autocorrelation for tempo (70–180 BPM, mild prior around 120) → fine
comb search for the exact period and phase → the beat phase with the strongest kick energy is the
downbeat → the bar with the largest energy rise is the drop. Always sanity-check by ear: the output
is a measurement, not ground truth (half/double tempo is the classic error; pass --bpm-range to steer).
"""
import argparse
import json
import math
import shutil
import subprocess
import sys
from array import array
from pathlib import Path

SR = 11025
HOP = 128


def decode(path):
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found")
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
        capture_output=True,
    )
    if r.returncode != 0:
        sys.exit(f"cannot decode {path}: {r.stderr.decode(errors='replace').strip()}")
    raw = r.stdout
    a = array("h")
    a.frombytes(raw[: len(raw) // 2 * 2])
    if sys.byteorder == "big":
        a.byteswap()
    return a


def envelopes(samples):
    # one-pole low-pass ≈150 Hz isolates the kick
    alpha = 1 - math.exp(-2 * math.pi * 150 / SR)
    lp = 0.0
    full, kick = [], []
    n = len(samples) // HOP
    for f in range(n):
        e = ek = 0.0
        for x in samples[f * HOP:(f + 1) * HOP]:
            x /= 32768.0
            lp += alpha * (x - lp)
            e += x * x
            ek += lp * lp
        full.append(e / HOP)
        kick.append(ek / HOP)
    return full, kick


def flux(energy):
    out = [0.0]
    prev = math.log10(energy[0] + 1e-10)
    for e in energy[1:]:
        cur = math.log10(e + 1e-10)
        out.append(max(0.0, cur - prev))
        prev = cur
    # remove slow trend so sustained loud parts do not dominate
    w = 16
    csum = [0.0]
    for v in out:
        csum.append(csum[-1] + v)
    res = []
    for i, v in enumerate(out):
        a, b = max(0, i - w), min(len(out), i + w + 1)
        res.append(max(0.0, v - (csum[b] - csum[a]) / (b - a)))
    return res


def sample(env, pos):
    i = int(pos)
    if i < 0 or i + 1 >= len(env):
        return 0.0
    f = pos - i
    return env[i] * (1 - f) + env[i + 1] * f


def comb_score(env, period, phase):
    s, p, k = 0.0, phase, 0
    while p < len(env) - 1:
        s += sample(env, p)
        p += period
        k += 1
    return s / max(k, 1)


def estimate(env, fps, lo, hi):
    best = None
    lag_lo, lag_hi = int(fps * 60 / hi), int(math.ceil(fps * 60 / lo))
    n = len(env)
    mean = sum(env) / n
    z = [v - mean for v in env]
    scores = {}
    for lag in range(max(lag_lo, 1), lag_hi + 1):
        ac = sum(z[i] * z[i + lag] for i in range(0, n - lag, 2))
        bpm = 60 * fps / lag
        prior = math.exp(-0.5 * (math.log2(bpm / 120) / 0.9) ** 2)
        scores[lag] = ac * prior
        if best is None or scores[lag] > scores[best]:
            best = lag
    # fine search around the coarse period, jointly with phase
    top = None
    period0 = best
    steps = [period0 * (1 + d / 400) for d in range(-12, 13)]
    for period in steps:
        for ph10 in range(int(period * 10)):
            ph = ph10 / 10
            sc = comb_score(env, period, ph)
            if top is None or sc > top[0]:
                top = (sc, period, ph)
    # how much the chosen period stands out over the average lag (≥ 3 is a clear pulse)
    vals = list(scores.values())
    avg = sum(abs(v) for v in vals) / len(vals)
    confidence = scores[best] / avg if avg > 0 else None
    return top[1], top[2], confidence


def analyse(path, lo=70.0, hi=180.0, beats_per_bar=4):
    samples = decode(path)
    if len(samples) < SR:
        sys.exit("audio shorter than 1 second")
    fps = SR / HOP
    full, kick = envelopes(samples)
    env_full, env_kick = flux(full), flux(kick)
    env = [a + 1.5 * b for a, b in zip(env_full, env_kick)]
    period, phase, conf = estimate(env, fps, lo, hi)
    duration = len(samples) / SR
    beats = []
    p = phase
    while p / fps < duration:
        beats.append(p / fps)
        p += period
    # downbeat = beat phase (mod beats_per_bar) with the most kick onset energy
    strength = [0.0] * beats_per_bar
    for i, b in enumerate(beats):
        strength[i % beats_per_bar] += sample(env_kick, b * fps) + 0.5 * sample(env_full, b * fps)
    d0 = max(range(beats_per_bar), key=lambda k: strength[k])
    downbeats = beats[d0::beats_per_bar]
    bars = []
    for i, t in enumerate(downbeats):
        end = downbeats[i + 1] if i + 1 < len(downbeats) else duration
        a, b = int(t * fps), max(int(t * fps) + 1, int(end * fps))
        e = sum(full[a:b]) / (b - a)
        bars.append({"index": i, "start": round(t, 4), "rmsDb": round(10 * math.log10(e + 1e-12), 2)})
    drop = None
    for i in range(2, len(bars)):
        rise = bars[i]["rmsDb"] - (bars[i - 1]["rmsDb"] + bars[i - 2]["rmsDb"]) / 2
        if drop is None or rise > drop["riseDb"]:
            drop = {"bar": i, "time": bars[i]["start"], "riseDb": round(rise, 2)}
    bpm = 60 * fps / period
    return {
        "source": str(path),
        "duration": round(duration, 3),
        "bpm": round(bpm, 2),
        "beat": round(60 / bpm, 5),
        "beatsPerBar": beats_per_bar,
        "offset": round(downbeats[0], 4) if downbeats else round(beats[0], 4),
        "confidence": round(conf, 2) if conf else None,
        "downbeats": [round(t, 4) for t in downbeats],
        "bars": bars,
        "drop": drop,
        "note": "measurement, not ground truth: listen with a click track before locking cuts",
    }


def snap_report(grid, plan):
    fps = (plan.get("format") or {}).get("fps") or 30
    rows = []
    for s in plan.get("shots", []):
        t = s.get("start", 0)
        nearest = min(grid["downbeats"], key=lambda d: abs(d - t)) if grid["downbeats"] else None
        beat = grid["beat"]
        k = round((t - grid["offset"]) / beat)
        nearest_beat = grid["offset"] + k * beat
        rows.append({
            "shot": s.get("id"), "start": t,
            "nearestDownbeat": nearest, "downbeatOffFrames": round((t - nearest) * fps, 1) if nearest is not None else None,
            "beatOffFrames": round((t - nearest_beat) * fps, 1),
        })
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio")
    ap.add_argument("--plan")
    ap.add_argument("--write", action="store_true", help="store audio.beatGrid and audio.drop in --plan")
    ap.add_argument("--bpm-range", default="70-180", help="e.g. 110-140 to avoid half/double tempo")
    ap.add_argument("--beats-per-bar", type=int, default=4)
    ap.add_argument("--out", help="write the full JSON report here")
    args = ap.parse_args()
    lo, hi = (float(x) for x in args.bpm_range.split("-"))
    grid = analyse(args.audio, lo, hi, args.beats_per_bar)
    report = dict(grid)
    if args.plan:
        plan_path = Path(args.plan)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        report["shots"] = snap_report(grid, plan)
        if args.write:
            audio = plan.setdefault("audio", {})
            audio["beatGrid"] = {"bpm": grid["bpm"], "offset": grid["offset"], "beatsPerBar": grid["beatsPerBar"],
                                 "source": grid["source"], "measured": True}
            if grid["drop"]:
                audio["drop"] = grid["drop"]
            plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.out:
        Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    brief = {k: report[k] for k in ("bpm", "offset", "confidence", "drop", "duration")}
    brief["bars"] = len(report["bars"])
    if "shots" in report:
        brief["shots"] = report["shots"]
    print(json.dumps(brief, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
