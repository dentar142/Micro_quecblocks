"""Verify SD-card write/read and record/playback through easy_api."""

import argparse
import sys
import time

from repl_flash_verify import RawRepl


CHECK = """
import gc
import easy_api as api

storage_path = "SD:codex_storage_check.txt"
audio_path = "SD:codex_audio_check.wav"
payload = b"Quectel SD storage verification 2026"

api.yinpin(0)
gc.collect()

storage_enabled = api.cunchu(1)
storage_write = api.writefile(storage_path, payload)
storage_data = api.readfile(storage_path, 256, b"")
storage_match = storage_data == payload
storage_remove = api.removefile(storage_path)
storage_probe = api.teststorage()

print("STORAGE_ENABLED", storage_enabled)
print("STORAGE_WRITE", storage_write)
print("STORAGE_READ_BYTES", len(storage_data))
print("STORAGE_MATCH", storage_match)
print("STORAGE_REMOVE", storage_remove)
print("STORAGE_PROBE", storage_probe)

audio_enabled = api.yinpin(1)
record_ok = api.record(audio_path, 2500) if audio_enabled else False
api.delay(500)
audio_sample = api.readfile(audio_path, 512, b"")
audio_stored = len(audio_sample) > 0
play_ok = api.playfile(audio_path, True) if audio_stored else False

print("AUDIO_ENABLED", audio_enabled)
print("AUDIO_RECORD", record_ok)
print("AUDIO_SAMPLE_BYTES", len(audio_sample))
print("AUDIO_STORED", audio_stored)
print("AUDIO_PLAY_END", play_ok)
print("AUDIO_FILE", audio_path)
api.yinpin(0)
"""


def safe_print(value):
    encoding = sys.stdout.encoding or "utf-8"
    value = value.encode(encoding, "replace").decode(encoding)
    print(value, end="" if value.endswith("\n") else "\n")


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM17")
    args = parser.parse_args(argv)

    repl = RawRepl(args.port)
    entered_raw_repl = False
    try:
        repl.enter_raw_repl()
        entered_raw_repl = True
        output, _error = repl.exec(CHECK, timeout=45.0)
        safe_print(output)
        required = (
            "STORAGE_WRITE True",
            "STORAGE_MATCH True",
            "STORAGE_REMOVE True",
            "STORAGE_PROBE True",
            "AUDIO_ENABLED True",
            "AUDIO_RECORD True",
            "AUDIO_STORED True",
            "AUDIO_PLAY_END True",
        )
        missing = [line for line in required if line not in output]
        if missing:
            print("[STORAGE_AUDIO_BOARD][FAIL] missing={}".format(missing))
            return 1
        print("[STORAGE_AUDIO_BOARD][PASS]")
        repl.exit_raw_repl()
        entered_raw_repl = False
        repl.serial.write(b"\x04")
        time.sleep(2.0)
        startup = repl.serial.read(8192).decode("utf-8", "replace")
        if startup:
            safe_print(startup)
        return 0
    finally:
        if entered_raw_repl:
            try:
                repl.exit_raw_repl()
                repl.serial.write(b"\x04")
            except Exception:
                pass
        repl.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
