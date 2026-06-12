#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for batch.py — concurrent submission + retry logic.

Run: python3 -m pytest tests/test_batch.py -v
Or:  python3 tests/test_batch.py
"""

import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import batch  # noqa: E402
import seedance  # noqa: E402


class TestEstimateTotal(unittest.TestCase):
    """estimate_total sums up costs for a list of task configs."""

    def test_single_task_default(self):
        tasks = [{"prompt": "test"}]
        total = batch.estimate_total(tasks)
        # Default: 15s 1080p pure gen = ¥33.63
        self.assertAlmostEqual(total, 33.63, places=1)

    def test_multiple_tasks(self):
        tasks = [
            {"prompt": "a", "duration": 4, "resolution": "480p", "draft": True},
            {"prompt": "b", "duration": 4, "resolution": "480p", "draft": True},
        ]
        total = batch.estimate_total(tasks)
        # 2 × 1.12 = 2.24
        self.assertAlmostEqual(total, 2.24, places=1)

    def test_mix_draft_and_final(self):
        tasks = [
            {"prompt": "draft", "duration": 4, "resolution": "480p", "draft": True},
            {"prompt": "final", "duration": 4, "resolution": "1080p"},
        ]
        total = batch.estimate_total(tasks)
        # 1.12 + 8.97 = 10.09
        self.assertAlmostEqual(total, 10.09, places=1)

    def test_with_video_input(self):
        tasks = [{"prompt": "ref", "video": "ref.mp4", "duration": 15, "resolution": "1080p"}]
        total = batch.estimate_total(tasks)
        # 15s 1080p with video = 40.88
        self.assertAlmostEqual(total, 40.88, places=1)


class TestSubmitOneRetry(unittest.TestCase):
    """Test submit_one retry logic with mocked api_request.

    Mock injects a fake api_request that simulates API responses.
    """

    def _make_mock(self, responses, sleeps=0):
        """Create a mock api_request that returns responses in sequence."""
        call_count = [0]
        sleep_count = [0]

        def mock_request(method, url, body=None, retries=2):
            call_count[0] += 1
            if sleeps > 0 and call_count[0] <= sleeps:
                time.sleep(sleeps)
            idx = min(call_count[0] - 1, len(responses) - 1)
            resp = responses[idx]
            if isinstance(resp, Exception):
                raise resp
            return resp

        return mock_request, call_count

    def _patch_db(self, task_id="test-task-1"):
        """Create a TaskDB pointing to a temp file."""
        from db import TaskDB
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "test_batch.db")
        return TaskDB(db_path), db_path, tmpdir

    def setUp(self):
        """Monkey-patch TaskDB() to use a temp DB so tests don't conflict with real DB."""
        from db import TaskDB as RealTaskDB
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test_batch.db")
        self.test_db_instance = RealTaskDB(self.db_path)

        # Replace the module-level TaskDB reference in batch.py
        # Since batch.py does 'from db import TaskDB', we need to replace
        # batch.TaskDB (the binding in batch module's namespace).
        self._orig_taskdb = batch.TaskDB
        batch.TaskDB = lambda *args, **kwargs: self.test_db_instance

    def tearDown(self):
        # Restore
        batch.TaskDB = self._orig_taskdb
        # Cleanup
        for suffix in ("", "-wal", "-shm"):
            p = self.db_path + suffix
            if os.path.exists(p):
                os.remove(p)
        os.rmdir(self.tmpdir)

    def test_submit_one_success(self):
        """Happy path: API returns task_id, should return success dict."""
        mock_req, calls = self._make_mock([{"id": "test-task-1", "status": "queued"}])

        task_cfg = {"prompt": "test", "duration": 4, "resolution": "1080p"}
        result = batch.submit_one(
            index=0,
            task_cfg=task_cfg,
            project="test-project",
            batch_id="batch-1",
            max_retries=1,
            _mock=mock_req,
        )
        # submit_one returns (index, task_id_or_None, error_or_None)
        self.assertIsNotNone(result)
        idx, task_id, err = result
        self.assertEqual(idx, 0)
        self.assertIsNotNone(task_id)
        self.assertIsNone(err)

    def test_submit_one_400_no_retry(self):
        """400 error should NOT be retried (client error)."""
        mock_req, calls = self._make_mock([
            seedance.SeedanceAPIError(400, "bad request"),
        ])
        task_cfg = {"prompt": "bad"}
        result = batch.submit_one(
            index=0, task_cfg=task_cfg, project="p", batch_id="b",
            max_retries=3, _mock=mock_req,
        )
        idx, task_id, err = result
        # Should return error tuple, not raise
        self.assertIsNone(task_id)
        self.assertIsNotNone(err)
        self.assertEqual(calls[0], 1)  # Only 1 attempt, no retry on 400

    def test_submit_one_500_with_retry(self):
        """5xx error should be retried up to max_retries."""
        mock_req, calls = self._make_mock([
            seedance.SeedanceAPIError(500, "server error"),
            seedance.SeedanceAPIError(500, "server error"),
            {"id": "task-1", "status": "queued"},
        ])
        task_cfg = {"prompt": "flaky"}
        result = batch.submit_one(
            index=0, task_cfg=task_cfg, project="p", batch_id="b",
            max_retries=2, _mock=mock_req,
        )
        idx, task_id, err = result
        self.assertIsNotNone(task_id)
        self.assertIsNone(err)
        self.assertEqual(calls[0], 3)  # 2 retries = 3 total attempts

    def test_submit_one_500_exhausts_retries(self):
        """All retries fail with 5xx → should return error."""
        mock_req, calls = self._make_mock([
            seedance.SeedanceAPIError(500, "server error"),
        ] * 5)  # Always 500
        task_cfg = {"prompt": "broken"}
        result = batch.submit_one(
            index=0, task_cfg=task_cfg, project="p", batch_id="b",
            max_retries=2, _mock=mock_req,
        )
        idx, task_id, err = result
        self.assertIsNone(task_id)
        self.assertIsNotNone(err)
        self.assertEqual(calls[0], 3)  # 1 + 2 retries

    def test_submit_one_429_retry(self):
        """429 (rate limit) should be retried."""
        mock_req, calls = self._make_mock([
            seedance.SeedanceAPIError(429, "rate limit"),
            {"id": "task-1", "status": "queued"},
        ])
        task_cfg = {"prompt": "rate-limited"}
        result = batch.submit_one(
            index=0, task_cfg=task_cfg, project="p", batch_id="b",
            max_retries=1, _mock=mock_req,
        )
        idx, task_id, err = result
        self.assertIsNotNone(task_id)
        self.assertEqual(calls[0], 2)

    def test_submit_one_network_error_retry(self):
        """Network error should be retried."""
        mock_req, calls = self._make_mock([
            seedance.SeedanceNetworkError("connection reset"),
            {"id": "task-1", "status": "queued"},
        ])
        task_cfg = {"prompt": "network"}
        result = batch.submit_one(
            index=0, task_cfg=task_cfg, project="p", batch_id="b",
            max_retries=1, _mock=mock_req,
        )
        idx, task_id, err = result
        self.assertIsNotNone(task_id)
        self.assertEqual(calls[0], 2)


    def test_submit_one_includes_model_in_body(self):
        """Regression: body must always include 'model' field, even when
        task_cfg['model'] is None (P1 bug: 2026-06-12 2.0 4 段并发全报
        'missing model parameter').
        """
        captured_bodies = []

        def mock_request(method, url, body=None, retries=2):
            captured_bodies.append(body)
            return {"id": f"task-{len(captured_bodies)}", "status": "queued"}

        # Simulate the inline CLI mode: --model not provided
        task_cfg = {"prompt": "x", "duration": 4, "resolution": "1080p", "model": None}
        batch.submit_one(0, task_cfg, "p", "b", _mock=mock_request)
        self.assertEqual(len(captured_bodies), 1)
        self.assertIn("model", captured_bodies[0])
        self.assertEqual(captured_bodies[0]["model"], seedance.DEFAULT_MODEL)


class TestConcurrentSpeedup(unittest.TestCase):
    """Test that concurrent submission is faster than serial (using mocks)."""

    def test_concurrent_speedup_with_sleep(self):
        """Submit N tasks with sleep; max_workers=2 should be faster than serial."""
        # Each API call "takes" 0.3 second
        sleep_duration = 0.3
        call_count = [0]

        def mock_request(method, url, body=None, retries=2):
            call_count[0] += 1
            time.sleep(sleep_duration)
            return {"id": f"task-{call_count[0]}", "status": "queued"}

        from concurrent.futures import ThreadPoolExecutor
        tasks = [{"prompt": f"task {i}", "duration": 4, "resolution": "1080p"} for i in range(4)]

        # Serial
        serial_start = time.time()
        for i, t in enumerate(tasks):
            batch.submit_one(i, t, "p", "b-serial", _mock=mock_request)
        serial_elapsed = time.time() - serial_start

        # Concurrent with max_workers=2
        call_count[0] = 0
        concurrent_start = time.time()
        with ThreadPoolExecutor(max_workers=2) as ex:
            list(ex.map(
                lambda i_t: batch.submit_one(i_t[0], i_t[1], "p", "b-concurrent", _mock=mock_request),
                list(enumerate(tasks))
            ))
        concurrent_elapsed = time.time() - concurrent_start

        # Concurrent should be faster (at least 1.2x for 4 tasks, 2 workers)
        speedup = serial_elapsed / concurrent_elapsed
        self.assertGreater(speedup, 1.2, f"speedup={speedup:.2f}x not enough")


if __name__ == "__main__":
    unittest.main(verbosity=2)
