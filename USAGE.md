# 📖 使用指南

## 快速开始（一句话生成视频）

```bash
# 1. 生成视频（Seedance 2.0）
python3 skills/Seedance2-skill/scripts/seedance.py create \
  --prompt "赛车在纽北赛道飞驰" --ratio 9:16 --duration 15 --resolution 1080p

# 2. 生成配音（MiniMax TTS）
python3 -c "
import requests, binascii, os
KEY = os.getenv('MINIMAX_API_KEY')
resp = requests.post('https://api.minimaxi.com/v1/t2a_v2',
  headers={'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'},
  json={'model': 'speech-2.8-hd', 'text': '小米又搞事情了...', 'stream': False,
    'voice_setting': {'voice_id': 'male-qn-qingse', 'speed': 1.0, 'vol': 1.0, 'pitch': 0},
    'audio_setting': {'audio_sample_rate': 32000, 'bitrate': 128000, 'format': 'mp3'}},
  timeout=60)
data = resp.json()
if data['base_resp']['status_code'] == 0:
    open('voice.mp3', 'wb').write(binascii.unhexlify(data['data']['audio']))
"

# 3. 生成 BGM（MiniMax Music）
python3 -c "
import requests, binascii, os
KEY = os.getenv('MINIMAX_API_KEY')
resp = requests.post('https://api.minimaxi.com/v1/music_generation',
  headers={'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'},
  json={'model': 'music-1.5', 'prompt': 'electronic, racing, 130bpm, energetic, no vocals',
    'lyrics': '[Instrumental]', 'stream': False},
  timeout=120)
data = resp.json()
if data['base_resp']['status_code'] == 0:
    audio = data['data']['audio']
    if audio.startswith('http'):
        import requests; audio = requests.get(audio, timeout=60).content
    else:
        audio = binascii.unhexlify(audio)
    open('bgm.mp3', 'wb').write(audio)
"

# 4. 混音合成
ffmpeg -y -i voice.mp3 -t 30 -c copy voice-30s.mp3
ffmpeg -y -i voice-30s.mp3 -i bgm.mp3 \
  -filter_complex "[1:a]volume=0.18,afade=t=in:st=0:d=1,afade=t=out:st=27:d=2[bgm];[0:a][bgm]amix=inputs=2:duration=shortest:normalize=0" \
  -c:a aac -b:a 192k mixed.m4a
ffmpeg -y -i video.mp4 -i mixed.m4a -c:v copy -c:a aac -b:a 192k -shortest final.mp4
```

## 完整流水线（OpenClaw 自动化）

```
video-pipeline-cn 生成视频 + 字幕
        ↓
minimax-audio-cn 生成配音 + BGM
        ↓
FFmpeg 混音 + 合成
        ↓
30s 完整 MP4（视频+人声+BGM）
```

## 音频配置

| 组件 | 模型 | 采样率 | 码率 | 声道 |
|------|------|--------|------|------|
| 配音 | speech-2.8-hd | 32kHz | 128kbps | 单声道 |
| BGM | music-1.5 | 44.1kHz | 256kbps | 立体声 |
| 混音 | AAC | 32kHz | 192kbps | 单声道 |

## 推荐音色

| voice_id | 描述 | 场景 |
|----------|------|------|
| `male-qn-qingse` | 青年男声 | 资讯/科普 |
| `male-qn-jingying` | 精英男声 | 商业/财经 |
| `female-shaonv` | 少女声 | 娱乐/生活 |
| `female-yujie` | 御姐声 | 高端/科技 |

## 推荐 BGM 风格

| 风格 | prompt |
|------|--------|
| 赛车电子 | `electronic, racing, 130bpm, energetic, futuristic, no vocals` |
| 科技资讯 | `electronic, tech, ambient, 120bpm, mysterious, no vocals` |
| 电影配乐 | `cinematic, epic, inspiring, orchestral electronic hybrid, no vocals` |

## 关键踩坑

1. **MiniMax TTS 响应是 hex 编码** — 用 `binascii.unhexlify()` 解码
2. **music-1.5 需要 lyrics 字段** — 纯音乐用 `[Instrumental]` 占位
3. **music-02 不存在** — 只有 `music-1.5` 和 `music-01`
4. **BGM 可能返回 URL** — 先用 `startswith('http')` 判断

## 环境变量

```bash
export ARK_API_KEY="你的火山引擎 Key"      # Seedance 视频
export MINIMAX_API_KEY="你的 MiniMax Key"   # 音频
```
