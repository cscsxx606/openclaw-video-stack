#!/usr/bin/env python3
"""
video-pipeline-cn 批量文章→视频生成脚本

批量读取 articles/ 目录下的 .md 文件，自动生成视频。

用法：
    python3 scripts/batch_article_to_video.py \
        --articles-dir ~/output/articles/ \
        --output-dir ~/output/videos/ \
        --budget 20 \
        --max-workers 4 \
        --limit 10

输出：
    - 每篇文章一个视频目录
    - 批量并发生成（max-workers 控制并发数）
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# 添加依赖路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from resolution_advisor import advise_resolution
except ImportError:
    print("❌ 需要 resolution_advisor.py")
    sys.exit(1)


def find_articles(articles_dir, limit=None):
    """查找 articles/ 目录下的 .md 文件"""
    articles_dir = Path(articles_dir)
    if not articles_dir.exists():
        print(f"❌ 目录不存在: {articles_dir}")
        return []
    
    articles = sorted(articles_dir.glob("*.md"))
    
    if limit:
        articles = articles[:limit]
    
    print(f"📚 找到 {len(articles)} 篇文章")
    for i, a in enumerate(articles):
        print(f"   [{i}] {a.name}")
    
    return articles


def generate_video_for_article(article_path, output_dir, budget, max_workers):
    """为单篇文章生成视频"""
    article_name = article_path.stem[:30]  # 限制长度
    video_dir = Path(output_dir) / article_name
    video_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n🎬 处理: {article_path.name}")
    print(f"   输出: {video_dir}")
    
    # 1. 自动选择分辨率
    resolution, workers, est_cost, rec = advise_resolution(budget)
    
    # 2. 调用 one_click_video.py
    one_click_script = Path(__file__).parent / "one_click_video.py"
    
    cmd = [
        "python3", str(one_click_script),
        "--article", str(article_path),
        "--output-dir", str(video_dir),
        "--budget", str(budget),
        "--resolution", resolution,
        "--max-workers", str(workers)
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=1800)
        print(f"   ✅ 完成: {video_dir}/最终成片.mp4")
        return video_dir / "最终成片.mp4"
    except subprocess.CalledProcessError as e:
        print(f"   ❌ 失败: {e.stderr[:200]}")
        return None
    except subprocess.TimeoutExpired:
        print(f"   ⏱️ 超时（30分钟）")
        return None


def batch_generate(articles, output_dir, budget, max_workers, max_parallel=2):
    """
    批量生成视频
    
    max_parallel: 同时处理的文章数（控制总并发）
    """
    print(f"\n📦 批量生成: {len(articles)} 篇文章")
    print(f"   预算: ¥{budget}/篇")
    print(f"   单篇并发: {max_workers} workers")
    print(f"   总并行: {max_parallel} 篇")
    
    results = []
    
    # 串行处理（避免 API rate limit）
    # 如需真正并行，可用 ThreadPoolExecutor
    for i, article in enumerate(articles):
        print(f"\n{'='*50}")
        print(f"[{i+1}/{len(articles)}] {article.name}")
        print(f"{'='*50}")
        
        start_time = time.time()
        result = generate_video_for_article(article, output_dir, budget, max_workers)
        elapsed = time.time() - start_time
        
        results.append({
            "article": article.name,
            "video": str(result) if result else None,
            "elapsed": elapsed,
            "success": result is not None
        })
        
        # 间隔 5s，避免 API rate limit
        if i < len(articles) - 1:
            print(f"\n⏳ 间隔 5s...")
            time.sleep(5)
    
    return results


def generate_report(results, output_dir):
    """生成批量报告"""
    report_path = Path(output_dir) / "batch_report.json"
    
    total = len(results)
    success = sum(1 for r in results if r["success"])
    failed = total - success
    total_time = sum(r["elapsed"] for r in results)
    
    report = {
        "total": total,
        "success": success,
        "failed": failed,
        "total_time": total_time,
        "avg_time": total_time / total if total > 0 else 0,
        "results": results
    }
    
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    
    print(f"\n{'='*50}")
    print(f"📊 批量生成报告")
    print(f"{'='*50}")
    print(f"   总计: {total} 篇")
    print(f"   ✅ 成功: {success}")
    print(f"   ❌ 失败: {failed}")
    print(f"   ⏱️ 总耗时: {total_time:.1f}s ({total_time/60:.1f}min)")
    print(f"   ⏱️ 平均每篇: {total_time/total:.1f}s" if total > 0 else "")
    print(f"   📄 报告: {report_path}")
    print(f"{'='*50}")
    
    return report


def main():
    parser = argparse.ArgumentParser(description='批量文章→视频生成')
    parser.add_argument('--articles-dir', default="~/output/articles/", help='文章目录')
    parser.add_argument('--output-dir', default="~/output/videos/batch/", help='输出目录')
    parser.add_argument('--budget', type=float, default=20, help='每篇预算（元）')
    parser.add_argument('--max-workers', type=int, default=4, help='单篇并发 workers')
    parser.add_argument('--max-parallel', type=int, default=1, help='同时处理的文章数')
    parser.add_argument('--limit', type=int, help='最多处理几篇')
    
    args = parser.parse_args()
    
    articles_dir = Path(args.articles_dir).expanduser()
    output_dir = Path(args.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🎬 批量文章→视频生成")
    print(f"   文章目录: {articles_dir}")
    print(f"   输出目录: {output_dir}")
    print(f"   预算: ¥{args.budget}/篇")
    
    # 1. 查找文章
    articles = find_articles(articles_dir, args.limit)
    if not articles:
        print("❌ 没有找到文章")
        sys.exit(1)
    
    # 2. 批量生成
    results = batch_generate(
        articles, output_dir, args.budget, args.max_workers, args.max_parallel
    )
    
    # 3. 生成报告
    report = generate_report(results, output_dir)
    
    # 4. 输出成功列表
    print(f"\n✅ 成功视频列表:")
    for r in results:
        if r["success"]:
            print(f"   📹 {r['video']}")


if __name__ == "__main__":
    main()
