import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime" / "starter"))

import easy_api


class EasyApiContractTests(unittest.TestCase):
    def _documented_names(self):
        doc = (ROOT / "docs" / "easy_api接口文档.md").read_text(encoding="utf-8")
        names = set(re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)\s*\(", doc))

        alias_start = doc.find("## 18. 全部别名汇总")
        alias_end = doc.find("## 19.", alias_start)
        alias_block = doc[alias_start:alias_end]
        names.update(re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", alias_block))

        # These names are mentioned only to explain that polling is not part
        # of easy_api.py. They must not become public backend functions.
        names.difference_update({
            "main",
            "refresh",
            "loop",
            "readxxx",
            "sendxxx",
            "setxxx",
            "testxxx",
            "writexxx",
            "xxx",
            # Upstream st7735 method names are documented as reference
            # implementation details; they are not easy_api exports.
            "set_rotation",
            "fill_screen",
            "flush",
            "draw_point",
            "draw_line",
            "fill_rectangle",
            "show_string",
            "COLOR565",
        })
        return names

    def test_documented_public_api_exists(self):
        missing = sorted(name for name in self._documented_names() if not hasattr(easy_api, name))
        self.assertEqual(missing, [])

    def test_star_import_contract_covers_documented_api(self):
        namespace = {}
        exec("from easy_api import *", namespace)
        exported = set(namespace)
        missing = sorted(self._documented_names() - exported)
        self.assertEqual(missing, [])

    def test_backend_stays_lazy(self):
        source = (ROOT / "runtime" / "starter" / "easy_api.py").read_text(encoding="utf-8")
        self.assertNotIn("CompetitionRuntime", source)
        self.assertNotIn(".snapshot(", source)
        self.assertIsNone(re.search(
            r"^def\s+(loop|refresh|refreshlcd|refreshguangmin|refreshwenhumi|refreshjiasudu|refreshstatus)\b",
            source,
            re.MULTILINE,
        ))

    def test_button_event_helpers_share_last_event_contract(self):
        source = (ROOT / "runtime" / "starter" / "easy_api_parts" / "10_led_buttons.py").read_text(encoding="utf-8")
        self.assertIn("def lastanjian():", source)
        self.assertIn("def readanjian_direction():", source)
        self.assertIn("return _nav.read_key()", source)
        self.assertIn("global _last_button_event", source)
        self.assertIn("_last_button_event = (name, event)", source)

    def test_runtime_exposes_version_and_capability_probe(self):
        source = (ROOT / "runtime" / "starter" / "easy_api_parts" / "00_core.py").read_text(encoding="utf-8")
        self.assertIn("EASY_API_VERSION", source)
        self.assertIn("def api_version()", source)
        self.assertIn("def api_capabilities()", source)


if __name__ == "__main__":
    unittest.main()
