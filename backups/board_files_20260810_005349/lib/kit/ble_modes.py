"""Lazy BLE server/client backend for easy_api."""


class EasyBLE:
    def __init__(self, config, sleep_ms, ticks_ms, ticks_diff, ascii_hex):
        self.config = config
        self.sleep_ms = sleep_ms
        self.ticks_ms = ticks_ms
        self.ticks_diff = ticks_diff
        self.ascii_hex = ascii_hex
        self.obj = None
        self.mode = getattr(config, "BLE_MODE", "server")
        self.active_mode = None
        self.target_name = getattr(config, "BLE_CLIENT_TARGET_NAME", config.BLE_NAME)
        self.error = None
        self.addr = None
        self.connected = False
        self.notify_enabled = False
        self.last_event = None
        self.last_value = None
        self.last_sent = None
        self.received_values = []
        self.target_addr = None
        self.target_addr_type = None
        self.scan_results = []
        self.conn_id = -1
        self.mtu = 0
        self.services = []
        self.chars = []
        self.current_char = None

    def normalize_mode(self, mode=None):
        mode = self.mode if mode is None else str(mode).strip().lower()
        if mode in ("client", "central", "master", "scan", "scanner", "客户端", "中心端"):
            return "client"
        return "server"

    def clean_name(self, name):
        return "" if name is None else str(name).replace("\x00", "").strip()

    def reset_runtime(self):
        self.addr = None
        self.connected = False
        self.notify_enabled = False
        self.last_event = None
        self.last_value = None
        self.last_sent = None
        self.received_values = []
        self.target_addr = None
        self.target_addr_type = None
        self.scan_results = []
        self.conn_id = -1
        self.mtu = 0
        self.services = []
        self.chars = []
        self.current_char = None

    def stop(self):
        if self.obj:
            try:
                if self.active_mode == "client" and self.connected:
                    fn = getattr(self.obj, "disconnect", None)
                    if fn:
                        fn()
                for name in ("stop", "deinit"):
                    fn = getattr(self.obj, name, None)
                    if fn:
                        fn()
            except Exception:
                pass
        self.obj = None
        self.active_mode = None
        self.reset_runtime()

    def set_mode(self, mode="server", target_name=None):
        mode = self.normalize_mode(mode)
        old_target_name = self.clean_name(self.target_name)
        if target_name is not None:
            self.target_name = self.clean_name(target_name)
            self.config.BLE_CLIENT_TARGET_NAME = self.target_name
        if mode != self.mode or (mode == "client" and target_name is not None and old_target_name != self.clean_name(self.target_name)):
            self.stop()
        self.mode = mode
        self.config.BLE_MODE = mode
        self.error = None
        return True

    def server_cb(self, evt):
        self.last_event = evt
        try:
            from quectel import BLE
            event = evt.get("event")
            if event == BLE.EVT_CONNECTED:
                self.connected = True
            elif event == BLE.EVT_DISCONNECTED:
                self.connected = False
                self.notify_enabled = False
            elif event == BLE.EVT_VAL_DATA:
                self.last_value = evt.get("value")
                self._queue_received(self.last_value)
            elif event == BLE.EVT_DESCDATA:
                if evt.get("desc_uuid") == self.config.BLE_CCCD_UUID and evt.get("uuid") == self.config.BLE_CHAR_UUID:
                    self.notify_enabled = str(evt.get("value")).upper() in ("0100", "0200")
        except Exception as exc:
            self.error = str(exc)

    def client_cb(self, evt):
        self.last_event = evt
        try:
            from quectel import BLEClient
            event = evt.get("event")
            if event == BLEClient.EVT_SCAN_RESULT:
                name = self.clean_name(evt.get("name"))
                item = {"name": name, "addr": evt.get("addr"), "addr_type": evt.get("addr_type"), "rssi": evt.get("rssi")}
                self.scan_results.append(item)
                if name == self.clean_name(self.target_name) and self.target_addr is None:
                    self.target_addr = item["addr"]
                    self.target_addr_type = item["addr_type"]
            elif event == BLEClient.EVT_CONNECTED:
                self.connected = True
                conn_id = evt.get("conn_id")
                self.conn_id = conn_id if conn_id is not None else -1
            elif event == BLEClient.EVT_DISCONNECTED:
                self.connected = False
                self.conn_id = -1
            elif event == BLEClient.EVT_MTU:
                self.mtu = evt.get("mtu", 0)
            elif event == BLEClient.EVT_SERVICE:
                uuid = evt.get("uuid")
                start = evt.get("start_handle")
                end = evt.get("end_handle")
                if uuid not in (0x1800, 0x1801) and start is not None and end is not None:
                    self.services.append({"uuid": uuid, "start": start, "end": end})
            elif event == BLEClient.EVT_CHARACTER:
                uuid = evt.get("uuid")
                decl = evt.get("handle")
                value = evt.get("value_handle")
                if uuid is not None and decl is not None and value is not None:
                    self.chars.append({"uuid": uuid, "decl_handle": decl, "value_handle": value, "prop": evt.get("properties"), "service_end": 0, "cccd": -1})
            elif event == BLEClient.EVT_DESCRIPTOR:
                if evt.get("uuid") == self.config.BLE_CCCD_UUID and self.current_char is not None:
                    self.current_char["cccd"] = evt.get("handle")
            elif event in (BLEClient.EVT_READ_RESULT, BLEClient.EVT_NOTIFY, BLEClient.EVT_INDICATE):
                self.last_value = evt.get("value")
                self._queue_received(self.last_value)
            elif event == BLEClient.EVT_WRITE_RESULT:
                self.last_value = evt
        except Exception as exc:
            self.error = str(exc)

    def _queue_received(self, value):
        if value is None:
            return
        queue_max = max(1, int(getattr(self.config, "BLE_RX_QUEUE_MAX", 8)))
        self.received_values.append(value)
        if len(self.received_values) > queue_max:
            self.received_values.pop(0)

    def read_received(self):
        if not self.received_values:
            return None
        return self.received_values.pop(0)

    def ensure_server(self):
        if self.obj and self.active_mode == "server":
            return self.obj
        self.stop()
        try:
            from quectel import BLE
            obj = BLE()
            if obj.init(self.server_cb) is False:
                self.error = "server init failed"
                return None
            fn = getattr(obj, "set_dataformat", None)
            if fn:
                fn(BLE.DATAFMT_STRING)
            try:
                obj.stop()
                self.sleep_ms(200)
            except Exception:
                pass
            try:
                result = obj.start(self.config.BLE_NAME)
            except Exception as exc:
                result = exc
            if result not in (None, True, 0):
                self.error = "server start failed: {}".format(result)
                try:
                    obj.stop()
                    self.sleep_ms(200)
                    obj.deinit()
                except Exception:
                    pass
                return None
            self.addr = getattr(obj, "get_addr", lambda: None)()
            obj.add_service(0, self.config.BLE_SERVICE_UUID, True)
            props = BLE.PROP_READ | BLE.PROP_WRITE | BLE.PROP_NOTIFY | BLE.PROP_INDICATE
            obj.add_character(0, 0, props, self.config.BLE_CHAR_UUID)
            obj.set_character_value(0, 0, BLE.PERM_READ | BLE.PERM_WRITE, self.config.BLE_CHAR_UUID, getattr(self.config, "BLE_CHAR_MAX_LEN", 32), self.ascii_hex("ready"))
            obj.add_descriptor(0, 0, BLE.PERM_READ | BLE.PERM_WRITE, self.config.BLE_CCCD_UUID, "0000")
            adv = getattr(obj, "advertise", None)
            if adv:
                adv()
            self.obj = obj
            self.active_mode = "server"
            self.error = None
            return obj
        except Exception as exc:
            self.error = str(exc)
            return None

    def ensure_client(self):
        if self.obj and self.active_mode == "client":
            return self.obj
        self.stop()
        try:
            from quectel import BLEClient
            obj = BLEClient()
            if obj.init(self.client_cb) is False:
                self.error = "client init failed"
                return None
            try:
                obj.stop()
                self.sleep_ms(200)
            except Exception:
                pass
            result = obj.start()
            if result not in (None, True, 0):
                self.error = "client start failed: {}".format(result)
                try:
                    obj.stop()
                    self.sleep_ms(200)
                    obj.deinit()
                except Exception:
                    pass
                return None
            try:
                scan_type = getattr(BLEClient, getattr(self.config, "BLE_SCAN_TYPE", "SCAN_ACTIVE"), None)
                if scan_type is None:
                    scan_type = getattr(BLEClient, "SCAN_ACTIVE", getattr(BLEClient, "SCAN_PASSIVE", 0))
                interval = int(getattr(self.config, "BLE_SCAN_INTERVAL", 0x60))
                window = int(getattr(self.config, "BLE_SCAN_WINDOW", interval))
                if window > interval:
                    window = interval
                filter_policy = getattr(BLEClient, "SCAN_FILTER_ALL", 0)
                addr_type = getattr(BLEClient, "ADDR_PUBLIC", 0)
                obj.set_scan_params(scan_type, interval, window, filter_policy, addr_type)
            except Exception as exc:
                self.error = str(exc)
            if self.clean_name(self.target_name):
                fn = getattr(obj, "set_name_filter", None)
                if fn:
                    fn(self.target_name)
            self.obj = obj
            self.active_mode = "client"
            self.error = None
            return obj
        except Exception as exc:
            self.error = str(exc)
            return None

    def enable(self, mode=None, target_name=None):
        if mode is not None or target_name is not None:
            self.set_mode(mode or self.mode, target_name)
        return (self.ensure_client() if self.mode == "client" else self.ensure_server()) is not None

    def scan(self, timeout=5000, target_name=None):
        self.set_mode("client", self.target_name if target_name is None else target_name)
        obj = self.ensure_client()
        if not obj:
            return []
        self.scan_results = []
        self.target_addr = None
        self.target_addr_type = None
        try:
            obj.scan(True)
            start = self.ticks_ms()
            while self.ticks_diff(self.ticks_ms(), start) < int(timeout):
                if self.target_name and self.target_addr is not None:
                    break
                self.sleep_ms(100)
            obj.scan(False)
        except Exception as exc:
            self.error = str(exc)
            try:
                obj.scan(False)
            except Exception:
                pass
        return self.scan_results

    def connect(self, target_name=None, timeout=10000):
        self.set_mode("client", self.target_name if target_name is None else target_name)
        obj = self.ensure_client()
        if not obj:
            return False
        if self.target_addr is None:
            self.scan(min(int(timeout), 5000), self.target_name)
        if self.target_addr is None:
            self.error = "client target not found"
            return False
        try:
            obj.connect(self.target_addr_type, self.target_addr)
            start = self.ticks_ms()
            while not self.connected and self.ticks_diff(self.ticks_ms(), start) < int(timeout):
                self.sleep_ms(100)
            return self.connected
        except Exception as exc:
            self.error = str(exc)
            return False

    def discover(self, timeout=5000):
        obj = self.ensure_client()
        if not obj or not self.connected:
            self.error = "client not connected"
            return False
        try:
            self.services = []
            self.chars = []
            obj.discover_services(self.conn_id)
            self.sleep_ms(min(1500, int(timeout)))
            for service in self.services:
                before = len(self.chars)
                obj.discover_characteristics(self.conn_id, service["start"], service["end"])
                self.sleep_ms(800)
                for index in range(before, len(self.chars)):
                    self.chars[index]["service_end"] = service["end"]
            ordered = sorted(self.chars, key=lambda item: item["decl_handle"])
            for index, char in enumerate(ordered):
                start = char["value_handle"] + 1
                end = ordered[index + 1]["decl_handle"] - 1 if index + 1 < len(ordered) else char["service_end"]
                if start <= end:
                    self.current_char = char
                    obj.discover_descriptors(self.conn_id, start, end)
                    self.sleep_ms(400)
            self.current_char = None
            self.error = None
            return True
        except Exception as exc:
            self.current_char = None
            self.error = str(exc)
            return False

    def read_handle(self, handle=None):
        self.set_mode("client")
        obj = self.ensure_client()
        handle = getattr(self.config, "BLE_CLIENT_VALUE_HANDLE", None) if handle is None else handle
        if not obj or not self.connected or handle is None:
            self.error = "client not connected or value handle missing"
            return None
        try:
            obj.read_char_by_handle(self.conn_id, int(handle))
            return True
        except Exception as exc:
            self.error = str(exc)
            return False

    def write_handle(self, handle, data):
        self.set_mode("client")
        obj = self.ensure_client()
        if not obj or not self.connected:
            self.error = "client not connected"
            return False
        try:
            text = str(data)
            obj.write_char(self.conn_id, int(handle), len(text.encode()), self.ascii_hex(text))
            return True
        except Exception as exc:
            self.error = str(exc)
            return False

    def send(self, data, handle=None):
        obj = self.ensure_client() if self.mode == "client" else self.ensure_server()
        if not obj:
            return None
        text = str(data)
        if self.mode == "client":
            handle = getattr(self.config, "BLE_CLIENT_VALUE_HANDLE", None) if handle is None else handle
            result = False if handle is None else self.write_handle(handle, text)
            if result:
                self.last_sent = text
            return result
        if not self.connected:
            self.error = "server not connected"
            return False
        try:
            from quectel import BLE
            obj.set_character_value(0, 0, BLE.PERM_READ | BLE.PERM_WRITE, self.config.BLE_CHAR_UUID, getattr(self.config, "BLE_CHAR_MAX_LEN", 32), self.ascii_hex(text))
            if self.connected and self.notify_enabled:
                fn = getattr(obj, "notify", None)
                if fn:
                    fn(self.config.BLE_CHAR_UUID, len(text), text)
            self.last_sent = text
            return True
        except Exception as exc:
            self.error = str(exc)
            return False

    def status(self):
        ready = self.obj is not None
        data = {"name": self.config.BLE_NAME, "mode": self.mode, "ready": ready, "error": self.error}
        if self.mode == "client":
            data.update({"target_name": self.target_name, "connected": self.connected, "conn_id": self.conn_id, "mtu": self.mtu, "target_addr": self.target_addr, "scan_count": len(self.scan_results), "services": self.services, "chars": self.chars, "last_value": self.last_value, "last_sent": self.last_sent, "last_event": self.last_event})
        else:
            data.update({"addr": self.addr, "connected": self.connected, "notify_enabled": self.notify_enabled, "last_value": self.last_value, "last_sent": self.last_sent, "last_event": self.last_event})
        return data
