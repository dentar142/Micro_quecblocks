"""Small-memory REPL check for BLE, GNSS, LBS and location fallback.

This host-side helper connects to the already-flashed board and runs several
short raw-REPL snippets instead of one large script. That keeps memory pressure
low on MicroPython boards and still prints enough status to diagnose failures.
"""

import argparse
import sys
import textwrap

from repl_flash_verify import RawRepl


STEPS = (
    (
        "cleanup_showcase",
        """
import os, gc
for p in ("easy_api_showcase/main.py", "easy_api_showcase/__init__.py", "easy_api_showcase/README.md"):
    try:
        os.remove(p)
        print("[DEL]", p)
    except Exception as exc:
        print("[DEL_SKIP]", p, exc)
try:
    os.rmdir("easy_api_showcase")
    print("[RMDIR] easy_api_showcase")
except Exception as exc:
    print("[RMDIR_SKIP] easy_api_showcase", exc)
gc.collect()
print("[MEM_FREE]", gc.mem_free() if hasattr(gc, "mem_free") else "unknown")
""",
        20.0,
    ),
    (
        "import_api",
        """
import gc
gc.collect()
import config
import easy_api as api
gc.collect()
print("[CONFIG] NAV_ADC_PIN", config.NAV_ADC_PIN)
print("[CONFIG] GNSS_TIMEOUT_MS", config.GNSS_TIMEOUT_MS)
print("[CONFIG] LBS_TIMEOUT_MS", config.LBS_TIMEOUT_MS)
print("[CONFIG] BLE_RETRY_INTERVAL_MS", getattr(config, "BLE_RETRY_INTERVAL_MS", None))
print("[CONFIG] LBS_RETRY_INTERVAL_MS", getattr(config, "LBS_RETRY_INTERVAL_MS", None))
print("[MEM_FREE]", gc.mem_free() if hasattr(gc, "mem_free") else "unknown")
""",
        40.0,
    ),
    (
        "gnss",
        """
import gc
gc.collect()
print("[GNSS][ENABLE]", api.gnss(1), "ERR", api._errors.get("gnss"))
print("[GNSS][READ]", api.readgnss(), "ERR", api._errors.get("gnss"))
gc.collect()
print("[MEM_FREE]", gc.mem_free() if hasattr(gc, "mem_free") else "unknown")
""",
        40.0,
    ),
    (
        "sim_network",
        """
import gc
gc.collect()
try:
    import sim
    print("[SIM][IMPORT] OK")
    try:
        print("[SIM][STATUS]", sim.getStatus())
    except Exception as exc:
        print("[SIM][STATUS][ERR]", repr(exc))
except Exception as exc:
    print("[SIM][IMPORT][ERR]", repr(exc))
try:
    import net
    print("[NET][IMPORT] OK")
    try:
        print("[NET][STATE]", net.getState())
    except Exception as exc:
        print("[NET][STATE][ERR]", repr(exc))
    try:
        print("[NET][CSQ]", net.csqQueryPoll())
    except Exception as exc:
        print("[NET][CSQ][ERR]", repr(exc))
except Exception as exc:
    print("[NET][IMPORT][ERR]", repr(exc))
try:
    from quectel import Network
    n = Network()
    print("[QUECTEL_NETWORK][IMPORT] OK")
    for method in ("query_usim", "status", "get_status", "get_signal", "query_signal"):
        fn = getattr(n, method, None)
        if fn:
            try:
                print("[QUECTEL_NETWORK][{}]".format(method), fn())
            except Exception as exc:
                print("[QUECTEL_NETWORK][{}][ERR]".format(method), repr(exc))
except Exception as exc:
    print("[QUECTEL_NETWORK][IMPORT][ERR]", repr(exc))
gc.collect()
print("[MEM_FREE]", gc.mem_free() if hasattr(gc, "mem_free") else "unknown")
""",
        60.0,
    ),
    (
        "lbs",
        """
import gc
gc.collect()
print("[LBS][ENABLE]", api.lbs(1), "ERR", api._errors.get("lbs"))
print("[LBS][READ]", api.readlbs(), "ERR", api._errors.get("lbs"))
gc.collect()
print("[MEM_FREE]", gc.mem_free() if hasattr(gc, "mem_free") else "unknown")
""",
        80.0,
    ),
    (
        "location",
        """
import gc
gc.collect()
print("[LOCATION][READ]", api.readlocation(), "ERRS", dict(api._errors))
gc.collect()
print("[MEM_FREE]", gc.mem_free() if hasattr(gc, "mem_free") else "unknown")
""",
        80.0,
    ),
    (
        "ble",
        """
import gc
gc.collect()
print("[BLE][ENABLE]", api.ble(1), "ERR", api._errors.get("ble"))
print("[BLE][READ]", api.readble(), "ERR", api._errors.get("ble"))
gc.collect()
print("[MEM_FREE]", gc.mem_free() if hasattr(gc, "mem_free") else "unknown")
""",
        60.0,
    ),
)


def wrap_step(name: str, code: str) -> str:
    body = textwrap.indent(textwrap.dedent(code).strip(), "    ")
    return (
        "print('[STEP][START] {0}')\n"
        "try:\n"
        "{1}\n"
        "except BaseException as exc:\n"
        "    print('[STEP][ERROR] {0}', repr(exc))\n"
        "print('[STEP][END] {0}')\n"
    ).format(name, body)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True)
    parser.add_argument("--baudrate", type=int, default=115200)
    args = parser.parse_args(argv)

    repl = RawRepl(args.port, args.baudrate)
    try:
        repl.enter_raw_repl()
        for name, code, timeout in STEPS:
            out, err = repl.exec(wrap_step(name, code), timeout=timeout)
            print(out, end="" if out.endswith("\n") else "\n")
            if err:
                print("[REPL_ERR][{}]".format(name))
                print(err, end="" if err.endswith("\n") else "\n")
        repl.exit_raw_repl()
        return 0
    finally:
        repl.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
