---
name: "video-pipeline-cn"
description: "中文视频流水线：文章/口播稿 → 30秒短视频全流程（改稿+分镜+提示词+配音+字幕）。一句话触发。"
---

# 🎬 视频流水线（中文）

> OpenClaw 原生视频生产工作流。基于 seedance-openclaw + Seedance2-skill + 已有 tts 工具。

## ⚡ 一句话用法

```
把 ~/output/articles/claude-opus-4-7-解读.md 做成 30 秒短视频
```

或：

```
把这段话做成视频：[粘贴内容]
```

## 📋 工作流（4 步）

### Step 1 · 改稿（30 秒口播稿）
- 输入：原文（任意长度）
- 输出：`口播稿-30s.md`（约 145 字，28-32 秒）
- 模板：钩子（3s）→ 卖点 1（8s）→ 卖点 2（8s）→ 卖点 3（8s）→ CTA（3s）

### Step 2 · 分镜（5 镜头表）
- 输出：`分镜表.md`
- 含：时间、画面、动效、字幕要点、配乐节点

### Step 3 · Seedance 提示词（直接粘贴即梦）
- 工具：调用 `seedance-openclaw` skill 的 `gen_prompt.py`
- 输出：`分镜-Seedance提示词.md`
- 适配：2 段 × 15 秒，9:16 竖版，2K

### Step 4 · 配音 + 字幕指引
- 工具：尝试 `tts`，失败则用 ElevenLabs / 剪映自带
- 输出：`配音说明.md`
- 字幕：基于分镜表自动生成时间轴

## 🎯 适用场景

- 公众号 / 知乎文章 → 抖音 / 视频号 / 小红书短视频
- 行业资讯 → 30 秒快讯
- 教程类长文 → 系列短视频

## 🔗 依赖的 skills / 工具

| 名称 | 用途 | 状态 |
|------|------|------|
| `seedance-openclaw` | 生成 Seedance 提示词 | ✅ 已装 |
| `Seedance2-skill` | 即梦 API 集成 | ✅ 已装 |
| `tts` | 中文配音 | ⚠️ 未配置 provider |
| `siliconflow-image-gen` | 封面图（可选） | ✅ 已装 |

## 📂 输出目录

```
~/.openclaw/workspace/output/videos/<文章slug>/
├── 口播稿-30s.md
├── 分镜表.md
├── 分镜-Seedance提示词.md
├── 配音.mp3  （如有 tts provider）
└── 视频.mp4  （合成后）
```

## 🚀 调用示例

### 示例 1：把现有文章做成视频
```bash
# 用户输入
"把 output/articles/claude-opus-4-7-解读.md 做成 30 秒短视频"

# 执行步骤
1. 读取文章
2. 生成 口播稿-30s.md
3. 生成分镜表.md
4. 调用 seedance-openclaw 生成 Seedance 提示词
5. 输出完整文件到 output/videos/opus47/
```

### 示例 2：粘贴原文直接做
```bash
# 用户输入
"把这段话做成视频：Anthropic 发布 Claude Opus 4.7..."

# 自动从输入中提取主题 + 生成 4 个文件
```

## 📝 内容质量标准

- **口播稿**：口语化、有钩子、数据可视化、不超过 150 字
- **分镜表**：每镜头含具体画面/动效/字幕文字/音效
- **Seedance 提示词**：分段时间轴、镜头语言、配色锁定、避免侵权元素
- **可立即粘贴到即梦使用**（不需要二次加工）

## ⚠️ 注意事项

1. **TTS 未配置**：配音需要用户用其他工具（剪映/配音神器）
2. **Seedance 不支持写实人脸**：所有镜头避开真人
3. **不能含 Logo/字幕/文字**：画面元素全部抽象化处理
4. **平台选择**：即梦（jimeng.jianying.com）或火山方舟 API

## 🔄 后续可扩展

- 接入 `video-use` skill → 自动剪辑成片
- 接入 `videocut-剪口播` → 优化口播节奏
- 接入 `hf-hyperframes` → 加片头片尾动画
- 接入 `hf-remotion-to-hyperframes` → 批量栏目化
