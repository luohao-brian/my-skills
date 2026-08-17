from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "vendor_updates.py"
SPEC = importlib.util.spec_from_file_location("vendor_updates", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class VendorUpdatesProxyTests(unittest.TestCase):
    def test_explicit_proxy_is_process_scoped(self) -> None:
        with (
            mock.patch.dict(MODULE.os.environ, {}, clear=True),
            mock.patch.object(MODULE.urllib.request, "install_opener") as install_opener,
        ):
            MODULE.configure_proxy(
                "http://127.0.0.1:8080",
                "http://127.0.0.1:8080",
                "internal.example",
            )
            self.assertEqual(MODULE.os.environ["HTTP_PROXY"], "http://127.0.0.1:8080")
            self.assertEqual(MODULE.os.environ["HTTPS_PROXY"], "http://127.0.0.1:8080")
            self.assertEqual(
                MODULE.os.environ["NO_PROXY"],
                "localhost,127.0.0.1,::1,internal.example",
            )
            install_opener.assert_called_once()


if __name__ == "__main__":
    unittest.main()
