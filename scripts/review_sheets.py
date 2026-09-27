#!/usr/bin/env python3
"""Produce review evidence for a rendered film: 2 fps contact sheets, a 10 fps strip of the
first 3 seconds (hook test), 10 fps transition strips around every cut, 320px thumbnail tests,
an optional loop-seam score, an audio spectrogram, per-second RMS and integrated loudness.

These are things to LOOK at. Nothing here says the film is good.

Copyright (c) 向阳乔木 — MIT License.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def probe(video: str) -> dict:
    data = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", video]).stdout)
    v = next((s for s in data["streams"] if s["codec_type"] == "video"), {})
    a = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    return {
        "duration": float(data["format"]["duration"]),
        "width": v.get("width"), "height": v.get("height"),
        "fps": v.get("avg_frame_rate"),
        "hasAudio": a is not None,
        "audioDuration": float(a["duration"]) if a and a.get("duration") else None,
    }


def contact_sheets(video: str, dur: float, out: Path) -> list[str]:
    half = dur / 2
    paths = []
    for i, (ss, t) in enumerate(((0, half), (half, dur - half)), 1):
        frames = max(1, math.ceil(t * 2))
        rows = math.ceil(frames / 6)
        p = out / f"contact-{i}.png"
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{ss:.3f}", "-t", f"{t:.3f}", "-i", video,
             "-vf", f"fps=2,scale=384:-1,tile=6x{rows}", "-frames:v", "1", str(p)])
        paths.append(str(p))
    return paths


def strips(video: str, cuts: list[tuple[str, float]], dur: float, out: Path) -> list[str]:
    paths = []
    for sid, t in cuts:
        if t <= 0 or t >= dur:
            continue
        p = out / f"cut-{t:06.2f}-{re.sub(r'[^A-Za-z0-9_-]', '_', sid)}.png"
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{max(0, t - 0.5):.3f}", "-t", "1", "-i", video,
             "-vf", "fps=10,scale=320:-1,tile=10x1", "-frames:v", "1", str(p)])
        paths.append(str(p))
    return paths


def hook_strip(video: str, out: Path) -> str:
    p = out / "hook-strip.png"
    run(["ffmpeg", "-y", "-v", "error", "-t", "3", "-i", video,
         "-vf", "fps=10,scale=320:-1,tile=10x3", "-frames:v", "1", str(p)])
    return str(p)


def thumbnails(video: str, times: list[tuple[str, float]], out: Path) -> list[str]:
    """Frames scaled to 320px wide: can the headline and product still be read in a feed?"""
    paths = []
    for name, t in times:
        p = out / f"thumb-{re.sub(r'[^A-Za-z0-9_-]', '_', name)}.png"
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{max(0.0, t):.3f}", "-i", video,
             "-vf", "scale=320:-1", "-frames:v", "1", str(p)])
        paths.append(str(p))
    return paths


def loop_seam(video: str, dur: float) -> dict:
    """SSIM between the first and last frame; ≥ 0.95 usually loops without a visible jump."""
    last = max(0.0, dur - 0.05)
    res = subprocess.run(["ffmpeg", "-v", "info", "-i", video, "-ss", f"{last:.3f}", "-i", video,
                          "-filter_complex", "[0:v]trim=end_frame=1,setpts=PTS-STARTPTS[a];"
                          "[1:v]trim=end_frame=1,setpts=PTS-STARTPTS[b];[a][b]ssim",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.search(r"All:([\d.]+)", res)
    ssim = float(m.group(1)) if m else None
    return {"firstLastSsim": ssim, "seamless": ssim is not None and ssim >= 0.95}


def compare_sheet(ours: str, ref: str, out: Path, n: int = 12) -> str:
    """Our film (top row) against a benchmark (bottom row), sampled at the same relative times."""
    rows = []
    for i, video in enumerate((ours, ref)):
        dur = probe(video)["duration"]
        tiles = []
        for k in range(n):
            t = dur * (k + 0.5) / n
            p = out / f"cmp-{i}-{k:02d}.png"
            run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", video, "-vf", "scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2:white", "-frames:v", "1", str(p)])
            tiles.append(p)
        row = out / f"cmp-row-{i}.png"
        run(["ffmpeg", "-y", "-v", "error", *sum([["-i", str(x)] for x in tiles], []), "-filter_complex", f"hstack=inputs={n}", str(row)])
        rows.append(row)
        for x in tiles:
            x.unlink()
    dst = out / "compare.png"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(rows[0]), "-i", str(rows[1]), "-filter_complex", "vstack", str(dst)])
    for r in rows:
        r.unlink()
    return str(dst)


def audio_evidence(video: str, out: Path) -> dict:
    spec = out / "spectrum.png"
    run(["ffmpeg", "-y", "-v", "error", "-i", video, "-lavfi",
         "showspectrumpic=s=1600x500:scale=log:fscale=log", str(spec)])
    rms = run(["ffmpeg", "-v", "error", "-i", video, "-af",
               "aresample=48000,asetnsamples=n=48000,astats=metadata=1:reset=1,"
               "ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-",
               "-f", "null", "-"]).stdout
    per_sec = []
    for m in re.finditer(r"RMS_level=(-?[\d.]+|-inf)", rms):
        v = m.group(1)
        per_sec.append(None if v == "-inf" else round(float(v), 1))
    ln = subprocess.run(["ffmpeg", "-v", "info", "-i", video, "-af",
                         "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    block = ln[ln.rfind("{"): ln.rfind("}") + 1]
    loud = json.loads(block) if block else {}
    return {
        "spectrum": str(spec),
        "rmsDbPerSecond": per_sec,
        "integratedLufs": loud.get("input_i"),
        "truePeakDbtp": loud.get("input_tp"),
        "lra": loud.get("input_lra"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--plan", help="plan.json; cut points are taken from shot starts")
    ap.add_argument("--cuts", help="comma-separated cut times in seconds (if no plan)")
    ap.add_argument("--out", default="evidence/review")
    ap.add_argument("--loop", action="store_true", help="score the loop seam (first vs last frame)")
    ap.add_argument("--compare", help="benchmark film to set beside ours (same relative sample times)")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    try:
        info = probe(args.video)
        cuts: list[tuple[str, float]] = []
        thumbs: list[tuple[str, float]] = [("first-frame", 0.0)]
        if args.plan:
            plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
            shots = [s for s in plan.get("shots", []) if "start" in s and "end" in s]
            cuts = [(s.get("id", "shot"), float(s["start"])) for s in shots]
            for s in shots:
                roles = s.get("role") or []
                roles = [roles] if isinstance(roles, str) else roles
                if "aha" in roles or "brand" in roles:
                    thumbs.append((f"{s.get('id', 'shot')}-mid", (float(s["start"]) + float(s["end"])) / 2))
        elif args.cuts:
            cuts = [(f"c{i}", float(x)) for i, x in enumerate(args.cuts.split(","))]
        report = {
            "video": info,
            "contactSheets": contact_sheets(args.video, info["duration"], out),
            "hookStrip": hook_strip(args.video, out),
            "thumbnailTests": thumbnails(args.video, thumbs, out),
            "transitionStrips": strips(args.video, cuts, info["duration"], out),
            "audio": audio_evidence(args.video, out) if info["hasAudio"] else None,
            "warnings": [],
            "reminder": "Open every image. Do the 3-second, mute and thumbnail tests. Listen to the MP4. Report what was actually seen/heard, then fill evidence/scorecard.md.",
        }
        if args.compare:
            report["compare"] = compare_sheet(args.video, args.compare, out)
        if args.loop:
            report["loop"] = loop_seam(args.video, info["duration"])
            if not report["loop"]["seamless"]:
                report["warnings"].append("first and last frames differ — the loop will show a jump")
        if not info["hasAudio"]:
            report["warnings"].append("no audio stream (fine only for muted/loop deliverables)")
        elif info["audioDuration"] and info["audioDuration"] + 0.2 < info["duration"]:
            report["warnings"].append("audio ends before video — check the ending")
    except (subprocess.CalledProcessError, FileNotFoundError, KeyError, ValueError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        print(json.dumps({"ok": False, "error": detail.strip()[:2000]}, ensure_ascii=False))
        return 1
    (out / "review.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
