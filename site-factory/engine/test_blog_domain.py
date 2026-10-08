import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import blog_domain


class BlogDomainRegistryTests(unittest.TestCase):
    def fixture(self, mutate=None):
        source = Path(__file__).parents[2] / ".github" / "site-factory-sites.json"
        data = json.loads(source.read_text(encoding="utf-8"))
        if mutate:
            mutate(data["sites"]["blog-fwith"])
        handle = tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8", delete=False)
        json.dump(data, handle)
        handle.close()
        self.addCleanup(lambda: Path(handle.name).unlink(missing_ok=True))
        return Path(handle.name)

    def test_exact_identity_passes(self):
        self.assertEqual(blog_domain.validate_registry(self.fixture())["worker"], blog_domain.WORKER)

    def test_worker_host_branch_and_root_mismatch_rejected(self):
        for key in ("worker", "siteUrl", "branch", "root"):
            with self.subTest(key=key):
                path = self.fixture(lambda site, key=key: site.__setitem__(key, "wrong"))
                with self.assertRaisesRegex(ValueError, "identity_mismatch"):
                    blog_domain.validate_registry(path)

    def test_production_or_growth_policy_mismatch_rejected(self):
        for key, value in (("productionEnabled", True), ("growthPaused", False)):
            with self.subTest(key=key):
                path = self.fixture(lambda site, key=key, value=value: site.__setitem__(key, value))
                with self.assertRaisesRegex(ValueError, "identity_mismatch"):
                    blog_domain.validate_registry(path)


class BlogDomainTransportTests(unittest.TestCase):
    account = "a" * 32

    def domains(self, rows, errors=[], success=True, status=200):
        calls = []
        def transport(method, path):
            self.assertEqual(method, "GET")
            self.assertEqual(path, f"/accounts/{self.account}/workers/domains")
            calls.append((method, path))
            transport.last_http_status = status
            return {"success": success, "errors": errors, "result": rows,
                    "result_info": {"page": 1, "per_page": len(rows), "count": len(rows),
                                    "total_count": len(rows), "total_pages": 1 if rows else 0}}
        transport.last_http_status = None
        transport.calls = calls
        return transport

    def test_exact_binding_passes_and_dns_is_unobserved(self):
        result = blog_domain.get_binding(self.domains([{"hostname": "blog.fwith.kr", "service": "blog-fwith-prod-disabled"}]), self.account)
        self.assertEqual(result["dnsState"], "not_observed")

    def test_wrong_duplicate_and_incomplete_bindings_rejected(self):
        cases = [
            [{"hostname": "blog.fwith.kr", "service": "wrong"}],
            [{"hostname": "blog.fwith.kr", "service": "blog-fwith-prod-disabled"}] * 2,
            [{"hostname": "blog.fwith.kr"}],
        ]
        for rows in cases:
            with self.subTest(rows=rows):
                with self.assertRaises(Exception):
                    blog_domain.get_binding(self.domains(rows), self.account)

    def test_errors_null_requires_verified_200_list(self):
        self.assertEqual(blog_domain.get_binding(self.domains([{"hostname": "blog.fwith.kr", "service": "blog-fwith-prod-disabled"}], None), self.account)["worker"], blog_domain.WORKER)
        rows = [{"hostname": "blog.fwith.kr", "service": blog_domain.WORKER}]
        for status, success, result in ((500, True, rows), (200, False, rows), (200, True, {})):
            with self.subTest(status=status, success=success, result=result):
                with self.assertRaises(blog_domain.PreflightError):
                    blog_domain.get_binding(self.domains(result, None, success, status), self.account)

    def test_malformed_account_makes_zero_requests(self):
        transport = self.domains([])
        with self.assertRaises(blog_domain.PreflightError):
            blog_domain.get_binding(transport, "bad")
        self.assertEqual(transport.calls, [])

    def test_attach_body_has_no_overrides_and_timeout_is_not_retried(self):
        calls = []
        def transport(method, path, body=None):
            calls.append((method, path, body))
            raise TimeoutError()
        with self.assertRaises(Exception):
            blog_domain.attach(transport, self.account)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], "PUT")
        self.assertEqual(calls[0][2]["override_scope"], False)
        self.assertEqual(calls[0][2]["override_existing_origin"], False)
        self.assertEqual(calls[0][2]["override_existing_dns_record"], False)


class BlogDomainCliTests(unittest.TestCase):
    account = "a" * 32

    def setUp(self):
        self.registry = Path(__file__).parents[2] / ".github" / "site-factory-sites.json"
        handle = tempfile.NamedTemporaryFile(delete=False)
        handle.close()
        self.report = Path(handle.name)
        self.addCleanup(lambda: self.report.unlink(missing_ok=True))

    def invoke(self, mode):
        return blog_domain.main(["--registry", str(self.registry), "--mode", mode, "--report", str(self.report)])

    @patch.dict("os.environ", {"CLOUDFLARE_ACCOUNT_ID": account, "CLOUDFLARE_API_TOKEN": "token"}, clear=False)
    def test_readback_never_calls_native_main_or_put(self):
        calls = []
        def factory(token, account_id):
            def transport(method, path):
                calls.append(method)
                transport.last_http_status = 200
                return {"success": True, "errors": [], "result": [{"hostname": "blog.fwith.kr", "service": blog_domain.WORKER}], "result_info": {"page": 1, "per_page": 1, "count": 1, "total_count": 1, "total_pages": 1}}
            transport.last_http_status = None
            return transport
        with patch.object(blog_domain, "_readback_transport", factory), patch.object(blog_domain.native, "main") as native_main:
            self.assertEqual(self.invoke("readback"), 0)
            native_main.assert_not_called()
        self.assertEqual(calls, ["GET"])

    @patch.dict("os.environ", {"CLOUDFLARE_ACCOUNT_ID": "bad", "CLOUDFLARE_API_TOKEN": "token"}, clear=False)
    def test_cli_malformed_account_makes_zero_requests(self):
        with patch.object(blog_domain, "_readback_transport") as factory, patch.object(blog_domain.native, "main") as native_main:
            self.assertEqual(self.invoke("readback"), 1)
            factory.assert_not_called()
            native_main.assert_not_called()

    @patch.dict("os.environ", {"CLOUDFLARE_ACCOUNT_ID": account}, clear=False)
    def test_preflight_and_attach_invoke_native_once_in_intended_mode(self):
        with patch.object(blog_domain.native, "main", return_value=0) as native_main:
            self.assertEqual(self.invoke("preflight"), 0)
            self.assertEqual(native_main.call_count, 1)
            self.assertEqual(native_main.call_args.args[0][0], "--preflight")
            self.assertEqual(native_main.call_args.args[0][1], "--report")
        with patch.object(blog_domain.native, "main", return_value=0) as native_main:
            self.assertEqual(self.invoke("attach"), 0)
            native_main.assert_called_once_with([])

    @patch.dict("os.environ", {"CLOUDFLARE_ACCOUNT_ID": account}, clear=False)
    def test_attach_failure_has_unknown_mutation_result(self):
        with patch.object(blog_domain.native, "main", return_value=1):
            self.assertEqual(self.invoke("attach"), 1)
        report = json.loads(self.report.read_text())
        self.assertIsNone(report["mutationsPerformed"])
        self.assertEqual(report["mutationStatus"], "unknown")


if __name__ == "__main__":
    unittest.main()
