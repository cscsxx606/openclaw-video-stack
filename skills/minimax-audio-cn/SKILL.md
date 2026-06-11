---
name: "minimax-audio-cn"
description: "MiniMax 中文音频生成：TTS 配音（speech-2.8-hd）+ BGM 音乐（music-1.5）。触发词：配音、TTS、BGM、音乐。"
---

# 🎵 MiniMax 音频生成

> 基于 MiniMax (MiniMax) 的中文 AI 音频能力，为视频流水线提供专业级配音和背景音乐。

## 能力

| 能力 | 模型 | 用途 |
|------|------|------|
| **TTS 配音** | `speech-2.8-hd` | 中文男声/女声/多种音色 |
| **音乐生成** | `music-1.5` | 任意风格的背景音乐（赛车、科技、电影等） |

## 一句话用法

```
用 MiniMax 给 SU7 Ultra 视频做配音（赛车电子 BGM）
```

或：

```
把这段话用 MiniMax 朗读：小米又搞事情了...
```

## 端点

| API | URL | 鉴权 |
|-----|-----|------|
| T2A v2（TTS） | `https://api.minimaxi.com/v1/t2a_v2` | `Authorization: Bearer <key>` |
| Music Generation | `https://api.minimaxi.com/v1/music_generation` | 同上 |

## 配置

```bash
# 在 ~/.zshrc 添加
export MINIMAX_API_KEY="sk-cp-..."
```

## 关键踩坑（已记录）

1. **`lyrics` 必填**——纯音乐用 `[Instrumental]` 占位
2. **响应是 hex 编码**——用 `binascii.unhexlify()` 解码
3. **URL 也可能返回**——先用 `startswith('http')` 判断
4. **`music-02` 不存在**——只有 `music-1.5` 和 `music-01`
5. **音色多**：`male-qn-qingse`（青年男声）、`female-yujie`（御姐声）等

## 推荐 BGM 风格

| 风格 | prompt 关键词 |
|------|--------------|
| 赛车电子 | `electronic, racing, 130bpm, energetic, futuristic, no vocals` |
| 科技资讯 | `electronic, tech, ambient, 120bpm, mysterious, no vocals` |
| 电影配乐 | `cinematic, epic, inspiring, orchestral electronic hybrid, no vocals` |

## 完整流水线

```
video-pipeline-cn 生成视频
        ↓
minimax-audio-cn 生成配音 + BGM
        ↓
FFmpeg 混音 + 烧字幕
        ↓
最终 MP4（30s 视频+人声+BGM）
```

## 成本

- TTS: ~¥0.001/百字
- BGM: ~¥0.1/首
- 30s 视频音频总成本: ~¥0.15
