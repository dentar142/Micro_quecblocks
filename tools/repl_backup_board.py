"""Back up all readable files from a MicroPython board over raw REPL."""

import argparse
import base64
from datetime import datetime
from pathlib import Path
import sys

from repl_flash_verify import RawRepl


LIST_CODE = r'''
import os

def _is_dir_mode(mode):
    return (mode & 0x4000) != 0

def _join(base, name):
    return name if not base else base + "/" + name

def _walk(base):
    try:
        names = os.listdir(base if base else ".")
    except Exception as exc:
        print("E|" + base + "|" + repr(exc))
        return
    for name in names:
        if name in (".", ".."):
            continue
        path = _join(base, name)
        try:
            st = os.stat(path)
            if _is_dir_mode(st[0]):
                print("D|" + path + "|0")
                _walk(path)
            else:
                print("F|" + path + "|" + str(st[6]))
        except Exception as exc:
            print("E|" + path + "|" + repr(exc))

_walk("")
'''


def read_code(path: str, chunk_size: int = 384) -> str:
    return r'''
import ubinascii
p = {path!r}
try:
    f = open(p, "rb")
    while True:
        data = f.read({chunk_size})
        if not data:
            break
        encoded = ubinascii.b2a_base64(data)
        try:
            encoded = encoded.decode()
        except Exception:
            pass
        print("C|" + encoded.strip())
    f.close()
    print("OK|")
except Exception as exc:
    print("ERR|" + repr(exc))
'''.format(path=path, chunk_size=chunk_size)


def safe_local_path(root: Path, board_path: str) -> Path:
    parts = [p for p in board_path.replace("\\", "/").split("/") if p and p not in (".", "..")]
    return root.joinpath(*parts)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True)
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument("--dest-root", default=None)
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args(argv)

    repo = Path(__file__).resolve().parents[2]
    workspace = repo.parent
    dest_parent = Path(args.dest_root) if args.dest_root else workspace / "backups"
    dest = dest_parent / ("board_files_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    dest.mkdir(parents=True, exist_ok=False)

    repl = RawRepl(args.port, args.baudrate)
    files: list[tuple[str, int]] = []
    dirs: list[str] = []
    errors: list[str] = []
    try:
        repl.enter_raw_repl()
        out, err = repl.exec(LIST_CODE, timeout=args.timeout)
        if err:
            errors.append("[LIST_REPL_ERR] " + err)
        for line in out.splitlines():
            parts = line.split("|", 2)
            if len(parts) != 3:
                continue
            kind, path, detail = parts
            if kind == "D":
                dirs.append(path)
                safe_local_path(dest, path).mkdir(parents=True, exist_ok=True)
            elif kind == "F":
                try:
                    size = int(detail)
                except ValueError:
                    size = -1
                files.append((path, size))
            elif kind == "E":
                errors.append("LIST " + path + ": " + detail)

        for board_path, expected_size in files:
            local_path = safe_local_path(dest, board_path)
            local_path.parent.mkdir(parents=True, exist_ok=True)
            out, err = repl.exec(read_code(board_path), timeout=args.timeout)
            chunks: list[bytes] = []
            ok = False
            if err:
                errors.append("READ_REPL_ERR " + board_path + ": " + err)
            for line in out.splitlines():
                if line.startswith("C|"):
                    try:
                        chunks.append(base64.b64decode(line[2:].encode()))
                    except Exception as exc:
                        errors.append("DECODE " + board_path + ": " + repr(exc))
                elif line.startswith("OK|"):
                    ok = True
                elif line.startswith("ERR|"):
                    errors.append("READ " + board_path + ": " + line[4:])
            if ok:
                data = b"".join(chunks)
                local_path.write_bytes(data)
                if expected_size >= 0 and len(data) != expected_size:
                    errors.append(
                        "SIZE " + board_path + ": expected {} got {}".format(expected_size, len(data))
                    )
        repl.exit_raw_repl()
    finally:
        repl.close()

    manifest = dest / "_manifest.txt"
    manifest.write_text(
        "\n".join(
            [
                "backup_dir=" + str(dest),
                "dirs=" + str(len(dirs)),
                "files=" + str(len(files)),
                "errors=" + str(len(errors)),
                "",
                "[FILES]",
            ]
            + ["{}\t{}".format(size, path) for path, size in files]
            + ["", "[ERRORS]"]
            + errors
        ),
        encoding="utf-8",
    )

    print("[BACKUP][DIR]", dest)
    print("[BACKUP][FILES]", len(files))
    print("[BACKUP][DIRS]", len(dirs))
    if errors:
        print("[BACKUP][ERRORS]", len(errors))
        for item in errors:
            print("[BACKUP][ERROR]", item)
        return 1
    print("[BACKUP][PASS]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
