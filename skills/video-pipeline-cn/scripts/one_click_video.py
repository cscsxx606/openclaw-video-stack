#!/usr/bin/env python3
"""
video-pipeline-cn 一键视频生成脚本

整合 P0 三项功能：
1. 自动视频合成（batch.py + FFmpeg）
2. TTS 自动 fallback（macOS say / MiniMax / 阿里云）
3. 720p 降本自动推荐（预算 < ¥20 自动选 720p）

用法：
    # 完整流程（从文章到视频）
    python3 scripts/one_click_video.py \
        --article ~/output/articles/my-article.md \
        --budget 20 \
        --output-dir ~/output/videos/my-video/
    
    # 已有口播稿，直接合成
    python3 scripts/one_click_video.py \
        --project-dir ~/output/videos/my-video/ \
        --prompts prompts.json \
        --budget 20 \
        --auto-resolution

输出：
    - 最终成片.mp4（含字幕 + 配音 + BGM）
    - 口播稿-30s.md
    - 分镜表.md
    - 分镜-Seedance提示词.md
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# 添加依赖路径
SEEDANCE2_DIR = Path(__file__).parent.parent / "Seedance2-skill" / "scripts"
sys.path.insert(0, str(SEEDANCE2_DIR))
sys.path.insert(0, str(Path(__file__).parent))  # 当前目录（tts_fallback, resolution_advisor）

try:
    import seedance
    import batch
    import db
    from tts_fallback import generate_tts, get_available_providers
    from resolution_advisor import advise_resolution
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)


# ───────────────────────────────────────────
# 配置
# ───────────────────────────────────────────

DEFAULT_MODEL = "doubao-seedance-2-0-260128"
VIDEO_DURATION = 30  # 默认 30s
VIDEO_SEGMENTS = 2   # 2 段 15s


def generate_koubo_gao(article_path, output_dir):
    """Step 1: 从文章生成口播稿"""
    print(f"📝 Step 1: 生成口播稿...")
    
    article_text = Path(article_path).read_text(encoding='utf-8')
    
    # 简化版：提取前 150 字作为口播稿
    # 实际应该用 LLM 改稿，这里做占位
    koubo_text = article_text[:150] + "..."
    
    koubo_path = Path(output_dir) / "口播稿-30s.md"
    koubo_path.write_text(koubo_text, encoding='utf-8')
    
    print(f"   ✅ 口播稿: {koubo_path}")
    return koubo_path


def generate_fenjing(koubo_path, output_dir):
    """Step 2: 生成分镜表"""
    print(f"🎬 Step 2: 生成分镜表...")
    
    # 简化版：固定 5 镜头
    fenjing = """# 分镜表

| 时间 | 画面 | 动效 | 字幕 | 音效 |
|------|------|------|------|------|
| 0-3s | 开场画面 | 推镜 | 钩子 | 强节奏 |
| 3-11s | 主体展示 | 环绕 | 卖点1 | 中节奏 |
| 11-19s | 细节特写 | 拉镜 | 卖点2 | 中节奏 |
| 19-27s | 对比/反转 | 摇镜 | 卖点3 | 强节奏 |
| 27-30s | CTA/结尾 | 定镜 | 行动号召 | 收尾 |
"""
    
    fenjing_path = Path(output_dir) / "分镜表.md"
    fenjing_path.write_text(fenjing, encoding='utf-8')
    
    print(f"   ✅ 分镜表: {fenjing_path}")
    return fenjing_path


def generate_prompts(fenjing_path, output_dir):
    """Step 3: 生成 Seedance 提示词"""
    print(f"✨ Step 3: 生成 Seedance 提示词...")
    
    # 简化版：基于分镜生成 2 段提示词
    prompts = [
        "电影感画面，清晨阳光透过窗户洒入，咖啡杯冒着热气，镜头缓缓推近，暖色调，4K 高清",
        "特写镜头，咖啡豆从高空坠落，慢动作，金色光线，粒子效果，电影级调色"
    ]
    
    prompts_path = Path(output_dir) / "分镜-Seedance提示词.json"
    prompts_path.write_text(json.dumps(prompts, ensure_ascii=False, indent=2), encoding='utf-8')
    
    print(f"   ✅ 提示词: {prompts_path}")
    return prompts_path


def generate_video_segments(prompts_path, project, resolution, max_workers):
    """Step 4: 生成视频段（Seedance API）"""
    print(f"🎥 Step 4: 生成视频段（{resolution}, {max_workers} 并发）...")
    
    with open(prompts_path) as f:
        prompts = json.load(f)
    
    # 构造任务
    tasks = []
    for prompt in prompts:
        task = {
            "prompt": prompt,
            "duration": 15,
            "resolution": resolution,
            "model": DEFAULT_MODEL
        }
        tasks.append(task)
    
    # 估算成本
    total_cost = batch.estimate_total(tasks)
    print(f"   💰 估算成本: ¥{total_cost:.2f}")
    
    # 提交任务
    batch_id = f"batch-{int(time.time())}"
    results = []
    
    for i, task_cfg in enumerate(tasks):
        result = batch.submit_one(i, task_cfg, project, batch_id, max_retries=1)
        results.append(result)
        print(f"   [{i}] 提交: {result[1] or '失败'}")
    
    # 等待完成
    video_segments = []
    for i, (idx, task_id, error) in enumerate(results):
        if error or not task_id:
            print(f"   ❌ 任务 {i} 失败: {error}")
            continue
        
        print(f"   ⏳ 等待 {task_id}...")
        result = batch.wait_one(task_id, project, download_dir=None)
        
        if result and result.get("local_path"):
            video_segments.append(result["local_path"])
            print(f"   ✅ 完成: {result['local_path']}")
        else:
            print(f"   ❌ {task_id} 未完成")
    
    return video_segments


def generate_audio(koubo_path, output_dir):
    """Step 5: 生成配音（TTS fallback）"""
    print(f"🎙️ Step 5: 生成配音...")
    
    koubo_text = Path(koubo_path).read_text(encoding='utf-8')
    audio_path = Path(output_dir) / "配音.mp3"
    
    # 使用 TTS fallback 模块
    generate_tts(koubo_text[:200], audio_path)  # 限制长度
    
    print(f"   ✅ 配音: {audio_path}")
    return audio_path


def generate_bgm(output_dir, duration=30):
    """Step 6: 生成 BGM"""
    print(f"🎵 Step 6: 生成 BGM...")
    
    bgm_path = Path(output_dir) / "BGM.mp3"
    
    # 简化版 BGM
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"sine=frequency=220:duration={duration}",
        "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}",
        "-filter_complex",
        "[0:a]volume=0.3[a0];[1:a]volume=0.2[a1];[a0][a1]amix=inputs=2:duration=first",
        "-ar", "44100", "-ac", "2", "-b:a", "192k",
        str(bgm_path)
    ], check=True, capture_output=True)
    
    print(f"   ✅ BGM: {bgm_path}")
    return bgm_path


def generate_subtitles(koubo_path, output_dir):
    """Step 7: 生成字幕"""
    print(f"📝 Step 7: 生成字幕...")
    
    koubo_text = Path(koubo_path).read_text(encoding='utf-8')
    subtitle_path = Path(output_dir) / "字幕.ass"
    
    # 简单 ASS 字幕
    lines = koubo_text.split('\n')
    mid = len(lines) // 2 if len(lines) > 1 else 1
    part1 = '\n'.join(lines[:mid])[:50]
    part2 = '\n'.join(lines[mid:])[:50] if mid < len(lines) else "..."
    
    ass_content = f"""[Script Info]
Title: Auto Generated
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Hiragino Sans GB,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,30,30,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:15.00,Default,,0,0,0,,{part1}
Dialogue: 0,0:00:15.00,0:00:30.00,Default,,0,0,0,,{part2}
"""
    
    subtitle_path.write_text(ass_content, encoding='utf-8')
    print(f"   ✅ 字幕: {subtitle_path}")
    return subtitle_path


def compose_final_video(video_segments, audio_path, bgm_path, subtitle_path, output_path):
    """Step 8: 合成最终视频"""
    print(f"🎬 Step 8: 合成最终视频...")
    
    # 1. 拼接视频
    concat_list = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    for seg in video_segments:
        concat_list.write(f"file '{seg}'\n")
    concat_list.close()
    
    temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list.name, "-c", "copy", temp_video.name
    ], check=True, capture_output=True)
    
    # 2. 合成音频
    temp_audio = tempfile.NamedTemporaryFile(suffix='.aac', delete=False)
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(audio_path), "-i", str(bgm_path),
        "-filter_complex", "[0:a]volume=0.8[a0];[1:a]volume=0.3[a1];[a0][a1]amix=inputs=2:duration=first",
        "-ar", "44100", "-ac", "2", temp_audio.name
    ], check=True, capture_output=True)
    
    # 3. 最终合成
    subprocess.run([
        "ffmpeg", "-y",
        "-i", temp_video.name, "-i", temp_audio.name,
        "-vf", f"subtitles={subtitle_path}:force_style='FontName=Hiragino Sans GB'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k", "-shortest",
        str(output_path)
    ], check=True, capture_output=True)
    
    # 清理
    os.unlink(concat_list.name)
    os.unlink(temp_video.name)
    os.unlink(temp_audio.name)
    
    print(f"   ✅ 最终视频: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description='video-pipeline-cn 一键视频生成')
    parser.add_argument('--article', help='输入文章路径')
    parser.add_argument('--project-dir', help='项目目录（已有口播稿）')
    parser.add_argument('--prompts', help='Seedance 提示词 JSON')
    parser.add_argument('--budget', type=float, default=50, help='预算（元）')
    parser.add_argument('--auto-resolution', action='store_true', help='自动选择分辨率')
    parser.add_argument('--resolution', choices=['720p', '1080p'], help='强制分辨率')
    parser.add_argument('--max-workers', type=int, help='并发数')
    parser.add_argument('--skip-video-gen', action='store_true', help='跳过视频生成')
    parser.add_argument('--output-dir', help='输出目录')
    
    args = parser.parse_args()
    
    # 确定输出目录
    if args.output_dir:
        output_dir = Path(args.output_dir)
    elif args.project_dir:
        output_dir = Path(args.project_dir)
    elif args.article:
        slug = Path(args.article).stem[:20]
        output_dir = Path.home() / ".openclaw" / "workspace" / "output" / "videos" / slug
    else:
        print("❌ 需要 --article 或 --project-dir")
        sys.exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    project_name = output_dir.name
    
    print(f"🎬 video-pipeline-cn 一键视频生成")
    print(f"   输出: {output_dir}")
    print(f"   预算: ¥{args.budget}")
    
    # 1. 自动选择分辨率
    if args.auto_resolution or not args.resolution:
        resolution, max_workers, est_cost, rec = advise_resolution(args.budget)
    else:
        resolution = args.resolution
        max_workers = args.max_workers or (4 if resolution == "720p" else 2)
        est_cost = 0
    
    print(f"\n⚙️ 配置: {resolution} + {max_workers} workers")
    
    # 2. 生成素材（如果提供了文章）
    if args.article:
        koubo_path = generate_koubo_gao(args.article, output_dir)
        fenjing_path = generate_fenjing(koubo_path, output_dir)
        prompts_path = generate_prompts(fenjing_path, output_dir)
    else:
        # 使用已有素材
        koubo_path = output_dir / "口播稿-30s.md"
        prompts_path = output_dir / "分镜-Seedance提示词.json"
        
        if not koubo_path.exists():
            print(f"❌ 找不到口播稿: {koubo_path}")
            sys.exit(1)
    
    # 3. 生成视频段
    video_segments = []
    if not args.skip_video_gen:
        if not prompts_path.exists():
            print(f"❌ 找不到提示词: {prompts_path}")
            sys.exit(1)
        
        video_segments = generate_video_segments(
            prompts_path, project_name, resolution, max_workers
        )
    else:
        for f in sorted(output_dir.glob("*.mp4")):
            if "final" not in f.name and "配音" not in f.name and "BGM" not in f.name:
                video_segments.append(str(f))
        print(f"📹 使用已有视频段: {len(video_segments)} 个")
    
    if len(video_segments) < 2:
        print(f"❌ 需要至少 2 个视频段")
        sys.exit(1)
    
    # 4. 生成配音
    audio_path = generate_audio(koubo_path, output_dir)
    
    # 5. 生成 BGM
    bgm_path = generate_bgm(output_dir)
    
    # 6. 生成字幕
    subtitle_path = generate_subtitles(koubo_path, output_dir)
    
    # 7. 合成最终视频
    final_path = output_dir / "最终成片.mp4"
    compose_final_video(video_segments, audio_path, bgm_path, subtitle_path, final_path)
    
    # 8. 完成报告
    print(f"\n{'='*50}")
    print(f"✅ 完成！")
    print(f"   最终视频: {final_path}")
    print(f"   分辨率: {resolution}")
    print(f"   并发: {max_workers}")
    print(f"   视频段: {len(video_segments)}")
    if est_cost > 0:
        print(f"   估算成本: ¥{est_cost:.2f}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
