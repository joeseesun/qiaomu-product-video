# Prior-art research — qiaomu-product-video

Researched: 2026-09-25 · Runner: `qiaomu-meta-skill/scripts/research_prior_art.py --strict`
Raw candidates: `reports/prior-art-candidates.json` (27 families, 3 queries)

## Queries

1. product promo video from code repository
2. release notes changelog video
3. software launch video real components

## Catalog status

- skills.sh: query 2 returned results (incl. the target repo); queries 1 and 3 returned no parseable candidates → **missing evidence**.
- SkillsMP: all 3 queries OK (5 / 10 / 10 candidates). Most hits were off-domain (release CI, changelog text, security testing).
- Metric semantics: skills.sh installs = adoption; SkillsMP stars = source repository stars; neither is a quality score.

## Shortlist (inspected in source)

| Candidate | Why shortlisted | Inspected | Lesson |
|---|---|---|---|
| op7418/guizang-product-video-skill | User-specified; the only on-domain catalog hit | Full SKILL.md, all 13 references, script interfaces, license files (cloned 2026-09-25) | Direction-before-code; product-derived devices; real components at video scale; evidence ledger; audio cue alignment by measured onset/peak; honest QA; case-study lessons |
| product-launch-video (local, HyperFrames) | Adjacent: URL/brief → promo on HyperFrames | SKILL.md header and workflow | Mature render engine, brief/storyboard gates, media-use integration; lacks repo-evidence and real-component requirements → use as renderer & routing neighbour |
| affaan-m/ecc:manim-video | Surfaced for query 1 | Description only | Different job (concept explainers); rejected as reference |

## Deduplication

No mirrors or forks of the guizang skill found. The openclaw release-* skills are one family of release-engineering tooling, not video.

## Synthesis

- **keep**: DIRECTION.md-first; 3 directions across axes; "因为产品有 X 所以用 Y"; anti-repetition across and within films; real business components with provider/fixture; ≥ 22px body text at 1080p; feature-evidence ledger with status + source; bilingual headline split with explicit fonts; plain-language copy read-through; music source order; SFX onset/peak alignment; three review checkpoints; contact sheet + transition strips; honest "seen/heard/unverified" delivery.
- **adapt**: render layer → user's installed HyperFrames stack instead of a bundled React/Playwright starter; mixing → hyperframes-audio; SFX → media-use first; covers → optional hand-off to qiaomu-cover-designer; check script rewritten as `check_plan.py` with `--final` strictness and explicit cue↔action frame math.
- **reject**: bundling the starter project, fx-lab, fallback style, fonts and WAV library (AGPL / BUSL-1.1 licensing incompatible with an MIT package, and duplicates HyperFrames); environment installer docs (HyperFrames owns onboarding); upstream's mix_audio.py (hyperframes-audio covers it).
- **invent**: explicit routing table vs. 4 neighbouring skills; `init_project.py` auto-lists sibling DIRECTION.md files to enforce cross-film anti-repetition; single `review_sheets.py` producing sheets + strips + spectrum + per-second RMS + LUFS/TP in one call; unit tests covering the full pipeline on synthetic media.

## License note

Upstream is AGPL-3.0 with BUSL-1.1 fallback assets. This package is a clean-room rewrite of the methodology in new prose and new code; no upstream file, code, asset or sentence was copied. Attribution is kept in SKILL.md and README.

---

# Iteration 1.1.0 — advertising craft research (2026-09-25)

Goal: move from "well-made product film" to "effective product ad". Web research on exemplary software ads and evidence-backed ad practice.

## Sources studied

| Source | Type | What was taken | Evidence strength |
|---|---|---|---|
| [Google Ads Help — About the ABCDs of effective video ads](https://support.google.com/google-ads/answer/14783551) | Platform guidance, built with Ipsos; reviewed by Nielsen/Kantar | Attention / Branding early & throughout / Connection / Direction; objective-specific emphasis | Strong framework; the +30% short-term / +17% long-term lift is Google's own reported average ([Think with Google](https://business.google.com/en-all/think/future-of-marketing/youtube-video-ad-creative/)) |
| [Wistia — optimal video length](https://wistia.com/learn/marketing/optimal-video-length), [audience retention](https://wistia.com/learn/marketing/understanding-audience-retention) | Analysis of 13M+ hosted videos | <1 min for awareness; 1–5 min for demos; biggest drop at the opening | Strong (large first-party dataset), B2B-hosted video bias |
| [advids — SaaS feature launch analysis](https://advids.co/blog/saas-feature-launch) | Comparative breakdown of 7 launch films (Linear, Raycast, Notion, Vercel, Figma, Loom, Stripe) | Focus suppression (blur/dim peripheral UI), zoom to single control, time compression, click feedback, abstract geometry for backend, pull-out-to-logo ending, problem-contrast-solution | Weak–medium: n=7, percentages are illustrative only |
| [Studio Maydit — Linear/Vercel/Raycast aesthetic](https://studiomaydit.com/blog/linear-vercel-raycast-aesthetic) | Design essay | Type system first, near-grayscale + one accent, one idea per section; warning against copying the surface | Opinion; aligns with anti-template rule |
| [sitesplaced — cinematic landing pages](https://sitesplaced.com/blog/cinematic-landing-pages-with-video-backgrounds) (search excerpt) | Design guide | Linear launch films: no VO, camera through real product, one action at a time; seamless hero loops; visible seam reads as cheap | Secondary description; verify against original films |
| [Failory — Lights, Camera, Arc-tion](https://newsletter.failory.com/p/lights-camera-arction) (search excerpt) | Case essay | Arc's CEO-hosted monthly changelog episodes; candour and behind-the-scenes reasoning | Secondary |
| [Superside — B2B SaaS video examples](https://www.superside.com/blog/saas-video-examples) | Curated list | Problem-solution framing, "interface does the talking" (Figma), modular chapters for repurposing (Stripe, GitHub) | Curated opinion |
| [Flowjam — 30 launch video examples](https://www.flowjam.com/blog/30-best-launch-video-examples-checklist) | Curated list + checklist | Single goal; 15-word pain hook; pain → solution → proof; mobile-first + captions; one CTA | Curated opinion |
| [AnnounceKit — video release notes](https://announcekit.app/blog/video-release-notes/) | Guide + 10 examples | Split long updates into one-feature clips; outline + chapters | Curated opinion |
| Meta vertical/sound-off guidance (via [Search Engine Land](https://searchengineland.com/meta-ads-vertical-video-formats-452902) and spec round-ups) | Secondary | Design for sound off; 9:16 / 4:5 native vertical; safe zones | "85% silent" figure is a 2016 Digiday report — cited as dated |
| Chinese platform spec round-ups ([secaiyun](https://www.secaiyun.com/docs/social-media-video-size-specification-guide-2026-08-28.html), [resouci](https://resouci.com/xiaohongshu-image-size-guide-2026/)) | Secondary spec tables | B站 16:9 cover readable at ~1/4; 小红书 3:4 / 9:16; 视频号 9:16 | Secondary; skill tells users to re-check platform rules |

## Gap analysis vs. 1.0.0

| Gap | Evidence | Change |
|---|---|---|
| No single-minded message / goal / CTA | ABCD "Focus the message", "Direction"; all breakdowns stress one mental shift | `references/strategy.md`; `plan.strategy`; check_plan strategy gate |
| No hook / early-brand rule | ABCD "Jump in", "Show up early"; Wistia opening drop | shot roles hook/brand/aha/cta; ≤5s brand warning; hook strip |
| Not muted-safe | ABCD audio+supers; Meta sound-off guidance | sound-off rule; claim shots need on-screen text; mute test |
| Single deliverable | Multi-format launch practice; Linear-style hero loops; changelog clip series | `references/deliverables.md`; `plan.deliverables`; loop-seam SSIM |
| No format archetypes | Linear / Apple / Arc / Slack patterns | `references/formats-and-cases.md` (7 formats + selection table) |
| Missing launch-film techniques | advids breakdown | focus dimming, interaction accent, time compression, split before/after, pull-out ending, invisible-process geometry |
| No quality bar | — (invented) | `references/quality-rubric.md`: 9 must-pass + 10 scored dimensions, blind review preferred; enforced by `--final` |

## Rejected

- Fixed numeric "hook rate > 30%", "3.4× view time for multi-format" and similar vendor stats: unverifiable, not used as rules.
- UGC / celebrity / mascot formats: outside a repo-driven code pipeline.
- Faking speed or states the product doesn't have (time compression keeps intermediate states).


---

# 1.3.0 — Opus 5.5 代码视频案例（2026-09-27）

## Sources

- Collection built for this iteration: [joeseesun/opus-video-prompts](https://github.com/joeseesun/opus-video-prompts) — 54 public cases, 18 verbatim author-published prompts (X, Bilibili, Linux.do, GitHub, YouMind), collected 2026-09-27, all dated 2026-09-22…25.
- Strongest mechanism sources: zero (@twoclipping) UI-morph and high-end product templates; Danny Stuart's Remotion promo write-up; JohnHeibel/PDoomVideo ANIMATION_GUIDE; WinterArc21/Battle-of-Austerlitz-Film; Alex Prompter 5-scene explainer; Rory Flynn Negroni explainer.
- Evidence quality: social posts and author self-reports; engagement numbers are not quality scores; costs/times are self-reported and not reproduced.

## Keep / adapt / reject / invent

| Mechanism seen | Decision | Where |
|---|---|---|
| Storyboard / beat-grid state list before any code | keep (already the three checkpoints) + adapt: quick path still produces a one-page storyboard | SKILL.md 快速通道 |
| Banned-effects list in the brief | adapt → mandatory DIRECTION section with a starter list | direction.md §7 |
| Beat grid measured from the song (numpy) | adapt → stdlib + ffmpeg `beat_grid.py`, writes `audio.beatGrid(measured)` + `drop`, per-shot frame offsets | scripts/beat_grid.py, audio.md |
| Closed-form springs; retargeting = sum of springs; two edges on different springs | adapt → `kit/spring.js` | visual-vocabulary.md 弹簧与形变 |
| Playwright subframes + ffmpeg tmix motion blur | adapt → `render.mjs --blur N --shutter` | render.mjs, review-and-delivery.md |
| Probe one frame per beat / 20+ frames before full render | keep | review-and-delivery.md step 5 |
| SFX placed by measured peak | already present (`sfx_landmarks.py`) | — |
| Gotchas: will-change blur, preserve-3d opacity, text swap in morphing container, loop incl. cursor speed, video as JPEG sequence | keep as pitfalls/tech notes | pitfalls.md, visual-vocabulary.md |
| Notes one at a time during iteration | keep | review-and-delivery.md step 6 |
| TTS via docs file + `.env` + deny Read(.env) | keep for voiceover | audio.md |
| Generative video (Seedance/Runway) as base plates | adapt with boundary: mood inserts / rotoscope plates only, never product UI; disclose | adapters.md |
| One-line prompts produce "launch videos" of abstract products | reject as a default for this skill — product films must show the real product; kept only as quick-path inspiration | formats-and-cases.md |
| Concept explainers (Transformer, history, physics) and editing talking-head footage | reject — out of scope, routed away; added as negative trigger cases | evals/trigger_cases.json |
| "One shot" claims | reject as a planning assumption; many took ≥2 passes; delivery note now records iterations and cost | pitfalls.md, review-and-delivery.md |

## Missing evidence

- `beat_grid.py` validated on a synthetic 128 BPM track (tempo ±0.6, downbeat ±25 ms, drop ±50 ms) and on one real code-scored track (96 BPM, measured 95.94); not yet on commercial songs with swing, tempo changes or no kick.
- Motion blur validated visually on a synthetic spring-driven box (4 subframes visibly stepped on very fast motion → docs recommend 8); not yet on a real product film.
- No new product film produced with 1.3.0.
