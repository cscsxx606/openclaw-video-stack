#!/bin/bash
# 🎵 自动音频生成脚本
# 为视频自动生成 MiniMax 配音 + BGM

set -e

VIDEO_DIR="${1:-.}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 加载环境变量
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
fi

if [ -z "$MINIMAX_API_KEY" ]; then
    echo "❌ 错误: MINIMAX_API_KEY 未设置"
    echo "   在 .env 文件添加: MINIMAX_API_KEY=你的Key"
    exit 1
fi

echo "🎵 自动音频生成: $VIDEO_DIR"

# 检查口播稿
if [ ! -f "$VIDEO_DIR/口播稿-30s.md" ]; then
    echo "❌ 未找到口播稿: $VIDEO_DIR/口播稿-30s.md"
    exit 1
fi

# 提取口播正文
echo "📖 提取口播稿..."
python3 << 'PYEOF'
import re
with open("$VIDEO_DIR/口播稿-30s.md") as f:
    content = f.read()
# 提取正文
m = re.search(r'## 📜 口播正文\n\n([\s\S]*?)\n\n---', content)
if not m:
    m = re.search(r'## 📜 口播正文\n\n([\s\S]*)', content)
text = m.group(1) if m else content
# 清理 markdown
text = re.sub(r'\n+', ' ', text).strip()
text = text.replace('（', '').replace('）', '').replace('"', '').replace('"', '').replace('"', '')
with open("/tmp/voiceover.txt", "w") as f:
    f.write(text)
print(f"提取文本: {len(text)} 字符")
PYEOF

TEXT=$(cat /tmp/voiceover.txt)
echo "📝 文本: ${TEXT:0:50}..."

# 生成配音
echo "🎤 生成 MiniMax 配音..."
python3 << 'PYEOF'
import requests, binascii, os

KEY = os.getenv('MINIMAX_API_KEY')
TEXT = open("/tmp/voiceover.txt").read()
OUTDIR = "$VIDEO_DIR"

resp = requests.post(
    'https://api.minimaxi.com/v1/t2a_v2',
    headers={'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'},
    json={
        'model': 'speech-2.8-hd',
        'text': TEXT,
        'stream': False,
        'voice_setting': {'voice_id': 'male-qn-qingse', 'speed': 1.0, 'vol': 1.0, 'pitch': 0},
        'audio_setting': {'audio_sample_rate': 32000, 'bitrate': 128000, 'format': 'mp3'},
    },
    timeout=60,
)

data = resp.json()
if data['base_resp']['status_code'] != 0:
    print(f"❌ TTS 失败: {data['base_resp']}")
    exit(1)

audio = binascii.unhexlify(data['data']['audio'])
with open(f"{OUTDIR}/minimax-voice.mp3", 'wb') as f:
    f.write(audio)

extra = data.get('extra_info', {})
print(f"✅ 配音: {len(audio)/1024:.1f} KB, {extra.get('audio_length',0)/1000:.1f} s")
PYEOF

# 生成 BGM（根据视频类型自动选择风格）
echo "🎵 生成 MiniMax BGM..."

# 检测视频类型
if echo "$VIDEO_DIR" | grep -qi "su7\|racing\|car\|race"; then
    BGM_PROMPT="electronic, racing, 130bpm, energetic, futuristic, no vocals"
elif echo "$VIDEO_DIR" | grep -qi "opus\|tech\|claude\|anthropic"; then
    BGM_PROMPT="electronic, tech, ambient, 120bpm, mysterious, futuristic, no vocals"
elif echo "$VIDEO_DIR" | grep -qi "deepseek\|v4\|pixsou\|cinematic"; then
    BGM_PROMPT="cinematic, epic, inspiring, orchestral electronic hybrid, no vocals"
else
    BGM_PROMPT="electronic, modern, 120bpm, energetic, no vocals"
fi

echo "🎵 BGM 风格: $BGM_PROMPT"

python3 << 'PYEOF'
import requests, binascii, os

KEY = os.getenv('MINIMAX_API_KEY')
OUTDIR = "$VIDEO_DIR"
BGM_PROMPT = "$BGM_PROMPT"

resp = requests.post(
    'https://api.minimaxi.com/v1/music_generation',
    headers={'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'},
    json={
        'model': 'music-1.5',
        'prompt': BGM_PROMPT,
        'lyrics': '[Instrumental]',
        'stream': False,
    },
    timeout=120,
)

data = resp.json()
if data['base_resp']['status_code'] != 0:
    print(f"❌ BGM 失败: {data['base_resp']}")
    exit(1)

audio = data['data']['audio']
if audio.startswith('http'):
    audio = requests.get(audio, timeout=60).content
else:
    audio = binascii.unhexlify(audio)

os.makedirs(f"{OUTDIR}/bgm", exist_ok=True)
with open(f"{OUTDIR}/bgm/minimax-bgm.mp3", 'wb') as f:
    f.write(audio)

extra = data.get('extra_info', {})
print(f"✅ BGM: {len(audio)/1024:.1f} KB, {extra.get('music_duration',0)/1000:.1f} s")
PYEOF

# 混音合成
echo "🔧 混音合成..."

cd "$VIDEO_DIR"

# 裁配音到 30 秒
ffmpeg -y -i minimax-voice.mp3 -t 30 -c copy voice-30s.mp3 2>/dev/null

# 混音
ffmpeg -y \
  -i voice-30s.mp3 -i bgm/minimax-bgm.mp3 \
  -filter_complex "[1:a]volume=0.18,afade=t=in:st=0:d=1,afade=t=out:st=27:d=2[bgm];[0:a][bgm]amix=inputs=2:duration=shortest:normalize=0" \
  -c:a aac -b:a 192k mixed.m4a 2>/dev/null

# 合成最终视频
VIDEO_FILE=$(ls *-with-subs.mp4 2>/dev/null | head -1)
if [ -z "$VIDEO_FILE" ]; then
    VIDEO_FILE=$(ls *.mp4 2>/dev/null | grep -v final | head -1)
fi

if [ -n "$VIDEO_FILE" ]; then
    FINAL_NAME=$(echo "$VIDEO_FILE" | sed 's/-with-subs//; s/\.mp4$//')-final.mp4
    ffmpeg -y -i "$VIDEO_FILE" -i mixed.m4a \
      -c:v copy -c:a aac -b:a 192k -shortest "$FINAL_NAME" 2>/dev/null
    echo "✅ 最终成片: $FINAL_NAME ($(ls -lh "$FINAL_NAME" | awk '{print $5}'))"
else
    echo "⚠️ 未找到视频文件，音频已生成:"
    echo "  - minimax-voice.mp3"
    echo "  - bgm/minimax-bgm.mp3"
    echo "  - mixed.m4a"
fi

echo "🎉 完成!"
