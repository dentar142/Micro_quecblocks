"""Upload a browser-generated main.py unchanged and collect a board smoke log."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import sys
import time

from repl_flash_verify import RawRepl


def upload_bytes(repl: RawRepl, data: bytes, chunk_size: int = 512) -> None:
    repl.exec(
        """
try:
    import uos as os
except ImportError:
    import os
try:
    os.remove('main.py')
except OSError:
    pass
f = open('main.py', 'wb')
f.close()
"""
    )
    for offset in range(0, len(data), chunk_size):
        chunk = data[offset : offset + chunk_size]
        repl.exec("f=open('main.py','ab'); f.write({!r}); f.close()".format(chunk))


def board_hash(repl: RawRepl) -> tuple[int, str]:
    output, _ = repl.exec(
        """
try:
    import uhashlib as hashlib
except ImportError:
    import hashlib
f = open('main.py', 'rb')
digest_obj = hashlib.sha256()
size = 0
while True:
    chunk = f.read(256)
    if not chunk:
        break
    size += len(chunk)
    digest_obj.update(chunk)
f.close()
digest = digest_obj.digest()
print(size)
print(''.join('{:02x}'.format(item) for item in digest))
"""
    )
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    return int(lines[-2]), lines[-1]


def collect_after_reset(repl: RawRepl, seconds: float) -> str:
    repl.exit_raw_repl()
    repl.serial.reset_input_buffer()
    repl.serial.write(b"\x04")
    deadline = time.time() + seconds
    data = bytearray()
    while time.time() < deadline:
        chunk = repl.serial.read(4096)
        if chunk:
            data.extend(chunk)
        else:
            time.sleep(0.02)
    repl.serial.write(b"\x03")
    time.sleep(0.2)
    data.extend(repl.serial.read(4096))
    return data.decode("utf-8", "replace")


def without_expected_interrupt(output: str) -> str:
    """Remove only tracebacks caused by the harness stopping an endless main."""
    return re.sub(
        r"Traceback \(most recent call last\):\s*.*?KeyboardInterrupt:\s*",
        "",
        output,
        flags=re.DOTALL,
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM17")
    parser.add_argument("--source", required=True)
    parser.add_argument("--log", required=True)
    parser.add_argument("--seconds", type=float, default=8.0)
    args = parser.parse_args(argv)

    source = Path(args.source).resolve()
    log_path = Path(args.log).resolve()
    if source.name.lower() != "main.py" or not source.is_file():
        raise SystemExit("--source must be an existing browser-downloaded main.py")
    data = source.read_bytes()
    compile(data.decode("utf-8"), str(source), "exec")
    expected_hash = hashlib.sha256(data).hexdigest()

    repl = RawRepl(args.port)
    try:
        repl.enter_raw_repl()
        upload_bytes(repl, data)
        size, actual_hash = board_hash(repl)
        if size != len(data) or actual_hash != expected_hash:
            raise RuntimeError(
                "board byte verification failed: size={}/{} hash={}/{}".format(
                    size, len(data), actual_hash, expected_hash
                )
            )
        output = collect_after_reset(repl, args.seconds)
    finally:
        repl.close()

    log_path.parent.mkdir(parents=True, exist_ok=True)
    header = "UPLOAD_PASS bytes={} sha256={} source={}\n".format(
        len(data), expected_hash, source
    )
    log_path.write_text(header + output, encoding="utf-8")
    print(header, end="")
    print(output, end="" if output.endswith("\n") else "\n")
    if "Traceback (most recent call last)" in without_expected_interrupt(output):
        print("BOARD_SMOKE_FAIL traceback detected", file=sys.stderr)
        return 1
    if "[TEST][LCD][FAIL]" in output:
        print("BOARD_SMOKE_FAIL LCD operation failed", file=sys.stderr)
        return 1
    print("BOARD_SMOKE_PASS seconds={}".format(args.seconds))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
