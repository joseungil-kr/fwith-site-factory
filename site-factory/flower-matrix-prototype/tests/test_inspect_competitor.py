"""Offline regression tests. No live competitor request is made."""
import base64
from datetime import datetime, timezone
from email.message import Message
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("inspect_competitor", ROOT / "scripts/inspect_competitor.py")
inspector = importlib.util.module_from_spec(spec); spec.loader.exec_module(inspector)
FIXTURE = (ROOT / "tests/fixtures/competitor.html").read_bytes()
NOW = lambda: datetime(2026, 10, 20, 7, 0, tzinfo=timezone.utc)


class Response:
    def __init__(self, body=FIXTURE, url=None, content_type="text/html; charset=utf-8", status=200):
        self.body = body; self.url = url or inspector.safe_url(inspector.RAW[0]); self.status = status
        self.headers = Message(); self.headers["Content-Type"] = content_type
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self): return self.body
    def geturl(self): return self.url


class CompetitorInspectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)
        self.no_network = patch.object(inspector, "urlopen", side_effect=AssertionError("live network forbidden"))
        self.no_network.start(); self.addCleanup(self.no_network.stop)

    def inspect(self, responses, urls=None):
        opener = Mock(side_effect=responses)
        report = inspector.inspect_urls(urls or inspector.RAW[:2], self.out, opener=opener, now=NOW)
        self.assertEqual(opener.call_count, len(urls or inspector.RAW[:2]))
        return report

    def pair(self, first=FIXTURE, second=FIXTURE):
        return [Response(first, inspector.safe_url(inspector.RAW[0])), Response(second, inspector.safe_url(inspector.RAW[1]))]

    def test_success_preserves_exact_bytes_body_and_self_contained_ci_json(self):
        report = self.inspect(self.pair())
        persisted = json.loads((self.out / "competitor-structure.json").read_text(encoding="utf-8"))
        self.assertEqual(report, persisted)
        for row in persisted["rows"]:
            self.assertEqual(row["captureStatus"], "success")
            self.assertEqual((self.out / row["rawHtml"]["path"]).read_bytes(), FIXTURE)
            self.assertEqual(base64.b64decode(row["rawHtml"]["base64"]), FIXTURE)
            self.assertEqual(row["rawHtml"]["sha256"], hashlib.sha256(FIXTURE).hexdigest())
            body = row["bodyText"]["text"].encode("utf-8")
            self.assertEqual((self.out / row["bodyText"]["path"]).read_bytes(), body)
            self.assertEqual(row["bodyText"]["sha256"], hashlib.sha256(body).hexdigest())
            self.assertEqual(row["collectedAtUtc"], "2026-10-20T07:00:00Z")
            self.assertEqual(row["collectedAtKst"], "2026-10-20T16:00:00+09:00")
            self.assertEqual(row["encoding"], "utf-8")
        self.assertEqual(report["comparison"]["state"], "compared")
        self.assertTrue(report["comparison"]["same2658VisibleText"])
        self.assertIsNone(report["similarityMetrics"])

    def test_body_metadata_headings_anchors_and_alt_are_separate(self):
        row = self.inspect(self.pair())["rows"][0]
        self.assertEqual(row["title"], "광진구 축하화환 자료")
        self.assertEqual(row["description"], "원문 설명 & 주문 안내")
        self.assertEqual(row["headingCounts"]["h1"], 1)
        self.assertEqual(row["headings"][0], {"level": 1, "text": "축하화환 안내"})
        self.assertEqual(row["links"][0]["anchor"], "상품 원문 확인")
        self.assertEqual(row["links"][0]["url"], "https://graduation.m-castle.co.kr/shop/item.php?id=1")
        self.assertEqual(row["images"][0]["alt"], "축하화환 실제 상품")
        body = row["bodyText"]["text"]
        self.assertIn("행사 주소와 희망시간을 확인하세요.", body)
        for excluded in [row["title"], row["description"], "headOnly", "bodyOnly", "-style", "제외할"]:
            self.assertNotIn(excluded, body)
        with_base = FIXTURE.replace(b'<meta charset="utf-8">', b'<meta charset="utf-8"><base href="https://catalog.example/">')
        row = self.inspect(self.pair(with_base, with_base))["rows"][0]
        self.assertEqual(row["links"][0]["url"], "https://catalog.example/shop/item.php?id=1")
        self.assertEqual(row["internalLinkCount"], 0)

    def test_two_http_failures_never_compare_none_as_equal(self):
        errors = [HTTPError(url, 403, "denied", None, None) for url in inspector.RAW[:2]]
        report = self.inspect(errors)
        self.assertEqual([r["status"] for r in report["rows"]], [403, 403])
        self.assertEqual(report["comparison"]["state"], "unverified")
        for key, value in report["comparison"].items():
            if key.startswith("same"): self.assertIsNone(value)
        self.assertFalse(list(self.out.rglob("*.html")))

    def test_two_transport_failures_are_explicit_and_do_not_leak_error_detail(self):
        report = self.inspect([URLError("private diagnostic"), TimeoutError("private diagnostic")])
        self.assertTrue(all(r["captureStatus"] == "failed" for r in report["rows"]))
        self.assertTrue(all(r["status"] is None for r in report["rows"]))
        self.assertNotIn("private diagnostic", json.dumps(report))
        self.assertIsNone(report["comparison"]["same2658Title"])

    def test_one_failed_input_prevents_pair_comparison(self):
        report = self.inspect([self.pair()[0], URLError("failed")])
        self.assertEqual([r["captureStatus"] for r in report["rows"]], ["success", "failed"])
        self.assertEqual(report["comparison"]["state"], "unverified")

    def test_head_changes_do_not_change_body_hash(self):
        other = FIXTURE.replace("광진구".encode(), "서울 광진구".encode()).replace("원문 설명".encode(), "다른 설명".encode())
        comparison = self.inspect(self.pair(second=other))["comparison"]
        self.assertFalse(comparison["same2658Title"])
        self.assertFalse(comparison["same2658Description"])
        self.assertTrue(comparison["same2658VisibleText"])

    def test_non_html_and_missing_body_preserve_raw_but_remain_unverified(self):
        report = self.inspect([Response(b'{"ok": true}', content_type="application/json"), Response(b"<html><head><title>Only head</title></head></html>")])
        self.assertTrue(all(r["captureStatus"] == "unverified" for r in report["rows"]))
        self.assertEqual([r["failureReason"] for r in report["rows"]], ["html_content_type_required", "nonempty_html_body_required"])
        self.assertTrue(all((self.out / r["rawHtml"]["path"]).is_file() for r in report["rows"]))
        self.assertEqual(report["comparison"]["state"], "unverified")

    def test_declared_korean_encoding_is_used_and_original_bytes_preserved(self):
        raw = '<html><head><meta charset="cp949"><title>축하화환</title></head><body><h1>상품 안내</h1></body></html>'.encode('cp949')
        row = self.inspect([Response(raw, content_type="text/html"), self.pair()[1]])["rows"][0]
        self.assertEqual(row["encoding"], "cp949")
        self.assertEqual(row["encodingSource"], "meta")
        self.assertEqual(row["title"], "축하화환")
        self.assertEqual(base64.b64decode(row["rawHtml"]["base64"]), raw)

    def test_lossy_decode_is_not_a_successful_comparison_input(self):
        raw = b"<html><body>bad: \xff</body></html>"
        report = self.inspect(self.pair(first=raw))
        self.assertTrue(report["rows"][0]["decodeLossy"])
        self.assertEqual(report["rows"][0]["failureReason"], "lossy_html_decode")
        self.assertEqual(report["comparison"]["state"], "unverified")

    def test_unsupported_text_codec_still_preserves_success_response_bytes(self):
        raw = b"<html><body>original bytes</body></html>"
        report = self.inspect([Response(raw, content_type="text/html; charset=base64_codec"), self.pair()[1]])
        row = report["rows"][0]
        self.assertEqual(row["captureStatus"], "unverified")
        self.assertEqual(row["failureReason"], "unsupported_html_encoding")
        self.assertEqual((self.out / row["rawHtml"]["path"]).read_bytes(), raw)
        self.assertEqual(report["comparison"]["state"], "unverified")

    def test_non_200_response_object_is_failed_without_original_html_claim(self):
        report = self.inspect([Response(status=503), self.pair()[1]])
        row = report["rows"][0]
        self.assertEqual(row["status"], 503)
        self.assertEqual(row["failureReason"], "http_status_not_200")
        self.assertEqual(row["captureStatus"], "failed")
        self.assertNotIn("rawHtml", row)
        self.assertEqual(report["comparison"]["state"], "unverified")

    def test_missing_metadata_is_unknown_instead_of_equal(self):
        raw = b"<html><body><p>body only</p></body></html>"
        comparison = self.inspect(self.pair(raw, raw))["comparison"]
        self.assertEqual(comparison["state"], "compared")
        self.assertIsNone(comparison["same2658Title"])
        self.assertIsNone(comparison["same2658Description"])
        self.assertEqual(comparison["unverifiedFields"], ["title", "description"])

    def test_changed_final_path_or_same_host_is_not_a_comparable_pair(self):
        for url in ["https://order.m-castle.co.kr/other.html", inspector.safe_url(inspector.RAW[0])]:
            with self.subTest(url=url):
                report = self.inspect([self.pair()[0], Response(url=url)])
                self.assertEqual(report["comparison"]["state"], "unverified")
                self.assertIsNone(report["comparison"]["same2658Images"])

    def test_encoded_path_is_not_double_encoded(self):
        encoded = inspector.safe_url(inspector.RAW[0])
        self.assertEqual(inspector.safe_url(encoded), encoded)
        self.assertNotIn("%25EC", encoded)

    def test_repeated_runs_preserve_prior_evidence(self):
        first = self.inspect(self.pair())
        second = self.inspect(self.pair())
        self.assertNotEqual(first["rows"][0]["rawHtml"]["path"], second["rows"][0]["rawHtml"]["path"])
        self.assertTrue((self.out / first["rows"][0]["rawHtml"]["path"]).is_file())


if __name__ == "__main__":
    unittest.main()
