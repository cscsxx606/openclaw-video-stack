# 🎬 OpenClaw Video Stack

> 一键部署：让 OpenClaw 拥有完整的 AI 视频生产能力

基于 **OpenClaw** + **Seedance 2.0**（字节跳动即梦）+ **FFmpeg**，从一篇文章自动生成 30 秒短视频（含分镜、AI 视频、中文字幕、配音、背景音乐）。

## ✨ 效果

输入一句话 → 输出 30 秒 MP4：

```
输入：小米又搞事情了，SU7 Ultra 纽北跑进 7 分
输出：30s 1080×1920 竖版短视频（带画面+字幕+配音+BGM）
耗时：~20 分钟
成本：~¥0.04（仅 API 费用）
```

## 🎯 包含的 Skills

| Skill | 用途 |
|-------|------|
| `video-pipeline-cn` | 主编排（文章 → 视频全流程） |
| `seedance-openclaw` | Seedance 提示词生成 |
| `Seedance2-skill` | Seedance 2.0 API 调用 |

## 🛠️ 系统要求

- macOS 12+ / Linux / Windows (WSL2)
- Python 3.10+
- FFmpeg 6.0+
- 火山引擎账号（[注册](https://www.volcengine.com/) 并开通 Seedance 2.0）

## 🚀 快速开始

### 1. 克隆

```bash
git clone https://github.com/你的用户名/openclaw-video-stack.git
cd openclaw-video-stack
```

### 2. 安装 FFmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows (Chocolatey)
choco install ffmpeg
```

### 3. 安装 OpenClaw

参考 [OpenClaw 官方文档](https://docs.openclaw.ai)。

### 4. 安装 Skills

```bash
# 复制 skills 到 OpenClaw workspace
cp -r skills/* ~/.openclaw/workspace/skills/

# 验证
ls ~/.openclaw/workspace/skills/ | grep -E "video-pipeline|seedance"
```

应该看到：
- `video-pipeline-cn/`
- `seedance-openclaw/`
- `Seedance2-skill/`

### 5. 配置 API Key

```bash
# 火山引擎 ARK API Key（[申请地址](https://www.volcengine.com/product/ark)）
export ARK_API_KEY="<your-volcengine-api-key>"

# 验证连通性
python3 ~/.openclaw/workspace/skills/Seedance2-skill/scripts/seedance.py list --page-size 1
```

成功时返回 `{"total": 0, "items": []}`。

### 6. 第一次生成

```bash
# 创建项目目录
mkdir -p ~/.openclaw/workspace/output/videos/my-first-video
cd ~/.openclaw/workspace/output/videos/my-first-video

# 调用 skill
openclaw run video-pipeline-cn --topic "小米又搞事情了，SU7 Ultra 纽北跑进 7 分"
```

或更简单——在 OpenClaw 对话中说：

```
帮我做一个 30 秒短视频，主题是"小米 SU7 Ultra 纽北跑进 7 分"
```

## 📂 目录结构

```
openclaw-video-stack/
├── README.md                  # 本文件
├── INSTALL.md                 # 详细安装指南
├── USAGE.md                   # 详细使用指南
├── TROUBLESHOOTING.md         # 常见问题
├── skills/                    # 要复制到 ~/.openclaw/workspace/skills/
│   ├── video-pipeline-cn/
│   ├── seedance-openclaw/
│   └── Seedance2-skill/
├── examples/                  # 示例项目
│   ├── su7-ultra-nurburgring/ # 完整案例（含最终成片）
│   ├── opus47-final/          # 第二个案例
│   └── deepseek-v4-pixsou/    # 第三个案例
├── scripts/                   # 辅助脚本
│   ├── one-click-generate.sh  # 一键生成
│   └── batch-generate.sh      # 批量生成
├── .env.example               # 环境变量模板
├── .gitignore                 # 防止泄露密钥
└── LICENSE
```

## 📖 文档导航

- [INSTALL.md](./INSTALL.md) — 完整安装步骤
- [USAGE.md](./USAGE.md) — 详细使用方法 + 高级选项
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) — 常见问题排查
- [examples/](./examples/) — 3 个完整案例

## 💰 成本

| 项 | 价格 |
|----|------|
| Seedance 2.0 文生视频（1080p × 15s） | ~¥0.018 / 段 |
| Seedance 2.0 参考视频延长 | ~¥0.025 / 段 |
| 完整 30s 视频 | ~¥0.04 / 条 |
| 中文配音 | ¥0（macOS `say`） |
| BGM | ¥0（FFmpeg 合成） |

## 🎬 完整视频流水线

```
┌──────────────────────────────────────────────────┐
│ 1. 改稿（OpenClaw + LLM）         < 5s          │
│ 2. 分镜表（OpenClaw + LLM）        < 5s          │
│ 3. Seedance 提示词（skill）        < 5s          │
│ 4. Seedance API 视频生成（2 段）   ~10 min      │
│ 5. FFmpeg 拼接                     ~3s          │
│ 6. ASS 字幕烧录                    ~30s         │
│ 7. macOS say 配音                  < 5s         │
│ 8. FFmpeg BGM 合成                 < 10s        │
│ 9. 音视频合成                      ~5s          │
│─────────────────────────────────────────────────│
│ 总耗时：~10-20 分钟                              │
│ 总成本：~¥0.04                                   │
└──────────────────────────────────────────────────┘
```

## ⚖️ 许可

MIT License — 自由使用、修改、分发。

## 🙏 致谢

- [OpenClaw](https://github.com/openclaw/openclaw) — AI Agent 运行时
- [Seedance 2.0](https://www.volcengine.com/product/ark) — 字节跳动即梦
- [FFmpeg](https://ffmpeg.org/) — 视频处理
- [HeyGen HyperFrames](https://github.com/heygen-com/hyperframes) — 动效视频参考
- [browser-use video-use](https://github.com/browser-use/video-use) — Agent 剪辑参考
