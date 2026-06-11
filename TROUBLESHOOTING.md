# 🐛 常见问题排查

## 1. API 相关

### ❌ `Error: ARK_API_KEY environment variable is not set`

**原因**：环境变量未设置。

**解决**：
```bash
export ARK_API_KEY="<your-key>"
# 永久生效：加到 ~/.zshrc
```

### ❌ `API Error (HTTP 401): Unauthorized`

**原因**：API Key 无效或过期。

**解决**：
1. 登录火山引擎控制台检查 Key 是否启用
2. 重新生成 API Key
3. 确认账号已开通 ARK 服务

### ❌ `API Error (HTTP 400): The parameter 'content' ... reference_video must be provided as a web url`

**原因**：Seedance API 限制——参考视频**必须**是公网 URL，不能用 base64。

**解决**：
```bash
# 错误方式（base64）
python3 seedance.py create --video ./local.mp4 ...

# 正确方式（公网 URL）
python3 seedance.py create --video "https://ark-...volces.com/xxx.mp4?..." ...
```

获取 URL 方法：
```bash
# 1. 跑完第 1 段后查 status
python3 seedance.py status <task_id>

# 2. response.content.video_url 就是公网 URL（24h 有效）
```

### ❌ `UnicodeEncodeError: 'latin-1' codec can't encode character '\u2026'`

**原因**：API Key 中混入了特殊字符（如 `…` U+2026 HORIZONTAL ELLIPSIS）。

**解决**：
```bash
# 错误：用了省略号占位
export ARK_API_KEY="<your-volcengine-api-key>"

# 正确：完整 Key
export ARK_API_KEY="<your-volcengine-api-key>"
```

## 2. 视频生成相关

### ❌ Seedance 任务一直 `running` 不结束

**正常情况**：
- 1080p × 15s：5-15 分钟
- 2K × 15s：10-25 分钟

**异常情况**（> 30 分钟）：

1. **网络问题**：
```bash
# 测试连通性
curl -v https://ark.cn-beijing.volces.com
```

2. **账号欠费**：登录火山引擎检查余额

3. **任务积压**：火山方舟服务有排队机制，等几分钟

4. **删除重试**：
```bash
python3 seedance.py status <task_id>  # 看 task_id
python3 seedance.py delete <task_id>
# 重新跑
```

### ❌ `Video URL: ...` 但下载失败

**原因**：URL 24h 过期。

**解决**：在 24h 内下载。下载后本地文件永久有效。

```bash
curl -L "<video_url>" -o segment.mp4
```

### ❌ Seedance 生成内容不符合预期

**原因**：提示词不清晰。

**解决**：
- 用 5W1H（什么、谁、何时、何地、为什么、怎么做）
- 加镜头语言（推镜、拉镜、环绕、固定）
- 加风格（电影级、纪录片、广告、3D 渲染）
- 加色板（深蓝、青蓝、暖橙）

参考 [`examples/`](./examples/) 中的提示词模板。

## 3. FFmpeg 相关

### ❌ 中文字幕显示为方块（□□□）

**原因**：FFmpeg 找不到中文字体。

**解决**：

**macOS**（自带 `Hiragino Sans GB`）：
```bash
fc-list :lang=zh | head -3
# 应能看到 Hiragino Sans GB
```

**Ubuntu / Debian**：
```bash
sudo apt install fonts-noto-cjk
fc-cache -fv
```

**修改字幕样式**：
```bash
# 在视频流水线中，编辑 字幕.ass
Style: Default,Noto Sans CJK SC,...
```

### ❌ `SRT 字幕换行没生效` / `SRT 字幕被裁切`

**原因**：SRT 格式在 libass 中换行处理有限。

**解决**：用 **ASS 格式**：
- 强制换行用 `\N`（不是 `\n`）
- 必须设 `PlayResX` 和 `PlayResY`
- 必须设 `Alignment`（2 = 底部居中）

参考 `examples/*/字幕.ass`。

### ❌ `Alignment=2 字幕出现在顶部` 而不是底部

**原因**：FFmpeg 某些版本 + libass 行为差异。

**解决**：用 ASS 格式 + 显式 `PlayResY: 1920` + `Alignment=2`。

### ❌ FFmpeg 报错 `fontconfig not found`

**解决**：
```bash
# Ubuntu
sudo apt install fontconfig

# macOS
brew install fontconfig
```

## 4. TTS 配音相关

### ❌ `say: command not found`（Linux / Windows）

**原因**：`say` 是 macOS 系统命令。

**解决**：

**Linux**：
```bash
sudo apt install espeak
# 改用 espeak（中文支持有限）
espeak -v zh "你好世界" -w output.wav
```

**Windows (WSL)**：
```bash
# 同 Linux
sudo apt install espeak
```

**通用方案（推荐）**：用 ElevenLabs API：
```python
# 修改 skills/video-pipeline-cn/scripts/tts.py
from elevenlabs import generate, save
audio = generate(text=script, voice="<voice-id>")
save(audio, "配音.mp3")
```

### ❌ macOS say 生成的 MP3 听不清

**原因**：默认音量较低。

**解决**：
```bash
# 提高音量
ffmpeg -i 配音.mp3 -filter:a "volume=2.0" 配音-loud.mp3
```

或用 `-r 200` 加快语速：
```bash
say -v "Eddy (中文（中国大陆）)" -r 200 -o voice.aiff
```

## 5. BGM 合成相关

### ❌ FFmpeg BGM 听起来像机器人

**原因**：4 轨纯合成器效果单调。

**解决**：用真实音乐：
- Pixabay: [https://pixabay.com/music/](https://pixabay.com/music/)（免登录直下）
- FreePD: 已关闭
- ccMixter: [http://ccmixter.org/](http://ccmixter.org/)

把下载的 BGM 放到：
```bash
mkdir -p ~/.openclaw/workspace/assets/bgm
cp your-track.mp3 ~/.openclaw/workspace/assets/bgm/
```

修改 `skills/video-pipeline-cn/scripts/mix_audio.py`：
```python
BGM_FILE = os.path.expanduser("~/.openclaw/workspace/assets/bgm/your-track.mp3")
```

## 6. 完整流水线失败

### ❌ 任务成功但文件找不到

**原因**：路径错误。

**解决**：
```bash
# 默认输出目录
~/.openclaw/workspace/output/videos/<项目名>/

# 查看最近生成的项目
ls -lt ~/.openclaw/workspace/output/videos/ | head -5
```

### ❌ 最终 MP4 没有声音

**原因**：配音生成失败但脚本没报错。

**排查**：
```bash
# 1. 检查配音文件
ls -la 配音.mp3
ffprobe 配音.mp3  # 看时长

# 2. 检查混合音轨
ls -la 混合音轨.m4a
ffprobe 混合音轨.m4a  # 看音轨

# 3. 检查最终成片
ffprobe su7-final.mp4  # 应该有音轨
```

## 📞 还是解决不了？

1. 提交 Issue: [https://github.com/你的用户名/openclaw-video-stack/issues](https://github.com/your-username/openclaw-video-stack/issues)
2. 附上：
   - 操作系统版本
   - Python 版本
   - OpenClaw 版本
   - 错误日志（完整）
   - 复现步骤

## 🎉 排查成功后

参考 [`USAGE.md`](./USAGE.md) 学习更多高级用法。
