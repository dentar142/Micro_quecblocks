"""Measure MicroPython heap usage while importing the competition API."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from repl_flash_verify import RawRepl, RawReplError


PROBES = (
    ("baseline", "pass"),
    ("config", "import config"),
    ("compat", "from lib.kit.compat import sleep_ms, ticks_diff, ticks_ms"),
    ("easy_api", "import easy_api"),
)


def run_probe(repl: RawRepl, label: str, statement: str) -> bool:
    code = """
import gc
gc.collect()
print('MEM_BEFORE {label}', gc.mem_free(), gc.mem_alloc())
{statement}
gc.collect()
print('MEM_AFTER {label}', gc.mem_free(), gc.mem_alloc())
""".format(label=label, statement=statement)
    try:
        output, _ = repl.exec(code, timeout=30.0)
    except RawReplError as exc:
        print("[PROBE][FAIL] {} {}".format(label, exc))
        return False
    print(output, end="" if output.endswith("\n") else "\n")
    return True


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM17")
    args = parser.parse_args(argv)

    repl = RawRepl(args.port, timeout=2.0)
    try:
        repl.enter_raw_repl()
        output, _ = repl.exec(
            """
import gc
import sys
try:
    import uos as os
except ImportError:
    import os
gc.collect()
print('BOARD_FILES', os.listdir())
print('CWD', os.getcwd())
print('SYS_PATH', sys.path)
try:
    print('API_PARTS', os.listdir('easy_api_parts'))
    for part_name in os.listdir('easy_api_parts'):
        print('API_PART', part_name, os.stat('easy_api_parts/' + part_name)[6])
except OSError as exc:
    print('API_PARTS_ERROR', exc)
print('HEAP', gc.mem_free(), gc.mem_alloc())
"""
        )
        print(output, end="" if output.endswith("\n") else "\n")
        for label, statement in PROBES:
            if not run_probe(repl, label, statement):
                return 1
        return 0
    finally:
        try:
            repl.exit_raw_repl()
        except Exception:
            pass
        repl.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
