#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seedance 任务登记册（SQLite）
目的：
1. 不丢 task_id —— 进程崩溃/超时后可恢复
2. 支持并发提交/等待时的状态共享
3. 成本核算（按 token 估算）

用法：
    from db import TaskDB
    db = TaskDB()  # 默认 ~/.openclaw/workspace/data/seedance_tasks.db
    db.insert(task_id, project="su7", prompt="...", ratio="9:16", duration=15)
    db.update_status(task_id, "succeeded", video_url="...", local_path="...")
    db.list_pending()  # 查所有未完成
    db.stats(project="su7")  # 统计
"""

import os
import sqlite3
import time
from pathlib import Path
from threading import Lock


# 默认数据库位置（用户工作区）
DEFAULT_DB_PATH = Path.home() / ".openclaw" / "workspace" / "data" / "seedance_tasks.db"


# 成本估算（基于官方定价 + 2026-06-11 SU7 实战账单校准）
# 纯文生视频：46 元/百万 tokens
# 含视频输入（参考延长）：28 元/百万 tokens
# 15s 1080p 实测：
#   - 纯文生：731,025 tokens × 46元/百万 = ¥33.63
#   - 参考延长：1,460,025 tokens × 28元/百万 = ¥40.88
# 来源：cgt-20260611151658-ghbs4（纯） + cgt-20260611152328-n55v9（延长）
TOKEN_PER_15S_PURE_GEN = 731_025       # 2026-06-11 真实数据
TOKEN_PER_15S_WITH_VIDEO = 1_460_025   # 2026-06-11 真实数据
COST_PURE_GEN = 46.0 / 1_000_000       # 元/token
COST_WITH_VIDEO = 28.0 / 1_000_000     # 元/token
# Flex 离线模式半价
FLEX_DISCOUNT = 0.5
# Draft 草稿折扣（2026-06-12 实测反推：4s 1080p 0.25x（480p）× 0.5x（draft）= 0.125x，24356/194940）
DRAFT_DISCOUNT = 0.5

# 分辨率缩放
# 480p 0.25x：2026-06-12 实测验证（基于 1.5 Pro + draft 反推，反推公式见 REFERENCE_POINTS）
# 720p 0.5x：理论值（面积 1/4，线数 1/2），无 720p 真实数据验证
# 1080p 1.0x：实测 4s 1080p = 196,425 tokens
RESOLUTION_FACTOR = {"480p": 0.25, "720p": 0.5, "1080p": 1.0}


def estimate_cost(duration, has_video_input=False, flex=False, draft=False, resolution="1080p"):
    """
    估算单条视频成本（元）

    Args:
        duration: 秒数
        has_video_input: 是否含参考视频（参考延长模式）
        flex: 离线模式
        draft: 草稿模式
        resolution: 分辨率（720p 时 tokens 约为 1080p 的 1/2，480p 约 1/4）
    """
    # tokens 与时长成线性（以 15s 为基准）
    base = TOKEN_PER_15S_WITH_VIDEO if has_video_input else TOKEN_PER_15S_PURE_GEN
    tokens = (duration / 15.0) * base

    # 分辨率按比例缩放（2026-06-12 实测 4s 1080p = 196,425 tokens）
    res_factor = RESOLUTION_FACTOR.get(resolution, 1.0)
    tokens *= res_factor

    # 选单价
    unit_price = COST_WITH_VIDEO if has_video_input else COST_PURE_GEN
    cost = tokens * unit_price

    if flex:
        cost *= FLEX_DISCOUNT
    if draft:
        cost *= DRAFT_DISCOUNT

    return round(cost, 4)


# 已验证的实测参考点（2026-06-11/12 SU7 + Opus47 + E2E 项目）
# 供 estimate_cost 准不准验证
REFERENCE_POINTS = [
    # (duration, has_input, flex, draft, resolution, expected_cost, source)
    (15, False, False, False, "1080p", 33.63, "cgt-20260611151658-ghbs4 (15s 1080p 纯文生)"),
    (15, True,  False, False, "1080p", 40.88, "cgt-20260611152328-n55v9 (15s 1080p 参考延长)"),
    (4,  False, False, False, "1080p",  9.04, "cgt-20260612093622-zwxq2 (4s 1080p 纯文生)"),
    (4,  False, False, True,  "480p",   1.12, "cgt-20260612092619-p255n (4s 480p draft)"),
    (4,  False, False, True,  "480p",   1.12, "cgt-20260612092619-rbtzw (4s 480p draft)"),
    # 4s 1080p 验证：4/15 * 731025 * 46/1M = 8.97元。实测 9.04，误差 0.8%（可接受）
    # 4s 480p draft 验证：4/15 * 731025 * 0.25(480p) * 0.5(draft) * 46/1M = 1.12元。实测 1.12 ✅
]


class TaskDB:
    """任务登记册（线程安全）"""

    def __init__(self, db_path=None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._init_schema()

    def _connect(self):
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        # WAL 模式：读写并发不阻塞
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_schema(self):
        with self._lock, self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id        TEXT PRIMARY KEY,
                    project        TEXT,
                    prompt         TEXT,
                    image          TEXT,
                    video          TEXT,
                    audio          TEXT,
                    ref_images     TEXT,
                    draft_task_id  TEXT,
                    model          TEXT,
                    ratio          TEXT,
                    duration       INTEGER,
                    resolution     TEXT,
                    service_tier   TEXT,
                    draft          INTEGER DEFAULT 0,
                    seed           INTEGER,
                    generate_audio INTEGER,
                    watermark      INTEGER,
                    has_video_input INTEGER DEFAULT 0,
                    status         TEXT DEFAULT 'queued',
                    video_url      TEXT,
                    last_frame_url TEXT,
                    local_path     TEXT,
                    cost_estimate  REAL,
                    cost_actual    REAL,
                    error_code     TEXT,
                    error_message  TEXT,
                    batch_id       TEXT,
                    batch_index    INTEGER,
                    created_at     REAL,
                    updated_at     REAL,
                    finished_at    REAL
                )
            """)
            # 索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON tasks(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_project ON tasks(project)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_batch ON tasks(batch_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON tasks(created_at)")

    def insert(self, task_id, project=None, prompt=None, batch_id=None,
               batch_index=None, **kwargs):
        """
        插入新任务。状态默认 'queued'。

        任务参数（与 seedance.py cmd_create 对齐）：
            image, video, audio, ref_images, draft_task_id, model, ratio,
            duration, resolution, service_tier, draft, seed, generate_audio,
            watermark
        """
        now = time.time()
        has_video_input = 1 if kwargs.get("video") else 0
        cost = estimate_cost(
            duration=kwargs.get("duration", 15),
            has_video_input=bool(has_video_input),
            flex=kwargs.get("service_tier") == "flex",
            draft=bool(kwargs.get("draft")),
            resolution=kwargs.get("resolution") or "1080p",
        )

        with self._lock, self._connect() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO tasks (
                    task_id, project, prompt, batch_id, batch_index,
                    image, video, audio, ref_images, draft_task_id, model,
                    ratio, duration, resolution, service_tier, draft, seed,
                    generate_audio, watermark, has_video_input,
                    cost_estimate, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'queued', ?, ?)
            """, (
                task_id, project, prompt, batch_id, batch_index,
                kwargs.get("image"), kwargs.get("video"), kwargs.get("audio"),
                ",".join(kwargs.get("ref_images") or []) or None,
                kwargs.get("draft_task_id"), kwargs.get("model"),
                kwargs.get("ratio"), kwargs.get("duration"),
                kwargs.get("resolution"), kwargs.get("service_tier"),
                1 if kwargs.get("draft") else 0, kwargs.get("seed"),
                kwargs.get("generate_audio"), kwargs.get("watermark"),
                has_video_input, cost, now, now,
            ))
        return task_id

    def update_status(self, task_id, status, video_url=None, last_frame_url=None,
                      local_path=None, error_code=None, error_message=None,
                      cost_actual=None, cost_estimate=None):
        """更新任务状态。状态枚举：queued/running/succeeded/failed/expired/cancelled"""
        now = time.time()
        finished = now if status in ("succeeded", "failed", "expired", "cancelled") else None

        with self._lock, self._connect() as conn:
            # 只更新非空字段
            updates = ["status = ?", "updated_at = ?"]
            params = [status, now]

            if video_url is not None:
                updates.append("video_url = ?")
                params.append(video_url)
            if last_frame_url is not None:
                updates.append("last_frame_url = ?")
                params.append(last_frame_url)
            if local_path is not None:
                updates.append("local_path = ?")
                params.append(local_path)
            if error_code is not None:
                updates.append("error_code = ?")
                params.append(error_code)
            if error_message is not None:
                updates.append("error_message = ?")
                params.append(error_message)
            if cost_actual is not None:
                updates.append("cost_actual = ?")
                params.append(cost_actual)
            if cost_estimate is not None:
                updates.append("cost_estimate = ?")
                params.append(cost_estimate)
            if finished:
                updates.append("finished_at = ?")
                params.append(finished)

            params.append(task_id)
            conn.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE task_id = ?", params)

    def get(self, task_id):
        """获取单条任务"""
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
            return dict(row) if row else None

    def list_by_status(self, status, project=None, limit=100):
        """按状态查询"""
        with self._connect() as conn:
            if project:
                rows = conn.execute(
                    "SELECT * FROM tasks WHERE status = ? AND project = ? ORDER BY created_at DESC LIMIT ?",
                    (status, project, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status, limit)
                ).fetchall()
            return [dict(r) for r in rows]

    def list_by_batch(self, batch_id):
        """查询一个批次的所有任务（按 batch_index 排序）"""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE batch_id = ? ORDER BY batch_index ASC",
                (batch_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def list_pending_recoverable(self, project=None, max_age_hours=24):
        """
        列出可恢复的未完成任务（崩溃恢复用）
        max_age_hours: 超过这个时间的过期任务忽略
        """
        cutoff = time.time() - max_age_hours * 3600
        with self._connect() as conn:
            if project:
                rows = conn.execute("""
                    SELECT * FROM tasks
                    WHERE status IN ('queued', 'running')
                      AND project = ?
                      AND created_at > ?
                    ORDER BY created_at ASC
                """, (project, cutoff)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM tasks
                    WHERE status IN ('queued', 'running')
                      AND created_at > ?
                    ORDER BY created_at ASC
                """, (cutoff,)).fetchall()
            return [dict(r) for r in rows]

    def stats(self, project=None):
        """统计：按状态分组 + 总成本"""
        with self._connect() as conn:
            if project:
                rows = conn.execute("""
                    SELECT status, COUNT(*) as count,
                           SUM(cost_estimate) as est_total,
                           SUM(COALESCE(cost_actual, cost_estimate)) as actual_total
                    FROM tasks WHERE project = ?
                    GROUP BY status
                """, (project,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT status, COUNT(*) as count,
                           SUM(cost_estimate) as est_total,
                           SUM(COALESCE(cost_actual, cost_estimate)) as actual_total
                    FROM tasks
                    GROUP BY status
                """).fetchall()
            return [dict(r) for r in rows]

    def delete(self, task_id):
        """删除任务"""
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        # 验证估算函数准不准
        print("🧪 estimate_cost 精度验证\n")
        all_ok = True
        for duration, has_input, flex, draft, res, expected, source in REFERENCE_POINTS:
            actual = estimate_cost(duration, has_input, flex, draft, res)
            delta = actual - expected
            pct = delta / expected * 100 if expected else 0
            ok = abs(pct) < 2  # 2% 内可接受
            mark = "✅" if ok else "❌"
            print(f"  {mark} {duration}s {res} 估=¥{actual:>6.2f}  实=¥{expected:>6.2f}  "
                  f"差={delta:+.2f} ({pct:+.1f}%)  {source}")
            if not ok:
                all_ok = False
        print()
        print("全部 ✅" if all_ok else "存在偏差，需调校常量")
        sys.exit(0 if all_ok else 1)
    elif len(sys.argv) > 1 and sys.argv[1] == "stats":
        db = TaskDB()
        for row in db.stats():
            print(f"{row['status']:12}  count={row['count']:3}  est=¥{row['est_total'] or 0:.2f}  actual=¥{row['actual_total'] or 0:.2f}")
    else:
        db = TaskDB()
        print(f"DB path: {db.db_path}")
        print(f"Tasks: {sum(s['count'] for s in db.stats())}")
        print()
        for row in db.stats():
            print(f"  {row['status']:12}  {row['count']:3}  est=¥{row['est_total'] or 0:.2f}")
        print()
        print("  验证精度: python3 db.py verify")
        print("  统计: python3 db.py stats")
