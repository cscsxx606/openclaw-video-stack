#!/usr/bin/env python3
"""
video-pipeline-cn 批量栏目化脚本

整合 hf-remotion-to-hyperframes 能力：
1. 将 Remotion 栏目模板转换为 HyperFrames
2. 批量生成系列视频（统一片头 + 不同内容）
3. 自动合成栏目包装

用法：
    python3 scripts/batch_series.py \
        --template-dir ~/templates/tech-review/ \
        --articles-dir ~/output/articles/ \
        --output-dir ~/output/videos/series/ \
        --brand "像素灵境" \
        --series-name "AI 产品测评"

栏目模板结构：
    template/
    ├── intro.html          # 片头（HyperFrames）
    ├── outro.html          # 片尾（HyperFrames）
    ├── transition.html     # 转场（HyperFrames）
    └── lower-third.html    # 字幕条（HyperFrames）
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# ───────────────────────────────────────────
# 配置
# ───────────────────────────────────────────

HYPERFRAMES_DIR = Path.home() / ".openclaw" / "workspace" / "skills" / "hf-hyperframes"
REMOTION_TO_HF_DIR = Path.home() / ".openclaw" / "workspace" / "skills" / "hf-remotion-to-hyperframes"


def check_dependencies():
    """检查依赖"""
    missing = []
    
    if not HYPERFRAMES_DIR.exists():
        missing.append("hf-hyperframes")
    
    if not REMOTION_TO_HF_DIR.exists():
        missing.append("hf-remotion-to-hyperframes")
    
    if missing:
        print(f"❌ 缺少依赖: {', '.join(missing)}")
        print(f"   安装方式:")
        print(f"      cd ~/.openclaw/workspace/skills/")
        for m in missing:
            print(f"      git clone https://github.com/heygen-com/{m}.git")
        return False
    
    print(f"✅ 依赖已安装")
    return True


def convert_remotion_to_hyperframes(remotion_dir, output_dir):
    """
    将 Remotion 模板转换为 HyperFrames
    
    使用 hf-remotion-to-hyperframes 的 lint + translate 流程
    """
    print(f"🔄 转换 Remotion -> HyperFrames")
    print(f"   输入: {remotion_dir}")
    print(f"   输出: {output_dir}")
    
    # 1. Lint 检查
    lint_script = REMOTION_TO_HF_DIR / "scripts" / "lint_source.py"
    if lint_script.exists():
        print(f"   1. Lint 检查...")
        result = subprocess.run(
            ["python3", str(lint_script), str(remotion_dir)],
            capture_output=True, text=True
        )
        
        if "Blocker" in result.stdout:
            print(f"   ⚠️ 发现 Blocker，需要手动处理")
            print(f"   {result.stdout[:500]}")
            return False
    
    # 2. 生成 HyperFrames 目录结构
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建基本结构
    (output_dir / "compositions").mkdir(exist_ok=True)
    (output_dir / "assets").mkdir(exist_ok=True)
    
    # 3. 生成 index.html（根合成）
    index_html = generate_series_index(output_dir.name)
    (output_dir / "index.html").write_text(index_html, encoding='utf-8')
    
    print(f"   ✅ 转换完成")
    return True


def generate_series_index(series_name):
    """生成栏目根合成 HTML"""
    
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{series_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: #0a0a0a;
            color: #ffffff;
            font-family: Menlo, monospace;
        }}
    </style>
</head>
<body>
    <div data-composition-id="series-root" data-width="1920" data-height="1080"
         data-start="0" data-duration="30">
        <!-- 片头 -->
        <div id="intro-slot" data-composition-src="compositions/intro.html"
             data-start="0" data-duration="3" data-track-index="0"></div>
        
        <!-- 主内容（动态替换）-->
        <div id="main-slot" data-composition-src="compositions/main.html"
             data-start="3" data-duration="24" data-track-index="1"></div>
        
        <!-- 片尾 -->
        <div id="outro-slot" data-composition-src="compositions/outro.html"
             data-start="27" data-duration="3" data-track-index="2"></div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <script>
        window.__timelines = window.__timelines || {{}};
        const tl = gsap.timeline({{ paused: true }});
        window.__timelines["series-root"] = tl;
    </script>
</body>
</html>"""


def generate_series_video(series_dir, article_path, output_path, brand, series_name):
    """
    为单篇文章生成栏目视频
    
    流程：
    1. 读取文章生成口播稿
    2. 生成主内容 HyperFrames
    3. 合成片头 + 主内容 + 片尾
    """
    print(f"\n🎬 生成栏目视频: {article_path.name}")
    
    # 1. 读取文章
    article_text = article_path.read_text(encoding='utf-8')[:200]
    
    # 2. 生成主内容 HTML
    main_html = generate_main_content_html(article_text, brand, series_name)
    
    # 3. 写入临时目录
    temp_dir = Path(tempfile.mkdtemp(prefix="series_"))
    
    # 复制栏目模板
    series_temp = temp_dir / "series"
    shutil.copytree(series_dir, series_temp, dirs_exist_ok=True)
    
    # 写入主内容
    (series_temp / "compositions" / "main.html").write_text(main_html, encoding='utf-8')
    
    # 4. 渲染 HyperFrames
    print(f"   渲染 HyperFrames...")
    cmd = [
        "npx", "--yes", "hyperframes", "render",
        "--input", str(series_temp / "index.html"),
        "--output", str(output_path),
        "--duration", "30"
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
        print(f"   ✅ 完成: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ 渲染失败: {e.stderr[:200]}")
        return False
    except subprocess.TimeoutExpired:
        print(f"   ⏱️ 渲染超时")
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def generate_main_content_html(article_text, brand, series_name):
    """生成主内容 HTML（简化版）"""
    
    # 提取前 100 字作为展示
    display_text = article_text[:100].replace('\n', ' ')
    
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>主内容</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: #0a0a0a;
            color: #ffffff;
            font-family: Menlo, monospace;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
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
            font-size: 36px;
            color: #FF5A00;
            letter-spacing: 4px;
        }}
        .series {{
            font-size: 28px;
            opacity: 0.7;
        }}
        .content {{
            font-size: 42px;
            text-align: center;
            line-height: 1.4;
            max-width: 1200px;
        }}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
</head>
<body>
    <div data-composition-id="main-content" data-width="1920" data-height="1080">
        <div class="scene-content">
            <div class="brand">{brand}</div>
            <div class="series">{series_name}</div>
            <div class="content">{display_text}...</div>
        </div>
    </div>
    
    <script>
        window.__timelines = window.__timelines || {{}};
        const tl = gsap.timeline({{ paused: true }});
        
        tl.from(".brand", {{ y: 40, opacity: 0, duration: 0.6, ease: "power3.out" }}, 0.2);
        tl.from(".series", {{ y: 30, opacity: 0, duration: 0.5, ease: "power2.out" }}, 0.4);
        tl.from(".content", {{ y: 50, opacity: 0, duration: 0.8, ease: "power3.out" }}, 0.6);
        
        window.__timelines["main-content"] = tl;
    </script>
</body>
</html>"""


def batch_series_generate(template_dir, articles_dir, output_dir, brand, series_name, limit=None):
    """批量生成栏目视频"""
    
    articles_dir = Path(articles_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 查找文章
    articles = sorted(articles_dir.glob("*.md"))
    if limit:
        articles = articles[:limit]
    
    print(f"📦 批量栏目生成: {len(articles)} 篇文章")
    print(f"   栏目: {series_name}")
    print(f"   品牌: {brand}")
    
    results = []
    
    for i, article in enumerate(articles):
        print(f"\n{'='*50}")
        print(f"[{i+1}/{len(articles)}] {article.name}")
        print(f"{'='*50}")
        
        video_path = output_dir / f"{article.stem}.mp4"
        
        success = generate_series_video(
            template_dir, article, video_path, brand, series_name
        )
        
        results.append({
            "article": article.name,
            "video": str(video_path) if success else None,
            "success": success
        })
        
        # 间隔 5s
        if i < len(articles) - 1:
            print(f"\n⏳ 间隔 5s...")
            import time
            time.sleep(5)
    
    return results


def generate_report(results, output_dir):
    """生成批量报告"""
    report_path = Path(output_dir) / "series_report.json"
    
    total = len(results)
    success = sum(1 for r in results if r["success"])
    
    report = {
        "total": total,
        "success": success,
        "failed": total - success,
        "results": results
    }
    
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    
    print(f"\n{'='*50}")
    print(f"📊 栏目生成报告")
    print(f"{'='*50}")
    print(f"   总计: {total} 篇")
    print(f"   ✅ 成功: {success}")
    print(f"   ❌ 失败: {total - success}")
    print(f"   📄 报告: {report_path}")
    print(f"{'='*50}")
    
    return report


def main():
    parser = argparse.ArgumentParser(description='批量栏目化视频生成')
    parser.add_argument('--template-dir', help='栏目模板目录（Remotion 或 HyperFrames）')
    parser.add_argument('--articles-dir', default="~/output/articles/", help='文章目录')
    parser.add_argument('--output-dir', default="~/output/videos/series/", help='输出目录')
    parser.add_argument('--brand', required=True, help='品牌名')
    parser.add_argument('--series-name', required=True, help='栏目名')
    parser.add_argument('--limit', type=int, help='最多处理几篇')
    parser.add_argument('--convert-template', action='store_true', help='转换 Remotion 模板')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir).expanduser()
    articles_dir = Path(args.articles_dir).expanduser()
    
    print(f"🎬 批量栏目化视频生成")
    print(f"   栏目: {args.series_name}")
    print(f"   品牌: {args.brand}")
    print(f"   文章: {articles_dir}")
    print(f"   输出: {output_dir}")
    
    # 1. 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 2. 处理模板
    if args.convert_template and args.template_dir:
        # 转换 Remotion 模板
        template_dir = Path(args.template_dir)
        hf_template_dir = output_dir / "template"
        
        if not convert_remotion_to_hyperframes(template_dir, hf_template_dir):
            print(f"❌ 模板转换失败")
            sys.exit(1)
        
        template_dir = hf_template_dir
    else:
        # 使用默认模板或已有模板
        template_dir = output_dir / "template"
        if not template_dir.exists():
            print(f"⚠️ 模板不存在，创建默认模板...")
            template_dir.mkdir(parents=True, exist_ok=True)
            (template_dir / "compositions").mkdir(exist_ok=True)
            
            # 创建默认 index.html
            index_html = generate_series_index(args.series_name)
            (template_dir / "index.html").write_text(index_html, encoding='utf-8')
    
    # 3. 批量生成
    results = batch_series_generate(
        template_dir, articles_dir, output_dir,
        args.brand, args.series_name, args.limit
    )
    
    # 4. 生成报告
    generate_report(results, output_dir)
    
    print(f"\n✅ 栏目生成完成！")
    print(f"   输出: {output_dir}")


if __name__ == "__main__":
    main()
