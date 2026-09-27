#!/usr/bin/env python3
"""Structural checks for a qiaomu-product-video plan.json.

Checks timeline, scope, DIRECTION completeness, claim sources, bilingual copy,
reading speed, sound-required actions and cue alignment. It cannot judge whether
claims are true, whether frames are clipped, or whether the film looks/sounds good.

Copyright (c) 向阳乔木 — MIT License.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

VAGUE = ["一气呵成", "触手可及", "自然流转", "更聪明", "更丝滑", "无缝", "极致", "赋能", "全新体验", "从未如此"]
LIMITS = [
    "no semantic verification of feature claims",
    "no visual clipping or taste assessment",
    "no listening assessment",
]


def cjk_count(text: str) -> int:
    return len(re.findall(r"[一-鿿]", text or ""))


def resolve_source(source: str, project: Path, repo: str) -> tuple[bool | None, str]:
    """Return (exists, path). None means not a file reference (URL, tag, commit)."""
    s = source.strip()
    if re.match(r"^[a-z]+://", s) or s.startswith(("tag:", "commit:", "pr:")):
        return None, s
    base_repo = Path(repo).expanduser() if repo else None
    if s.startswith("repo:"):
        rel, base = s[5:], base_repo
    elif s.startswith("file:"):
        rel, base = s[5:], project
    else:
        rel, base = s, None
    rel = re.split(r"#L\d+|:\d+$", rel)[0]
    candidates = [base / rel] if base else [project / rel] + ([base_repo / rel] if base_repo else [])
    for c in candidates:
        if c and c.exists():
            return True, str(c)
    return False, rel


def direction_filled(path: Path) -> tuple[bool, list[str]]:
    if not path.exists():
        return False, ["DIRECTION.md missing"]
    text = path.read_text(encoding="utf-8")
    problems = []
    if "选定：\n" in text or re.search(r"选定：\s*\n理由：\s*\n", text):
        problems.append("DIRECTION.md: no direction chosen")
    if "因为产品有 ______" in text or not re.search(r"因为.{1,60}所以", text):
        problems.append("DIRECTION.md: no product-derived devices (因为产品有 X，所以用 Y)")
    table = text.split("## 8.")[-1] if "## 8." in text else ""
    rows = [l for l in table.splitlines() if l.startswith("|") and not set(l) <= set("|- ")]
    if len(rows) < 2:
        problems.append("DIRECTION.md: shot table is empty")
    return not problems, problems


STRATEGY_FIELDS = ("goal", "audience", "singleMessage", "ahaMoment", "cta")
ASPECTS = {"16:9", "9:16", "1:1", "4:5", "3:4", "4:3", "21:9"}
SCORE_DIMENSIONS = 11


def roles_of(shot: dict) -> set[str]:
    r = shot.get("role") or []
    return {r} if isinstance(r, str) else set(r)


def strategy_checks(plan: dict, shots: list[dict], strict: list[str], warnings: list[str]) -> None:
    strat = plan.get("strategy") or {}
    for f in STRATEGY_FIELDS:
        if not str(strat.get(f, "")).strip():
            if f == "cta" and plan.get("ctaExceptionReason"):
                continue
            strict.append(f"strategy.{f} is empty — decide it before designing shots")
    msg = str(strat.get("singleMessage", ""))
    if cjk_count(msg) > 30 or len(msg) > 90:
        warnings.append("strategy.singleMessage is long — it should be one sentence a viewer can repeat")
    if not shots:
        return
    first = shots[0]
    if "hook" not in roles_of(first):
        strict.append("first shot has no role 'hook'")
    hook_end = first.get("hookEnd", min(first.get("end", 0) - first.get("start", 0), 3.5))
    if hook_end > 4:
        warnings.append("hook moment is longer than 4s — check the 3-second test")
    d_at = first.get("descriptionAt")
    hook_text = (first.get("headline") or "") + (first.get("description") or "" if not isinstance(d_at, (int, float)) or d_at < hook_end else "")
    if cjk_count(hook_text) > 18:
        warnings.append(f"hook copy has {cjk_count(hook_text)} 中文字 — aim for ≤15, readable in 1.5s")
    brand = [s for s in shots if "brand" in roles_of(s)]
    if not brand:
        strict.append("no shot has role 'brand' — the product must be recognisable early")
    elif brand[0].get("start", 0) > 5:
        warnings.append(f"product first recognisable at {brand[0]['start']}s — aim for ≤5s")
    if not any("aha" in roles_of(s) for s in shots):
        strict.append("no shot has role 'aha' — which frame proves the single message?")
    if not plan.get("ctaExceptionReason") and not any("cta" in roles_of(s) for s in shots):
        strict.append("no shot has role 'cta' (or set ctaExceptionReason)")
    for s in shots:
        if s.get("claim") and not (s.get("headline") or s.get("description")):
            strict.append(f"{s.get('id')}: claim has no on-screen text — fails the sound-off test")


def deliverable_checks(plan: dict, strict: list[str], warnings: list[str]) -> None:
    items = plan.get("deliverables") or []
    if not items:
        strict.append("no deliverables listed — decide formats before shooting")
        return
    ids = {d.get("id") for d in items}
    main = plan.get("duration")
    for d in items:
        did = d.get("id", "?")
        if d.get("aspect") not in ASPECTS:
            warnings.append(f"deliverable {did}: unusual aspect {d.get('aspect')}")
        if d.get("sound") not in ("on", "off", "none"):
            strict.append(f"deliverable {did}: sound must be on / off / none")
        if d.get("from") and d["from"] not in ids:
            strict.append(f"deliverable {did}: from '{d['from']}' is not a deliverable id")
        if d.get("from") and isinstance(main, (int, float)) and isinstance(d.get("duration"), (int, float)):
            if d["duration"] < main and not d.get("shots"):
                warnings.append(f"deliverable {did}: shorter cut without a shot list — re-edit, don't speed up")
        if d.get("aspect") != (items[0].get("aspect")) and d.get("from") and not d.get("layout"):
            warnings.append(f"deliverable {did}: different aspect without layout notes — re-layout, don't crop")
        if d.get("loop") and d.get("sound") == "on":
            warnings.append(f"deliverable {did}: loops usually autoplay muted")


def scorecard_checks(path: Path, errors: list[str], warnings: list[str]) -> None:
    if not path.exists():
        errors.append("evidence/scorecard.md missing — fill the quality rubric before delivery")
        return
    text = path.read_text(encoding="utf-8")
    unchecked = re.findall(r"- \[ \] (G\d)", text)
    if unchecked:
        errors.append("scorecard must-pass items not passed: " + ", ".join(unchecked))
    scores = [int(m) for m in re.findall(r"^\|[^|\n]+\|\s*([1-5])\s*\|", text, re.M)]
    if len(scores) < SCORE_DIMENSIONS:
        errors.append(f"scorecard has {len(scores)}/{SCORE_DIMENSIONS} dimension scores")
    elif min(scores) <= 2 or sum(scores) / len(scores) < 4:
        errors.append(f"scorecard below premium bar (avg {sum(scores) / len(scores):.1f}, min {min(scores)}; need avg ≥ 4 and none ≤ 2)")
    reviewer = re.search(r"评审人：\s*([^　\n]*)", text)
    if not reviewer or reviewer.group(1).startswith("（") or "自评" in reviewer.group(1):
        warnings.append("scorecard reviewer not recorded or self-review only — prefer a blind review")


TIERS = ("quick", "standard", "premium")


def apply_overrides(plan: dict, errors: list[str], warnings: list[str]) -> list[str]:
    """A written override turns a matching default-rule message into a note. Invariants never bend."""
    notes = []
    invariant = ("claim without source", "source not found", "gap", "overlaps", "invalid start/end", "audioExceptionReason", "sfxRequired=false")
    for o in plan.get("overrides") or []:
        key, reason = str(o.get("rule", "")), str(o.get("reason", "")).strip()
        if not key or not reason:
            warnings.append(f"override without rule/reason: {o}")
            continue
        for bucket in (errors, warnings):
            for msg in list(bucket):
                if key.lower() in msg.lower() and not any(i in msg for i in invariant):
                    bucket.remove(msg)
                    notes.append(f"overridden ({reason}): {msg}")
    return notes


def check(plan: dict, project: Path, final: bool, tier: str = "standard") -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    strict = errors if (final or not plan.get("demo", True)) else warnings
    fps = (plan.get("format") or {}).get("fps", 30)
    frame = 1.0 / fps
    shots = plan.get("shots") or []
    duration = plan.get("duration")

    if not shots:
        errors.append("plan has no shots")
    # timeline
    prev_end = 0.0
    for i, s in enumerate(shots):
        sid = s.get("id", f"#{i}")
        st, en = s.get("start"), s.get("end")
        if not isinstance(st, (int, float)) or not isinstance(en, (int, float)) or en <= st:
            errors.append(f"{sid}: invalid start/end")
            continue
        if st - prev_end > frame / 2:
            errors.append(f"{sid}: gap {st - prev_end:.2f}s before shot")
        if prev_end - st > frame / 2:
            errors.append(f"{sid}: overlaps previous shot by {prev_end - st:.2f}s")
        prev_end = en
    if shots and isinstance(duration, (int, float)) and abs(prev_end - duration) > frame:
        errors.append(f"last shot ends at {prev_end}s but duration is {duration}s")

    # scope
    scope = plan.get("scope") or {}
    if not scope.get("versions") or not scope.get("platforms"):
        strict.append("scope.versions / scope.platforms not set — the user must decide scope")

    # direction
    ok, probs = direction_filled(project / "DIRECTION.md")
    if not ok:
        strict.extend(probs)

    # typography
    typo = plan.get("typography") or {}
    if not typo.get("exceptionReason") and not (typo.get("fontEn") and typo.get("fontZh")):
        strict.append("typography.fontEn / fontZh not assigned separately")

    # per shot copy and claims
    action_times: dict[str, float] = {}
    types = set()
    for s in shots:
        sid = s.get("id", "?")
        types.add(s.get("type", ""))
        st, en = s.get("start", 0), s.get("end", 0)
        if s.get("claim"):
            src = s.get("source", "")
            if not src:
                errors.append(f"{sid}: claim without source")
            else:
                exists, where = resolve_source(src, project, plan.get("repo", ""))
                if exists is False:
                    errors.append(f"{sid}: source not found: {where}")
            if not s.get("plainExplanation"):
                strict.append(f"{sid}: claim shot lacks plainExplanation")
        if s.get("type") not in ("title", "brand", "chapter", "end") and s.get("description"):
            if not typo.get("exceptionReason") and not s.get("headlineEn"):
                warnings.append(f"{sid}: no English short headline")
        desc = s.get("description", "")
        if desc:
            # the description is read from descriptionAt (or shot start) to the end of the shot
            d_at = s.get("descriptionAt")
            span = en - st - (d_at if isinstance(d_at, (int, float)) else 0)
            chars = cjk_count(desc)
            if span > 0 and chars / span > 9:
                warnings.append(f"{sid}: description ~{chars / span:.1f} 中文字/秒, may be too fast to read")
            for w in VAGUE:
                if w in desc:
                    warnings.append(f"{sid}: vague phrase '{w}' — do the plain-language read-through")
        if s.get("type") not in ("title", "brand", "chapter", "end") and not s.get("actions"):
            warnings.append(f"{sid}: no recorded actions (state change or camera move)")
        for a in s.get("actions") or []:
            if "id" in a and isinstance(a.get("at"), (int, float)):
                action_times[a["id"]] = st + a["at"]
    if len(shots) >= 4 and len(types) <= 1:
        warnings.append("all shots share one type — review visual rhythm")

    # audio
    audio = plan.get("audio") or {}
    cues = audio.get("cues") or []
    if plan.get("audioRequired", True):
        music = (audio.get("music") or {}).get("file")
        if not music:
            strict.append("audioRequired but no audio.music.file")
        elif not (project / music).exists():
            warnings.append(f"music file not found yet: {music}")
    elif not plan.get("audioExceptionReason"):
        errors.append("audioRequired=false without audioExceptionReason")

    if plan.get("sfxRequired", True) and plan.get("audioRequired", True):
        cued = {c.get("actionId") for c in cues}
        required = [a.get("id") for s in shots for a in (s.get("actions") or []) if a.get("soundRequired")]
        if not required:
            strict.append("no action marked soundRequired — pick one feedback moment per feature group")
        for aid in required:
            if aid not in cued:
                strict.append(f"action {aid} is soundRequired but has no cue")
        roles = {c.get("role") or c.get("kind") for c in cues}
        if isinstance(duration, (int, float)) and duration >= 30 and cues and len(roles) < 3:
            warnings.append("fewer than three SFX roles in a 30s+ film — review sound variety")
    elif not plan.get("audioExceptionReason"):
        errors.append("sfxRequired=false without audioExceptionReason")

    beat = audio.get("beatGrid") or {}
    for c in cues:
        aid = c.get("actionId")
        if not isinstance(c.get("at"), (int, float)):
            errors.append(f"cue {aid}: missing at")
            continue
        f = c.get("file")
        if f and not (project / f).exists():
            warnings.append(f"cue {aid}: file not found: {f}")
        if aid in action_times:
            heard = c["at"] + (c.get("syncOffset") or 0)
            err = (heard - action_times[aid]) / frame
            if abs(err) > 2:
                (errors if final else warnings).append(
                    f"cue {aid}: heard {err:+.1f} frames from its action (cue.at + syncOffset should equal shot.start + action.at)")
        elif aid:
            warnings.append(f"cue {aid}: no matching action id")
        if c.get("onBeat") and beat.get("bpm"):
            step = 60 / beat["bpm"] / (c.get("beatDivision") or 1)
            heard = c["at"] + (c.get("syncOffset") or 0) - (beat.get("offset") or 0)
            off = (heard - round(heard / step) * step) / frame
            if abs(off) > 2:
                warnings.append(f"cue {aid}: {off:+.1f} frames off its beat — move picture and sound together")

    strategy_checks(plan, shots, strict, warnings)
    deliverable_checks(plan, strict, warnings)
    if final and tier != "quick":
        scorecard_checks(project / "evidence" / "scorecard.md", errors if tier == "premium" else warnings, warnings)

    if plan.get("demo", True) and not final:
        warnings.append("demo mode: not a finished promo; run with --final before delivery")
    notes = apply_overrides(plan, errors, warnings)
    return {"ok": not errors, "tier": tier, "errors": errors, "warnings": warnings, "notes": notes, "limits": LIMITS}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan")
    ap.add_argument("--final", action="store_true", help="treat missing evidence/direction/sound as errors")
    ap.add_argument("--tier", choices=TIERS, help="quick: draft gates only; standard (default); premium: scorecard is a hard gate")
    args = ap.parse_args()
    path = Path(args.plan).expanduser()
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)], "warnings": []}))
        return 1
    result = check(plan, path.parent, args.final, args.tier or plan.get("tier", "standard"))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
