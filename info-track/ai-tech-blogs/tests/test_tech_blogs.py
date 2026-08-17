from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "tech_blogs.py"
SPEC = importlib.util.spec_from_file_location("tech_blogs", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class TechBlogsProxyTests(unittest.TestCase):
    def test_explicit_proxy_overrides_inherited_scheme_settings(self) -> None:
        inherited = {
            "HTTP_PROXY": "http://old.example:8080",
            "http_proxy": "http://old.example:8080",
        }
        with (
            mock.patch.dict(MODULE.os.environ, inherited, clear=True),
            mock.patch.object(MODULE.urllib.request, "install_opener") as install_opener,
        ):
            MODULE.configure_proxy(None, "http://127.0.0.1:8080", "example.cn")
            self.assertNotIn("HTTP_PROXY", MODULE.os.environ)
            self.assertNotIn("http_proxy", MODULE.os.environ)
            self.assertEqual(MODULE.os.environ["HTTPS_PROXY"], "http://127.0.0.1:8080")
            self.assertEqual(
                MODULE.os.environ["NO_PROXY"],
                "localhost,127.0.0.1,::1,example.cn",
            )
            install_opener.assert_called_once()


if __name__ == "__main__":
    unittest.main()
