#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seedance 批量并发提交/等待脚本
核心：把 N 个独立视频任务并发丢给 API，max_workers 控制并发度，所有完成后按顺序输出。

用法：
  # 1) 简单批量（从 JSON 文件读）
  python3 batch.py --config tasks.json --max-workers 3 --download ~/Desktop

  # 2) 命令行内联（不便写文件时）
  python3 batch.py --prompt "prompt A" --prompt "prompt B" --max-workers 2

  # 3) 纯成本预估（不发请求）
  python3 batch.py --config tasks.json --dry-run

tasks.json 格式（每条对应一个视频任务）：
  [
    {
      "prompt": "...",
      "ratio": "9:16", "duration": 15, "resolution": "1080p",
      "image": "first_frame.jpg" (可选),
      "video": "ref.mp4" (可选，用于参考延长),
      "service_tier": "flex" (可选, "default"|"flex"),
      "draft": false (可选, 1.5 Pro 才支持),
      "model": "doubao-seedance-2-0-260128" (可选)
    },
    ...
  ]

设计要点：
- 提交与轮询解耦：先并发提交得到 task_ids，再并发等待
- task_id 全部入 SQLite，崩溃后可恢复
- 失败任务默认重试 1 次（避免网络抖动白扔钱）
- 输出：results.json 含每个 task 的 status/video_url/local_path
"""

import argparse
import concurrent.futures
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# 共用 seedance.py 的底层能力
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from db import TaskDB
    _DB = True
except ImportError:
    _DB = False

# 从 seedance.py 导入底层调用函数（避免重复实现）
import seedance


def submit_one(index, task_cfg, project, batch_id, max_retries=1, _mock=None):
    """
    提交单个视频任务。返回 (index, task_id_or_None, error_msg_or_None)

    实现方式：直接调 seedance.api_request() + db.insert()，
    跳过 CLI 子进程（更快 + 更易控并发）。

    _mock: 测调用。传入一个函数 (method, url, body) -> dict 代替真 API。
    """
    prompt = task_cfg.get("prompt")
    if not prompt:
        return index, None, "缺少 prompt"

    # 构建 content 数组（参考 seedance.cmd_create 的逻辑）
    content = []
    try:
        if task_cfg.get("image"):
            # 首帧图
            if task_cfg["image"].startswith(("http://", "https://", "data:")):
                image_url = task_cfg["image"]
            else:
                image_url = seedance.image_to_data_url(task_cfg["image"])
            content.append({"type": "image_url", "image_url": {"url": image_url}, "role": "first_frame"})
            if task_cfg.get("last_frame"):
                lf = task_cfg["last_frame"]
                if not lf.startswith(("http://", "https://", "data:")):
                    lf = seedance.image_to_data_url(lf)
                content.append({"type": "image_url", "image_url": {"url": lf}, "role": "last_frame"})

        if task_cfg.get("ref_images"):
            for img in task_cfg["ref_images"]:
                if not img.startswith(("http://", "https://", "data:")):
                    img = seedance.image_to_data_url(img)
                content.append({"type": "image_url", "image_url": {"url": img}, "role": "reference_image"})

        if task_cfg.get("video"):
            for v in task_cfg["video"] if isinstance(task_cfg["video"], list) else [task_cfg["video"]]:
                if not v.startswith(("http://", "https://", "data:")):
                    v = seedance.file_to_data_url(v, "video")
                content.append({"type": "video_url", "video_url": {"url": v}, "role": task_cfg.get("video_role", "reference_video")})

        if task_cfg.get("audio"):
            for a in task_cfg["audio"] if isinstance(task_cfg["audio"], list) else [task_cfg["audio"]]:
                if not a.startswith(("http://", "https://", "data:")):
                    a = seedance.file_to_data_url(a, "audio")
                content.append({"type": "audio_url", "audio_url": {"url": a}})
    except (FileNotFoundError, ValueError) as e:
        # 文件不存在/过大：让 submit_one 返回错误，不重试
        return index, None, str(e)

    if prompt:
        content.insert(0, {"type": "text", "text": prompt})

    body = {"model": task_cfg.get("model", seedance.DEFAULT_MODEL), "content": content}
    for k in ("ratio", "duration", "resolution", "seed", "camera_fixed", "watermark",
              "generate_audio", "draft", "return_last_frame", "frames",
              "execution_expires_after", "callback_url"):
        if k in task_cfg and task_cfg[k] is not None:
            body[k] = task_cfg[k]
    # service_tier: 只在显式 'flex' 时发送（其他模型可能不支持，空值会报 400）
    if task_cfg.get("service_tier") == "flex":
        body["service_tier"] = "flex"

    # 重试
    last_err = None
    api_fn = _mock or seedance.api_request
    for attempt in range(max_retries + 1):
        try:
            result = api_fn("POST", seedance.BASE_URL, body)
            task_id = result.get("id", "")
            if not task_id:
                last_err = f"API 返回无 id: {result}"
                continue

            # 入库
            if _DB:
                try:
                    db = TaskDB()
                    db.insert(
                        task_id,
                        project=project,
                        prompt=prompt,
                        batch_id=batch_id,
                        batch_index=index,
                        image=task_cfg.get("image"),
                        video=(task_cfg["video"] if isinstance(task_cfg.get("video"), str)
                               else (task_cfg["video"][0] if task_cfg.get("video") else None)),
                        model=task_cfg.get("model"),
                        ratio=task_cfg.get("ratio"),
                        duration=task_cfg.get("duration"),
                        resolution=task_cfg.get("resolution"),
                        service_tier=task_cfg.get("service_tier"),
                        draft=task_cfg.get("draft"),
                        seed=task_cfg.get("seed"),
                    )
                except Exception as e:
                    print(f"  ⚠️  入库失败: {e}", file=sys.stderr)

            return index, task_id, None
        except seedance.SeedanceAPIError as e:
            # API 错误：某些错误可重试（429/5xx），某些不可（400/401/403）
            retryable = e.status_code in (408, 429, 500, 502, 503, 504)
            last_err = f"API Error (HTTP {e.status_code}): {e.message}"
            if not retryable or attempt >= max_retries:
                return index, None, last_err
            time.sleep(2)
        except seedance.SeedanceNetworkError as e:
            last_err = f"Network Error: {e}"
            if attempt >= max_retries:
                return index, None, last_err
            time.sleep(2)
        except Exception as e:
            last_err = str(e)
            if attempt >= max_retries:
                return index, None, last_err
            time.sleep(2)

    return index, None, last_err


def wait_one(task_id, project=None, download_dir=None, interval=15, max_wait=1800):
    """
    等待单个任务完成。复用 seedance.cmd_wait_logic。
    返回 (task_id, video_url_or_None, local_path_or_None, error_msg)
    """
    try:
        # 复用 seedance 的轮询 + 下载 + 入库逻辑
        result = seedance.cmd_wait_logic(task_id, interval=interval,
                                         download_dir=download_dir, project=project,
                                         max_wait=max_wait)
        if result and result.get("status") == "succeeded":
            video_url = result.get("content", {}).get("video_url", "")
            # 从 DB 取 local_path
            local_path = None
            if _DB:
                try:
                    t = TaskDB().get(task_id)
                    local_path = t.get("local_path") if t else None
                except Exception:
                    pass
            return task_id, video_url, local_path, None
        return task_id, None, None, "未知状态"
    except SystemExit as e:
        # cmd_wait_logic 超时/失败时 exit 1
        return task_id, None, None, f"等待被中断 (exit={e.code})"
    except Exception as e:
        return task_id, None, None, str(e)


def estimate_total(tasks):
    """纯本地估算，不发请求"""
    from db import estimate_cost
    total = 0
    for i, t in enumerate(tasks):
        c = estimate_cost(
            duration=t.get("duration", 15),
            has_video_input=bool(t.get("video")),
            flex=t.get("service_tier") == "flex",
            draft=bool(t.get("draft")),
            resolution=t.get("resolution", "1080p"),
        )
        total += c
        print(f"  [{i}] {c:>6.2f}元  ({t.get('duration', 15)}s "
              f"{t.get('resolution', '1080p')}, "
              f"{'参考延长' if t.get('video') else '文生'}"
              f"{', flex' if t.get('service_tier') == 'flex' else ''}"
              f"{', draft' if t.get('draft') else ''})")
    print(f"\n  合计: {total:.2f}元")
    return total


def main():
    parser = argparse.ArgumentParser(description="Seedance 批量并发提交/等待")
    parser.add_argument("--config", help="JSON 配置文件路径（任务列表）")
    parser.add_argument("--prompt", action="append", help="内联 prompt（可多次传）")
    parser.add_argument("--ratio", default="9:16")
    parser.add_argument("--duration", type=int, default=15)
    parser.add_argument("--resolution", default="1080p")
    parser.add_argument("--service-tier", choices=["default", "flex"], default="default")
    parser.add_argument("--draft", action="store_true", help="草稿模式（低成本预览）")
    parser.add_argument("--model", default=None, help="模型 ID（覆盖 config）")
    parser.add_argument("--project", help="项目名（登记用）")
    parser.add_argument("--batch-id", help="批次 ID（默认自动生成）")
    parser.add_argument("--max-workers", type=int, default=3, help="并发度（默认 3）")
    parser.add_argument("--interval", type=int, default=15, help="轮询间隔秒")
    parser.add_argument("--download", help="下载目录")
    parser.add_argument("--max-wait", type=int, default=1800, help="单个任务最长等待秒")
    parser.add_argument("--dry-run", action="store_true", help="仅估算成本，不发请求")
    parser.add_argument("--output", default="results.json", help="结果输出文件")
    args = parser.parse_args()

    # 解析任务
    if args.config:
        with open(args.config) as f:
            tasks = json.load(f)
        if not isinstance(tasks, list):
            print("config 必须是任务列表", file=sys.stderr)
            sys.exit(1)
        # CLI 全局参数会覆盖 config 里的同名 key（如果 config 里未设）
        for t in tasks:
            if "ratio" not in t: t["ratio"] = args.ratio
            if "duration" not in t: t["duration"] = args.duration
            if "resolution" not in t: t["resolution"] = args.resolution
            if "service_tier" not in t: t["service_tier"] = args.service_tier
            if "draft" not in t: t["draft"] = args.draft
            if args.model and "model" not in t: t["model"] = args.model
    elif args.prompt:
        # 内联模式：每个 --prompt 对应一个任务
        tasks = []
        for p in args.prompt:
            tasks.append({
                "prompt": p,
                "ratio": args.ratio,
                "duration": args.duration,
                "resolution": args.resolution,
                "service_tier": args.service_tier,
                "draft": args.draft,
                "model": args.model,
            })
    else:
        parser.error("需要 --config 或至少一个 --prompt")

    print(f"📦 共 {len(tasks)} 个任务  并发度={args.max_workers}  项目={args.project or '-'}")
    if args.service_tier == "flex":
        print("  ⚡ 离线模式（flex）— 价格 5 折，可能排队")
    if args.draft:
        print("  📝 草稿模式（draft）— 低成本预览")
    print()

    # 干跑
    if args.dry_run:
        print("💰 成本预估：")
        estimate_total(tasks)
        return

    # 生成 batch_id
    batch_id = args.batch_id or f"batch-{int(time.time())}"
    print(f"🆔 批次 ID: {batch_id}\n")

    # 阶段 1：并发提交
    print("=" * 60)
    print("📤 阶段 1/2：并发提交任务")
    print("=" * 60)
    t_submit_start = time.time()
    submit_results = []  # [(index, task_id, error)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futures = {
            ex.submit(submit_one, i, t, args.project, batch_id): i
            for i, t in enumerate(tasks)
        }
        for fut in concurrent.futures.as_completed(futures):
            idx, task_id, err = fut.result()
            submit_results.append((idx, task_id, err))
            if err:
                print(f"  [{idx}] ❌ 提交失败: {err}")
            else:
                print(f"  [{idx}] ✅ {task_id}")

    # 按 index 排序
    submit_results.sort(key=lambda x: x[0])
    task_ids = [(idx, tid) for idx, tid, err in submit_results if tid]
    failed_submit = [(idx, err) for idx, tid, err in submit_results if not tid]

    print(f"\n  提交完成: {len(task_ids)} 成功 / {len(failed_submit)} 失败")
    print(f"  提交耗时: {time.time() - t_submit_start:.1f}s\n")

    if not task_ids:
        print("❌ 所有任务都提交失败，退出")
        sys.exit(1)

    # 阶段 2：并发等待
    print("=" * 60)
    print("⏳ 阶段 2/2：并发等待完成（轮询中）")
    print("=" * 60)
    t_wait_start = time.time()
    wait_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        futures = {
            ex.submit(wait_one, tid, args.project, args.download,
                      args.interval, args.max_wait): idx
            for idx, tid in task_ids
        }
        for fut in concurrent.futures.as_completed(futures):
            idx = futures[fut]
            try:
                task_id, video_url, local_path, err = fut.result()
            except Exception as e:
                task_id, video_url, local_path, err = None, None, None, str(e)

            wait_results.append({
                "index": idx,
                "task_id": task_id,
                "video_url": video_url,
                "local_path": local_path,
                "error": err,
            })
            if err:
                print(f"  [{idx}] ❌ 等待失败: {err}")
            else:
                path_short = local_path.split("/")[-1] if local_path else "-"
                print(f"  [{idx}] ✅ {task_id}  →  {path_short}")

    wait_results.sort(key=lambda x: x["index"])
    elapsed = time.time() - t_wait_start

    # 汇总
    print("\n" + "=" * 60)
    print("📊 汇总")
    print("=" * 60)
    success = [r for r in wait_results if r["video_url"]]
    failed = [r for r in wait_results if r["error"]]
    print(f"  成功: {len(success)}/{len(wait_results)}")
    print(f"  失败: {len(failed)}")
    print(f"  等待耗时: {elapsed:.1f}s  ({elapsed/60:.1f} min)")
    if args.max_workers > 1 and len(success) > 1:
        # 估算串行需要的时间 vs 实际（粗略）
        print(f"  💡 理论串行时间 ≈ {len(success) * 5}min（按 5min/条估算）")
    if _DB:
        try:
            stats = TaskDB().stats(project=args.project)
            total = sum(s.get("est_total") or 0 for s in stats)
            print(f"  💰 项目累计估算成本: ¥{total:.2f}")
        except Exception:
            pass

    # 写 results.json
    output = {
        "batch_id": batch_id,
        "project": args.project,
        "config": {
            "max_workers": args.max_workers,
            "service_tier": args.service_tier,
            "draft": args.draft,
        },
        "elapsed_sec": round(elapsed, 1),
        "results": wait_results,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n💾 结果已保存到: {args.output}")
    print(f"📊 批次详情查询: python3 seedance.py db batch {batch_id}")


if __name__ == "__main__":
    main()
