# Seedance2-skill

**[English](README_EN.md)** | 中文

ByteDance Seedance AI 视频创意工作台 + **生产级批量并发工具** — 让 AI Agent 变身视频创意总监，并能在生产环境里跑多镜头流水线。

> 不是提示词模板，是一套有审美门槛的创意系统。
> **v2.1 新增**（2026-06-12）：SQLite 任务登记册、并发批量提交、降本开关组合拳。

## 核心特性

- 🎬 **自主创意总监** — Agent 自行决定分析顺序、迭代轮数、输出方式（不是固定流程）
- 🎯 **创意审核机制** — 每条 prompt 必须过四关：记忆点、意外感、情绪弧线、叙事变化
- 📚 **完整词库** — 镜头语言 12 类 100+ 词条、导演风格速查 10 位、动漫作画术语 9 项
- 🎥 **Seedance 2.0 全模态** — 文本 / 图片 / 视频 / 音频输入，运动复刻、音乐卡点、多镜头叙事
- ⚡ **批量并发**（v2.1）— 多镜头场景下并发提交，max-workers 2-4 加速 1.6-2x
- 📊 **任务登记册**（v2.1）— SQLite WAL 模式，崩溃可恢复，13 条任务估算误差 0.003%
- 💰 **降本开关**（v2.1）— `--draft` / `--service-tier flex` / `720p` 组合省 50-80%

## 项目结构

```
Seedance2-skill/
├── SKILL.md          # 技能主文档 · 中文（Agent 读取入口）
├── SKILL_EN.md       # 技能主文档 · English
├── reference.md      # 词库、技巧、官方示例
├── scripts/
│   ├── seedance.py   # Volcengine Ark API CLI（单条生成 + 任务查询）
│   ├── batch.py      # v2.1 批量并发提交（max-workers 2-4）
│   └── db.py         # v2.1 SQLite 任务登记册（stats/verify/pending）
├── README.md         # 本文件（中文）
└── README_EN.md      # English README
```

## 快速开始

### 1. 安装

将本仓库克隆到你的 Agent 技能目录：

```bash
git clone https://github.com/cscsxx606/openclaw-video-stack.git
# 或单独使用
git clone https://github.com/zhanghaonan777/Seedance2-skill.git
```

### 2. 设置 API Key

```bash
export ARK_API_KEY="your-volcengine-ark-api-key"
```

在 [火山引擎控制台](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey) 获取 API Key。

### 3. 三种使用场景

#### A. 单条生成（v1.0 起就有）

```bash
# 文本生成视频
python3 scripts/seedance.py create --prompt "镜头跟随黑衣男子快速逃亡" --ratio 16:9 --duration 5 --wait --download ~/Desktop

# 图片生成视频
python3 scripts/seedance.py create --prompt "画面中的人物缓缓转身" --image photo.jpg --ratio adaptive --wait --download ~/Desktop

# 视频参考 + 运动复刻（Seedance 2.0）
python3 scripts/seedance.py create --prompt "参考视频的运镜和节奏" --video reference.mp4 --wait --download ~/Desktop
```

#### B. 批量并发生成（v2.1 推荐 — 多镜头场景）

```bash
# 4 段 480p 草稿并发预演 = ¥4.48，~30s 完成
python3 scripts/batch.py \
  --prompt "镜头1：城市俯瞰" \
  --prompt "镜头2：人物特写" \
  --prompt "镜头3：街道跟随" \
  --prompt "镜头4：日落全景" \
  --duration 4 --resolution 480p --draft --max-workers 4 \
  --project my-video --download ./out

# 先干跑看成本（不下发）
python3 scripts/batch.py --prompt "s1" --duration 5 --resolution 720p --dry-run
```

#### C. 任务持久化 + 崩溃恢复（v2.1）

```bash
# 创建任务（不等待，后台跑）
python3 scripts/seedance.py create --prompt "..." --project su7

# 进程崩了？查未完成列表
python3 scripts/seedance.py db pending --project su7

# 重连等任务完成
python3 scripts/seedance.py wait cgt-20260612093622-zwxq2 --download ./out
```

## 💰 降本开关组合拳（v2.1 实测）

| 开关 | 节省 | 限制 | 实测场景 |
|------|------|------|---------|
| `--draft`（1.5 Pro）| 5 折 | 强制 480p；不能与 flex 同用 | 4s 480p = **¥1.12/条** |
| `--service-tier flex` | 5 折 | Seedance 2.0 不支持 | 5s 1080p = ¥2.37/条 |
| `--resolution 720p` | tokens 减半 | 理论值未实测 | 预估 ¥4.5/条 |
| **组合：草稿 + 5s × 5 段** | **-80%** | vs 15s 正片 | **¥4.74/批** vs ¥23.68/批 |

### 生产推荐

1. **预演** → 1.5P + draft + 480p（¥1.12/13s/段）做 4-8 段分镜验证
2. **正片** → Seedance 2.0（¥9.04/7min/段）并发 4 段，总 ~7 min
3. **省钱** → Seedance 2.0 + 720p（预估 ¥4.5/段），先单条跑验证

## 📊 任务登记册（v2.1）

所有任务默认写入 SQLite：`~/.openclaw/workspace/data/seedance_tasks.db`

```bash
# 全部任务成本统计
python3 scripts/seedance.py db stats
# 输出：succeeded count=13 est=¥239.22 actual=¥239.28

# 按项目过滤
python3 scripts/seedance.py db stats --project su7

# 估算精度自动验证（5/5 个参考点）
python3 scripts/db.py verify

# 查未完成（崩溃恢复用）
python3 scripts/seedance.py db pending --project su7

# 看某个批次
python3 scripts/seedance.py db batch batch-1781229824
```

## 支持的模型

| 模型 | Model ID | 能力 |
|------|----------|------|
| **Seedance 2.0**（默认）| `doubao-seedance-2-0-260128` | 文/图/视频/音频多模态、运动复刻、多镜头叙事 |
| Seedance 1.5 Pro | `doubao-seedance-1-5-pro-251215` | 文/图生视频、音画同生、**Draft 样片**、**Flex 离线推理** |
| Seedance 1.0 Pro | `doubao-seedance-1-0-pro-250528` | 文/图生视频、首尾帧、精确帧数控制 |
| Seedance 1.0 Pro Fast | `doubao-seedance-1-0-pro-fast-251015` | 文/图生视频、速度优先 |
| Seedance 1.0 Lite I2V | `doubao-seedance-1-0-lite-i2v-250428` | 多参考图（[图1][图2]语法）|

## CLI 参数速查

### `seedance.py create`（单条）

| 参数 | 说明 |
|------|------|
| `--prompt` | 视频描述提示词 |
| `--image` / `--last-frame` / `--ref-images` | 首帧 / 尾帧 / 参考图（1-9 张）|
| `--video` | 参考视频（1-3 个，Seedance 2.0）|
| `--audio` | 参考音频（1-3 个，Seedance 2.0）|
| `--model` | 模型 ID（默认 Seedance 2.0）|
| `--ratio` | 宽高比：16:9 / 4:3 / 1:1 / 3:4 / 9:16 / 21:9 / adaptive |
| `--duration` | 时长（秒），-1 为自动 |
| `--resolution` | 480p / 720p / 1080p |
| `--draft` | 样片模式（1.5 Pro only）|
| `--service-tier` | `default` 或 `flex`（离线半价，**Seedance 2.0 不支持**）|
| `--generate-audio` | 是否生成音频 |
| `--return-last-frame` | 返回尾帧（用于视频接龙）|
| `--callback-url` | Webhook 回调地址 |
| `--wait` | 等待任务完成 |
| `--download` | 下载目录 |
| **`--project`** (v2.1) | 任务分组标签（用于 `db stats --project`）|
| **`--max-wait`** (v2.1) | `wait` 子命令超时（默认 1800s）|
| **`--no-db`** (v2.1) | 跳过 SQLite 登记 |

### `batch.py`（v2.1 新增）

```bash
# 多 --prompt 内联 或 --config tasks.json
python3 scripts/batch.py \
  --prompt "s1" --prompt "s2" --prompt "s3" \
  --duration 4 --resolution 480p --draft \
  --max-workers 2 --service-tier flex \
  --project batch1 --download ./out \
  [--dry-run]
```

| 参数 | 说明 |
|------|------|
| `--prompt` | 多段提示词（可重复 N 次）|
| `--config` | JSON 配置文件路径（多任务更整洁）|
| `--max-workers` | 并发度（2-4 甜区，1.6-2x 加速）|
| `--service-tier` | `default` 或 `flex` |
| `--draft` | 样片模式 |
| `--resolution` / `--ratio` | 分辨率 / 宽高比 |
| `--duration` | 时长 |
| `--dry-run` | 只看成本估算，不下发 |
| `--project` | 任务分组 |
| `--download` | 视频下载目录 |

## 🎯 创意系统

这个 Skill 的核心不是 API 调用，而是**创意审核机制**：

1. **记忆点** — 观众看完能记住什么？
2. **意外感** — 是否有反转、对比、夸张？
3. **情绪** — 有没有情绪弧线？
4. **叙事** — 哪怕 5 秒也要有变化

Agent 会反复自检 prompt 质量，不够好就推翻重来，直到"有意思"为止。

## 接入 AI Agent

本技能兼容任何支持 Skill / Tool 加载的 AI Agent 平台。中文环境使用 `SKILL.md`，英文环境使用 `SKILL_EN.md`。

### OpenClaw

将本目录放入 OpenClaw 的 skills 目录（如 `~/.openclaw/workspace/skills/Seedance2-skill/`），Agent 会在用户提到「即梦」「Seedance」「视频生成」等关键词时自动加载。

### Cursor / 其他

将本目录放入 `~/.cursor/skills/seedance-skill/`，或把 `SKILL.md` 作为 system prompt 注入，`reference.md` 按需加载。

## 踩过的坑（必看）

1. **`ARK_API_KEY` 永远别用 `…` 省略号** — HTTP header 强制 latin-1，会触发 `UnicodeEncodeError`
2. **Seedance 2.0 不要传 `service_tier`** — 报错 `must be empty`
3. **不要 `draft + flex` 同用** — 报错 `draft task only support service_tier default`
4. **draft 强制 480p** — 传 720p/1080p 报错

## 依赖

- Python 3.6+（仅标准库，无第三方依赖）
- [火山引擎 Ark API Key](https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey)

## 许可

MIT
