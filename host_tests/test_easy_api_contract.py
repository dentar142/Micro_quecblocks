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


if __name__ == "__main__":
    unittest.main()
