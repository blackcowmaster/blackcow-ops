from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from scripts.blackcow_swarm_lib.browser_smoke import run_browser_smoke


class TestBrowserSmoke(unittest.TestCase):
    def test_browser_smoke_passes_when_expected_text_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            chrome = _fake_chrome(Path(temp_dir), "<html><body>25:00</body></html>", 0)

            result = run_browser_smoke(
                "http://localhost:8088",
                expect=("25:00",),
                reject=("Something went wrong",),
                chrome_bin=str(chrome),
            )

            self.assertTrue(result.ok, result.error)

    def test_browser_smoke_fails_on_rejected_runtime_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            chrome = _fake_chrome(Path(temp_dir), "<html><body>Something went wrong</body></html>", 0)

            result = run_browser_smoke(
                "http://localhost:8088",
                expect=(),
                reject=("Something went wrong",),
                chrome_bin=str(chrome),
            )

            self.assertFalse(result.ok)
            self.assertIn("Rejected text present", result.error)

    def test_browser_smoke_can_capture_screenshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            screenshot = root / "screen.png"
            chrome = _fake_chrome(root, "<html><body>25:00</body></html>", 0)

            result = run_browser_smoke(
                "http://localhost:8088",
                expect=("25:00",),
                reject=(),
                chrome_bin=str(chrome),
                screenshot_path=screenshot,
            )

            self.assertTrue(result.ok, result.error)
            self.assertEqual(screenshot.read_bytes(), b"PNG")


def _fake_chrome(temp_dir: Path, dom: str, exit_code: int) -> Path:
    path = temp_dir / "chrome"
    path.write_text(
        "#!/usr/bin/env sh\n"
        "for arg in \"$@\"; do case \"$arg\" in --screenshot=*) printf 'PNG' > \"${arg#--screenshot=}\";; esac; done\n"
        f"printf '%s' '{dom}'\n"
        f"exit {exit_code}\n",
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | 0o111)
    return path


if __name__ == "__main__":
    unittest.main()
