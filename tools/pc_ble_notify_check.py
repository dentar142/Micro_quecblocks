"""Verify the running full-showcase main.py BLE notifications from a PC."""

from __future__ import annotations

import argparse
import asyncio
from collections import Counter
import time

from bleak import BleakClient, BleakScanner
import serial


DEFAULT_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
EXPECTED_PREFIXES = ("T:", "L:", "X:", "Y:", "Z:")


def reset_board(port: str, baudrate: int) -> None:
    connection = serial.Serial(port, baudrate, timeout=1.0)
    try:
        connection.write(b"\x03")
        time.sleep(0.2)
        connection.reset_input_buffer()
        connection.write(b"\x04")
    finally:
        connection.close()


async def find_device(name: str, timeout: float):
    try:
        return await BleakScanner.find_device_by_name(name, timeout=timeout)
    except AttributeError:
        devices = await BleakScanner.discover(timeout=timeout)
        return next((item for item in devices if item.name == name), None)


async def verify(args: argparse.Namespace) -> Counter:
    device = await find_device(args.name, args.scan_timeout)
    if device is None:
        raise RuntimeError("BLE device not found: {}".format(args.name))

    counts: Counter = Counter()
    received = []

    def on_notify(_sender, data: bytearray) -> None:
        text = bytes(data).decode("utf-8", "replace")
        received.append(text)
        for prefix in EXPECTED_PREFIXES:
            if text.startswith(prefix):
                counts[prefix] += 1
                break
        print("[BLE_NOTIFY] {}".format(text), flush=True)

    async with BleakClient(device) as client:
        if not client.is_connected:
            raise RuntimeError("BLE connection failed")
        await client.start_notify(args.char_uuid, on_notify)
        await asyncio.sleep(args.duration)
        await client.stop_notify(args.char_uuid)

    missing = [
        prefix for prefix in EXPECTED_PREFIXES
        if counts[prefix] < args.minimum_cycles
    ]
    if missing:
        raise RuntimeError(
            "notification stream incomplete: counts={} missing={} raw={}".format(
                dict(counts), missing, received
            )
        )
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM17")
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument("--name", default="Uniknect_BLE_DEMO")
    parser.add_argument("--char-uuid", default=DEFAULT_CHAR_UUID)
    parser.add_argument("--scan-timeout", type=float, default=20.0)
    parser.add_argument("--startup-wait", type=float, default=5.0)
    parser.add_argument("--duration", type=float, default=8.0)
    parser.add_argument("--minimum-cycles", type=int, default=2)
    args = parser.parse_args()

    reset_board(args.port, args.baudrate)
    time.sleep(args.startup_wait)
    counts = asyncio.run(verify(args))
    print("BLE_NOTIFY_PASS {}".format(dict(counts)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
