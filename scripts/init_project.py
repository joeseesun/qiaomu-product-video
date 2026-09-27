#!/usr/bin/env python3
"""Initialize a qiaomu-product-video project: BRIEF, DIRECTION template, plan skeleton, evidence files.

Copyright (c) 向阳乔木 — MIT License.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

STARTER = Path(__file__).resolve().parent.parent / "assets" / "starter"
TASTE = Path.home() / ".qiaomu-product-video" / "taste.md"  # per-user taste memory, grows after every film

BRIEF = """# BRIEF

- 产品 / 仓库：{repo}
- 风格：{style}（repo 沿用产品设计 / default 中性包装 / hybrid 保留识别换外层）
- 版本范围：（待用户确认，例如 v0.10.12..v0.11.0 或"最近 4 周"）
- 平台面：（待用户确认：desktop / web / cli-tui / mobile / api）
- 发布渠道与画幅：{width}x{height} @ {fps}fps，目标时长约 {duration} 秒
- 语言：中文说明 + 英文短标题
- 是否允许出现链接：（待确认）
- 参考视频：（无 / 路径）
- 创建日期：{today}

## 策略（先填这里）

- goal（只选一个）：
- audience：
- singleMessage（看完能复述的一句话）：
- ahaMoment（证明它的那个画面）：
- cta：
- 片型：

## 用户原话与决定

-
"""

DIRECTION = """# DIRECTION

> 填完再搭镜头。每个手法都要写得出"因为产品有 X，所以用 Y"。

## 0. 同工作区之前的片子（反重复）

{previous}

## 0b. 口味记忆（来自 ~/.qiaomu-product-video/taste.md）

{taste}

## 1. 参考拆解

| 手法 | 表达什么 | 出现位置 / 时长 | 本片是否采用、改写成什么、依据 |
|---|---|---|---|

## 2. 产品气质

- 谁在用、什么情境、什么感觉：
- 设计语言（附文件路径）：
- 母题候选：

## 3. 三个方向（两两至少三个轴不同）

| 轴 | 方向 A | 方向 B | 方向 C |
|---|---|---|---|
| 底色与光 | | | |
| 字体声音 | | | |
| 母题来源 | | | |
| 镜头语言 | | | |
| 转场 | | | |
| 节奏 | | | |
| 声音 | | | |

选定：
理由：

## 4. 本片专属手法（3–5 条）

1. 因为产品有 ______，所以用 ______。

## 5. 片内反重复

- 主角 / 辅助 / 背景的出场方式：
- 相邻镜头取景或明暗如何变化：

## 6. 叙事结构

## 7. 画面规范

- 画幅 / 帧率 / 底色 / 安全区：
- 字号阶梯（中 / 英分别）：
- 界面上镜倍数（≈ 22 ÷ 产品正文 px）：
- 明暗主题：
- 动效语法（入场、缓动、时长）与本片不用什么：

## 8. 镜头表

| id | 时间 | 唯一主角 | 画面与动作（子拍时间） | 上屏文案 | 声音 |
|---|---|---|---|---|---|
"""

FEATURE_EVIDENCE = """# Feature evidence

| feature | benefit | status | release | source | component | demoState | limits |
|---|---|---|---|---|---|---|---|
"""

STYLE_AUDIT = """# Style audit

1. 色板语义与来源：
2. 字体（英文标题 / 中文标题 / 正文，实际加载结果）：
3. 间距、圆角、阴影、线宽、密度：
4. 品牌资产（app icon / logo / 单色）：
5. 镜头适配与暗色主题：
6. 母题候选：
7. 决策（repo / default / hybrid）与理由：
"""

SCORECARD = """# Scorecard

评审人：（自评 / 他人 / 无上下文子代理）　观看文件：renders/

## 必过项
- [ ] G1 一句话复述：
- [ ] G2 3 秒测试：
- [ ] G3 品牌识别：
- [ ] G4 静音测试：
- [ ] G5 事实：
- [ ] G6 真组件：
- [ ] G7 可读性：
- [ ] G8 技术：
- [ ] G9 CTA：

## 评分（1–5）
| 维度 | 分 | 证据 |
|---|---|---|
| 单一信息 | | |
| 开场 | | |
| aha 时刻 | | |
| 产品推导 | | |
| 克制与焦点 | | |
| 节奏 | | |
| 文案 | | |
| 声音 | | |
| 画面质感 | | |
| 多版本 | | |
| 记忆点 | | |

## 下一轮只改
1.
2.
"""

COPY_REVIEW = """# Copy review

| shot | 白话事实（以前 → 现在 → 结果） | 英文标题 | 中文标题 | 中文说明 | 遮画面试读结论 |
|---|---|---|---|---|---|
"""


def previous_directions(output: Path) -> str:
    parent = output.parent
    found = []
    if parent.is_dir():
        for p in sorted(parent.glob("*/DIRECTION.md")):
            if p.parent.resolve() != output.resolve():
                found.append(f"- {p.parent.name}/DIRECTION.md：列出它的开场、章节、背景、配乐，本片避开")
    return "\n".join(found) if found else "- （未发现同工作区的其他片子）"


def taste_summary() -> str:
    """Global taste memory: what this user liked/rejected in earlier films. Read, never auto-edited here."""
    if not TASTE.exists():
        return f"- （还没有口味记忆；交付后把用户反馈写进 {TASTE}）"
    lines = [l for l in TASTE.read_text(encoding="utf-8").splitlines() if l.startswith("- ")]
    return "\n".join(lines[-12:]) or "- （口味记忆为空）"


def plan_skeleton(args: argparse.Namespace) -> dict:
    return {
        "title": "",
        "demo": True,
        "repo": args.repo or "",
        "style": args.style,
        "scope": {"versions": "", "platforms": []},
        "tier": "standard",
        "strategy": {"goal": "", "audience": "", "singleMessage": "", "ahaMoment": "", "cta": "", "format": ""},
        "overrides": [],
        "deliverables": [
            {"id": "hero", "aspect": "16:9", "duration": args.duration, "sound": "on", "use": ""}
        ],
        "format": {"width": args.width, "height": args.height, "fps": args.fps},
        "duration": args.duration,
        "typography": {"fontEn": "", "fontZh": "", "exceptionReason": ""},
        "audioRequired": True,
        "sfxRequired": True,
        "audioExceptionReason": "",
        "shots": [
            {
                "id": "open",
                "start": 0,
                "end": 3,
                "type": "title",
                "role": ["hook"],
                "headlineEn": "",
                "headline": "",
                "plainExplanation": "",
                "description": "",
                "claim": False,
                "source": "",
                "component": "",
                "actions": [],
            }
        ],
        "audio": {
            "music": {"file": "assets/music.wav", "gain": 0.65, "source": ""},
            "beatGrid": {"bpm": 120, "offset": 0},
            "cues": [],
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", required=True, help="video project directory")
    ap.add_argument("--repo", help="product repository path")
    ap.add_argument("--style", choices=["repo", "default", "hybrid"], default="repo")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--duration", type=float, default=48)
    ap.add_argument("--force", action="store_true", help="overwrite existing template files")
    ap.add_argument("--engine", choices=["starter", "none"], default="starter",
                    help="starter: copy the bundled render project (default); none: keep your own engine")
    args = ap.parse_args()

    if args.style in ("repo", "hybrid") and not args.repo:
        print("error: --repo is required for style repo/hybrid", file=sys.stderr)
        return 2
    if args.repo and not Path(args.repo).expanduser().is_dir():
        print(f"error: repo not found: {args.repo}", file=sys.stderr)
        return 2

    out = Path(args.output).expanduser()
    for d in ("evidence/review", "evidence/stills", "assets/sfx", "renders"):
        (out / d).mkdir(parents=True, exist_ok=True)

    fmt = dict(
        repo=args.repo or "（无）", style=args.style, width=args.width, height=args.height,
        fps=args.fps, duration=args.duration, today=dt.date.today().isoformat(),
    )
    files = {
        "BRIEF.md": BRIEF.format(**fmt),
        "DIRECTION.md": DIRECTION.format(previous=previous_directions(out), taste=taste_summary()),
        "plan.json": json.dumps(plan_skeleton(args), ensure_ascii=False, indent=2) + "\n",
        "evidence/feature-evidence.md": FEATURE_EVIDENCE,
        "evidence/style-audit.md": STYLE_AUDIT,
        "evidence/copy-review.md": COPY_REVIEW,
        "evidence/scorecard.md": SCORECARD,
        "evidence/component-usage.json": "[]\n",
        "evidence/audio-selection.json": json.dumps({"music": {}, "sfx": []}, indent=2) + "\n",
    }
    written, kept = [], []
    if args.engine == "starter":
        for src in STARTER.rglob("*"):
            if "node_modules" in src.parts or src.is_dir():
                continue
            rel = src.relative_to(STARTER)
            dst = out / rel
            if dst.exists() and not args.force:
                kept.append(str(rel))
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            written.append(str(rel))
    for rel, text in files.items():
        p = out / rel
        if p.exists() and not args.force:
            kept.append(rel)
            continue
        p.write_text(text, encoding="utf-8")
        written.append(rel)

    print(json.dumps({"project": str(out), "written": written, "kept": kept,
                      "next": "confirm scope and strategy with the user, fill evidence/ and DIRECTION.md, then `npm install` in the project"},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
