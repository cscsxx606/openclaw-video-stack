---
name: "video-pipeline-cn"
description: "中文视频流水线：文章/口播稿 → 30秒短视频全流程（改稿+分镜+提示词+视频生成+配音+字幕+BGM+合成）。一句话触发。"
---

# 🎬 视频流水线（中文）

> OpenClaw 原生视频生产工作流。基于 seedance-openclaw + Seedance2-skill + FFmpeg + TTS fallback。
>
> **v2.1 新增（2026-06-12）**：自动视频合成、TTS 自动 fallback、720p 降本自动推荐。

## ⚡ 一句话用法

```
把 ~/output/articles/claude-opus-4-7-解读.md 做成 30 秒短视频
```

或：

```
把这段话做成视频：[粘贴内容]
```

## 📋 工作流（8 步，全自动）

### Step 1 · 改稿（30 秒口播稿）
- 输入：原文（任意长度）
- 输出：`口播稿-30s.md`（约 145 字，28-32 秒）
- 模板：钩子（3s）→ 卖点 1（8s）→ 卖点 2（8s）→ 卖点 3（8s）→ CTA（3s）

### Step 2 · 分镜（5 镜头表）
- 输出：`分镜表.md`
- 含：时间、画面、动效、字幕要点、配乐节点

### Step 3 · Seedance 提示词
- 工具：调用 `seedance-openclaw` skill 的 `gen_prompt.py`
- 输出：`分镜-Seedance提示词.json`
- 适配：2 段 × 15 秒，9:16 竖版，2K

### Step 4 · 视频生成（Seedance API）
- 工具：`Seedance2-skill` 的 `batch.py` 并发提交
- **自动降本**：预算 < ¥20 自动选 720p（省 55%）
- 输出：2 段 15s MP4

### Step 5 · 配音（TTS 自动 fallback）
- 工具：`tts_fallback.py`
- 优先级：macOS say（免费）→ MiniMax TTS → 阿里云百炼 TTS → 静音占位
- 输出：`配音.mp3`

### Step 6 · BGM（FFmpeg 合成）
- 工具：FFmpeg lavfi 4 轨合成
- 输出：`BGM.mp3`

### Step 7 · 字幕（ASS 格式）
- 工具：自动生成 ASS 字幕
- 字体：Hiragino Sans GB（macOS）
- 输出：`字幕.ass`

### Step 8 · 合成最终视频
- 工具：FFmpeg 拼接 + 混音 + 字幕烧录
- 输出：`最终成片.mp4`（30s / 1080×1920 / 含字幕+配音+BGM）

## 🎯 适用场景

- 公众号 / 知乎文章 → 抖音 / 视频号 / 小红书短视频
- 行业资讯 → 30 秒快讯
- 教程类长文 → 系列短视频

## 🔗 依赖的 skills / 工具

| 名称 | 用途 | 状态 |
|------|------|------|
| `seedance-openclaw` | 生成 Seedance 提示词 | ✅ 已装 |
| `Seedance2-skill` | 即梦 API 集成 + 并发 + 任务登记册 | ✅ 已装 v2.1 |
| `tts_fallback.py` | 配音自动 fallback（macOS/MiniMax/阿里云） | ✅ 已装 |
| `resolution_advisor.py` | 720p 降本自动推荐 | ✅ 已装 |
| `siliconflow-image-gen` | 封面图（可选） | ✅ 已装 |

## 📂 输出目录

```
~/.openclaw/workspace/output/videos/<文章slug>/
├── 口播稿-30s.md              # 口播稿
├── 分镜表.md                  # 5 镜头表
├── 分镜-Seedance提示词.json   # 2 段提示词
├── 视频段1.mp4               # 第 1 段 15s
├── 视频段2.mp4               # 第 2 段 15s
├── 配音.mp3                  # TTS 配音
├── BGM.mp3                   # 背景音乐
├── 字幕.ass                  # ASS 字幕
└── 最终成片.mp4              # 30s 完整视频（含字幕+配音+BGM）
```

## 🚀 调用示例

### 示例 1：一键生成（完整流程）
```bash
# 从文章到视频（全自动）
python3 ~/.openclaw/workspace/skills/video-pipeline-cn/scripts/one_click_video.py \
    --article ~/output/articles/my-article.md \
    --budget 20 \
    --auto-resolution

# 输出：最终成片.mp4（30s / 720p / 含字幕+配音+BGM）
```

### 示例 2：已有口播稿，直接合成
```bash
# 已有口播稿 + 提示词，直接生成视频
python3 ~/.openclaw/workspace/skills/video-pipeline-cn/scripts/one_click_video.py \
    --project-dir ~/output/videos/my-video/ \
    --prompts ~/output/videos/my-video/分镜-Seedance提示词.json \
    --budget 20 \
    --auto-resolution
```

### 示例 3：仅合成（已有视频段）
```bash
# 跳过视频生成，直接合成配音+字幕+BGM
python3 ~/.openclaw/workspace/skills/video-pipeline-cn/scripts/one_click_video.py \
    --project-dir ~/output/videos/my-video/ \
    --skip-video-gen
```

### 示例 4：OpenClaw 对话触发
```
"把 output/articles/claude-opus-4-7-解读.md 做成 30 秒短视频"

# 执行步骤
1. 读取文章
2. 生成 口播稿-30s.md
3. 生成分镜表.md
4. 调用 seedance-openclaw 生成 Seedance 提示词
5. 调用 Seedance2-skill batch.py 并发生成 2 段视频
6. 调用 tts_fallback.py 生成配音
7. 调用 FFmpeg 生成 BGM
8. 生成 ASS 字幕
9. 合成最终成片.mp4
10. 输出完整文件到 output/videos/opus47/
```

## 📝 内容质量标准

- **口播稿**：口语化、有钩子、数据可视化、不超过 150 字
- **分镜表**：每镜头含具体画面/动效/字幕文字/音效
- **Seedance 提示词**：分段时间轴、镜头语言、配色锁定、避免侵权元素
- **可立即粘贴到即梦使用**（不需要二次加工）

## ⚠️ 注意事项

1. **TTS 自动 fallback**：macOS say 免费但音质一般；MiniMax/阿里云需要配置 API Key
2. **720p 降本**：预算 < ¥20 自动选 720p，省 55% 成本 + 4x 加速
3. **Seedance 不支持写实人脸**：所有镜头避开真人
4. **不能含 Logo/字幕/文字**：画面元素全部抽象化处理
5. **成本估算**：30s 1080p ≈ ¥67.26 / 30s 720p ≈ ¥16.06（实测）
6. **并发限制**：720p 支持 4 并发，1080p 建议 2 并发
7. **平台选择**：即梦（jimeng.jianying.com）或火山方舟 API

## 💰 成本参考（实测，2026-06-12）

| 配置 | 成本 | 耗时 | 适用场景 |
|------|------|------|----------|
| **1080p × 2 段串行** | **¥67.26** | ~14 min | 高质量最终成片 |
| **1080p × 2 段并发** | **¥67.26** | ~7 min | 质量优先，时间敏感 |
| **720p × 4 段并发** | **¥16.06** | ~4 min | **性价比最高** |
| **1.5P draft 480p** | **¥2.24** | ~30s | 草稿预演 |

> 推荐：草稿用 1.5P draft → 确认后用 720p 并发 → 最终用 1080p

## 🔄 后续可扩展（P2 已整合）

- ✅ **接入 videocut-skills → 自动后处理**（剪口播 + 高清化 + 字幕）
- 接入 `video-use` skill → 专业视频编辑
- 接入 `hf-hyperframes` → 加片头片尾动画
- 接入 `hf-remotion-to-hyperframes` → 批量栏目化
- **接入 `social-auto-upload` → 多平台分发（抖音/快手/视频号/小红书）** ⬅️ 2026-06-11 已规划

---

## 🎬 P2 视频后处理（videocut-skills 整合）

> 2026-06-12 新增：一键调用 videocut-skills 的剪口播、高清化、导入字幕能力

### 功能

| 功能 | 脚本 | 说明 |
|------|------|------|
| **剪口播** | `post_process.py --mode cut` | 口误识别 + 自动剪辑 |
| **高清化** | `post_process.py --mode hd` | 2-pass 编码 + 锐化 |
| **导入字幕** | `post_process.py --mode subtitle` | 剪映草稿生成 |
| **全部** | `post_process.py --mode all` | 剪口播 → 高清化 → 字幕 |

### 用法

```bash
# 全部后处理（剪口播 → 高清化 → 字幕）
python3 ~/.openclaw/workspace/skills/video-pipeline-cn/scripts/post_process.py \
    --video ~/output/videos/my-video/最终成片.mp4 \
    --mode all \
    --auto-confirm

# 仅剪口播
python3 scripts/post_process.py --video final.mp4 --mode cut

# 仅高清化（1.5x 码率）
python3 scripts/post_process.py --video final.mp4 --mode hd --bitrate-multiplier 1.5

# 仅字幕（带花字）
python3 scripts/post_process.py --video final.mp4 --mode subtitle \
    --effect 火焰燃烧花字 --anim 渐显
```

### 依赖

| 工具 | 路径 | 状态 |
|------|------|------|
| `cut_video.sh` | `videocut-skills/剪口播/scripts/` | ✅ 已装 |
| `hd_export.sh` | `videocut-skills/高清化/scripts/` | ✅ 已装 |
| `srt_to_draft.py` | `videocut-skills/导入字幕/scripts/` | ✅ 已装 |
| `VOLCENGINE_API_KEY` | `.env` 文件 | ⚠️ 需配置 |

### 注意事项

1. **剪口播需要火山引擎 API Key**：在 `.env` 填入 `VOLCENGINE_API_KEY=xxx`
2. **首次字幕需要 capcut-mate 服务**：`srt_to_draft.py` 会自动检测安装
3. **高清化可选**：剪辑后画质已很好，高清化是额外增强
4. **人工审核**：默认生成审核网页，加 `--auto-confirm` 跳过

### 输出

```
post/
├── 剪口播_最终成片/
│   ├── 1_转录/
│   │   ├── audio.mp3
│   │   └── subtitles_words.json
│   ├── 2_分析/
│   │   └── auto_selected.json
│   └── 3_审核/
│       ├── review.html
│       └── 最终成片_cut.mp4
├── 最终成片_hd.mp4          # 高清化后
└── video.srt                # 字幕文件
```

---

## 📤 多平台分发（规划中）

> 目标：视频成片后一键分发到抖音/快手/视频号/小红书

### 技术方案
- 工具：`social-auto-upload` (GitHub 10.9k+ star，Playwright 浏览器自动化)
- 支持：个人号扫码登录，Cookie 复用

### 平台支持
| 平台 | 个人号 | 方式 | 状态 |
|------|--------|------|------|
| 抖音 | ✅ | 创作者服务中心网页版 | 待集成 |
| 快手 | ✅ | 网页版上传 | 待集成 |
| 视频号 | ✅ | 视频号助手网页版 | 待集成 |
| 小红书 | ✅ | 创作中心网页版 | 待集成 |
| B站 | ✅ | 已接入 CLI | 待集成 |

### 使用方式（预计）
```bash
# 生成视频 + 自动分发
"把这篇文章做成视频并分发到抖音快手"

# 仅分发已有视频
"把 output/videos/xxx/final.mp4 分发到全平台"
```

### 待办
- [ ] 集成 social-auto-upload 依赖
- [ ] 封装 `publish` 命令
- [ ] 多平台元数据配置（标题/标签/话题差异化）
- [ ] 登录状态管理（Cookie 复用）
- [ ] 风控规避（上传间隔、失败重试）
- [ ] 日志记录（发布链接、状态）

### 注意事项
1. 个人号**无官方 API**，只能走浏览器自动化
2. 首次需手动扫码登录，后续 Cookie 复用
3. 平台网页结构更新可能导致脚本失效
4. 建议控制发布频率，避免触发风控
