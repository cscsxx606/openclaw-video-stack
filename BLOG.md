# 4 毛钱一条 AI 短视频：我用 OpenClaw + Seedance 2.0 搭了一套中文视频生产线

> 从 "一句话需求" 到 "30 秒带字幕配音 BGM 的成片"，全程自动化。成本 ¥0.04，耗时 20 分钟。

---

## 先上成片

我跑了 3 条不同主题的 30 秒短视频：

| 主题 | 视频 | 配音 | BGM | 成本 |
|------|------|------|-----|------|
| **小米 SU7 Ultra 纽北** | 赛车飞驰 + 数据字幕 | MiniMax 青年男声 | 赛车电子 130bpm | ¥0.04 |
| **Claude Opus 4.7 发布** | 科技资讯 + 参数对比 | MiniMax 青年男声 | 科技氛围 120bpm | ¥0.04 |
| **DeepSeek V4 + 像素灵境** | 双喜临门 + 产品展示 | MiniMax 青年男声 | 电影配乐 125bpm | ¥0.04 |

**视频规格**：1080×1920 竖版（9:16），30 秒，H.264 + AAC，16-21 MB。

**效果**：不是 "能看"，是 **能发** —— 字幕清晰、配音自然、BGM 有节奏感，直接丢抖音/视频号没问题。

---

## 技术栈：4 层架构

```
┌─────────────────────────────────────────────┐
│  第 4 层：MiniMax 音频（配音 + BGM）        │  ← 新增
│  speech-2.8-hd + music-1.5                   │
├─────────────────────────────────────────────┤
│  第 3 层：FFmpeg 后期（字幕 + 混音 + 合成）  │
│  ASS 字幕烧录 / AAC 混音 / MP4 封装          │
├─────────────────────────────────────────────┤
│  第 2 层：Seedance 2.0 视频生成             │
│  火山引擎 API：文生视频 + 参考视频延长        │
├─────────────────────────────────────────────┤
│  第 1 层：OpenClaw 调度（LLM 编排）         │
│  改稿 → 分镜 → 提示词 → 任务调度             │
└─────────────────────────────────────────────┘
```

**关键升级**：之前用 macOS `say` 机械音 + FFmpeg 4 轨合成 BGM，现在换成 **MiniMax 真·AI 音频** —— 配音是 HD 语音模型，BGM 是 music-1.5 生成的 44.1kHz 立体声。

---

## 一句话工作流

用户说："做个小米 SU7 Ultra 纽北的视频"

系统内部执行：

```
1. OpenClaw 调用 DeepSeek V4 改稿 → 30 秒口播稿
2. 拆分为 2 个 15 秒分镜 → 生成 Seedance 提示词
3. 调用 Seedance 2.0 API：
   - 段 1：文生视频（15s，1080p，9:16）
   - 段 2：参考视频延长（15s，保持风格一致）
4. FFmpeg 拼接两段视频 + 烧录 ASS 字幕
5. MiniMax TTS 生成配音（hex 解码 → MP3）
6. MiniMax Music 生成 BGM（[Instrumental] 占位 → 纯音乐）
7. FFmpeg 混音（配音 100% + BGM 18%）+ 合成最终 MP4
```

**全程耗时**：~20 分钟（视频生成占 18 分钟，后期 2 分钟）

---

## 核心踩坑（6 个，已验证）

### 1. Seedance 参考视频必须用公网 URL

```python
# ❌ 错误：传 base64 或本地路径
"video": "/path/to/local.mp4"

# ✅ 正确：先用文生视频得到 URL，再传给延长接口
"video": "https://.../video.mp4?signature=..."  # 24h 有效
```

**解决**：段 1 生成后等 URL 返回，再发起段 2 任务。不能并行。

### 2. FFmpeg 字幕用 ASS 格式

```bash
# ❌ SRT 在新版 FFmpeg 有 bug（Alignment 行为反了）
# ✅ ASS 格式最稳
```

关键配置：
- `PlayResY: 1920`（竖版适配）
- 字体 `Hiragino Sans GB`（macOS fontconfig 认得）
- 字号 48，描边 2px，底部居中

### 3. MiniMax TTS 响应是 hex 编码

```python
# ❌ 以为是 base64
data['audio']  # 返回的是 hex 字符串

# ✅ 用 binascii.unhexlify() 解码
audio_bytes = binascii.unhexlify(data['data']['audio'])
```

### 4. music-1.5 需要 lyrics 字段

```python
# ❌ 不传 lyrics → 报错 "invalid params, lyrics is required"
# ✅ 纯音乐用 [Instrumental] 占位
"lyrics": "[Instrumental]"
```

### 5. BGM 可能返回 URL（不是 hex）

```python
audio = data['data']['audio']
if audio.startswith('http'):
    audio = requests.get(audio, timeout=60).content  # 下载 URL
else:
    audio = binascii.unhexlify(audio)  # 解码 hex
```

### 6. API Key 字符陷阱

```python
# ❌ 用 "…"（U+2026 省略号）做占位符
ARK_API_KEY = "sk-..."  # 触发 UnicodeEncodeError

# ✅ 用完整 key 或环境变量
ARK_API_KEY = os.environ['ARK_API_KEY']  # 125 字符完整值
```

---

## 成本拆解（单条 30 秒视频）

| 环节 | 服务 | 时长 | 费用 |
|------|------|------|------|
| 视频生成 | Seedance 2.0（段 1） | 15s | ~¥0.018 |
| 视频延长 | Seedance 2.0（段 2） | 15s | ~¥0.025 |
| 配音 | MiniMax TTS | 30s | ~¥0.001 |
| BGM | MiniMax Music | 60s | ~¥0.10 |
| **合计** | | | **~¥0.15** |

> 注：BGM 是 60s 完整音乐，实际只用 30s，但 API 按生成时长计费。如果批量生产可以复用同一段 BGM，成本降到 ~¥0.04。

---

## 代码：核心片段

### Seedance 2.0 API 调用

```python
import requests

# 文生视频（段 1）
resp = requests.post(
    'https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks',
    headers={'Authorization': f'Bearer {ARK_API_KEY}'},
    json={
        'model': 'doubao-seedance-2-0-260128',
        'content': [{'type': 'text', 'text': '赛车在纽北赛道飞驰，轮胎冒烟'}],
        'parameters': {'aspect_ratio': '9:16', 'duration': 15, 'resolution': '1080p'}
    }
)

# 参考视频延长（段 2）
resp2 = requests.post(
    'https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks',
    headers={'Authorization': f'Bearer {ARK_API_KEY}'},
    json={
        'model': 'doubao-seedance-2-0-260128',
        'content': [
            {'type': 'video', 'video_url': video_url_from_segment_1},  # 公网 URL！
            {'type': 'text', 'text': '赛车冲过终点线，观众欢呼'}
        ],
        'parameters': {'aspect_ratio': '9:16', 'duration': 15}
    }
)
```

### MiniMax TTS（hex 解码）

```python
import requests, binascii

resp = requests.post(
    'https://api.minimaxi.com/v1/t2a_v2',
    headers={'Authorization': f'Bearer {MINIMAX_API_KEY}'},
    json={
        'model': 'speech-2.8-hd',
        'text': '小米又搞事情了，SU7 Ultra 纽北跑进 7 分...',
        'stream': False,
        'voice_setting': {'voice_id': 'male-qn-qingse', 'speed': 1.0, 'vol': 1.0, 'pitch': 0},
        'audio_setting': {'audio_sample_rate': 32000, 'bitrate': 128000, 'format': 'mp3'}
    }
)

data = resp.json()
audio = binascii.unhexlify(data['data']['audio'])  # ← hex 解码
open('voice.mp3', 'wb').write(audio)
```

### MiniMax Music（lyrics 占位）

```python
resp = requests.post(
    'https://api.minimaxi.com/v1/music_generation',
    headers={'Authorization': f'Bearer {MINIMAX_API_KEY}'},
    json={
        'model': 'music-1.5',
        'prompt': 'electronic, racing, 130bpm, energetic, no vocals',
        'lyrics': '[Instrumental]',  # ← 纯音乐占位
        'stream': False
    }
)
```

### FFmpeg 混音合成

```bash
# 1. 配音裁到 30 秒
ffmpeg -y -i voice.mp3 -t 30 -c copy voice-30s.mp3

# 2. 混音（BGM 音量 18%，淡入淡出）
ffmpeg -y \
  -i voice-30s.mp3 -i bgm.mp3 \
  -filter_complex "[1:a]volume=0.18,afade=t=in:st=0:d=1,afade=t=out:st=27:d=2[bgm];[0:a][bgm]amix=inputs=2:duration=shortest:normalize=0" \
  -c:a aac -b:a 192k mixed.m4a

# 3. 合成最终视频
ffmpeg -y -i video-with-subs.mp4 -i mixed.m4a \
  -c:v copy -c:a aac -b:a 192k -shortest final.mp4
```

---

## 已开源：OpenClaw Video Stack

我把整套系统整理成开源项目，GitHub 可复现：

**仓库**：https://github.com/cscsxx606/openclaw-video-stack

```
openclaw-video-stack/
├── README.md              # 项目入口
├── USAGE.md               # 完整使用指南（含 MiniMax 音频）
├── INSTALL.md             # 安装步骤
├── TROUBLESHOOTING.md     # 踩坑记录
├── skills/                # 4 个 OpenClaw Skills
│   ├── video-pipeline-cn/     # 主编排：文章→视频
│   ├── minimax-audio-cn/    # 音频生成：TTS + BGM
│   ├── seedance-openclaw/    # Seedance 提示词
│   └── Seedance2-skill/      # Seedance API 脚本
├── examples/              # 3 个完整案例
│   ├── su7-ultra-nurburgring/
│   ├── opus47-final/
│   └── deepseek-v4-pixsou/
└── scripts/
    ├── auto-audio.sh        # 一键音频生成
    ├── one-click-generate.sh
    └── batch-generate.sh
```

**4 个 Skills 全部可用**：

| Skill | 功能 | 触发词 |
|-------|------|--------|
| `video-pipeline-cn` | 视频生成流水线 | "做个视频"、"文章转视频" |
| `minimax-audio-cn` | 音频生成 | "配音"、"生成 BGM" |
| `seedance-openclaw` | Seedance 提示词 | "生成视频提示词" |
| `Seedance2-skill` | Seedance API 调用 | "调用 Seedance" |

---

## 快速开始（3 步）

```bash
# 1. 克隆项目
git clone https://github.com/cscsxx606/openclaw-video-stack.git
cd openclaw-video-stack

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env：
#   ARK_API_KEY=你的火山引擎 Key
#   MINIMAX_API_KEY=你的 MiniMax Key

# 3. 一键生成音频 + 合成
./scripts/auto-audio.sh /path/to/video-project/
```

`auto-audio.sh` 会自动：
1. 从 `口播稿-30s.md` 提取正文
2. 检测视频类型（SU7/Opus/V4）选择 BGM 风格
3. 调用 MiniMax TTS + Music
4. FFmpeg 混音合成最终成片

---

## 为什么这套方案能跑通？

**3 个关键设计**：

1. **本地调度 + 云端生成**：OpenClaw 在本地做 LLM 编排（改稿、分镜、提示词优化），Seedance 在云端做重体力活（视频生成），无需本地 GPU。

2. **两段式视频**：15s + 15s 拼接，而不是一次生成 30s。因为 Seedance 2.0 的参考视频延长比直接生成长视频更稳定，且风格一致性更好。

3. **MiniMax 音频兜底**：TTS 和 Music 都是国内 API，延迟低、中文好、成本低。不用 ElevenLabs（贵）、不用 Suno（慢）、不用 macOS say（机械）。

---

## 下一步

- [ ] 批量生产：把 10 篇文章丢进队列，自动出 10 条视频
- [ ] 封面图自动生成：用 FLUX 模型给每条视频配封面
- [ ] 多音色支持：MiniMax 有 20+ 音色，按内容类型自动选择
- [ ] 视频号/抖音直接发布：接入平台 API 自动上传

---

**GitHub**：https://github.com/cscsxx606/openclaw-video-stack

**关键词**：OpenClaw, Seedance 2.0, MiniMax, AI 视频, 自动化, 短视频生成, 中文视频

---

> 写于 2026-06-11。技术栈版本：OpenClaw 2026.4.27, Seedance 2.0 (doubao-seedance-2-0-260128), MiniMax speech-2.8-hd / music-1.5.
