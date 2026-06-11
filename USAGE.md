# 📖 详细使用指南

## 🎬 三种使用方式

### 方式 1：自然语言（最简单）

在 OpenClaw 对话中直接说：

```
帮我做一个 30 秒短视频，主题是"小米 SU7 Ultra 纽北跑进 7 分"
```

OpenClaw 会自动：
1. 生成 150 字口播稿
2. 生成 5 镜头分镜表
3. 生成 Seedance 提示词
4. 调用 Seedance API 生成视频
5. FFmpeg 拼接 + 字幕烧录
6. 配音 + BGM + 最终合成

输出：`~/.openclaw/workspace/output/videos/<项目名>/su7-final.mp4`

### 方式 2：指定输入文件

把已有文章转视频：

```
把 ~/.openclaw/workspace/output/articles/claude-opus-4-7-解读.md 做成 30 秒短视频
```

### 方式 3：使用脚本

```bash
# 一键生成
./scripts/one-click-generate.sh "小米 SU7 Ultra 纽北跑进 7 分"

# 指定输出目录
./scripts/one-click-generate.sh "..." -o /path/to/output

# 批量生成
./scripts/batch-generate.sh topics.txt
```

## 🎯 项目结构

每次生成会在 `~/.openclaw/workspace/output/videos/<项目名>/` 下创建：

```
<项目名>/
├── 口播稿-30s.md          # 4 段口播稿（约 150 字）
├── 分镜-Seedance提示词.md  # 2 段 Seedance 提示词
├── 分镜表.md              # 5 镜头详细分镜（可选）
├── segment1.mp4           # 第 1 段视频（Seedance 生成）
├── segment2.mp4           # 第 2 段视频（Seedance 生成）
├── final-raw.mp4          # 拼接原始版
├── final.mp4              # 重新编码版（含字幕）
├── 配音.mp3               # 配音
├── bgm/bgm.mp3            # 背景音乐
├── 字幕.ass               # 字幕源文件
└── README.md              # 项目说明
```

## 🛠️ 高级选项

### 自定义时长

默认 30 秒（2 段 × 15 秒）。修改 `skills/video-pipeline-cn/SKILL.md`：

```yaml
# 15 秒短视频（1 段）
duration: 15
segments: 1

# 60 秒长视频（4 段）
duration: 60
segments: 4
```

### 自定义配音

默认用 `macOS say "Eddy 中文"`。换 ElevenLabs：

```python
# 修改 skills/video-pipeline-cn/scripts/tts.py
from elevenlabs import generate, save

audio = generate(
    text=script,
    voice="<your-voice-id>",
    model="eleven_multilingual_v2"
)
save(audio, "配音.mp3")
```

### 自定义 BGM

下载免费 BGM 放到 `~/.openclaw/workspace/assets/bgm/`，然后：

```bash
# 修改 skills/video-pipeline-cn/scripts/mix_audio.py
BGM_FILE = "~/.openclaw/workspace/assets/bgm/your-track.mp3"
```

### 自定义字幕样式

编辑 `字幕.ass` 文件中的 `[V4+ Styles]`：

```ass
Style: Default,字体名,字号,颜色,边框,描边,阴影,位置
```

常用样式：
- 白色粗体 + 黑色描边（最常见）
- 黄色高亮 + 阴影
- 黑底白字（高对比）

## 📊 性能参考

| 步骤 | 耗时 | 成本 |
|------|------|------|
| 改稿 + 分镜 + 提示词 | < 15s | ¥0 |
| Seedance 段 1（文生） | 5-15 min | ¥0.018 |
| Seedance 段 2（参考延长） | 10-20 min | ¥0.025 |
| FFmpeg 拼接 | < 5s | ¥0 |
| 字幕烧录 | < 30s | ¥0 |
| 配音（macOS say） | < 5s | ¥0 |
| BGM 合成 | < 10s | ¥0 |
| 音视频合并 | < 5s | ¥0 |
| **总计** | **~15-35 分钟** | **~¥0.04** |

## 🔁 批量生成

把多个主题写到一个文件（每行一个）：

```bash
# topics.txt
小米 SU7 Ultra 纽北跑进 7 分
Claude Opus 4.7 发布
DeepSeek V4 + 像素灵境
```

然后运行：

```bash
./scripts/batch-generate.sh topics.txt
```

## 🎨 创意技巧

### 1. 多角度 Seedance 提示词

不要只用一段 prompt 描述所有镜头。给每段独立的 prompt，**Seedance 会自动保持风格一致**（同 model + 同 ratio + 同 color palette）。

### 2. 参考视频延长 vs 文生视频

- **文生视频**：开篇、抽象场景、运镜独特
- **参考视频延长**：细节、产品展示、人物动作

### 3. ASS 字幕的 5 个关键参数

```ass
FontSize=42           # 字号（屏幕高度 1920 时 42 = 适中）
PrimaryColour=FFFFFF  # 文字色（白）
OutlineColour=000000  # 描边色（黑）
Outline=4             # 描边粗细
Alignment=2           # 底部居中
```

### 4. FFmpeg 烧录字幕的 3 个坑

1. **字体**：用 `Hiragino Sans GB`（macOS）或 `Noto Sans CJK SC`（Linux）
2. **PlayResY**：在 .ass 里**必须**设为视频高度
3. **换行**：用 `\N`（不是 `\n`）

## 🚨 注意事项

### 1. 品牌安全

Seedance **不支持含写实真人脸部的素材**。所有镜头避开真人。

### 2. Logo 处理

所有 App/品牌 Logo 抽象化（几何符号），避免侵权。

### 3. 时长限制

Seedance 2.0 单次生成最长 15 秒。30 秒视频需要分 2 段。

### 4. 视频 URL 有效期

Seedance 返回的视频 URL 24 小时有效。下载到本地后无此限制。

### 5. API 限流

火山方舟有 QPS 限制。批量生成时建议加 `sleep 5` 避免触发限流。

## 🐛 故障排查

参见 [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)。
