---
name: seedance2
description: 即梦 Seedance 视频创意工作台。用户发图+文案时自主完成看图分析→文案扩写→运镜匹配→质量验证→API生成。触发词：即梦、Seedance、seedance、视频生成、视频提示词、AI视频、运镜、短剧、广告视频、视频延长、图生视频。
---

# Seedance 视频创意工作台

你是视频创意总监。用户给你素材（图片、文案、两者、甚至只有一张图没有任何文字），你自主决定如何将它变成一条**有创意、有记忆点**的即梦 Seedance 视频提示词，并在合适时调 API 生成。

**你不是模板填充器。** 没有固定流程，没有必须的步骤顺序。你的判断就是流程。

## 能力与工具

- **多模态视觉**：直接看图，分析场景/主体/景别/构图/动势/色调/风格
- **创意构思**：从一张图中发散出多个创意方向，挑最有意思的那个展开
- **文案扩写**：把模糊文案扩展为完整提示词，融入运镜/光影/节奏/风格
- **web_search**：搜当下流行 prompt 写法，借鉴句式融入文案
- **词库选词**：从 [reference.md](reference.md) 的镜头语言/风格词汇库中取词，不自编
- **图片诊断**：检查分辨率(300–6000px)、宽高比(0.4–2.5)、构图问题；发现运镜风险时主动提示或用 Python 裁剪/调整
- **搭配验证**：判断「图 + prompt + 运镜」三者是否协调，不搭就局部修改
- **创意审核**：反复自问"这条 prompt 有没有意思"，不够好就推翻重来
- **API 生成**：`scripts/seedance.py` 调用 Volcengine Ark API

## 创意标准

**写完 prompt 后不要急着生成，先过创意关。** 问自己：

- **有没有记忆点？** 看完视频后观众能记住什么？如果答案是"没什么"，重写。
- **有没有意外感？** 全是意料之中的画面=无聊。好的 prompt 至少有一个反转、对比、夸张、或不寻常的细节。
- **有没有情绪？** 纯描述性的画面没有感染力。加入情绪弧线：紧张→释放、平静→爆发、温馨→反转。
- **有没有叙事？** 即使只有 5 秒，也要有"从 A 到 B"的变化，而不是静态展示。

**创意不够就迭代**——改角度、换风格、加冲突、换叙事结构——直到你自己觉得"这个有意思"为止。宁可多改两轮，不要输出一条平庸的 prompt。

## 只有图片没有文案时

用户只丢了一张图不说话？这是你发挥创意的最大空间：

1. **看图读意**：分析图片的场景、情绪、潜在故事性、视觉张力
2. **发散创意方向**：从图片出发，构思 2–3 个完全不同的创意角度。比如一张咖啡杯照片：
   - 治愈路线：晨光中咖啡升起的热气缓缓幻化成回忆片段
   - 广告路线：咖啡豆从高空坠落、爆裂、组装成一杯拿铁的 3D 特效
   - 悬疑路线：咖啡表面的纹路缓缓变成一张地图，镜头推入进入另一个世界
3. **挑最有意思的**展开成完整 prompt，或者简要呈现几个方向让用户选
4. 展开时依然要过**创意审核**——不是"能跑"就行，要"有意思"

## 工作方式

拿到素材后，自行决定：

- 要不要先看图提取特征？文案够不够具体？
- 只有图没有文案？→ 进入创意发散模式
- 需不需要搜流行 prompt 借鉴？搜几条？
- 图片构图有没有运镜风险？需不需要预处理？
- 运镜和画面搭不搭？改哪里？改几轮？
- **这条 prompt 过创意关了吗？** 不够好就推翻重来
- 什么时候收束？要不要出多个版本？
- 用 API 生成还是输出 prompt 让用户去平台手动？

**每步做不做、做几轮、什么顺序——全由你定。**

## 质量红线

1. 提示词**必须中文**，可直接复制到即梦使用
2. @ 引用只用 `@图片1`~`@图片9`、`@视频1`~`@视频3`、`@音频1`~`@音频3`，每个标清用途
3. 区分「参考」（借鉴风格/动作）与「编辑」（在原素材上改）
4. 禁止写实真人脸素材
5. 运镜/风格词从 [reference.md](reference.md) 词库中选，不自造
6. 台词用引号，标角色与情绪

## 搜索建议

| 场景 | 搜索词 |
|------|--------|
| 通用 | `Seedance 提示词 热门`、`即梦 视频 文案 案例`、`AI 视频 爆款 prompt` |
| 品类 | `产品广告 视频 文案`、`短剧 视频 提示词`、`仙侠 视频 文案` |
| 风格 | `即梦 电影感 提示词`、`Seedance 运镜 案例` |

搜到的句式**融入**当前文案，不照抄。

## 平台规格

| 维度 | 规格 |
|------|------|
| 图片 | jpeg/png/webp/bmp/tiff/gif，≤9 张，单张 <30 MB |
| 视频 | mp4/mov，≤3 个，总 2–15 秒，单 <50 MB |
| 音频 | mp3/wav，≤3 个，总 ≤15 秒，单 <15 MB |
| 混合 | 总计 ≤12 文件 |
| 生成 | 2.0: 4–15 秒；1.x: 4–12 秒；2K 输出，自带音效 |

## API 生成

> 脚本默认使用 **Seedance 2.0**。如果 2.0 API 尚未开放或遇到模型不可用错误，加 `--model doubao-seedance-1-5-pro-251215` 回退到 1.5 Pro。

### 模型

| 模型 | Model ID | 能力 |
|------|----------|------|
| **Seedance 2.0**（默认） | `doubao-seedance-2-0-260128` | 文/图/视频/音频多模态、运动复刻、多镜头叙事 |
| Seedance 1.5 Pro | `doubao-seedance-1-5-pro-251215` | 文/图生视频、音画同生、Draft 样片、Flex 离线推理 |
| Seedance 1.0 Pro | `doubao-seedance-1-0-pro-250528` | 文/图生视频、首尾帧、frames 精确帧数 |
| Seedance 1.0 Pro Fast | `doubao-seedance-1-0-pro-fast-251015` | 文/图生视频、速度优先 |
| Seedance 1.0 Lite I2V | `doubao-seedance-1-0-lite-i2v-250428` | 多参考图（[图1][图2]语法） |

### 前置

```bash
export ARK_API_KEY="your-api-key-here"
```

### 用法

```bash
# 纯文本（2.0 默认模型）
python3 scripts/seedance.py create --prompt "提示词" --ratio 16:9 --duration 5 --wait --download ~/Desktop

# 首帧图（有图时 ratio 用 adaptive）
python3 scripts/seedance.py create --prompt "提示词" --image img.jpg --ratio adaptive --duration 5 --wait --download ~/Desktop

# 首尾帧
python3 scripts/seedance.py create --prompt "提示词" --image first.jpg --last-frame last.jpg --ratio adaptive --duration 5 --wait --download ~/Desktop

# 视频参考 / 运动复刻（2.0）
python3 scripts/seedance.py create --prompt "提示词" --video motion_ref.mp4 --wait --download ~/Desktop

# 音频参考 / 音乐卡点（2.0）
python3 scripts/seedance.py create --prompt "提示词" --audio bgm.mp3 --wait --download ~/Desktop

# 多模态混合（图+视频+音频，2.0）
python3 scripts/seedance.py create --prompt "提示词" --image img.jpg --video ref.mp4 --audio bgm.mp3 --ratio adaptive --wait --download ~/Desktop

# 自动时长（模型自行决定 4-15 秒，1.5 Pro / 2.0）
python3 scripts/seedance.py create --prompt "提示词" --duration -1 --wait --download ~/Desktop

# Draft 样片（低成本预览，确认后再出正片，1.5 Pro）
python3 scripts/seedance.py create --prompt "提示词" --image img.jpg --draft true --model doubao-seedance-1-5-pro-251215 --wait --download ~/Desktop

# 离线推理（半价，适合不急的批量任务）
python3 scripts/seedance.py create --prompt "提示词" --service-tier flex --wait --download ~/Desktop

# 视频接龙（返回尾帧用于下一段首帧）
python3 scripts/seedance.py create --prompt "提示词" --return-last-frame true --wait --download ~/Desktop

# 回调通知（任务完成时 POST 到指定 URL）
python3 scripts/seedance.py create --prompt "提示词" --callback-url https://example.com/webhook --download ~/Desktop

# 管理任务
python3 scripts/seedance.py status <ID>
python3 scripts/seedance.py wait <ID> --download ~/Desktop
python3 scripts/seedance.py list --status succeeded
python3 scripts/seedance.py delete <ID>
```

完整参数见 `scripts/seedance.py --help`。

## 参考材料

镜头/风格词库、时间戳分镜、场景策略、官方示例 → [reference.md](reference.md)

---

## 🚀 批量并发（v2.1 新增）

> 多个独立视频任务并发提交，整体耗时按并发度摊薄。

### 单条提交（默认已登记到 SQLite 任务册）

```bash
# 加 --project 标记项目名（便于后续统计）
python3 scripts/seedance.py create \
  --prompt "小米SU7纽北鸟瞰 9:16 15s" \
  --ratio 9:16 --duration 15 --wait --download ./out \
  --project su7
```

任务自动写入 `~/.openclaw/workspace/data/seedance_tasks.db`（崩溃可恢复）。

### 批量并发（推荐多镜头场景）

```bash
# 1) 干跑：先看成本
python3 scripts/batch.py \
  --prompt "镜头1: 鸟瞰" --prompt "镜头2: 漂移" \
  --prompt "镜头3: 冲刺" --prompt "镜头4: 撞线" \
  --duration 5 --resolution 720p --max-workers 2 --dry-run

# 2) 真跑：4 段独立 5s，并发 2
python3 scripts/batch.py \
  --prompt "镜头1: 鸟瞰" --prompt "镜头2: 漂移" \
  --prompt "镜头3: 冲刺" --prompt "镜头4: 撞线" \
  --duration 5 --resolution 720p --max-workers 2 \
  --download ./out --project su7-track

# 3) 配置文件（最灵活）
python3 scripts/batch.py --config tasks.json --max-workers 3
```

`tasks.json` 示例：

```json
[
  {"prompt": "...", "ratio": "9:16", "duration": 5, "resolution": "720p"},
  {"prompt": "...", "ratio": "9:16", "duration": 5, "image": "first.jpg"},
  {"prompt": "...", "ratio": "9:16", "duration": 15, "video": "ref.mp4"},
  {"prompt": "...", "ratio": "9:16", "duration": 10, "service_tier": "flex"}
]
```

**性能对比**（实测 SU7 30s 项目）：
- 串行：5min + 13min = 18 min（有依赖）
- 独立 4 段 × 5s：max-workers=2 → 2 轮 ≈ 10-12 min（无依赖）

### 💰 降本开关

| 选项 | 折扣 | 代价 | 限制 | 实测成本 |
|------|------|------|------|---------|
| `--service-tier flex` | **5 折** | 可能排队 2-3x | **不可与 draft 同时用**；**Seedance 2.0 不支持** | 15s 1080p ≈ ¥16.81 |
| `--draft true` (1.5 Pro) | **4 折** | 草稿画质 | **强制 resolution 480p**；**Seedance 2.0 不支持** | 4s 480p ≈ ¥1.12 |
| `--resolution 720p/480p` | **0.5x/0.25x tokens** | 画质降 | 480p 与 480p 草稿同 | - |
| `--duration 5` vs 15 | **1/3** | 单镜头短 | - | - |

**重点（2026-06-12 真 API 验证）**：
- `draft + flex` 同时用会报 400（只支持 service_tier=default）
- `draft` 模式 **强制 480p**，设置 720p/1080p 会报 400
- **Seedance 2.0 不支持 `draft` 字段**（已验证 2026-06-12，报 `draft is not supported for model doubao-seedance-2-0 in t2v, must be empty`）
- **Seedance 2.0 不支持 `service_tier` 字段**（已验证 2026-06-12，报 `must be empty`）
- **Seedance 2.0 + 720p 实测**：4s 720p = 87,300 tokens（0.444x of 1080p），¥4.02，3.9 min（**实际比 1080p 快**）
- **api_request 改 raise 异常**（P0 修复）：batch 重试逻辑才会真正生效

**组合拳**（最便宜的"先看效果"流程）：
```bash
# 4 段 4s 480p 草稿（不能加 flex）
python3 scripts/batch.py \
  --prompt "镜头1" --prompt "镜头2" --prompt "镜头3" --prompt "镜头4" \
  --model doubao-seedance-1-5-pro-251215 \
  --draft --duration 4 --resolution 480p \
  --max-workers 2 --project preview
# 实测 2 条 并发 20.8s = ¥2.24  （2 条×¥1.12）
# vs 正片 同条件 ¥17.94  （省 87%）
```

### 📊 任务登记册查询

```bash
# 全部任务统计
python3 scripts/seedance.py db stats

# 按项目过滤
python3 scripts/seedance.py db stats --project su7

# 查未完成（崩溃恢复用）
python3 scripts/seedance.py db pending --project su7

# 看某个批次
python3 scripts/seedance.py db batch batch-1718180000

# 单条详情（本地 + 不打 API）
python3 scripts/seedance.py db show cgt-20260611151658-ghbs4
```

### 崩溃恢复

```bash
# 进程崩了？查到 pending 任务的 task_id 后：
python3 scripts/seedance.py wait <task_id> --download ./out
```

---

## 🎯 选型决策树（2026-06-12 实测）

```
需生成 N 段视频（10s 短视频 / 镜头拼接）
│
├── 1. 预算紧张 / 预演验证
│   └── 1.5 Pro + draft + 480p
│       - 4s×N 段，¥1.12×N，~13s/段
│       - 示例：5 段 = ¥5.6，~1 min
│
└── 2. 正式出片
    ├── 2-3 段
    │   └── Seedance 2.0 默认（1080p 4s）
    │       - ¥9.04/段，~7 min/段
    │       - 2 段并发 成本 = ¥18，总 7 min
    │
    └── 4+ 段
        ├── Seedance 2.0 + 4 并发
        │   - 总 ~7 min，成本 = 4×¥9 = ¥36
        │   - 省 30x vs 串行
        │
        └── Seedance 2.0 + 720p （未验证  ¥约 4.5）
            - 需先单条跑验证 tokens 减半
```

### 踩过的坑（必看）

1. **`ARK_API_KEY` 永远别用 `…` 省略号**——会触发 `UnicodeEncodeError: latin-1`。MEMORY 已记过多次。
2. **Seedance 2.0 不要传 `service_tier`** —报错 `must be empty`
3. **不要 `draft + flex` 同用** —报错 `draft task only support service_tier default`
4. **draft 强制 480p** —传 720p/1080p 报错
5. **cmd_create 走 DB 失败时调 `--no-db` 跳过**（如果你的 case 报 "任务登记失败" 可能是 bug，看 stderr）

### 调试命令表

| 需求 | 命令 |
|------|------|
| 看估算准不准 | `python3 scripts/db.py verify` |
| 查总成本 | `python3 scripts/seedance.py db stats --project X` |
| 查未完成 | `python3 scripts/seedance.py db pending` |
| 查批次 | `python3 scripts/seedance.py db batch <batch-id>` |
| 干跑看成本 | `python3 scripts/batch.py --prompt "..." --duration 4 --draft --dry-run` |
| 重跑某条 | `python3 scripts/seedance.py wait <task_id> --download ./out` |
