# 📦 详细安装指南

## 1. 系统要求

| 项 | 最低 | 推荐 |
|----|------|------|
| 操作系统 | macOS 12 / Ubuntu 20.04 / WSL2 | macOS 14+ |
| Python | 3.10 | 3.12+ |
| Node.js | 18+ | 20+ |
| 内存 | 4 GB | 8 GB+ |
| 磁盘 | 2 GB | 5 GB+ |
| 网络 | 能访问火山引擎 API | 稳定网络 |

## 2. 安装 FFmpeg

### macOS

```bash
brew install ffmpeg

# 验证
ffmpeg -version
```

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install ffmpeg

# 验证
ffmpeg -version
```

### Windows (WSL2)

```bash
sudo apt update
sudo apt install ffmpeg
```

## 3. 安装 OpenClaw

参考 [OpenClaw 官方文档](https://docs.openclaw.ai/getting-started/installation)。

```bash
# 全局安装（推荐）
npm install -g @openclaw/cli

# 验证
openclaw --version
```

## 4. 初始化 Workspace

```bash
# OpenClaw 默认 workspace 在 ~/.openclaw/workspace
# 如果不存在会自动创建
openclaw init
```

## 5. 复制 Skills

```bash
# 克隆本仓库
git clone https://github.com/你的用户名/openclaw-video-stack.git
cd openclaw-video-stack

# 复制 skills 到 OpenClaw workspace
cp -r skills/* ~/.openclaw/workspace/skills/

# 验证
ls ~/.openclaw/workspace/skills/ | grep -E "video-pipeline|seedance"
```

应该看到：
- `video-pipeline-cn`
- `seedance-openclaw`
- `Seedance2-skill`

## 6. 申请火山引擎 API Key

### 步骤 1：注册火山引擎

访问 [https://www.volcengine.com/](https://www.volcengine.com/)，注册并完成实名认证。

### 步骤 2：开通 ARK 服务

访问 [https://www.volcengine.com/product/ark](https://www.volcengine.com/product/ark)，开通"火山方舟"服务。

### 步骤 3：创建 API Key

在 ARK 控制台 → API Key 管理 → 创建 API Key。

复制 API Key（形如 `abcd1234-5678-90ef-...`）。

### 步骤 4：充值

Seedance 2.0 是付费服务，需要在火山方舟控制台充值（建议先充 ¥10 测试）。

## 7. 配置环境变量

### macOS / Linux (临时)

```bash
export ARK_API_KEY="<your-volcengine-api-key>"
```

### macOS / Linux (永久)

```bash
# 添加到 ~/.zshrc 或 ~/.bashrc
echo 'export ARK_API_KEY="<your-volcengine-api-key>"' >> ~/.zshrc
source ~/.zshrc
```

### Windows (PowerShell)

```powershell
[System.Environment]::SetEnvironmentVariable('ARK_API_KEY', '<your-volcengine-api-key>', 'User')
```

重启终端生效。

## 8. 验证安装

```bash
# 验证 API 连通
python3 ~/.openclaw/workspace/skills/Seedance2-skill/scripts/seedance.py list --page-size 1
```

成功时返回：
```json
{
  "total": 0,
  "items": []
}
```

如果返回 `401 Unauthorized` 或 `Error`，请检查 API Key 是否正确。

## 9. 第一次生成

### 方式 A：使用 OpenClaw 对话

在 OpenClaw 交互中输入：

```
帮我做一个 30 秒短视频，主题是"小米 SU7 Ultra 纽北跑进 7 分"
```

OpenClaw 会自动调用 `video-pipeline-cn` skill，生成完整项目。

### 方式 B：使用 CLI

```bash
# 进入 OpenClaw 交互
openclaw chat

# 在对话中：
帮我做一个 30 秒短视频，主题是"小米 SU7 Ultra 纽北跑进 7 分"
```

### 方式 C：使用脚本

```bash
# 使用项目自带的脚本
./scripts/one-click-generate.sh "小米 SU7 Ultra 纽北跑进 7 分"
```

输出文件位置：
```
~/.openclaw/workspace/output/videos/<项目名>/su7-final.mp4
```

## 🔧 常见安装问题

### Q: pip 提示权限错误

```bash
# 用 venv
python3 -m venv ~/.openclaw/venv
source ~/.openclaw/venv/bin/activate
pip install -r ~/.openclaw/workspace/skills/Seedance2-skill/requirements.txt
```

### Q: macOS 提示 "无法打开 'say'"

`say` 是 macOS 系统命令，Linux/Windows 不可用。Linux 可用 `espeak`：

```bash
sudo apt install espeak
# 改用 espeak 命令
```

### Q: FFmpeg 烧录字幕中文显示为方块

说明 FFmpeg 找不到中文字体。macOS 用户已自带 `Hiragino Sans GB`，其他系统：

```bash
# Ubuntu
sudo apt install fonts-noto-cjk

# 然后用 fc-list :lang=zh 验证
```

修改 `skills/video-pipeline-cn/SKILL.md` 中的 `FontName=Hiragino Sans GB` 为 `Noto Sans CJK SC`。

### Q: Seedance 视频生成超时

正常情况下：
- 1080p × 15s：5-15 分钟
- 2K × 15s：10-25 分钟

如果超过 30 分钟还在 `running`，可能是网络问题。在 Seedance 控制台查看任务状态，必要时删除重试。

## 📋 安装验证清单

- [ ] FFmpeg 已安装并能 `ffmpeg -version`
- [ ] OpenClaw 已安装并能 `openclaw --version`
- [ ] 3 个 skills 已复制到 `~/.openclaw/workspace/skills/`
- [ ] `ARK_API_KEY` 环境变量已设置
- [ ] `seedance.py list` 返回 JSON 不报错
- [ ] 第一次生成成功（30s 视频）

## 🎉 安装完成

参考 [USAGE.md](./USAGE.md) 学习详细使用方法。
