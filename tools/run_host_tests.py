"""Run host-side syntax checks and pure-Python tests."""

from pathlib import Path
import subprocess
import sys
import tokenize

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime" / "starter"


def compile_python_files():
    failed = []
    for path in ROOT.rglob("*.py"):
        try:
            with tokenize.open(path) as source_file:
                compile(source_file.read(), str(path), "exec")
        except Exception as exc:  # pragma: no cover - surfaced by return code
            failed.append((path, exc))
    if failed:
        for path, exc in failed:
            print("[COMPILE][FAIL] {} {}".format(path, exc))
        return 1
    print("[COMPILE][PASS] all python files")
    return 0


def run_unittest():
    cmd = [sys.executable, "-B", "-m", "unittest", "discover", "-s", str(ROOT / "host_tests")]
    env = dict(__import__("os").environ)
    env["PYTHONPATH"] = str(RUNTIME) + ";" + env.get("PYTHONPATH", "")
    return subprocess.call(cmd, env=env)


if __name__ == "__main__":
    rc = compile_python_files()
    if rc:
        sys.exit(rc)
    sys.exit(run_unittest())
