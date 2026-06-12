#!/usr/bin/env python3
"""
video-pipeline-cn 片头片尾动画生成脚本

整合 hf-hyperframes 能力：
1. 生成片头动画（品牌展示 + 标题）
2. 生成片尾动画（CTA + 关注引导）
3. 合成到视频中

用法：
    python3 scripts/generate_intros.py \
        --brand "像素灵境" \
        --title "AI 视频生产指南" \
        --output-dir ~/output/videos/my-video/ \
        --style tech

风格：
    - tech: 科技/技术感（深色背景 + 橙色强调）
    - minimal: 极简（白色背景 + 黑色文字）
    - cinematic: 电影感（渐变背景 + 大字体）
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# ───────────────────────────────────────────
# 配置
# ───────────────────────────────────────────

HYPERFRAMES_DIR = Path.home() / ".openclaw" / "workspace" / "skills" / "hf-hyperframes"

# 风格预设
STYLES = {
    "tech": {
        "bg": "#0a0a0a",
        "accent": "#FF5A00",
        "text": "#ffffff",
        "font": "Menlo, monospace",
        "easing": "power3.out"
    },
    "minimal": {
        "bg": "#ffffff",
        "accent": "#000000",
        "text": "#333333",
        "font": "Helvetica, Arial, sans-serif",
        "easing": "power2.out"
    },
    "cinematic": {
        "bg": "linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)",
        "accent": "#e94560",
        "text": "#ffffff",
        "font": "Georgia, serif",
        "easing": "expo.out"
    }
}


def check_hyperframes():
    """检查 hf-hyperframes 是否安装"""
    if not HYPERFRAMES_DIR.exists():
        print(f"❌ hf-hyperframes 未安装")
        print(f"   期望路径: {HYPERFRAMES_DIR}")
        return False
    
    # 检查 npx hyperframes 是否可用
    result = subprocess.run(["which", "npx"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ npx 不可用（需要 Node.js）")
        return False
    
    print(f"✅ hf-hyperframes 已安装")
    return True


def generate_intro_html(brand, title, style_config, duration=3):
    """生成片头 HTML（HyperFrames 格式）"""
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>片头 - {brand}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: {style_config['bg']};
            color: {style_config['text']};
            font-family: {style_config['font']};
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            overflow: hidden;
        }}
        .scene-content {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            width: 100%;
            height: 100%;
            padding: 120px 160px;
            gap: 24px;
        }}
        .brand {{
            font-size: 48px;
            font-weight: bold;
            color: {style_config['accent']};
            letter-spacing: 8px;
        }}
        .title {{
            font-size: 72px;
            font-weight: bold;
            text-align: center;
            line-height: 1.2;
        }}
        .subtitle {{
            font-size: 32px;
            opacity: 0.8;
            margin-top: 16px;
        }}
        .line {{
            width: 120px;
            height: 4px;
            background: {style_config['accent']};
            margin: 32px 0;
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
</head>
<body>
    <div data-composition-id="intro" data-width="1920" data-height="1080">
        <div class="scene-content">
            <div class="brand">{brand}</div>
            <div class="line"></div>
            <div class="title">{title}</div>
            <div class="subtitle">AI 视频生产指南</div>
        </div>
    </div>
    
    <script>
        window.__timelines = window.__timelines || {{}};
        const tl = gsap.timeline({{ paused: true }});
        
        // 入场动画
        tl.from(".brand", {{ y: 60, opacity: 0, duration: 0.8, ease: "{style_config['easing']}" }}, 0.2);
        tl.from(".line", {{ scaleX: 0, duration: 0.6, ease: "power2.out" }}, 0.6);
        tl.from(".title", {{ y: 40, opacity: 0, duration: 0.7, ease: "{style_config['easing']}" }}, 0.8);
        tl.from(".subtitle", {{ y: 30, opacity: 0, duration: 0.5, ease: "power2.out" }}, 1.0);
        
        // 停留
        tl.to("", {{ duration: 0.5 }}, 1.5);
        
        // 出场（仅最后场景）
        tl.to(".brand", {{ y: -30, opacity: 0, duration: 0.4, ease: "power2.in" }}, 2.2);
        tl.to(".line", {{ scaleX: 0, duration: 0.3, ease: "power2.in" }}, 2.3);
        tl.to(".title", {{ y: -20, opacity: 0, duration: 0.4, ease: "power2.in" }}, 2.4);
        tl.to(".subtitle", {{ y: -15, opacity: 0, duration: 0.3, ease: "power2.in" }}, 2.5);
        
        window.__timelines["intro"] = tl;
    </script>
</body>
</html>"""
    
    return html


def generate_outro_html(brand, cta, style_config, duration=3):
    """生成片尾 HTML（HyperFrames 格式）"""
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>片尾 - {brand}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: {style_config['bg']};
            color: {style_config['text']};
            font-family: {style_config['font']};
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            overflow: hidden;
        }}
        .scene-content {{
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            width: 100%;
            height: 100%;
            padding: 120px 160px;
            gap: 32px;
        }}
        .cta {{
            font-size: 56px;
            font-weight: bold;
            text-align: center;
            line-height: 1.3;
        }}
        .brand {{
            font-size: 36px;
            color: {style_config['accent']};
            letter-spacing: 4px;
        }}
        .follow {{
            font-size: 28px;
            opacity: 0.7;
            margin-top: 16px;
        }}
        .icons {{
            display: flex;
            gap: 24px;
            margin-top: 24px;
        }}
        .icon {{
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: {style_config['accent']};
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 20px;
            color: white;
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
</head>
<body>
    <div data-composition-id="outro" data-width="1920" data-height="1080">
        <div class="scene-content">
            <div class="cta">{cta}</div>
            <div class="brand">{brand}</div>
            <div class="follow">关注获取更多 AI 视频技巧</div>
            <div class="icons">
                <div class="icon">抖</div>
                <div class="icon">红</div>
                <div class="icon">B</div>
            </div>
        </div>
    </div>
    
    <script>
        window.__timelines = window.__timelines || {{}};
        const tl = gsap.timeline({{ paused: true }});
        
        // 入场动画
        tl.from(".cta", {{ y: 50, opacity: 0, duration: 0.7, ease: "{style_config['easing']}" }}, 0.2);
        tl.from(".brand", {{ scale: 0.8, opacity: 0, duration: 0.6, ease: "power2.out" }}, 0.5);
        tl.from(".follow", {{ y: 30, opacity: 0, duration: 0.5, ease: "power2.out" }}, 0.7);
        tl.from(".icons", {{ y: 20, opacity: 0, duration: 0.4, ease: "power2.out" }}, 0.9);
        tl.from(".icon", {{ scale: 0, duration: 0.3, stagger: 0.1, ease: "back.out(1.7)" }}, 1.0);
        
        // 停留
        tl.to("", {{ duration: 0.8 }}, 1.5);
        
        // 出场
        tl.to(".cta", {{ y: -20, opacity: 0, duration: 0.4, ease: "power2.in" }}, 2.3);
        tl.to(".brand", {{ scale: 0.9, opacity: 0, duration: 0.3, ease: "power2.in" }}, 2.4);
        tl.to(".follow", {{ y: -15, opacity: 0, duration: 0.3, ease: "power2.in" }}, 2.5);
        tl.to(".icons", {{ y: -10, opacity: 0, duration: 0.3, ease: "power2.in" }}, 2.6);
        
        window.__timelines["outro"] = tl;
    </script>
</body>
</html>"""
    
    return html


def render_hyperframes(html_content, output_path, duration=3):
    """使用 HyperFrames CLI 渲染 HTML 为 MP4"""
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="hf_render_")
    html_path = Path(temp_dir) / "index.html"
    html_path.write_text(html_content, encoding='utf-8')
    
    print(f"   渲染: {html_path} -> {output_path}")
    
    # 使用 npx hyperframes render
    cmd = [
        "npx", "--yes", "hyperframes", "render",
        "--input", str(html_path),
        "--output", str(output_path),
        "--duration", str(duration)
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
        print(f"   ✅ 渲染成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ 渲染失败: {e.stderr[:200]}")
        return False
    except subprocess.TimeoutExpired:
        print(f"   ⏱️ 渲染超时")
        return False
    finally:
        # 清理临时目录
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def compose_with_intros(main_video, intro_video, outro_video, output_path):
    """将片头、主视频、片尾合成为最终视频"""
    
    print(f"🎬 合成最终视频")
    
    # 创建 concat 列表
    concat_list = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    for video in [intro_video, main_video, outro_video]:
        concat_list.write(f"file '{video}'\n")
    concat_list.close()
    
    # 使用 ffmpeg concat
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list.name,
        "-c", "copy",
        str(output_path)
    ], check=True, capture_output=True)
    
    os.unlink(concat_list.name)
    
    print(f"   ✅ 合成完成: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description='生成片头片尾动画')
    parser.add_argument('--brand', required=True, help='品牌名')
    parser.add_argument('--title', required=True, help='视频标题')
    parser.add_argument('--cta', default="关注获取更多 AI 视频技巧", help='片尾 CTA')
    parser.add_argument('--style', choices=['tech', 'minimal', 'cinematic'], default='tech',
                        help='动画风格')
    parser.add_argument('--output-dir', required=True, help='输出目录')
    parser.add_argument('--main-video', help='主视频路径（可选，提供则合成）')
    parser.add_argument('--duration', type=int, default=3, help='片头/片尾时长（秒）')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🎬 生成片头片尾动画")
    print(f"   品牌: {args.brand}")
    print(f"   标题: {args.title}")
    print(f"   风格: {args.style}")
    
    # 1. 检查依赖
    if not check_hyperframes():
        sys.exit(1)
    
    # 2. 获取风格配置
    style_config = STYLES.get(args.style, STYLES['tech'])
    
    # 3. 生成片头
    print(f"\n🎬 生成片头...")
    intro_html = generate_intro_html(args.brand, args.title, style_config, args.duration)
    intro_path = output_dir / "intro.mp4"
    
    if not render_hyperframes(intro_html, intro_path, args.duration):
        print(f"❌ 片头生成失败")
        sys.exit(1)
    
    # 4. 生成片尾
    print(f"\n🎬 生成片尾...")
    outro_html = generate_outro_html(args.brand, args.cta, style_config, args.duration)
    outro_path = output_dir / "outro.mp4"
    
    if not render_hyperframes(outro_html, outro_path, args.duration):
        print(f"❌ 片尾生成失败")
        sys.exit(1)
    
    # 5. 合成（如果提供了主视频）
    if args.main_video and Path(args.main_video).exists():
        final_path = output_dir / "最终成片_含片头片尾.mp4"
        compose_with_intros(args.main_video, intro_path, outro_path, final_path)
        
        print(f"\n{'='*50}")
        print(f"✅ 完成！")
        print(f"   片头: {intro_path}")
        print(f"   片尾: {outro_path}")
        print(f"   最终: {final_path}")
        print(f"{'='*50}")
    else:
        print(f"\n{'='*50}")
        print(f"✅ 片头片尾生成完成！")
        print(f"   片头: {intro_path}")
        print(f"   片尾: {outro_path}")
        print(f"   （未提供主视频，跳过合成）")
        print(f"{'='*50}")


if __name__ == "__main__":
    main()
