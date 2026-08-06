"""Verify Scratch-style easy_api operators on an already-flashed board."""

import argparse
import sys
import time

from repl_flash_verify import RawRepl


INSPECT = """
import os
import sys
print("EASY_SIZE", os.stat("easy_api.py")[6])
print("OPERATORS_SIZE", os.stat("lib/alg/operators.py")[6])
print("EASY_LOADED", "easy_api" in sys.modules)
print("ROOT", os.listdir(b"."))
print("LIB", os.listdir(b"lib"))
print("ALG", os.listdir(b"lib/alg"))
"""


CHECK = """
import gc
import os
gc.collect()
import easy_api as api
print("OPERATORS_SIZE", os.stat("lib/alg/operators.py")[6])
print("ADD", api.yunsuan(7, "+", 5))
print("DIV0", api.yunsuan(1, "/", 0))
print("SQRT", api.shuxue("sqrt", 81))
print("COMPARE", api.bijiao("HELLO", "==", "hello"))
print("LOGIC", api.luoji(True, "and", 1))
print("LETTER", api.wenbenzifu("ABC", 2))
print("CONTAINS", api.wenbenbaohan("UniKnect", "knect"))
print("TO_NUMBER", api.zhuanshuzi("12.5"))
numeric_ok = (
    api.yunsuan(7, "-", 5) == 2 and
    api.yunsuan(7, "*", 5) == 35 and
    api.yunsuan(7, "/", 2) == 3.5 and
    api.yunsuan(7, "//", 2) == 3 and
    api.yunsuan(7, "%", 2) == 1 and
    api.yunsuan(2, "**", 3) == 8
)
random_ok = True
for _ in range(20):
    value = api.suijishu(2, 4)
    if value not in (2, 3, 4):
        random_ok = False
math_ok = (
    api.shuxue("round", 2.5) == 3 and
    api.shuxue("abs", -3) == 3 and
    api.shuxue("floor", 2.9) == 2 and
    api.shuxue("ceil", 2.1) == 3 and
    api.shuxue("sqrt", -1) is None and
    abs(api.shuxue("sin", 30) - 0.5) < 0.001 and
    abs(api.shuxue("cos", 60) - 0.5) < 0.001 and
    abs(api.shuxue("tan", 45) - 1.0) < 0.001 and
    abs(api.shuxue("asin", 0.5) - 30.0) < 0.001 and
    abs(api.shuxue("acos", 0.5) - 60.0) < 0.001 and
    abs(api.shuxue("atan", 1) - 45.0) < 0.001 and
    abs(api.shuxue("ln", 1)) < 0.001 and
    abs(api.shuxue("log10", 100) - 2.0) < 0.001 and
    abs(api.shuxue("exp", 1) - 2.7182818) < 0.001 and
    api.shuxue("pow10", 2) == 100
)
compare_ok = (
    api.bijiao(2, "!=", 3) and
    api.bijiao(3, ">", 2) and
    api.bijiao(3, ">=", 3) and
    api.bijiao(2, "<", 3) and
    api.bijiao(3, "<=", 3)
)
logic_ok = api.luoji(False, "or", True) and api.luoji(False, "not")
text_ok = (
    api.wenbenchangdu("ABC") == 3 and
    api.wenbenzifu("ABC", 0) == "" and
    api.zhuanshuzi("bad") == 0 and
    api.zhuanwenzi(12) == "12"
)
print("NUMERIC_ALL", numeric_ok)
print("RANDOM", random_ok)
print("MATH_ALL", math_ok)
print("COMPARE_ALL", compare_ok)
print("LOGIC_ALL", logic_ok)
print("TEXT_ALL", text_ok)
"""


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM17")
    args = parser.parse_args(argv)

    repl = RawRepl(args.port)
    entered_raw_repl = False
    try:
        repl.enter_raw_repl()
        entered_raw_repl = True
        inspection, _error = repl.exec(INSPECT, timeout=10.0)
        print(inspection, end="" if inspection.endswith("\n") else "\n")
        output, _error = repl.exec(CHECK, timeout=30.0)
        print(output, end="" if output.endswith("\n") else "\n")
        required = (
            "ADD 12",
            "DIV0 None",
            "SQRT 9.0",
            "COMPARE True",
            "LOGIC True",
            "LETTER B",
            "CONTAINS True",
            "TO_NUMBER 12.5",
            "NUMERIC_ALL True",
            "RANDOM True",
            "MATH_ALL True",
            "COMPARE_ALL True",
            "LOGIC_ALL True",
            "TEXT_ALL True",
        )
        missing = [line for line in required if line not in output]
        if missing:
            print("[OPERATOR_BOARD][FAIL] missing={}".format(missing))
            return 1
        print("[OPERATOR_BOARD][PASS]")
        repl.exit_raw_repl()
        entered_raw_repl = False
        repl.serial.write(b"\x04")
        time.sleep(1.0)
        startup = repl.serial.read(8192).decode("utf-8", "replace")
        if startup:
            encoding = sys.stdout.encoding or "utf-8"
            safe_startup = startup.encode(encoding, "replace").decode(encoding)
            print(safe_startup, end="" if safe_startup.endswith("\n") else "\n")
        return 0
    finally:
        if entered_raw_repl:
            try:
                repl.exit_raw_repl()
            except Exception:
                pass
        repl.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
