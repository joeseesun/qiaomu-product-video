#!/usr/bin/env python3
"""Derive a re-timed plan for a deliverable that uses a subset of shots (e.g. a vertical cut).

    python3 derive_plan.py plan.json --deliverable vertical [--out plan.vertical.json]

Shots listed in deliverable.shots are laid back to back from 0 (the render runtime does the
same), their actions keep shot-relative times, and every audio cue that belonged to an
included shot is shifted with it. Cues of dropped shots are removed. Then score and mix the
derived plan with its own outputs:

    python3 score.py plan.vertical.json --out assets/music-vertical.wav
    python3 mix_audio.py plan.vertical.json --name vertical

Copyright (c) 向阳乔木 — MIT License.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path


def derive(plan: dict, deliverable_id: str) -> dict:
    d = next((x for x in plan.get("deliverables", []) if x.get("id") == deliverable_id), None)
    if not d:
        raise SystemExit(f"no deliverable {deliverable_id}")
    keep = d.get("shots")
    if not keep:
        raise SystemExit(f"deliverable {deliverable_id} has no shot list; it plays the full timeline")
    out = copy.deepcopy(plan)
    shots, cursor, shift = [], 0.0, {}
    for s in plan["shots"]:
        if s["id"] not in keep:
            continue
        length = s["end"] - s["start"]
        shift[s["id"]] = (s["start"], s["end"], cursor - s["start"])
        ns = dict(s, start=round(cursor, 3), end=round(cursor + length, 3))
        shots.append(ns)
        cursor += length
    out["shots"] = shots
    out["duration"] = round(cursor, 3)
    cues = []
    for c in (plan.get("audio") or {}).get("cues", []):
        heard = c["at"] + float(c.get("syncOffset", 0))
        for sid, (a, b, delta) in shift.items():
            if a - 0.5 <= heard < b:  # sounds may start a little before their shot (whoosh pre-roll)
                cues.append(dict(c, at=round(c["at"] + delta, 3)))
                break
    out.setdefault("audio", {})["cues"] = cues
    if out["audio"].get("music", {}).get("file"):
        stem = Path(out["audio"]["music"]["file"])
        out["audio"]["music"]["file"] = str(stem.with_name(f"{stem.stem}-{deliverable_id}{stem.suffix}"))
    out["deliverables"] = [dict(d, duration=out["duration"], shots=None, derivedFrom=plan.get("title", "plan"))]
    out["derivedFrom"] = {"deliverable": deliverable_id}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan")
    ap.add_argument("--deliverable", required=True)
    ap.add_argument("--out")
    args = ap.parse_args()
    src = Path(args.plan)
    plan = json.loads(src.read_text(encoding="utf-8"))
    out = derive(plan, args.deliverable)
    dst = Path(args.out) if args.out else src.with_name(f"{src.stem}.{args.deliverable}.json")
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"plan": str(dst), "duration": out["duration"], "shots": [s["id"] for s in out["shots"]], "cues": len(out["audio"]["cues"]), "music": out["audio"].get("music", {}).get("file")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
