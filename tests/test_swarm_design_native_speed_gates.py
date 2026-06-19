from __future__ import annotations

import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from scripts.blackcow_swarm_lib.design_gate import run_design_gate
from scripts.blackcow_swarm_lib.expo_clean_gate import run_expo_clean_gate
from scripts.blackcow_swarm_lib.expo_native_smoke import run_expo_native_smoke
from scripts.blackcow_swarm_lib.native_smoke import run_native_capability_gate, run_native_smoke
from scripts.blackcow_swarm_lib.source_text_gate import run_source_text_gate
from scripts.blackcow_swarm_lib.speed_gate import run_speed_gate
from scripts.blackcow_swarm_lib.visual_review import run_visual_review


class TestDesignNativeSpeedGates(unittest.TestCase):
    def test_design_gate_fails_without_design_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pomodoro-app").mkdir()

            result = run_design_gate(root, "pomodoro-app")

            self.assertFalse(result.ok)
            self.assertIn("DESIGN.md", result.message)

    def test_design_gate_passes_with_project_design_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "pomodoro-app"
            project.mkdir()
            (project / "DESIGN.md").write_text("# Pomodoro Design\n", encoding="utf-8")

            result = run_design_gate(root, "pomodoro-app")

            self.assertTrue(result.ok, result.message)

    def test_native_gate_reports_missing_xcrun(self) -> None:
        result = run_native_capability_gate("pomodoro-app", "ios", xcrun_bin="/missing/xcrun")

        self.assertFalse(result.ok)
        self.assertIn("xcrun", result.message)

    def test_expo_clean_gate_rejects_node_modules_tsconfig_extends(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "water-app"
            project.mkdir()
            (project / "package.json").write_text(
                json.dumps({"scripts": {"typecheck": "tsc --noEmit", "lint": "node scripts/lint.js"}}),
                encoding="utf-8",
            )
            (project / "tsconfig.json").write_text(json.dumps({"extends": "expo/tsconfig.base"}), encoding="utf-8")

            result = run_expo_clean_gate(root, "water-app")

            self.assertFalse(result.ok)
            self.assertIn("expo/tsconfig.base", result.message)

    def test_expo_clean_gate_rejects_no_install_eslint_script(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "water-app"
            project.mkdir()
            (project / "package.json").write_text(
                json.dumps({"scripts": {"typecheck": "tsc --noEmit", "lint": "eslint ."}}),
                encoding="utf-8",
            )
            (project / "tsconfig.json").write_text(json.dumps({"compilerOptions": {"strict": True}}), encoding="utf-8")

            result = run_expo_clean_gate(root, "water-app")

            self.assertFalse(result.ok)
            self.assertIn("before npm install", result.message)

    def test_expo_clean_gate_rejects_external_imports_without_local_declarations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "water-app"
            project.mkdir()
            (project / "package.json").write_text(
                json.dumps({"scripts": {"typecheck": "tsc --noEmit", "lint": "node scripts/lint.js"}}),
                encoding="utf-8",
            )
            (project / "tsconfig.json").write_text(
                json.dumps({"compilerOptions": {"strict": True, "moduleResolution": "bundler", "jsx": "react-jsx"}}),
                encoding="utf-8",
            )
            (project / "App.tsx").write_text(
                "import React from 'react';\n"
                "import { View } from 'react-native';\n"
                "export default function App() { return <View />; }\n",
                encoding="utf-8",
            )

            result = run_expo_clean_gate(root, "water-app")

            self.assertFalse(result.ok)
            self.assertIn("external modules", result.message)
            self.assertIn("react-native", result.message)
            self.assertIn("react/jsx-runtime", result.message)

    def test_expo_clean_gate_accepts_external_imports_with_local_declarations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "water-app"
            types_dir = project / "src" / "types"
            types_dir.mkdir(parents=True)
            (project / "package.json").write_text(
                json.dumps({"scripts": {"typecheck": "tsc --noEmit", "lint": "node scripts/lint.js"}}),
                encoding="utf-8",
            )
            (project / "tsconfig.json").write_text(
                json.dumps({"compilerOptions": {"strict": True, "moduleResolution": "bundler", "jsx": "react-jsx"}}),
                encoding="utf-8",
            )
            (project / "App.tsx").write_text(
                "import React from 'react';\n"
                "import { View } from 'react-native';\n"
                "export default function App() { return <View />; }\n",
                encoding="utf-8",
            )
            (types_dir / "native.d.ts").write_text(
                "declare module 'react';\n"
                "declare module 'react-native';\n"
                "declare module 'react/jsx-runtime';\n",
                encoding="utf-8",
            )

            result = run_expo_clean_gate(root, "water-app")

            self.assertTrue(result.ok, result.message)

    def test_expo_clean_gate_accepts_self_contained_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "water-app"
            project.mkdir()
            (project / "package.json").write_text(
                json.dumps({"scripts": {"typecheck": "tsc --noEmit", "lint": "node scripts/lint.js"}}),
                encoding="utf-8",
            )
            (project / "tsconfig.json").write_text(
                json.dumps({"compilerOptions": {"strict": True, "moduleResolution": "bundler"}}),
                encoding="utf-8",
            )

            result = run_expo_clean_gate(root, "water-app")

            self.assertTrue(result.ok, result.message)

    def test_source_text_gate_requires_expected_ui_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "water-app"
            project.mkdir()
            (project / "App.tsx").write_text("export default function App() { return 'Hydrate'; }\n", encoding="utf-8")

            result = run_source_text_gate(root, "water-app", ("Water",))

            self.assertFalse(result.ok)
            self.assertIn("Water", result.message)

    def test_source_text_gate_passes_when_expected_ui_text_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "water-app"
            project.mkdir()
            (project / "App.tsx").write_text("export default function App() { return 'Water'; }\n", encoding="utf-8")

            result = run_source_text_gate(root, "water-app", ("Water",))

            self.assertTrue(result.ok, result.message)

    def test_native_gate_can_capture_simulator_screenshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            fake_xcrun = root / "xcrun"
            screenshot_path = root / "ios.png"
            fake_xcrun.write_text(
                "#!/usr/bin/env sh\n"
                "if [ \"$2\" = \"list\" ]; then echo 'iPhone 17 Pro (Booted)'; exit 0; fi\n"
                "if [ \"$2\" = \"io\" ]; then printf 'PNG' > \"$5\"; exit 0; fi\n"
                "exit 1\n",
                encoding="utf-8",
            )
            os.chmod(fake_xcrun, 0o755)

            result = run_native_smoke("pomodoro-app", "ios", xcrun_bin=str(fake_xcrun), screenshot_path=screenshot_path)

            self.assertTrue(result.ok, result.message)
            self.assertTrue(screenshot_path.exists())

    def test_expo_native_smoke_fast_fails_when_start_command_exits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            project = root / "water-app"
            project.mkdir()
            (project / "package.json").write_text(json.dumps({"dependencies": {"expo": "latest"}}), encoding="utf-8")

            started = time.monotonic()
            result = run_expo_native_smoke(
                project_root=root,
                project="water-app",
                platform="ios",
                screenshot_path=root / "ios.png",
                review_output=root / "review.md",
                expect=("Water",),
                startup_wait_seconds=2,
                start_command=("/bin/sh", "-lc", "echo expo missing >&2; exit 127"),
            )
            duration = time.monotonic() - started

            self.assertFalse(result.ok)
            self.assertLess(duration, 1.0)
            self.assertIn("expo missing", result.message)

    def test_visual_review_requires_screenshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            result = run_visual_review(root / "missing.png", root / "review.md", codex_bin="/missing/codex")

            self.assertFalse(result.ok)
            self.assertIn("missing screenshot", result.message)

    def test_visual_review_fails_on_codex_fail_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            image = root / "screen.png"
            output = root / "review.md"
            fake_codex = root / "codex"
            image.write_bytes(b"PNG")
            fake_codex.write_text("#!/usr/bin/env sh\necho 'FAIL text is unreadable'\n", encoding="utf-8")
            os.chmod(fake_codex, 0o755)

            result = run_visual_review(image, output, codex_bin=str(fake_codex))

            self.assertFalse(result.ok)
            self.assertIn("visual review failed", result.message)
            self.assertIn("FAIL text is unreadable", output.read_text(encoding="utf-8"))

    def test_visual_review_passes_on_codex_pass_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            image = root / "screen.png"
            output = root / "review.md"
            fake_codex = root / "codex"
            image.write_bytes(b"PNG")
            fake_codex.write_text("#!/usr/bin/env sh\necho 'PASS native screen is readable'\n", encoding="utf-8")
            os.chmod(fake_codex, 0o755)

            result = run_visual_review(image, output, codex_bin=str(fake_codex), expect=("25:00",))

            self.assertTrue(result.ok, result.message)
            self.assertIn("PASS native screen is readable", output.read_text(encoding="utf-8"))

    def test_speed_gate_requires_worker_timing_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            (run_dir / "state.json").write_text(json.dumps({"workers": {}}), encoding="utf-8")

            result = run_speed_gate(run_dir, min_speedup=1.1)

            self.assertFalse(result.ok)
            self.assertIn("timing", result.message)

    def test_speed_gate_passes_with_parallel_timing_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            state = {
                "workers": {
                    "a": {"status": "SUCCEEDED", "started_at": 0.0, "finished_at": 10.0},
                    "b": {"status": "SUCCEEDED", "started_at": 0.0, "finished_at": 10.0},
                }
            }
            (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

            result = run_speed_gate(run_dir, min_speedup=1.1)

            self.assertTrue(result.ok, result.message)


if __name__ == "__main__":
    unittest.main()
