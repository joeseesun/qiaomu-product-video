---
name: qiaomu-product-video
description: "自包含地制作软件产品宣传片、广告片、版本更新片、changelog / release notes 视频：从代码仓库、真实产品界面、官网 URL 或截图出发，先定广告策略（单一主张、aha 画面、CTA、片型、多画幅交付清单）并锁定功能证据，写 DIRECTION.md，用真实组件或真实运行录制上镜，自带渲染管线、原创配乐、音效合成、混音、封面与审片工具，过 3 秒/静音/缩略图测试和精品评分卡后交付主片、竖版、剪版与循环版。Use for 产品宣传片、产品广告片、更新视频、新版本介绍视频、功能演示片、product promo、release video、changelog promo、launch video for web apps, Obsidian/VS Code plugins, CLI tools, APIs, AI agents and mobile apps. Not for article/book explainer videos, script-only requests, or editing someone's existing footage."
license: MIT
metadata:
  version: 1.3.0
  author: 向阳乔木
---

# 乔木产品视频

一支片子只让观众记住一句话：3 秒抓住、5 秒认出产品、静音也看得懂；画面来自真实产品（真组件或真实运行），每个手法都说得出它来自产品的哪一点。

**完全自包含**：策略、证据、渲染（`assets/starter`）、产品适配器（`assets/adapters`）、配乐、音效、混音、封面、审片都在本 skill 内。用户已有 Remotion 等工程时可沿用其渲染，其余流程不变。

## 规则分三层

- **底线（不能破）**：主张有证据；画面来自真实产品（真组件 / 真实运行录制 / 经同意的忠实重建）；上镜可读（1080p 正文 ≥ 22px 等效）；诚实验收；素材授权；不碰隐私数据。
- **默认（可破，写理由）**：3 秒 hook、5 秒品牌、中文标题无衬线、字号阶梯、片长、片型、镜头长度……破格时写进 `plan.json.overrides[{rule, reason}]`，检查器把对应提示降为 note。好片常常来自有理由的破格。
- **灵感（随便用）**：视觉词汇、案例、配器表——都是推导示范，不是菜单。

每条默认规则都写了它的意图（见 [原则](references/principles.md)）；意图还成立时，形式可以变。

## 档位

| tier | 用在 | 必做 |
|---|---|---|
| `quick` | 草稿、内部看、单功能短片 | 策略五项、真实画面、结构检查 |
| `standard`（默认） | 正式发布 | + DIRECTION、逐镜头静帧、声音、审片图、评分卡（提示） |
| `premium` | 发布会级主片 | + 三方向真实静帧给用户选、破格方向、盲评、评分卡硬门槛、标杆对照 |

三个低成本确认点：**策略一页纸 → 三个方向的真实静帧 → 粗剪**。在最便宜的时候纠偏。

**快速通道**：用户只给一句话或说"直接做"时，走 `quick`，从仓库和官网推断策略五项，最多合并问一次；仍然先给一页"策略 + 逐秒分镜"再写代码——这一页最便宜，也是社区好片的共同点。

## 流程

1. **锁范围与策略（用户拍板）。** 未指定时一次问清：版本范围、平台面、渠道与画幅、语言、能否出现链接、参考视频、风格（`repo` 推荐 / `default` / `hybrid`）、档位。按 [广告策略](references/strategy.md) 定 `goal / audience / singleMessage / ahaMoment / cta`。先读 `~/.qiaomu-product-video/taste.md`（口味记忆）。
2. **选片型与交付清单。** [片型与案例](references/formats-and-cases.md) 选片型；[交付物](references/deliverables.md) 写 `plan.deliverables`（竖版重排、剪版重剪、循环无缝）。
3. **初始化。** `python3 <skill-dir>/scripts/init_project.py --output <video-dir> --repo <repo>`（拷入渲染工程、模板、证据目录、口味记忆），`npm install`。
4. **接通真实产品。** 按 [产品适配](references/adapters.md) 选路径：Web/React 组件、Obsidian 等插件宿主、官网 URL 截取、CLI 终端录制回放、API 真实请求、AI Agent 真实运行回放、移动端、原生应用。**先录真实数据**（`FILM_RECORD=1 node tools/lab.mjs --record …`），之后离线确定性渲染。写 `evidence/feature-evidence.md`（每条主张有来源；**数字以 UI 实际显示为准**，文档常过时）和 `style-audit.md`。
5. **定方向，写 `DIRECTION.md`。** [影片方向](references/direction.md)：三个方向 + **一个破格方向**、3–5 条"因为产品有 X，所以用 Y"、**一个签名时刻**、画面规范（数字）、**禁用清单**、逐秒镜头表（标 hook / brand / aha / cta）。
6. **写文案。** [文案与节奏](references/copy-and-pacing.md)：白话事实 → 英文短标题 + 中文标题 + 说明；上屏文字独立讲完故事；`check_glyphs.py` 确认字体覆盖。
7. **逐镜头搭建。** 每个镜头 = 产品 iframe + `director()`（按时间驱动真实交互）+ GSAP 摄像机与字幕。手法见 [视觉手法词汇](references/visual-vocabulary.md)；界面状态变化用 `kit/spring.js` 的闭式弹簧，保持纯函数。每搭完一个镜头 `node tools/stills.mjs … --shot <id>` 出静帧对照镜头表。
8. **声音。** [声音](references/audio.md)：用户曲子先 `beat_grid.py` 实测节拍与 drop，切点落强拍；否则 `score.py` 按镜头结构原创配乐→ `make_sfx.py` 合成音效（或授权录音）→ `sfx_landmarks.py` 实测 → cue 按动作对齐 → `mix_audio.py` 让位混音、响度、可闻度报告。
9. **审片、评分、出多版本。** 整片渲染前按拍抽帧（≥ 20 帧）修问题；成片 `node tools/render.mjs --d <id> --blur 4 --final`（子帧动态模糊）→ `review_sheets.py`（联系表、3 秒条带、转场条带、缩略图、循环接缝、频谱响度、`--compare` 标杆对照）→ [精品评分卡](references/quality-rubric.md)（**评审与制作分开**：交给无上下文子代理盲评）→ `check_plan.py --final`。派生版本用 `derive_plan.py` 重排时间并单独配乐混音。封面用 `tools/cover.mjs`。
10. **交付并记住口味。** 用户意见一次改一条。交付说明分开写"自动检查 / 实际看过听过 / 评审方式 / 未验证 / 实际轮数与花费"。把用户反馈追加到 `~/.qiaomu-product-video/taste.md`。

## 工具

```bash
python3 <skill-dir>/scripts/init_project.py --output <dir> [--repo <repo>] [--style repo|default|hybrid] [--engine starter|none]
node tools/lab.mjs [--record] --steps lab/flows.mjs --shot out.png      # 驱动真实产品、录制真实请求
node tools/stills.mjs <outDir> <t…> | --shot <id> [--d <deliverable>]    # 静帧
node tools/render.mjs --d <deliverable> [--audio assets/master.wav] [--blur 4]  # 逐帧渲染 → MP4（--blur 子帧动态模糊，成片用）
node tools/capture.mjs steps.json                                       # 只有 URL 时：截取真实网页状态
node tools/cover.mjs                                                    # 3:4 / 4:3 / 16:9 封面
python3 <skill-dir>/scripts/check_plan.py plan.json [--final] [--tier quick|standard|premium]
python3 <skill-dir>/scripts/beat_grid.py song.mp3 --plan plan.json [--write]   # 用户曲子：实测 BPM、首个强拍、drop、镜头离拍帧差
python3 <skill-dir>/scripts/score.py plan.json --mood warm|bright|tech|ambient|punchy --key D
python3 <skill-dir>/scripts/make_sfx.py --out assets/sfx [--bright 0.85]
python3 <skill-dir>/scripts/sfx_landmarks.py assets/sfx/*.wav
python3 <skill-dir>/scripts/mix_audio.py plan.json [--name vertical]
python3 <skill-dir>/scripts/derive_plan.py plan.json --deliverable vertical
python3 <skill-dir>/scripts/review_sheets.py renders/hero.mp4 --plan plan.json [--loop] [--compare ref.mp4] --out evidence/review
python3 <skill-dir>/scripts/record_terminal.py --out assets/demo.cast -- <command…>   # CLI 产品：真实终端录制
python3 <skill-dir>/scripts/check_glyphs.py <font> plan.json
```

依赖：Python ≥ 3.9、FFmpeg、Node ≥ 20、Chrome（或 `npx playwright install chromium`）。Python 脚本只用标准库（`check_glyphs.py` 需 fontTools）。

## 参考

- 策略：[原则](references/principles.md) · [广告策略](references/strategy.md) · [片型与案例](references/formats-and-cases.md) · [交付物](references/deliverables.md)
- 制作：[产品适配](references/adapters.md) · [证据与组件](references/evidence-and-components.md) · [影片方向](references/direction.md) · [视觉手法词汇](references/visual-vocabulary.md) · [文案与节奏](references/copy-and-pacing.md) · [声音](references/audio.md)
- 验收：[审片与交付](references/review-and-delivery.md) · [精品评分卡](references/quality-rubric.md) · [踩坑表](references/pitfalls.md)
- 实战记录：`reports/validation-qiaomu-ai-rss.md` · 社区代码视频案例：`reports/prior-art-research.md`（Opus 5.5 一节）

方法论学习自 [op7418/guizang-product-video-skill](https://github.com/op7418/guizang-product-video-skill)（AGPL-3.0），本包为独立重写，未复制其代码、素材或默认样式。
