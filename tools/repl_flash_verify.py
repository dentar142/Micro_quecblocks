"""Upload starter files to a MicroPython board over REPL and run checks.

Example:
    python -B competition-offline-kit/tools/repl_flash_verify.py --port COM17

This uses raw REPL, so no network, Thonny automation, or mpremote dependency is
required.  Close Thonny's serial connection before running this script.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import time

import serial


ROOT = Path(__file__).resolve().parents[1]
STARTER = ROOT / "runtime" / "starter"


DEFAULT_VERIFY_COMMANDS = (
    "preflight",
    "led",
    "adc",
    "i2c",
    "sensors",
    "timer",
    "spi_lcd",
    "storage",
)


class RawReplError(RuntimeError):
    pass


class RawRepl:
    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 2.0):
        self.serial = serial.Serial(port, baudrate, timeout=timeout, write_timeout=timeout)

    def close(self) -> None:
        self.serial.close()

    def read_until(self, marker: bytes, timeout: float = 8.0) -> bytes:
        deadline = time.time() + timeout
        data = bytearray()
        while time.time() < deadline:
            chunk = self.serial.read(1)
            if chunk:
                data.extend(chunk)
                if data.endswith(marker):
                    return bytes(data)
            else:
                time.sleep(0.02)
        raise TimeoutError("timed out waiting for {!r}; got {!r}".format(marker, bytes(data[-200:])))

    def enter_raw_repl(self, timeout: float = 120.0) -> None:
        self.serial.reset_input_buffer()
        marker = b"raw REPL; CTRL-B to exit\r\n>"
        deadline = time.time() + timeout
        last_error = None
        while time.time() < deadline:
            self.serial.write(b"\r\x03\x03")
            time.sleep(0.15)
            self.serial.write(b"\x01")
            try:
                data = self.read_until(marker, timeout=min(2.0, max(0.1, deadline - time.time())))
                if data.endswith(marker):
                    return
            except TimeoutError as error:
                last_error = error
        raise TimeoutError("timed out entering raw REPL: {}".format(last_error))

    def exit_raw_repl(self) -> None:
        self.serial.write(b"\x02")
        time.sleep(0.2)

    def exec(self, code: str, timeout: float = 20.0) -> tuple[str, str]:
        payload = code.encode("utf-8")
        self.serial.write(payload)
        self.serial.write(b"\x04")
        ok = self.read_until(b"OK", timeout=timeout)
        if not ok.endswith(b"OK"):
            raise RawReplError("no OK from raw REPL: {!r}".format(ok))
        stdout = self.read_until(b"\x04", timeout=timeout)[:-1]
        stderr = self.read_until(b"\x04", timeout=timeout)[:-1]
        self.read_until(b">", timeout=timeout)
        out_text = stdout.decode("utf-8", "replace")
        err_text = stderr.decode("utf-8", "replace")
        if err_text.strip():
            raise RawReplError(err_text)
        return out_text, err_text


def board_path_for(local_path: Path) -> str:
    rel = local_path.relative_to(STARTER).as_posix()
    return rel


def iter_upload_files() -> list[Path]:
    files = []
    for path in STARTER.rglob("*"):
        if path.is_file() and path.suffix == ".py":
            if "__pycache__" not in path.parts:
                files.append(path)
    return sorted(files)


def iter_upload_dirs(files: list[Path]) -> list[str]:
    dirs = set()
    for path in files:
        parent = path.parent
        if parent == STARTER:
            continue
        rel = parent.relative_to(STARTER)
        parts = rel.parts
        for index in range(1, len(parts) + 1):
            dirs.add(Path(*parts[:index]).as_posix())
    return sorted(dirs, key=lambda item: (item.count("/"), item))


def mkdirs(repl: RawRepl, files: list[Path]) -> None:
    dirs = iter_upload_dirs(files)
    code = """
try:
    import uos as os
except ImportError:
    import os
for d in {!r}:
    try:
        os.mkdir(d)
    except OSError:
        pass
""".format(tuple(dirs))
    repl.exec(code)


def remove_existing(repl: RawRepl, remote_path: str) -> None:
    repl.exec(
        """
try:
    import uos as os
except ImportError:
    import os
try:
    os.remove({!r})
except OSError:
    pass
""".format(remote_path)
    )


def upload_file(repl: RawRepl, local_path: Path, chunk_size: int = 512) -> None:
    remote_path = board_path_for(local_path)
    data = local_path.read_bytes()
    remove_existing(repl, remote_path)
    repl.exec("f=open({!r}, 'wb'); f.close()".format(remote_path))
    for offset in range(0, len(data), chunk_size):
        chunk = data[offset : offset + chunk_size]
        repl.exec(
            "f=open({!r}, 'ab'); f.write({!r}); f.close()".format(remote_path, chunk),
            timeout=20.0,
        )
    repl.exec(
        """
import os
size = os.stat({!r})[6]
print('UPLOADED {} bytes=' + str(size))
""".format(remote_path, remote_path)
    )


def verify(repl: RawRepl, commands: tuple[str, ...]) -> str:
    command_list = ",".join(commands)
    code = """
from universal_main import UniversalKit
app = UniversalKit()
for name in {!r}.split(','):
    if name:
        app.run(name)
app.reporter.summary()
""".format(command_list)
    out, _err = repl.exec(code, timeout=90.0)
    return out


def soft_reset(repl: RawRepl) -> str:
    # Keep reset optional: main.py enters interactive mode, which is useful for
    # contestants but not necessary for automated verification.
    repl.serial.write(b"\x04")
    time.sleep(2.0)
    return repl.serial.read(8192).decode("utf-8", "replace")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True)
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument("--verify", default=",".join(DEFAULT_VERIFY_COMMANDS))
    parser.add_argument("--skip-verify", action="store_true")
    parser.add_argument("--soft-reset", action="store_true")
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        help="upload only this starter-relative path; may be repeated",
    )
    args = parser.parse_args(argv)

    files = iter_upload_files()
    if args.only:
        requested = {item.replace("\\", "/") for item in args.only}
        files = [path for path in files if board_path_for(path) in requested]
        missing = sorted(requested - {board_path_for(path) for path in files})
        if missing:
            print("[FLASH][FAIL] unknown --only paths: {}".format(", ".join(missing)), file=sys.stderr)
            return 2
    if not files:
        print("[FLASH][FAIL] no starter Python files found", file=sys.stderr)
        return 2

    repl = RawRepl(args.port, args.baudrate)
    try:
        repl.enter_raw_repl()
        mkdirs(repl, files)
        for path in files:
            remote = board_path_for(path)
            print("[FLASH][WRITE] {} -> {}".format(path.relative_to(ROOT), remote))
            upload_file(repl, path)
        print("[FLASH][PASS] files={}".format(len(files)))
        if not args.skip_verify:
            commands = tuple(item.strip() for item in args.verify.split(",") if item.strip())
            output = verify(repl, commands)
            print(output, end="" if output.endswith("\n") else "\n")
        if args.soft_reset:
            print(soft_reset(repl), end="")
        repl.exit_raw_repl()
        return 0
    finally:
        repl.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
