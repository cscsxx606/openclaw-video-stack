# Seedance2-skill

English | **[中文](README.md)**

ByteDance Seedance AI Video Creative Studio + **production-grade batch concurrency toolkit** — turns any AI Agent into a video creative director and runs multi-shot pipelines in production.

> Not a prompt template. A creative system with taste.
> **v2.1 new** (2026-06-12): SQLite task registry, concurrent batch submission, cost-control switches.

## Core Features

- 🎬 **Autonomous Creative Director** — No fixed pipeline. Agent decides analysis order, iteration rounds, output format.
- 🎯 **Creativity Gate** — Every prompt must pass four checks: memorability, surprise, emotional arc, narrative.
- 📚 **Comprehensive Vocabulary** — 100+ cinematography terms (12 categories), 10 director styles, 9 anime techniques.
- 🎥 **Seedance 2.0 Full Multimodal** — Text / image / video / audio input. Motion replication, beat-sync, multi-shot.
- ⚡ **Batch Concurrency** (v2.1) — Multi-shot scenarios: concurrent submission, max-workers 2-4 yields 1.6-2x speedup.
- 📊 **Task Registry** (v2.1) — SQLite WAL mode, crash-recoverable, 13-task estimation error 0.003%.
- 💰 **Cost-Control Switches** (v2.1) — `--draft` / `--service-tier flex` / `720p` combinations save 50-80%.

## Project Structure

```
Seedance2-skill/
├── SKILL.md          # Skill document · Chinese (Agent entry point)
├── SKILL_EN.md       # Skill document · English
├── reference.md      # Vocabulary, techniques, official examples
├── scripts/
│   ├── seedance.py   # Volcengine Ark API CLI (single + queries)
│   ├── batch.py      # v2.1 Concurrent batch submission (max-workers 2-4)
│   └── db.py         # v2.1 SQLite task registry (stats/verify/pending)
├── README.md         # 中文 README
└── README_EN.md      # This file (English)
```

## Quick Start

### 1. Install

Clone this repo into your Agent's skill directory:

```bash
git clone https://github.com/cscsxx606/openclaw-video-stack.git
# or standalone
git clone https://github.com/zhanghaonan777/Seedance2-skill.git
```

### 2. Set Up API Key

```bash
export ARK_API_KEY="your-volcengine-ark-api-key"
```

Get your API Key from the [Volcengine Console](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey).

### 3. Three Usage Scenarios

#### A. Single Video Generation (since v1.0)

```bash
# Text-to-video
python3 scripts/seedance.py create --prompt "A man in black running through a crowded market" --ratio 16:9 --duration 5 --wait --download ~/Desktop

# Image-to-video
python3 scripts/seedance.py create --prompt "The character slowly turns around" --image photo.jpg --ratio adaptive --wait --download ~/Desktop

# Video reference / motion replication (Seedance 2.0)
python3 scripts/seedance.py create --prompt "Follow the camera movement from the reference" --video reference.mp4 --wait --download ~/Desktop
```

#### B. Concurrent Batch Generation (v2.1 recommended — multi-shot)

```bash
# 4x 480p draft concurrent preview = ¥4.48, ~30s
python3 scripts/batch.py \
  --prompt "Shot 1: aerial city view" \
  --prompt "Shot 2: character close-up" \
  --prompt "Shot 3: street follow" \
  --prompt "Shot 4: sunset panorama" \
  --duration 4 --resolution 480p --draft --max-workers 4 \
  --project my-video --download ./out

# Dry-run to see cost first (no submission)
python3 scripts/batch.py --prompt "s1" --duration 5 --resolution 720p --dry-run
```

#### C. Task Persistence + Crash Recovery (v2.1)

```bash
# Create task (don't wait, runs in background)
python3 scripts/seedance.py create --prompt "..." --project su7

# Process crashed? List pending tasks
python3 scripts/seedance.py db pending --project su7

# Reconnect to a task and wait
python3 scripts/seedance.py wait cgt-20260612093622-zwxq2 --download ./out
```

## 💰 Cost-Control Switch Combo (v2.1, measured)

| Switch | Saving | Limitations | Measured Cost |
|--------|--------|-------------|---------------|
| `--draft` (1.5 Pro) | 50% off | Forces 480p; cannot combine with flex | 4s 480p = **¥1.12/shot** |
| `--service-tier flex` | 50% off | Not supported by Seedance 2.0 | 5s 1080p = ¥2.37/shot |
| `--resolution 720p` | 50% tokens | Theoretical (not measured) | Est. ¥4.5/shot |
| **Combo: draft + 5s × 5 shots** | **-80%** | vs 15s 2.0 main render | **¥4.74/batch** vs ¥23.68/batch |

### Production Recommendations

1. **Preview** → 1.5P + draft + 480p (¥1.12/13s/shot) for 4-8 shot storyboard validation
2. **Final** → Seedance 2.0 (¥9.04/7min/shot) with 4 concurrent, total ~7 min
3. **Save more** → Seedance 2.0 + 720p (est. ¥4.5/shot), run a single 720p first to verify

## 📊 Task Registry (v2.1)

All tasks are written to SQLite by default: `~/.openclaw/workspace/data/seedance_tasks.db`

```bash
# Total cost statistics
python3 scripts/seedance.py db stats
# Output: succeeded count=13 est=¥239.22 actual=¥239.28

# Filter by project
python3 scripts/seedance.py db stats --project su7

# Auto-verify estimation accuracy (5/5 reference points)
python3 scripts/db.py verify

# Find pending tasks (for crash recovery)
python3 scripts/seedance.py db pending --project su7

# Inspect a batch
python3 scripts/seedance.py db batch batch-1781229824
```

## Supported Models

| Model | Model ID | Capabilities |
|-------|----------|-------------|
| **Seedance 2.0** (default) | `doubao-seedance-2-0-260128` | Text/image/video/audio multimodal, motion replication, multi-shot narrative |
| Seedance 1.5 Pro | `doubao-seedance-1-5-pro-251215` | Text/image-to-video, native audio, **draft preview**, **flex offline inference** |
| Seedance 1.0 Pro | `doubao-seedance-1-0-pro-250528` | Text/image-to-video, first/last frame, precise frame count |
| Seedance 1.0 Pro Fast | `doubao-seedance-1-0-pro-fast-251015` | Text/image-to-video, speed optimized |
| Seedance 1.0 Lite I2V | `doubao-seedance-1-0-lite-i2v-250428` | Multi-reference images ([img1][img2] syntax) |

## CLI Reference

### `seedance.py create` (single)

| Flag | Description |
|------|-------------|
| `--prompt` | Video description prompt |
| `--image` / `--last-frame` / `--ref-images` | First frame / last frame / reference images (1-9) |
| `--video` | Reference videos (1-3, Seedance 2.0) |
| `--audio` | Reference audio (1-3, Seedance 2.0) |
| `--model` | Model ID (defaults to Seedance 2.0) |
| `--ratio` | Aspect ratio: 16:9 / 4:3 / 1:1 / 3:4 / 9:16 / 21:9 / adaptive |
| `--duration` | Duration in seconds, -1 for auto |
| `--resolution` | 480p / 720p / 1080p |
| `--draft` | Draft mode (1.5 Pro only) |
| `--service-tier` | `default` or `flex` (offline 50% off, **Seedance 2.0 not supported**) |
| `--generate-audio` | Generate synchronized audio |
| `--return-last-frame` | Return last frame URL (for video chaining) |
| `--callback-url` | Webhook URL for status notifications |
| `--wait` | Wait for task completion |
| `--download` | Download directory |
| **`--project`** (v2.1) | Task grouping tag (used by `db stats --project`) |
| **`--max-wait`** (v2.1) | `wait` subcommand timeout (default 1800s) |
| **`--no-db`** (v2.1) | Skip SQLite registration |

### `batch.py` (v2.1 new)

```bash
# Multiple --prompt inline OR --config tasks.json
python3 scripts/batch.py \
  --prompt "s1" --prompt "s2" --prompt "s3" \
  --duration 4 --resolution 480p --draft \
  --max-workers 2 --service-tier flex \
  --project batch1 --download ./out \
  [--dry-run]
```

| Flag | Description |
|------|-------------|
| `--prompt` | Multiple prompts (repeat N times) |
| `--config` | JSON config file path (cleaner for many tasks) |
| `--max-workers` | Concurrency (2-4 sweet spot, 1.6-2x speedup) |
| `--service-tier` | `default` or `flex` |
| `--draft` | Draft mode |
| `--resolution` / `--ratio` | Resolution / aspect ratio |
| `--duration` | Duration |
| `--dry-run` | Show cost estimate only, no submission |
| `--project` | Task grouping |
| `--download` | Video download directory |

## 🎯 The Creativity System

The core of this Skill isn't API calls — it's the **creativity gate**:

1. **Memorability** — What will the viewer remember after watching?
2. **Surprise** — Is there a twist, contrast, exaggeration, or unusual detail?
3. **Emotion** — Does it have an emotional arc (tension → release, calm → explosion)?
4. **Narrative** — Even in 5 seconds, there should be a change from A to B.

The Agent self-reviews every prompt and rewrites until it passes. No mediocre output allowed.

## Agent Integration

Compatible with any AI Agent platform supporting skill/tool loading.

### OpenClaw

Place this directory in OpenClaw's skills folder (e.g. `~/.openclaw/workspace/skills/Seedance2-skill/`). Agent loads automatically when users mention "Seedance", "video generation", "AI video", etc.

### Cursor / Other

Place in `~/.cursor/skills/seedance-skill/`, or inject `SKILL.md` as a system prompt, load `reference.md` on demand.

## Known Pitfalls (Must Read)

1. **Never use `…` (U+2026) in `ARK_API_KEY`** — HTTP headers require latin-1, triggers `UnicodeEncodeError`
2. **Don't pass `service_tier` for Seedance 2.0** — Errors with `must be empty`
3. **Don't combine `draft + flex`** — Errors with `draft task only support service_tier default`
4. **Draft forces 480p** — Passing 720p/1080p errors out

## Requirements

- Python 3.6+ (stdlib only, no third-party dependencies)
- [Volcengine Ark API Key](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey)

## License

MIT
