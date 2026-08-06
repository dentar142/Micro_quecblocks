"""麦克风、扬声器和文件系统封装。"""

from .compat import sleep_ms
from .compat import ticks_ms, ticks_diff


class StorageProbe:
    def __init__(self, directory="competition_test"):
        from quectel import File
        self.File = File
        self.directory = directory

    def run(self):
        root = "{}_{}".format(self.directory, ticks_ms())
        path = root + "/probe.txt"
        created_dir = False
        try:
            self.File.mkdir(root)
            created_dir = True
            payload = b"Quectel competition storage test\n"
            with self.File.open(path, "w") as fp:
                fp.write(payload)
            with self.File.open(path, "r") as fp:
                data = fp.read(128)
            ok = data == payload
            try:
                self.File.remove(path)
                if created_dir:
                    self.File.rmdir(root, False)
            except Exception:
                pass
            return ok, "bytes={}".format(len(data))
        except Exception as exc:
            return False, str(exc)


class AudioProbe:
    def __init__(self, record_file="SD:competition_test.wav"):
        from quectel import Audio
        self.Audio = Audio
        self.record_file = record_file
        self.events = []
        self.audio = None

    def _callback(self, event):
        self.events.append(event)

    def init(self):
        self.audio = self.Audio()
        return self.audio.init(self._callback)

    def _wait_event(self, expected, timeout_ms=6000):
        start = ticks_ms()
        while ticks_diff(ticks_ms(), start) < timeout_ms:
            if expected in self.events:
                return True
            sleep_ms(100)
        return False

    def _file_readable(self):
        try:
            from quectel import File
            with File.open(self.record_file, "r") as fp:
                data = fp.read(16)
            return bool(data), "record_bytes_sample={}".format(len(data or b""))
        except Exception as exc:
            return False, "record_file_check_failed={}".format(exc)

    def close(self):
        if self.audio:
            self.audio.deinit()
            self.audio = None

    def record_and_play(self, record_ms=1500):
        if not self.init():
            return False, "audio init failed"
        try:
            self.audio.record_start(self.record_file)
            sleep_ms(record_ms)
            self.audio.record_stop()
            sleep_ms(200)
            ok, detail = self._file_readable()
            if not ok:
                return False, detail
            self.audio.play_local(self.record_file, False)
            if not self._wait_event(self.Audio.PLAY_END, 8000):
                return False, "play_end_timeout events={}".format(self.events)
            return True, "record_file={} events={}".format(self.record_file, self.events)
        except Exception as exc:
            return False, str(exc)
        finally:
            self.close()

    def tts(self, text="移远比赛测试"):
        if not self.init():
            return False, "audio init failed"
        try:
            self.audio.tts_play(text)
            if not self._wait_event(self.Audio.TTS_END, 8000):
                return False, "tts_end_timeout events={}".format(self.events)
            return True, "tts={} events={}".format(text, self.events)
        except Exception as exc:
            return False, str(exc)
        finally:
            self.close()
