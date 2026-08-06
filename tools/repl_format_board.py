"""Format the board's MicroPython user filesystem over raw REPL."""

import argparse
import sys

from repl_flash_verify import RawRepl


FORMAT = """
import os
import pyb
if not hasattr(os, "VfsFat"):
    raise RuntimeError("VfsFat is unavailable on this firmware")
disk = pyb.Flash()
mbr = bytearray(512)
disk.readblocks(0, mbr)
entry = mbr[446:462]
part_start = int.from_bytes(entry[8:12], "little")
part_size = int.from_bytes(entry[12:16], "little")
if part_start <= 0 or part_size <= 0:
    raise RuntimeError("invalid flash partition table")

class Partition:
    def __init__(self, device, start, size):
        self.device = device
        self.start = start
        self.size = size

    def readblocks(self, block, buffer):
        return self.device.readblocks(self.start + block, buffer)

    def writeblocks(self, block, buffer):
        return self.device.writeblocks(self.start + block, buffer)

    def ioctl(self, operation, argument):
        if operation == 4:
            return self.size
        if operation == 5:
            return 512
        return self.device.ioctl(operation, argument)

print("CWD_BEFORE", os.getcwd())
print("PARTITION", part_start, part_size)
os.chdir("/")
try:
    os.umount("/flash")
except OSError:
    pass
partition = Partition(disk, part_start, part_size)
os.VfsFat.mkfs(partition)
print("FORMAT_PASS")
"""


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM17")
    args = parser.parse_args(argv)

    repl = RawRepl(args.port)
    try:
        repl.enter_raw_repl()
        output, _error = repl.exec(FORMAT, timeout=90.0)
        print(output, end="" if output.endswith("\n") else "\n")
        if "FORMAT_PASS" not in output:
            return 1
        print("[FORMAT][PASS]")
        return 0
    finally:
        repl.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
