#!/usr/bin/env python3
"""
video-pipeline-cn TTS 自动 fallback 模块

支持：
1. macOS say（免费，中文支持）
2. MiniMax TTS API（你已有 key）
3. 阿里云百炼 TTS API（你已有 key）

用法：
    from tts_fallback import generate_tts
    
    # 自动检测可用 TTS，优先 macOS say
    audio_path = generate_tts("你好世界", "output.mp3")
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# TTS 配置
TTS_FALLBACK_VOICE = "Eddy (中文（中国大陆）)"  # macOS say 中文语音

# API Keys（从环境变量或 MEMORY.md 读取）
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")
ALIYUN_API_KEY = os.environ.get("ALIYUN_API_KEY", "")


def _check_macos_say():
    """检查 macOS say 是否可用"""
    try:
        result = subprocess.run(["which", "say"], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False


def _check_minimax():
    """检查 MiniMax TTS 是否可用"""
    return bool(MINIMAX_API_KEY)


def _check_aliyun():
    """检查阿里云百炼 TTS 是否可用"""
    return bool(ALIYUN_API_KEY)


def generate_tts_macos_say(text, output_path, voice=TTS_FALLBACK_VOICE):
    """使用 macOS say 生成配音"""
    print(f"🎙️ macOS say 生成配音...")
    
    # say 输出 aiff，需要转 mp3
    aiff_path = output_path.with_suffix('.aiff')
    
    cmd = ["say", "-v", voice, "-o", str(aiff_path), text]
    subprocess.run(cmd, check=True, capture_output=True, timeout=30)
    
    # 转 mp3
    subprocess.run([
        "ffmpeg", "-y", "-i", str(aiff_path),
        "-ar", "44100", "-ac", "2", "-b:a", "192k",
        str(output_path)
    ], check=True, capture_output=True)
    
    aiff_path.unlink(missing_ok=True)
    return output_path


def generate_tts_minimax(text, output_path, voice_id="male-qn-qingse"):
    """使用 MiniMax TTS API 生成配音"""
    print(f"🎙️ MiniMax TTS 生成配音...")
    
    import requests
    
    url = "https://api.minimax.chat/v1/t2a_v2"
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "speech-01-turbo",
        "text": text,
        "voice_setting": {
            "voice_id": voice_id,
            "speed": 1.0,
            "vol": 1.0,
            "pitch": 0
        },
        "audio_setting": {
            "sample_rate": 44100,
            "bitrate": 192000,
            "format": "mp3"
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    data = response.json()
    
    # MiniMax 返回 base64 音频
    if "data" in data and "audio" in data["data"]:
        import base64
        audio_base64 = data["data"]["audio"]
        audio_bytes = base64.b64decode(audio_base64)
        output_path.write_bytes(audio_bytes)
        return output_path
    
    raise RuntimeError(f"MiniMax TTS 返回异常: {data}")


def generate_tts_aliyun(text, output_path, voice="zhiyuan"):
    """使用阿里云百炼 TTS API 生成配音"""
    print(f"🎙️ 阿里云百炼 TTS 生成配音...")
    
    import requests
    
    url = "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/speech"
    headers = {
        "Authorization": f"Bearer {ALIYUN_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "sambert-zhiyuan-v1",
        "input": {"text": text},
        "parameters": {
            "sample_rate": 44100,
            "format": "mp3"
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    # 阿里云返回音频二进制
    output_path.write_bytes(response.content)
    return output_path


def generate_tts(text, output_path, preferred_provider=None):
    """
    自动选择 TTS 提供商生成配音
    
    优先级：
    1. preferred_provider（如果指定）
    2. macOS say（免费，中文好）
    3. MiniMax TTS（你已有 key）
    4. 阿里云百炼 TTS（你已有 key）
    5. 静音占位（兜底）
    
    Args:
        text: 要合成的文本
        output_path: 输出路径（Path 或 str）
        preferred_provider: 优先使用的提供商（"macos", "minimax", "aliyun"）
    
    Returns:
        Path: 生成的音频文件路径
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    providers = []
    
    # 如果指定了优先提供商
    if preferred_provider:
        providers.append(preferred_provider)
    
    # 默认优先级
    providers.extend(["macos", "minimax", "aliyun", "silence"])
    
    for provider in providers:
        try:
            if provider == "macos" and _check_macos_say():
                return generate_tts_macos_say(text, output_path)
            
            elif provider == "minimax" and _check_minimax():
                return generate_tts_minimax(text, output_path)
            
            elif provider == "aliyun" and _check_aliyun():
                return generate_tts_aliyun(text, output_path)
            
            elif provider == "silence":
                # 兜底：生成静音文件
                print(f"⚠️ 所有 TTS 失败，生成静音占位文件")
                subprocess.run([
                    "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                    "-t", "30", "-acodec", "aac", str(output_path)
                ], check=True, capture_output=True)
                return output_path
                
        except Exception as e:
            print(f"   ⚠️ {provider} TTS 失败: {e}")
            continue
    
    raise RuntimeError("所有 TTS 提供商都失败了")


def get_available_providers():
    """返回可用的 TTS 提供商列表"""
    providers = []
    if _check_macos_say():
        providers.append("macos")
    if _check_minimax():
        providers.append("minimax")
    if _check_aliyun():
        providers.append("aliyun")
    return providers


if __name__ == "__main__":
    # 测试
    print("可用 TTS 提供商:", get_available_providers())
    
    test_text = "你好，这是一个测试。"
    test_output = Path("/tmp/test_tts.mp3")
    
    try:
        result = generate_tts(test_text, test_output)
        print(f"✅ 生成成功: {result}")
    except Exception as e:
        print(f"❌ 生成失败: {e}")
