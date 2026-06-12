#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for db.py — TaskDB + estimate_cost.

Run: python3 -m pytest tests/test_db.py -v
Or:  python3 tests/test_db.py
"""

import os
import sys
import tempfile
import unittest

# Add scripts/ to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import db  # noqa: E402


class TestEstimateCost(unittest.TestCase):
    """Verify the cost estimation function across all known dimensions."""

    def test_15s_1080p_pure_gen(self):
        # Known: 15s 1080p 纯文生 = ¥33.63 (实测)
        cost = db.estimate_cost(15, has_video_input=False, resolution="1080p")
        self.assertAlmostEqual(cost, 33.63, places=2)

    def test_15s_1080p_with_video(self):
        # Known: 15s 1080p 参考延长 = ¥40.88 (实测)
        cost = db.estimate_cost(15, has_video_input=True, resolution="1080p")
        self.assertAlmostEqual(cost, 40.88, places=2)

    def test_4s_1080p_pure_gen(self):
        # Known: 4s 1080p = ¥8.97 估 / ¥9.04 实 (估精度 0.8%)
        cost = db.estimate_cost(4, has_video_input=False, resolution="1080p")
        self.assertAlmostEqual(cost, 8.97, places=2)

    def test_4s_480p_draft(self):
        # Known: 4s 480p + draft = ¥1.12 (实测)
        cost = db.estimate_cost(4, has_video_input=False, draft=True, resolution="480p")
        self.assertAlmostEqual(cost, 1.12, places=2)

    def test_4s_720p(self):
        # Known: 4s 720p ≈ ¥3.98 (公式: 4 × 731025/15 × 0.444 × 46/1M)
        # 实测 87300 tokens × 46/1M = ¥4.02 (token 计数有 ~1% 波动)
        cost = db.estimate_cost(4, has_video_input=False, resolution="720p")
        # 接受 ±5% 误差（公式估算 vs 实测 token 计数的固有差异）
        self.assertAlmostEqual(cost, 4.02, delta=0.21)

    def test_flex_discount_15s_1080p(self):
        # flex = 0.5x of normal
        normal = db.estimate_cost(15, has_video_input=False, resolution="1080p")
        flex = db.estimate_cost(15, has_video_input=False, flex=True, resolution="1080p")
        self.assertAlmostEqual(flex, normal * 0.5, places=4)

    def test_draft_discount_4s_1080p(self):
        # draft = 0.5x of normal
        normal = db.estimate_cost(4, has_video_input=False, resolution="1080p")
        draft = db.estimate_cost(4, has_video_input=False, draft=True, resolution="1080p")
        self.assertAlmostEqual(draft, normal * 0.5, places=4)

    def test_resolution_factor_known_values(self):
        """720p factor should be 0.444, not 0.5 (verified 2026-06-12)."""
        self.assertEqual(db.RESOLUTION_FACTOR["480p"], 0.25)
        self.assertEqual(db.RESOLUTION_FACTOR["720p"], 0.444)
        self.assertEqual(db.RESOLUTION_FACTOR["1080p"], 1.0)

    def test_cost_is_positive(self):
        """Cost should always be positive for valid inputs."""
        for dur in [4, 5, 10, 15]:
            for res in ["480p", "720p", "1080p"]:
                cost = db.estimate_cost(dur, has_video_input=False, resolution=res)
                self.assertGreater(cost, 0, f"dur={dur} res={res} cost={cost}")

    def test_with_video_input_costs_more(self):
        """With video input (28¥/M) costs more than pure (46¥/M) per 1080p second? No.

        Actually with_video_input means reference video is included, and that
        scenario uses 28¥/M token pricing vs 46¥/M for pure text-to-video.
        But reference videos typically need MORE tokens overall, hence higher
        total cost.

        Verify: with_video > pure for same duration."""
        pure = db.estimate_cost(15, has_video_input=False, resolution="1080p")
        with_video = db.estimate_cost(15, has_video_input=True, resolution="1080p")
        self.assertGreater(with_video, pure)
        # 40.88 / 33.63 = 1.215 (because reference video adds tokens)
        self.assertAlmostEqual(with_video / pure, 40.88 / 33.63, places=2)


class TestTaskDB(unittest.TestCase):
    """Test TaskDB persistence layer with isolated temp database.

    Note: insert() always sets status='queued' (by design).
    Use update_status() to transition queued -> running -> succeeded/failed.
    """

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test_tasks.db")
        self.db = db.TaskDB(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        if os.path.exists(self.db_path + "-wal"):
            os.remove(self.db_path + "-wal")
        if os.path.exists(self.db_path + "-shm"):
            os.remove(self.db_path + "-shm")
        os.rmdir(self.tmpdir)

    def _make_tasks(self, count, project="test-project"):
        """Helper: insert N tasks, all in 'queued' status."""
        for i in range(count):
            self.db.insert(
                task_id=f"test-{i}",
                project=project,
                prompt=f"prompt {i}",
                duration=4,
                resolution="1080p",
            )

    def test_insert_and_get(self):
        """Insert a task and retrieve it."""
        self.db.insert(
            task_id="test-1",
            project="test-project",
            prompt="a test prompt",
            duration=4,
            resolution="1080p",
        )
        result = self.db.get("test-1")
        self.assertIsNotNone(result)
        self.assertEqual(result["project"], "test-project")
        self.assertEqual(result["prompt"], "a test prompt")
        self.assertEqual(result["duration"], 4)
        self.assertEqual(result["resolution"], "1080p")
        self.assertEqual(result["status"], "queued")  # Default

    def test_update_status_lifecycle(self):
        """Status updates should be persisted: queued -> running -> succeeded."""
        self.db.insert(task_id="t-1", project="p", prompt="p", duration=4, resolution="1080p")
        # queued initially
        self.assertEqual(self.db.get("t-1")["status"], "queued")

        self.db.update_status("t-1", "running")
        self.assertEqual(self.db.get("t-1")["status"], "running")

        self.db.update_status("t-1", "succeeded", video_url="https://example.com/v.mp4")
        result = self.db.get("t-1")
        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(result["video_url"], "https://example.com/v.mp4")

    def test_update_status_failure_path(self):
        """Failure path should record error_code and error_message."""
        self.db.insert(task_id="t-fail", project="p", prompt="p", duration=4, resolution="1080p")
        self.db.update_status("t-fail", "failed", error_code=400, error_message="bad request")
        result = self.db.get("t-fail")
        self.assertEqual(result["status"], "failed")
        # error_code is stored as string in SQLite (no type affinity enforced)
        self.assertEqual(int(result["error_code"]), 400)
        self.assertEqual(result["error_message"], "bad request")

    def test_list_by_status_after_transitions(self):
        """After transitioning statuses, list_by_status should filter correctly."""
        # Create 4 tasks, all queued initially
        for i in range(4):
            self.db.insert(task_id=f"t-{i}", project="p", prompt="p", duration=4, resolution="1080p")
        # Transition: 0,1 -> succeeded, 2 -> running, 3 stays queued
        self.db.update_status("t-0", "succeeded")
        self.db.update_status("t-1", "succeeded")
        self.db.update_status("t-2", "running")

        queued = self.db.list_by_status("queued")
        succeeded = self.db.list_by_status("succeeded")
        running = self.db.list_by_status("running")
        self.assertEqual(len(queued), 1)
        self.assertEqual(len(succeeded), 2)
        self.assertEqual(len(running), 1)

    def test_list_by_status_with_project_filter(self):
        """Project filter should narrow results."""
        for i in range(3):
            self.db.insert(task_id=f"a-{i}", project="project-a", prompt="p", duration=4, resolution="1080p")
        for i in range(2):
            self.db.insert(task_id=f"b-{i}", project="project-b", prompt="p", duration=4, resolution="1080p")

        a_tasks = self.db.list_by_status("queued", project="project-a")
        b_tasks = self.db.list_by_status("queued", project="project-b")
        all_queued = self.db.list_by_status("queued")
        self.assertEqual(len(a_tasks), 3)
        self.assertEqual(len(b_tasks), 2)
        self.assertEqual(len(all_queued), 5)

    def test_stats(self):
        """Stats should aggregate across statuses."""
        # Insert + transition 3 to succeeded
        for i in range(3):
            self.db.insert(task_id=f"t-{i}", project="p", prompt="p", duration=4, resolution="1080p")
            self.db.update_status(f"t-{i}", "succeeded")
        # 1 failed
        self.db.insert(task_id="t-fail", project="p", prompt="p", duration=4, resolution="1080p")
        self.db.update_status("t-fail", "failed")
        # 1 queued (no transition)
        self.db.insert(task_id="t-q", project="p", prompt="p", duration=4, resolution="1080p")

        stats = self.db.stats()
        # stats returns a list of dicts, one per status
        by_status = {s["status"]: s for s in stats}
        self.assertEqual(by_status["succeeded"]["count"], 3)
        # 3 succeeded × 4s 1080p = 3 × ¥8.9672 = ¥26.9016
        self.assertAlmostEqual(by_status["succeeded"]["est_total"], 26.90, places=1)
        self.assertEqual(by_status["failed"]["count"], 1)
        self.assertEqual(by_status["queued"]["count"], 1)

    def test_delete(self):
        """delete should remove a task."""
        self.db.insert(task_id="t-del", project="p", prompt="p", duration=4, resolution="1080p")
        self.assertIsNotNone(self.db.get("t-del"))
        self.db.delete("t-del")
        self.assertIsNone(self.db.get("t-del"))

    def test_list_pending_recoverable(self):
        """Pending tasks should be listable for crash recovery."""
        # Insert task (default queued)
        self.db.insert(task_id="orphan-1", project="p", prompt="p", duration=4, resolution="1080p")
        pending = self.db.list_pending_recoverable(max_age_hours=24)
        self.assertGreaterEqual(len(pending), 1)
        # And completed tasks should NOT be in pending
        self.db.update_status("orphan-1", "succeeded")
        pending = self.db.list_pending_recoverable(max_age_hours=24)
        self.assertEqual(len([p for p in pending if p["task_id"] == "orphan-1"]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
