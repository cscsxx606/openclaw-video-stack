#!/usr/bin/env python3
"""
Seedance 视频生成 CLI（Volcengine Ark API）
用法见本 skill 的 SKILL.md「API 生成」一节。

  python3 seedance.py create --prompt "描述" [options]
  python3 seedance.py create --prompt "描述" --image img.jpg [options]
  python3 seedance.py create --prompt "描述" --image first.jpg --last-frame last.jpg [options]
  python3 seedance.py create --prompt "描述" --ref-images ref1.jpg ref2.jpg [options]
  python3 seedance.py create --prompt "描述" --video motion_ref.mp4 [options]
  python3 seedance.py create --prompt "描述" --audio bgm.mp3 [options]
  python3 seedance.py create --draft-task-id <task_id> [options]
  python3 seedance.py status <task_id>
  python3 seedance.py wait <task_id> [--interval 15] [--download DIR]
  python3 seedance.py list [--status succeeded] [--page 1] [--page-size 10]
  python3 seedance.py delete <task_id>

# 任务持久化：默认写入 SQLite 任务登记册（~/.openclaw/workspace/data/seedance_tasks.db）
# 跳过登记请加 --no-db；指定项目名便于分类查询 --project <name>
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# 任务登记册（可选；导入失败时不影响主功能）
try:
    from db import TaskDB
    _DB_AVAILABLE = True
except ImportError:
    _DB_AVAILABLE = False
    TaskDB = None


BASE_URL = "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks"
DEFAULT_MODEL = "doubao-seedance-2-0-260128"


def get_api_key():
    key = os.environ.get("ARK_API_KEY")
    if not key:
        print("Error: ARK_API_KEY environment variable is not set.", file=sys.stderr)
        print("Set it with: export ARK_API_KEY='your-api-key-here'", file=sys.stderr)
        sys.exit(1)
    return key


def api_request(method, url, data=None):
    """Make an API request and return parsed JSON response."""
    api_key = get_api_key()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp_body = resp.read().decode("utf-8")
            if resp_body:
                return json.loads(resp_body)
            return {}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        try:
            error_json = json.loads(error_body)
            error_msg = error_json.get("error", {}).get("message", error_body)
        except json.JSONDecodeError:
            error_msg = error_body
        # raise 而非 sys.exit：让调用方（batch 重试 / cmd_create CLI）决定如何处理
        raise SeedanceAPIError(e.code, error_msg) from e
    except urllib.error.URLError as e:
        raise SeedanceNetworkError(e.reason) from e


class SeedanceAPIError(Exception):
    """Seedance API 返回的错误（4xx/5xx）"""
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error (HTTP {status_code}): {message}")


class SeedanceNetworkError(Exception):
    """网络错误（超时、连接失败等）"""
    pass


def image_to_data_url(image_path):
    """Convert a local image file to a base64 data URL."""
    p = Path(image_path)
    if not p.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    ext = p.suffix.lower().lstrip(".")
    mime_map = {
        "jpg": "jpeg", "jpeg": "jpeg", "png": "png",
        "webp": "webp", "bmp": "bmp", "tiff": "tiff",
        "tif": "tiff", "gif": "gif", "heic": "heic", "heif": "heif",
    }
    mime_ext = mime_map.get(ext, ext)

    file_size = p.stat().st_size
    if file_size > 30 * 1024 * 1024:
        raise ValueError(f"Image file too large ({file_size / 1024 / 1024:.1f} MB). Max 30 MB.")

    with open(p, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    return f"data:image/{mime_ext};base64,{b64}"


def resolve_image(image_input):
    """Resolve image input to a URL or data URL. Accepts URL or local file path."""
    if image_input.startswith(("http://", "https://", "data:")):
        return image_input
    return image_to_data_url(image_input)


def file_to_data_url(file_path, media_type):
    """Convert a local file to a base64 data URL. media_type: 'video' or 'audio'."""
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"{media_type.title()} file not found: {file_path}")

    max_size = {"video": 50, "audio": 15}.get(media_type, 50)
    file_size = p.stat().st_size
    if file_size > max_size * 1024 * 1024:
        raise ValueError(f"{media_type.title()} file too large ({file_size / 1024 / 1024:.1f} MB). Max {max_size} MB.")

    mime, _ = mimetypes.guess_type(str(p))
    if not mime:
        ext_map = {
            "mp4": "video/mp4", "mov": "video/quicktime", "webm": "video/webm",
            "mp3": "audio/mpeg", "wav": "audio/wav", "ogg": "audio/ogg",
        }
        mime = ext_map.get(p.suffix.lower().lstrip("."), f"{media_type}/octet-stream")

    with open(p, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    return f"data:{mime};base64,{b64}"


def resolve_media(media_input, media_type):
    """Resolve media input (video/audio) to URL or data URL."""
    if media_input.startswith(("http://", "https://", "data:")):
        return media_input
    return file_to_data_url(media_input, media_type)


def cmd_create(args):
    """Create a video generation task."""
    content = []

    if args.draft_task_id:
        content.append({
            "type": "draft_task",
            "draft_task": {"id": args.draft_task_id}
        })
    else:
        if args.prompt:
            content.append({"type": "text", "text": args.prompt})

        if args.ref_images:
            for img in args.ref_images:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": resolve_image(img)},
                    "role": "reference_image"
                })
        elif args.image:
            content.append({
                "type": "image_url",
                "image_url": {"url": resolve_image(args.image)},
                "role": "first_frame"
            })
            if args.last_frame:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": resolve_image(args.last_frame)},
                    "role": "last_frame"
                })

        if args.video:
            video_role = getattr(args, 'video_role', 'reference_video')
            for v in args.video:
                content.append({
                    "type": "video_url",
                    "video_url": {"url": resolve_media(v, "video")},
                    "role": video_role
                })

        if args.audio:
            for a in args.audio:
                content.append({
                    "type": "audio_url",
                    "audio_url": {"url": resolve_media(a, "audio")}
                })

    if not content:
        print("Error: Must provide --prompt, --image, --video, --audio, or --draft-task-id.", file=sys.stderr)
        sys.exit(1)

    body = {
        "model": args.model,
        "content": content,
    }

    # 过滤掉 service_tier 以外的可选参数
    for k in ("ratio", "duration", "resolution", "seed", "camera_fixed",
              "watermark", "generate_audio", "draft", "return_last_frame",
              "frames", "execution_expires_after"):
        v = getattr(args, k, None)
        if v is not None:
            body[k] = v
    if getattr(args, 'callback_url', None):
        body["callback_url"] = args.callback_url
    # service_tier 特殊处理：仅 "flex" 才发送（Seedance 2.0 不支持该字段）
    if args.service_tier == "flex":
        body["service_tier"] = "flex"

    result = api_request("POST", BASE_URL, body)
    task_id = result.get("id", "")

    # 写入任务登记册（默认开启，--no-db 禁用）
    if _DB_AVAILABLE and not getattr(args, "no_db", False):
        try:
            db = TaskDB()
            task_kwargs = {
                "image": args.image,
                "video": args.video[0] if args.video else None,
                "audio": args.audio[0] if args.audio else None,
                "ref_images": args.ref_images,
                "draft_task_id": args.draft_task_id,
                "model": args.model,
                "ratio": args.ratio,
                "duration": args.duration,
                "resolution": args.resolution,
                "service_tier": args.service_tier,
                "draft": args.draft,
                "seed": args.seed,
                "generate_audio": args.generate_audio,
                "watermark": args.watermark,
            }
            db.insert(
                task_id,
                project=getattr(args, "project", None),
                prompt=args.prompt,
                **task_kwargs,
            )
            est_cost = db.get(task_id).get("cost_estimate", 0)
            print(f"📝 已登记到任务册 (project={args.project or '-'}  预估 ¥{est_cost})", file=sys.stderr)
        except Exception as e:
            print(f"⚠️  任务登记失败（不影响主流程）: {e}", file=sys.stderr)

    print(json.dumps({"task_id": task_id, "status": "created", "response": result}, indent=2))

    if args.wait:
        return cmd_wait_logic(task_id, args.interval or 15, args.download,
                               project=getattr(args, "project", None),
                               max_wait=getattr(args, "max_wait", 1800) or 1800)

    return task_id


def cmd_status(args):
    """Query task status."""
    url = f"{BASE_URL}/{args.task_id}"
    result = api_request("GET", url)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def cmd_wait_logic(task_id, interval=15, download_dir=None, project=None, max_wait=1800):
    """Wait for task completion, optionally download result.

    Args:
        max_wait: 单个任务最长等待秒（默认 30 分钟）。超时后退出 1，不入 DB 'expired' 状态。
    """
    url = f"{BASE_URL}/{task_id}"
    print(f"Waiting for task {task_id} to complete (polling every {interval}s, max {max_wait}s)...")

    # 标记 running
    if _DB_AVAILABLE:
        try:
            TaskDB().update_status(task_id, "running")
        except Exception:
            pass

    start_ts = time.time()
    while True:
        if time.time() - start_ts > max_wait:
            print(f"\n⏱️  超时（>{max_wait}s），退出等待。任务在远端仍在 running。")
            print(f"   可稍后: python3 seedance.py status {task_id}")
            sys.exit(1)
        result = api_request("GET", url)
        status = result.get("status", "unknown")

        if status == "succeeded":
            video_url = result.get("content", {}).get("video_url", "")
            last_frame_url = result.get("content", {}).get("last_frame_url")
            duration = result.get("duration", "?")
            resolution = result.get("resolution", "?")
            ratio = result.get("ratio", "?")

            # 计算实际成本（从 API 返回的 usage.completion_tokens）
            usage = result.get("usage", {})
            completion_tokens = usage.get("completion_tokens")
            cost_actual = None
            if completion_tokens is not None:
                # 从 DB 取 task 原始参数以判断定价（46 vs 28 元/百万 tokens）
                actual_cost_calc = None
                if _DB_AVAILABLE:
                    try:
                        t = TaskDB().get(task_id)
                        if t and t.get("has_video_input"):
                            actual_cost_calc = completion_tokens * 28 / 1_000_000
                        else:
                            actual_cost_calc = completion_tokens * 46 / 1_000_000
                    except Exception:
                        pass
                if actual_cost_calc is None:
                    # 保守默认：用 46/M
                    actual_cost_calc = completion_tokens * 46 / 1_000_000
                cost_actual = round(actual_cost_calc, 4)

            print(f"\nVideo generation succeeded!")
            print(f"  Duration: {duration}s | Resolution: {resolution} | Ratio: {ratio}")
            print(f"  Video URL: {video_url}")
            if last_frame_url:
                print(f"  Last Frame URL: {last_frame_url}")
            if cost_actual is not None:
                print(f"  Actual cost: ¥{cost_actual:.4f} ({completion_tokens} tokens)")

            local_path = None
            if download_dir and video_url:
                download_path = Path(download_dir).expanduser()
                download_path.mkdir(parents=True, exist_ok=True)
                filename = f"seedance_{task_id}_{int(time.time())}.mp4"
                filepath = download_path / filename

                print(f"\nDownloading video to {filepath}...")
                try:
                    urllib.request.urlretrieve(video_url, str(filepath))
                    local_path = str(filepath)
                    print(f"Saved to: {filepath}")

                    if sys.platform == "darwin":
                        os.system(f'open "{filepath}"')
                except Exception as e:
                    print(f"Download failed: {e}", file=sys.stderr)

            # 更新任务登记册
            if _DB_AVAILABLE:
                try:
                    update_kwargs = {
                        "video_url": video_url,
                        "last_frame_url": last_frame_url,
                        "local_path": local_path,
                    }
                    if cost_actual is not None:
                        update_kwargs["cost_actual"] = cost_actual
                    TaskDB().update_status(task_id, "succeeded", **update_kwargs)
                except Exception as e:
                    print(f"⚠️  更新任务登记失败: {e}", file=sys.stderr)

            print(json.dumps(result, indent=2, ensure_ascii=False))
            return result

        elif status == "failed":
            error = result.get("error", {})
            error_code = error.get("code", "unknown")
            error_msg = error.get("message", "Unknown error")
            print(f"\nVideo generation failed!")
            print(f"  Error: {error_code} - {error_msg}")

            if _DB_AVAILABLE:
                try:
                    TaskDB().update_status(
                        task_id, "failed",
                        error_code=error_code, error_message=error_msg,
                    )
                except Exception:
                    pass

            print(json.dumps(result, indent=2, ensure_ascii=False))
            sys.exit(1)

        elif status == "expired":
            print(f"\nVideo generation task expired.")
            if _DB_AVAILABLE:
                try:
                    TaskDB().update_status(task_id, "expired")
                except Exception:
                    pass
            print(json.dumps(result, indent=2, ensure_ascii=False))
            sys.exit(1)

        else:
            print(f"  Status: {status}...", flush=True)
            time.sleep(interval)


def cmd_wait(args):
    """Wait for task completion."""
    return cmd_wait_logic(args.task_id, args.interval, args.download,
                           project=getattr(args, "project", None),
                           max_wait=args.max_wait)


def cmd_list(args):
    """List video generation tasks (compressed view)."""
    params = []
    if args.page:
        params.append(f"page_num={args.page}")
    if args.page_size:
        params.append(f"page_size={args.page_size}")
    if args.status:
        params.append(f"filter.status={args.status}")

    url = BASE_URL
    if params:
        url += "?" + "&".join(params)

    result = api_request("GET", url)
    items = result.get("items", []) if isinstance(result, dict) else result

    # 打印汇总
    print(f"📋 共 {len(items)} 条任务  页={args.page}  每页={args.page_size}"
          + (f"  状态={args.status}" if args.status else ""))
    print(f"{'id':32}  {'status':10}  {'model':24}  {'dur':4}  {'res':5}  {'tokens':>8}  {'est¥':>7}  {'created':12}")
    print("-" * 120)
    # 加载本地 cost_estimate（如果有）
    local_costs = {}
    if _DB_AVAILABLE:
        try:
            # 按多个状态都查一次，覆盖不传状态的情况
            for st in [args.status] if args.status else ["queued", "running", "succeeded", "failed", "expired", "cancelled"]:
                for r in TaskDB().list_by_status(st):
                    local_costs[r["task_id"]] = r.get("cost_estimate") or 0
        except Exception:
            pass
    for it in items:
        usage = it.get("usage", {}) or {}
        tokens = usage.get("total_tokens", 0) or 0
        created = it.get("created_at", 0)
        created_str = time.strftime("%m-%d %H:%M", time.localtime(created)) if created else "-"
        # 从本地 DB 拉成本估算
        est = local_costs.get(it.get("id", ""), 0) or 0
        est_str = f"¥{est:.2f}" if est else "-"
        print(f"{it.get('id', '-'):32}  {it.get('status', '-'):10}  "
              f"{it.get('model', '-'):24}  {it.get('duration', '-'):>4}  "
              f"{it.get('resolution', '-'):5}  {tokens:>8}  {est_str:>7}  {created_str:12}")

    # 完整 JSON 加 --verbose
    if getattr(args, "verbose", False):
        print()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def cmd_delete(args):
    """Cancel or delete a task."""
    url = f"{BASE_URL}/{args.task_id}"
    api_request("DELETE", url)
    # 同步本地登记册状态
    if _DB_AVAILABLE:
        try:
            TaskDB().update_status(args.task_id, "cancelled")
        except Exception as e:
            print(f"⚠️  同步 DB 状态失败: {e}", file=sys.stderr)
    print(f"Task {args.task_id} cancelled/deleted successfully.")


def cmd_db(args):
    """Local task registry queries (no API call)."""
    if not _DB_AVAILABLE:
        print("⚠️  db.py 未找到，本地登记册不可用", file=sys.stderr)
        sys.exit(1)

    db = TaskDB()
    sub = args.db_command

    if sub == "show":
        task = db.get(args.task_id)
        if task:
            print(json.dumps(task, indent=2, ensure_ascii=False, default=str))
        else:
            print(f"任务不存在: {args.task_id}")
            sys.exit(1)

    elif sub == "pending":
        tasks = db.list_pending_recoverable(project=args.project, max_age_hours=args.max_age_hours)
        print(f"🟡 {len(tasks)} 个未完成任务（{args.max_age_hours}h 内）")
        if tasks:
            print(f"{'task_id':34}  {'status':10}  {'est¥':>7}  {'project':15}  {'age':>8}  prompt")
            print("-" * 100)
            for t in tasks:
                prompt = (t.get("prompt") or "")[:50]
                age_min = (time.time() - t.get("created_at", 0)) / 60
                print(f"  {t['task_id']:32}  {t['status']:10}  ¥{t.get('cost_estimate', 0):>5.2f}  "
                      f"{t.get('project') or '-':15}  {age_min:>6.1f}m  {prompt}")

    elif sub == "stats":
        stats = db.stats(project=args.project)
        total_count = sum(s["count"] for s in stats)
        total_cost = sum(s.get("est_total") or 0 for s in stats)
        print(f"📊 {'项目: ' + args.project if args.project else '全部任务'}  共 {total_count} 条  估算总成本 ¥{total_cost:.2f}")
        print(f"{'状态':12} {'数量':>5}  {'估算成本':>10}  {'实际成本':>10}")
        for s in stats:
            est = s.get("est_total") or 0
            act = s.get("actual_total") or 0
            print(f"  {s['status']:10} {s['count']:>5}  ¥{est:>8.2f}  ¥{act:>8.2f}")

    elif sub == "batch":
        tasks = db.list_by_batch(args.batch_id)
        print(f"📦 批次 {args.batch_id}: {len(tasks)} 个任务")
        for t in tasks:
            print(f"  [{t['batch_index']}] {t['task_id']}  {t['status']:10}  est=¥{t.get('cost_estimate', 0):.4f}")

    else:
        print("可用子命令: show / pending / stats / batch")


def parse_bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("true", "1", "yes"):
        return True
    if v.lower() in ("false", "0", "no"):
        return False
    raise argparse.ArgumentTypeError(f"Boolean expected, got '{v}'")


def main():
    parser = argparse.ArgumentParser(description="Seedance Video Generation CLI (Volcengine Ark)")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    p_create = subparsers.add_parser("create", help="Create a video generation task")
    p_create.add_argument("--prompt", "-p", help="Text prompt describing the video")
    p_create.add_argument("--image", "-i", help="First frame image (URL or local file path)")
    p_create.add_argument("--last-frame", help="Last frame image (URL or local file path)")
    p_create.add_argument("--ref-images", nargs="+", help="Reference images (1-9 URLs or paths)")
    p_create.add_argument("--video", nargs="+", help="Reference videos (URL or local file, max 3, Seedance 2.0)")
    p_create.add_argument("--video-role", default="reference_video", help="Video role: reference_video (default) | first_frame | last_frame")
    p_create.add_argument("--audio", nargs="+", help="Reference audio (URL or local file, max 3, Seedance 2.0)")
    p_create.add_argument("--draft-task-id", help="Draft task ID to generate final video from")
    p_create.add_argument("--model", "-m", default=DEFAULT_MODEL, help=f"Model ID (default: {DEFAULT_MODEL})")
    p_create.add_argument("--ratio", choices=["16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "adaptive"], help="Aspect ratio")
    p_create.add_argument("--duration", "-d", type=int, help="Duration in seconds (4-15, or -1 for auto)")
    p_create.add_argument("--resolution", "-r", choices=["480p", "720p", "1080p"], help="Resolution")
    p_create.add_argument("--seed", type=int, help="Random seed (-1 for random)")
    p_create.add_argument("--camera-fixed", type=parse_bool, help="Fix camera position (true/false)")
    p_create.add_argument("--watermark", type=parse_bool, help="Add watermark (true/false)")
    p_create.add_argument("--generate-audio", type=parse_bool, help="Generate audio (true/false)")
    p_create.add_argument("--draft", type=parse_bool, help="Draft/preview mode (true/false, 1.5 Pro)")
    p_create.add_argument("--return-last-frame", type=parse_bool, help="Return last frame URL (true/false)")
    p_create.add_argument("--service-tier", choices=["default", "flex"], help="Service tier (flex = offline, 50%% cheaper)")
    p_create.add_argument("--frames", type=int, help="Exact frame count (25+4n, range 29-289, 1.0 models only)")
    p_create.add_argument("--execution-expires-after", type=int, help="Task timeout in seconds (3600-259200)")
    p_create.add_argument("--callback-url", help="Webhook URL for task status notifications")
    p_create.add_argument("--wait", "-w", action="store_true", help="Wait for completion after creating")
    p_create.add_argument("--interval", type=int, default=15, help="Poll interval in seconds (default: 15)")
    p_create.add_argument("--download", help="Download directory (e.g. ~/Desktop)")
    p_create.add_argument("--project", help="Project name for task registry (e.g. 'su7', 'holiday-ad')")
    p_create.add_argument("--no-db", action="store_true", help="Skip writing to task registry")

    p_status = subparsers.add_parser("status", help="Query task status")
    p_status.add_argument("task_id", help="Task ID to query")

    # ===== 本地登记册查询子命令（不调远程 API） =====
    p_db = subparsers.add_parser("db", help="Local task registry queries")
    db_sub = p_db.add_subparsers(dest="db_command")
    p_db_show = db_sub.add_parser("show", help="Show task by ID")
    p_db_show.add_argument("task_id", help="Task ID")
    p_db_pending = db_sub.add_parser("pending", help="List queued/running tasks")
    p_db_pending.add_argument("--project", help="Filter by project")
    p_db_pending.add_argument("--max-age-hours", type=int, default=24, help="Max age in hours (default 24)")
    p_db_stats = db_sub.add_parser("stats", help="Show stats grouped by status")
    p_db_stats.add_argument("--project", help="Filter by project")
    p_db_batch = db_sub.add_parser("batch", help="List tasks in a batch")
    p_db_batch.add_argument("batch_id", help="Batch ID")

    p_wait = subparsers.add_parser("wait", help="Wait for task completion")
    p_wait.add_argument("task_id", help="Task ID to wait for")
    p_wait.add_argument("--interval", type=int, default=15, help="Poll interval in seconds (default: 15)")
    p_wait.add_argument("--download", help="Download directory (e.g. ~/Desktop)")
    p_wait.add_argument("--max-wait", type=int, default=1800, help="Max wait seconds (default 1800 = 30min)")

    p_list = subparsers.add_parser("list", help="List video generation tasks")
    p_list.add_argument("--status", choices=["queued", "running", "cancelled", "succeeded", "failed", "expired"])
    p_list.add_argument("--page", type=int, default=1)
    p_list.add_argument("--page-size", type=int, default=10)
    p_list.add_argument("--verbose", action="store_true", help="Print full JSON")

    p_delete = subparsers.add_parser("delete", help="Cancel or delete a task")
    p_delete.add_argument("task_id", help="Task ID to cancel/delete")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "create": cmd_create,
        "status": cmd_status,
        "wait": cmd_wait,
        "list": cmd_list,
        "delete": cmd_delete,
        "db": cmd_db,
    }
    try:
        commands[args.command](args)
    except SeedanceAPIError as e:
        print(f"API Error (HTTP {e.status_code}): {e.message}", file=sys.stderr)
        sys.exit(1)
    except SeedanceNetworkError as e:
        print(f"Network Error: {e}", file=sys.stderr)
        sys.exit(1)
    except UnicodeEncodeError as e:
        # API key 含非 ASCII 字符（如 …）会触发
        print(f"Encoding Error: {e}", file=sys.stderr)
        print("⚠️  ARK_API_KEY 含非 ASCII 字符（如 …），HTTP header 不支持", file=sys.stderr)
        print("   请检查 shell 是否被展开为含 … 字符的脱敏 key", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
