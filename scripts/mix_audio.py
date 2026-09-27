#!/usr/bin/env python3
"""Mix music + SFX (+ optional voice) from plan.json with cue-driven ducking and two-pass loudness.

    python3 mix_audio.py plan.json [--target -16] [--tp -1.5]

Reads plan.audio: music {file, gain}, cues [{at, file, gain, role, syncOffset, duck?}],
voice {file, at, gain}? and ducking {enabled, db?, attack?, hold?, release?}.
Writes assets/sfx-stem.wav, assets/music-ducked.wav, assets/master.wav and
evidence/audio-mix.json (per-cue alignment in frames, audibility margin vs ducked music,
final loudness). Stdlib + FFmpeg; numbers are hints — listen to the master.

Copyright (c) 向阳乔木 — MIT License.
"""
from __future__ import annotations

import argparse
import array
import hashlib
import json
import math
import re
import subprocess
import sys
import wave
from pathlib import Path

SR = 48000
# role → (duck dB, attack s, hold s, release s). Starting points, not standards.
DUCK = {
    "click": (3.0, 0.04, 0.11, 0.22), "popup": (3.5, 0.04, 0.12, 0.24), "typing": (2.5, 0.04, 0.35, 0.25),
    "transition": (4.0, 0.04, 0.18, 0.32), "complete": (5.5, 0.04, 0.42, 0.38), "notice": (5.5, 0.04, 0.42, 0.38),
    "brand": (5.0, 0.04, 0.55, 0.45), "voice": (8.0, 0.08, 0.0, 0.3),
}


def decode(path: Path) -> array.array:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "2", "-ar", str(SR), "-f", "s16le", "-"],
                         check=True, capture_output=True).stdout
    a = array.array("h")
    a.frombytes(raw[: len(raw) // 4 * 4])
    if sys.byteorder == "big":
        a.byteswap()
    return a


def write_wav(path: Path, frames: array.array):
    pcm = array.array("h", (max(-32767, min(32767, int(v * 32767))) for v in frames))
    if sys.byteorder == "big":
        pcm.byteswap()
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def loudnorm(src: Path, dst: Path, target: float, tp: float) -> dict:
    first = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(src), "-af", f"loudnorm=I={target}:TP={tp}:LRA=11:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
    m = json.loads(first[first.rfind("{"): first.rfind("}") + 1])
    af = (f"loudnorm=I={target}:TP={tp}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true:print_format=json")
    second = subprocess.run(["ffmpeg", "-hide_banner", "-y", "-i", str(src), "-af", af, "-ar", str(SR), str(dst)], capture_output=True, text=True).stderr
    m2 = json.loads(second[second.rfind("{"): second.rfind("}") + 1])
    return {"first": {k: m[k] for k in ("input_i", "input_tp", "input_lra")}, "normalization_type": m2.get("normalization_type"),
            "output_i": m2.get("output_i"), "output_tp": m2.get("output_tp")}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan")
    ap.add_argument("--target", type=float, default=-16.0, help="integrated loudness LUFS")
    ap.add_argument("--tp", type=float, default=-1.5, help="true peak dBTP")
    ap.add_argument("--name", default="", help="suffix for outputs, e.g. vertical → master-vertical.wav")
    args = ap.parse_args()
    plan_path = Path(args.plan).resolve()
    root = plan_path.parent
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    audio = plan.get("audio") or {}
    fps = (plan.get("format") or {}).get("fps", 30)
    dur = float(plan["duration"])
    n = int(dur * SR)
    warnings: list[str] = []

    # music
    music = audio.get("music") or {}
    mbuf = array.array("f", bytes(4 * n * 2))
    mpath = root / music["file"] if music.get("file") else None
    if mpath and mpath.exists():
        m = decode(mpath)
        if len(m) // 2 > n + SR:
            warnings.append(f"music is {len(m) / 2 / SR - dur:.1f}s longer than the film; it is cut — check the ending")
        g = float(music.get("gain", 0.7)) / 32768
        for i in range(min(len(m), 2 * n)):
            mbuf[i] = m[i] * g
    elif plan.get("audioRequired", True):
        warnings.append("no music file")

    # duck envelope at 1 ms control rate: deepest duck wins (no stacking)
    ctrl = int(dur * 1000) + 1
    duck_db = [0.0] * ctrl
    duck_cfg = audio.get("ducking") or {"enabled": True}
    cues = audio.get("cues") or []
    sfx = array.array("f", bytes(4 * n * 2))
    report_cues = []
    actions = {a["id"]: s["start"] + a["at"] for s in plan.get("shots", []) for a in s.get("actions", []) if "id" in a}
    for c in cues:
        f = root / c["file"]
        if not f.exists():
            warnings.append(f"missing cue file {c['file']}")
            continue
        data = decode(f)
        gain = float(c.get("gain", 0.5)) / 32768
        i0 = int(c["at"] * SR) * 2
        peak = 0.0
        for k in range(len(data)):
            j = i0 + k
            if 0 <= j < len(sfx):
                v = data[k] * gain
                sfx[j] += v
                peak = max(peak, abs(v))
        heard = c["at"] + float(c.get("syncOffset", 0))
        role = c.get("role", "click")
        db, att, hold, rel = DUCK.get(role, DUCK["click"])
        if isinstance(c.get("duck"), dict):
            db = c["duck"].get("db", db); att = c["duck"].get("attack", att); hold = c["duck"].get("hold", hold); rel = c["duck"].get("release", rel)
        for key in ("db", "attack", "hold", "release"):
            if key in duck_cfg and key != "enabled":
                pass  # global overrides could be applied here per project needs
        if duck_cfg.get("enabled", True) and db > 0:
            t_a, t_h, t_r = heard - att, heard + hold, heard + hold + rel
            for ms in range(max(0, int(t_a * 1000)), min(ctrl, int(t_r * 1000) + 1)):
                t = ms / 1000
                d = db * ((t - t_a) / att if t < heard else 1.0 if t <= t_h else 1 - (t - t_h) / rel)
                duck_db[ms] = max(duck_db[ms], d)
        entry = {"file": c["file"], "role": role, "at": c["at"], "heard": round(heard, 3), "peakDbfs": round(20 * math.log10(peak), 1) if peak else None}
        if c.get("actionId") in actions:
            entry["actionId"] = c["actionId"]
            entry["alignmentFrames"] = round((heard - actions[c["actionId"]]) * fps, 2)
        report_cues.append(entry)

    # apply duck to music, measure audibility margin per cue
    ducked = array.array("f", bytes(4 * n * 2))
    for i in range(n):
        g = 10 ** (-duck_db[min(ctrl - 1, i // 48)] / 20)
        ducked[2 * i] = mbuf[2 * i] * g
        ducked[2 * i + 1] = mbuf[2 * i + 1] * g
    for e in report_cues:
        a = int(e["heard"] * SR)
        seg = ducked[max(0, 2 * (a - 2400)): 2 * (a + 4800)]
        mpk = max((abs(v) for v in seg), default=0.0)
        if mpk and e["peakDbfs"] is not None:
            e["musicPeakDbfs"] = round(20 * math.log10(mpk), 1)
            e["marginDb"] = round(e["peakDbfs"] - e["musicPeakDbfs"], 1)
            if e["marginDb"] < -3:
                warnings.append(f"{e['file']} @ {e['heard']}s may be masked (sfx {e['marginDb']} dB under music)")
        if abs(e.get("alignmentFrames", 0)) > 2:
            warnings.append(f"{e.get('actionId')} is {e['alignmentFrames']} frames off its action")

    voice = audio.get("voice")
    vbuf = None
    if voice and voice.get("file"):
        v = decode(root / voice["file"])
        vbuf = array.array("f", bytes(4 * n * 2))
        g = float(voice.get("gain", 1.0)) / 32768
        o = int(float(voice.get("at", 0)) * SR) * 2
        for k in range(len(v)):
            if 0 <= o + k < len(vbuf):
                vbuf[o + k] = v[k] * g

    pre = array.array("f", bytes(4 * n * 2))
    for i in range(2 * n):
        pre[i] = ducked[i] + sfx[i] + (vbuf[i] if vbuf else 0.0)
    clip = max(abs(v) for v in pre)
    if clip > 1.0:
        s = 0.98 / clip
        for i in range(2 * n):
            pre[i] *= s
        warnings.append(f"pre-master peaked at {20 * math.log10(clip):+.1f} dBFS; scaled before loudnorm — lower cue gains")

    assets = root / "assets"
    sfx_ = f"-{args.name}" if args.name else ""
    write_wav(assets / f"sfx-stem{sfx_}.wav", sfx)
    write_wav(assets / f"music-ducked{sfx_}.wav", ducked)
    write_wav(assets / f"premaster{sfx_}.wav", pre)
    ln = loudnorm(assets / f"premaster{sfx_}.wav", assets / f"master{sfx_}.wav", args.target, args.tp)

    report = {
        "inputs": {"plan": sha(plan_path), "music": sha(mpath) if mpath and mpath.exists() else None,
                   "cues": {c["file"]: sha(root / c["file"]) for c in cues if (root / c["file"]).exists()}},
        "outputs": {"master": f"assets/master{sfx_}.wav", "masterSha": sha(assets / f"master{sfx_}.wav"), "sfxStem": f"assets/sfx-stem{sfx_}.wav", "musicDucked": f"assets/music-ducked{sfx_}.wav"},
        "loudness": ln, "target": {"I": args.target, "TP": args.tp},
        "cues": report_cues, "warnings": warnings,
        "limits": ["levels and margins are measurements, not listening", "ducking presets are starting points"],
    }
    (root / "evidence").mkdir(exist_ok=True)
    (root / "evidence" / f"audio-mix{sfx_}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("loudness", "warnings")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
