#!/usr/bin/env python3
"""Measure onset, peak time and peak level of sound effects (any format FFmpeg reads).

Use onset for clicks/keys/pops, peak for whooshes/impacts/risers:
    cue.at = shot.start + action.at - syncOffset

Copyright (c) 向阳乔木 — MIT License.
"""
from __future__ import annotations

import argparse
import array
import json
import math
import subprocess
import sys

RATE = 48000


def decode(path: str) -> array.array:
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(RATE), "-f", "s16le", "-"],
        check=True, capture_output=True,
    ).stdout
    samples = array.array("h")
    samples.frombytes(raw[: len(raw) // 2 * 2])
    if sys.byteorder == "big":
        samples.byteswap()
    return samples


def landmarks(path: str, onset_db: float = -20.0, window_ms: float = 1.0) -> dict:
    s = decode(path)
    if not s:
        return {"file": path, "error": "no audio samples"}
    win = max(1, int(RATE * window_ms / 1000))
    env = [max(abs(v) for v in s[i:i + win]) for i in range(0, len(s), win)]
    peak = max(env)
    if peak == 0:
        return {"file": path, "duration": round(len(s) / RATE, 4), "silent": True}
    peak_idx = env.index(peak)
    thresh = peak * 10 ** (onset_db / 20)
    onset_idx = next(i for i, v in enumerate(env) if v >= thresh)
    tail_idx = len(env) - 1 - next(i for i, v in enumerate(reversed(env)) if v >= thresh)
    to_s = lambda i: round(i * win / RATE, 4)
    return {
        "file": path,
        "duration": round(len(s) / RATE, 4),
        "onset": to_s(onset_idx),
        "peakTime": to_s(peak_idx),
        "peakDbfs": round(20 * math.log10(peak / 32768), 2),
        "audibleEnd": to_s(tail_idx + 1),
        "note": "syncOffset = onset for clicks/pops/keys; = peakTime for whoosh/impact/riser",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--onset-db", type=float, default=-20.0, help="onset threshold relative to peak (dB)")
    args = ap.parse_args()
    out, failed = [], False
    for f in args.files:
        try:
            out.append(landmarks(f, args.onset_db))
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            failed = True
            out.append({"file": f, "error": str(exc)})
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
