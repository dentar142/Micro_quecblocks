"""PC + board BLE verification for the competition offline kit.

The script uses COM17 raw REPL to control the board-side easy_api BLE backend,
and uses the PC Bluetooth adapter to verify both board BLE modes:

* board server/peripheral mode: PC scans, connects, reads/writes GATT data.
* board client/central mode: PC publishes a BLE advertisement and the board
  starts client mode then scans for nearby advertisements.

Windows blocks arbitrary Local Name advertising from normal Python processes,
so the client-mode proof uses manufacturer-data advertising unless another
named BLE peripheral is already nearby.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import sys
import time
from typing import Any

try:
    from bleak import BleakClient, BleakScanner
except Exception as exc:  # pragma: no cover - host dependency guard
    raise SystemExit(
        "Missing bleak. Install with: python -m pip install --user bleak\n{}".format(exc)
    )

from winrt.windows.devices.bluetooth.genericattributeprofile import (
    GattCharacteristicProperties,
    GattLocalCharacteristicParameters,
    GattProtectionLevel,
    GattServiceProvider,
    GattServiceProviderAdvertisingParameters,
)
from winrt.windows.storage.streams import DataWriter

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from repl_flash_verify import RawRepl  # noqa: E402


DEFAULT_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
DEFAULT_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"


def log(tag: str, message: str) -> None:
    print("[BLE_VERIFY][{}] {}".format(tag, message), flush=True)


def board_exec(repl: RawRepl, code: str, timeout: float = 30.0) -> str:
    out, _err = repl.exec(code, timeout=timeout)
    return out.strip()


def parse_json_line(output: str) -> dict[str, Any]:
    for line in reversed(output.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict):
            return value
    return {"raw": output}


def board_ble_server(repl: RawRepl, name: str) -> dict[str, Any]:
    code = """
import gc, json
gc.collect()
import easy_api as api
api.ble(0)
gc.collect()
ok = api.ble(1, "server")
status = api.readble()
status["start_ok"] = ok
print(json.dumps(status))
"""
    status = parse_json_line(board_exec(repl, code, timeout=45.0))
    if not status.get("start_ok") or not status.get("ready"):
        raise RuntimeError("board server start failed: {}".format(status))
    if status.get("name") != name:
        log("WARN", "board BLE name is {}, expected {}".format(status.get("name"), name))
    log("SERVER_BOARD", json.dumps(status, ensure_ascii=False))
    return status


def board_ble_client_scan(repl: RawRepl, scan_ms: int) -> dict[str, Any]:
    code = """
import gc, json
gc.collect()
import easy_api as api
api.ble(0)
gc.collect()
ok = api.ble(1, "client", "")
items = api.scanble(%d, "")
status = api.readble()
status["start_ok"] = ok
status["items"] = items
print(json.dumps(status))
""" % scan_ms
    timeout = max(30.0, scan_ms / 1000.0 + 20.0)
    status = parse_json_line(board_exec(repl, code, timeout=timeout))
    if not status.get("start_ok") or not status.get("ready"):
        raise RuntimeError("board client start failed: {}".format(status))
    log("CLIENT_BOARD", json.dumps(status, ensure_ascii=False))
    return status


def board_ble_stop(repl: RawRepl) -> None:
    try:
        out = board_exec(repl, "import easy_api as api\nprint(api.ble(0))\n", timeout=20.0)
        log("BOARD_STOP", out)
    except Exception as exc:
        log("WARN", "board BLE stop failed: {}".format(exc))


async def find_ble_device(name: str, timeout: float):
    log("SERVER_PC_SCAN", "scanning for {} during {:.1f}s".format(name, timeout))
    try:
        device = await BleakScanner.find_device_by_name(name, timeout=timeout)
    except AttributeError:
        devices = await BleakScanner.discover(timeout=timeout)
        device = next((item for item in devices if item.name == name), None)
    if not device:
        devices = await BleakScanner.discover(timeout=5.0)
        names = sorted({getattr(item, "name", None) or "<no name>" for item in devices})
        raise RuntimeError("PC did not find board BLE name {}; seen={}".format(name, names[:20]))
    log("SERVER_PC_SCAN", "found {} {}".format(device.name, device.address))
    return device


async def pc_connect_board_server(name: str, char_uuid: str, scan_timeout: float) -> dict[str, Any]:
    device = await find_ble_device(name, scan_timeout)
    async with BleakClient(device) as client:
        if not bool(client.is_connected):
            raise RuntimeError("PC could not connect to board server")
        services = getattr(client, "services", None)
        char_hit = None
        if services:
            for service in services:
                for char in service.characteristics:
                    if str(char.uuid).lower() == char_uuid.lower():
                        char_hit = char
                        break
                if char_hit:
                    break
        target = char_hit or char_uuid
        try:
            data = await client.read_gatt_char(target)
        except Exception as exc:
            raise RuntimeError("PC connected but characteristic {} unreadable: {}".format(char_uuid, exc))
        try:
            await client.write_gatt_char(target, b"PC_TEST", response=True)
        except Exception:
            await client.write_gatt_char(target, b"PC_TEST", response=False)
        result = {
            "connected": True,
            "address": device.address,
            "char_uuid": str(getattr(char_hit, "uuid", target)),
            "read": bytes(data).decode("utf-8", "replace"),
            "write_ok": True,
        }
        log("SERVER_PC_CONN", json.dumps(result, ensure_ascii=False))
        return result


def _buffer_from_bytes(data: bytes):
    writer = DataWriter()
    writer.write_bytes(bytearray(data))
    return writer.detach_buffer()


class PcGattAdvertiser:
    def __init__(self, service_uuid: str, char_uuid: str, value: bytes = b"PC_READY"):
        self.service_uuid = service_uuid
        self.char_uuid = char_uuid
        self.value = value
        self.provider = None

    async def _create(self) -> None:
        import uuid

        result = await GattServiceProvider.create_async(uuid.UUID(self.service_uuid))
        if int(result.error) != 0:
            raise RuntimeError("PC GATT service create failed: {}".format(result.error))
        provider = result.service_provider
        params = GattLocalCharacteristicParameters()
        params.characteristic_properties = (
            GattCharacteristicProperties.READ
            | GattCharacteristicProperties.WRITE
            | GattCharacteristicProperties.WRITE_WITHOUT_RESPONSE
            | GattCharacteristicProperties.NOTIFY
        )
        params.read_protection_level = GattProtectionLevel.PLAIN
        params.write_protection_level = GattProtectionLevel.PLAIN
        params.user_description = "Uniknect BLE Test"
        params.static_value = _buffer_from_bytes(self.value)
        char_result = await provider.service.create_characteristic_async(uuid.UUID(self.char_uuid), params)
        if int(char_result.error) != 0:
            raise RuntimeError("PC GATT characteristic create failed: {}".format(char_result.error))
        self.provider = provider

    def start(self) -> int:
        asyncio.run(self._create())
        params = GattServiceProviderAdvertisingParameters()
        params.is_discoverable = True
        params.is_connectable = True
        self.provider.start_advertising_with_parameters(params)
        time.sleep(1.0)
        return int(self.provider.advertisement_status)

    def stop(self) -> int:
        if not self.provider:
            return -1
        self.provider.stop_advertising()
        time.sleep(0.2)
        return int(self.provider.advertisement_status)


def run_once(args: argparse.Namespace, cycle: int) -> dict[str, Any]:
    log("CYCLE", "start {}".format(cycle))
    repl = RawRepl(args.port, args.baudrate, timeout=args.serial_timeout)
    advertiser = None
    try:
        repl.enter_raw_repl()
        server_status = board_ble_server(repl, args.name)
        pc_server = asyncio.run(pc_connect_board_server(args.name, args.char_uuid, args.scan_timeout))
        board_ble_stop(repl)
        advertiser = PcGattAdvertiser(args.service_uuid, args.char_uuid)
        adv_status = advertiser.start()
        log("CLIENT_PC_ADV", "connectable GATT advertisement status={}".format(adv_status))
        client_status = board_ble_client_scan(repl, args.client_scan_ms)
        scan_count = int(client_status.get("scan_count") or len(client_status.get("items") or []))
        if scan_count <= 0:
            raise RuntimeError("board client scan returned no advertisements")
        result = {
            "cycle": cycle,
            "server_board": server_status,
            "server_pc": pc_server,
            "pc_adv_status": adv_status,
            "client_board": {
                "ready": client_status.get("ready"),
                "scan_count": scan_count,
                "items_sample": (client_status.get("items") or [])[:5],
            },
        }
        log("CYCLE_PASS", json.dumps(result, ensure_ascii=False))
        return result
    finally:
        if advertiser:
            try:
                log("CLIENT_PC_ADV", "stop status={}".format(advertiser.stop()))
            except Exception as exc:
                log("WARN", "advertiser stop failed: {}".format(exc))
        try:
            board_ble_stop(repl)
            repl.exit_raw_repl()
        finally:
            repl.close()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="COM17")
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument("--serial-timeout", type=float, default=2.0)
    parser.add_argument("--name", default="Uniknect_BLE_DEMO")
    parser.add_argument("--service-uuid", default=DEFAULT_SERVICE_UUID)
    parser.add_argument("--char-uuid", default=DEFAULT_CHAR_UUID)
    parser.add_argument("--scan-timeout", type=float, default=20.0)
    parser.add_argument("--client-scan-ms", type=int, default=8000)
    parser.add_argument("--cycles", type=int, default=1, help="0 means run forever")
    parser.add_argument("--delay", type=float, default=2.0)
    args = parser.parse_args(argv)
    results = []
    cycle = 1
    while True:
        results.append(run_once(args, cycle))
        if args.cycles and cycle >= args.cycles:
            break
        cycle += 1
        time.sleep(max(0.0, args.delay))
    log("PASS", "server/client BLE verification cycles={}".format(len(results)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
