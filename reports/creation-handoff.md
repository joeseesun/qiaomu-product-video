# Creation handoff — qiaomu-product-video 1.0.0

## Result

- Skill: `qiaomu-product-video` 1.0.0 (Production mode)
- Job: turn a real software repository/UI into a promo or release-update video with evidence-backed claims, product-derived visuals, real components, aligned sound and honest QA.
- Path: `~/.claude/skills/qiaomu-product-video` · Publication: not published.

## Reference skills studied

- op7418/guizang-product-video-skill — full source review; mechanisms mapped in `reports/prior-art-research.md`.
- product-launch-video (local) — render/routing neighbour.

## Advantages

- [design advantage] Reuses the installed HyperFrames stack rather than shipping a second render engine; package stays small (7 references, 4 scripts, stdlib only).
- [design advantage] MIT-clean: no AGPL/BUSL code or assets carried over.
- [design advantage] Explicit routing boundaries against product-launch-video, qiaomu-video-composer, qiaomu-video-script, qiaomu-cut.
- [validated advantage] Trigger eval 17/17 (8 positive, 6 negative, 3 near-neighbour) — `reports/trigger-eval.json`.
- [validated advantage] 4/4 unit tests pass incl. full pipeline on synthetic video/audio (init → landmarks → check_plan pass/fail → review sheets).
- [hypothesis] Films made with this skill match upstream quality — **missing evidence**: no real product film produced yet.

## Missing evidence

- No end-to-end film on a real repository.
- React-component-in-HyperFrames mounting guidance is a recommended approach, not yet validated on a real project.
- skills.sh returned no parseable candidates for 2 of 3 queries.

---

# 1.1.0 — premium iteration (2026-09-25)

- Added advertising strategy layer (single message, aha, CTA, ABCD), 7 format archetypes with case lessons, multi-format deliverables, premium scorecard.
- Scripts: `check_plan.py` gains strategy / shot-role / deliverable / scorecard gates; `review_sheets.py` gains hook strip, thumbnail tests, loop-seam SSIM.
- [validated advantage] trigger eval 21/21; unit tests 6/6 (incl. scorecard below-bar and must-pass failures, loop seam).
- [design advantage] quality bar is explicit and machine-checked for completeness; blind review recommended.
- [hypothesis] films made with 1.1.0 are more effective ads than 1.0.0 — **missing evidence**: no real film or audience test yet.


---

# 1.3.0 — Opus 5.5 code-video research iteration (2026-09-27)

## Reference material studied

- 54 community cases + 18 author-published prompts, collected in [joeseesun/opus-video-prompts](https://github.com/joeseesun/opus-video-prompts). Mapping in `reports/prior-art-research.md` (1.3.0 section).
- Candidate-specific lessons: zero's templates → banned list, beat-grid-first storyboard, subframe blur, closed-form springs; Danny Stuart → storyboard before code, reference video over adjectives; PDoomVideo → determinism guide, "one-shot" was two passes; Alex Prompter → fixed five-scene skeleton; WY/Axton → TTS key hygiene, notes-one-at-a-time.

## Changes

- New: `scripts/beat_grid.py`, `assets/starter/src/kit/spring.js`, `render.mjs --blur/--shutter`, `tests/test_beat_grid.py`.
- References: quick path, mandatory banned list, springs & morph section, motion blur, 8 new pitfalls, generative-video boundary, frame probing and one-note iteration, case table.
- README / interface drift fixed (they still described HyperFrames as the default engine).

## Advantages

- [validated advantage] trigger eval 26/26 (5 new cases incl. 2 near-scope negatives) — `reports/trigger-eval.json`.
- [validated advantage] unit tests 12/12 incl. beat grid on synthetic audio and spring purity.
- [validated advantage] `--blur` end-to-end render: frame count/fps unchanged (45 @ 30 fps), blurred frame visually inspected.
- [design advantage] all additions are stdlib/ffmpeg or dependency-free JS; no new install burden.
- [hypothesis] films made with 1.3.0 look less template-like and cut more musically — **missing evidence**: no real film or blind comparison yet.
