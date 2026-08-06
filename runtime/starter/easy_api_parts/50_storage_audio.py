# Storage and audio


def cunchu(enabled=1):
    _set_feature("storage", enabled)
    return True


storage = cunchu


def writefile(path, data):
    if not _feature("storage"):
        return _skip("STORAGE", "disabled")
    try:
        # Let pending BLE/audio AT callbacks leave the shared modem channel.
        sleep_ms(250)
        from quectel import File
        with File.open(path, "w") as fp:
            fp.write(_payload(data))
        _clear_error("storage")
        return True
    except Exception as exc:
        _remember_error("storage", exc)
        _fail("STORAGE", exc)
        return False


def readfile(path, size=1024, default=""):
    if not _feature("storage"):
        _skip("STORAGE", "disabled")
        return default
    try:
        sleep_ms(250)
        from quectel import File
        with File.open(path, "r") as fp:
            data = fp.read(size)
        _clear_error("storage")
        return data
    except Exception as exc:
        _remember_error("storage", exc)
        return default


def removefile(path):
    if not _feature("storage"):
        return _skip("STORAGE", "disabled")
    try:
        sleep_ms(250)
        from quectel import File
        File.remove(path)
        _clear_error("storage")
        return True
    except Exception as exc:
        _remember_error("storage", exc)
        return False


def teststorage():
    from lib.kit.audio_storage import StorageProbe
    ok, detail = StorageProbe(config.STORAGE_TEST_DIR).run()
    return _pass("STORAGE", detail) if ok else _fail("STORAGE", detail)


def _audio_callback(event):
    _audio_events.append(event)


def yinpin(enabled=1):
    global _audio, _audio_events
    _set_feature("audio", enabled)
    if not enabled:
        if _audio:
            _audio.deinit()
        _audio = None
        _audio_events = []
        return True
    try:
        from quectel import Audio
        _audio_events = []
        _audio = Audio()
        if not _audio.init(_audio_callback):
            _audio = None
            return _fail("AUDIO", "audio init failed")
        return True
    except Exception as exc:
        _audio = None
        return _fail("AUDIO", exc)


audio = yinpin


def _audio_obj():
    if _audio is None:
        result = yinpin(1)
        if result is False:
            return None
    return _audio


def _wait_audio_event(expected, timeout=8000):
    start = ticks_ms()
    while ticks_diff(ticks_ms(), start) < timeout:
        if expected in _audio_events:
            return True
        sleep_ms(100)
    return False


def _audio_call_any(audio_obj, names, *args):
    for name in names:
        fn = getattr(audio_obj, name, None)
        if fn:
            return fn(*args)
    return None


def _audio_has_any(audio_obj, names):
    return any(getattr(audio_obj, name, None) for name in names)


def _apply_audio_settings(audio_obj):
    if _audio_volume is not None:
        volume_names = ("set_volume", "setvolume", "volume", "set_pa_volume", "set_speaker_volume")
        try:
            _audio_call_any(audio_obj, volume_names, _audio_volume)
        except ValueError as exc:
            if "0~5" not in str(exc):
                raise
            _audio_call_any(audio_obj, volume_names, min(_audio_volume, 5))
    if _audio_tts_speed is not None:
        _audio_call_any(
            audio_obj,
            ("set_tts_speed", "tts_set_speed", "setTtsSpeed"),
            _audio_tts_speed,
        )
    if _audio_tts_pitch is not None:
        _audio_call_any(
            audio_obj,
            ("set_tts_pitch", "tts_set_pitch", "setTtsPitch"),
            _audio_tts_pitch,
        )


def recordstart(path=None):
    """开始录音：api.recordstart() 或 api.recordstart("SD:test.wav")。"""
    global _audio_current_record_file
    path = path or config.AUDIO_RECORD_FILE
    audio_obj = _audio_obj()
    if not audio_obj:
        return False
    _audio_current_record_file = path
    try:
        from quectel import File
        try:
            File.remove(path)
            sleep_ms(100)
        except Exception:
            pass
    except Exception:
        pass
    audio_obj.record_start(path)
    return True


def recordstop():
    """停止录音：api.recordstop()。"""
    global _audio_record_until
    audio_obj = _audio
    if not audio_obj:
        _audio_record_until = None
        return False
    audio_obj.record_stop()
    _audio_record_until = None
    return True


def record(path=None, ms=1500):
    """录音一段时间后自动停止：api.record()。"""
    if not recordstart(path):
        return False
    sleep_ms(ms)
    return recordstop()


def recordtimed(path=None, ms=1500):
    """Start recording and let updateaudio() stop it after the requested time."""
    global _audio_record_until
    if not recordstart(path):
        return False
    _audio_record_until = ticks_ms() + max(0, int(ms))
    return True


def updateaudio():
    """Poll non-blocking timed recording state; call this from the fast loop."""
    global _audio_record_until
    if _audio_record_until is None:
        return False
    if ticks_diff(ticks_ms(), _audio_record_until) >= 0:
        return recordstop()
    return True


def playfile(path=None, wait=True):
    """播放本地音频文件：api.playfile() 或 api.playfile("SD:test.wav")。"""
    path = path or getattr(config, "AUDIO_PLAY_FILE", config.AUDIO_RECORD_FILE)
    audio_obj = _audio_obj()
    if not audio_obj:
        return False
    _apply_audio_settings(audio_obj)
    audio_obj.play_local(path, False)
    if not wait:
        return True
    from quectel import Audio
    return _wait_audio_event(Audio.PLAY_END, getattr(config, "AUDIO_WAIT_TIMEOUT_MS", 8000))


def play(path=None, wait=True):
    """播放本地音频文件别名：api.play()。"""
    return playfile(path, wait)


def stopplay():
    """停止本地音频播放：api.stopplay()。"""
    audio_obj = _audio
    if not audio_obj:
        return False
    stop_names = ("play_stop", "stop_play", "playstop", "stop")
    if not _audio_has_any(audio_obj, stop_names):
        return False
    result = _audio_call_any(audio_obj, stop_names)
    return True if result is None else bool(result)


def playstop():
    """停止本地音频播放别名：api.playstop()。"""
    return stopplay()


def tts(text=None, wait=True):
    """TTS 播放文字：api.tts() 或 api.tts("hello")。"""
    text = text if text is not None else getattr(config, "AUDIO_TTS_TEXT", "Quectel test")
    audio_obj = _audio_obj()
    if not audio_obj:
        return False
    _apply_audio_settings(audio_obj)
    audio_obj.tts_play(text)
    if not wait:
        return True
    from quectel import Audio
    return _wait_audio_event(Audio.TTS_END, getattr(config, "AUDIO_WAIT_TIMEOUT_MS", 8000))


def say(text=None):
    """TTS 播放文字别名：api.say("hello")。"""
    return tts(text)


def settts(speed=None, pitch=None, volume=None):
    """设置 TTS 参数：api.settts(speed, pitch, volume)。None 表示保持不变。"""
    global _audio_tts_speed, _audio_tts_pitch
    if speed is not None:
        _audio_tts_speed = speed
    if pitch is not None:
        _audio_tts_pitch = pitch
    if volume is not None:
        setvolume(volume)
    if _audio is not None:
        _apply_audio_settings(_audio)
    return True


def setttsparams(speed=None, pitch=None, volume=None):
    """设置 TTS 参数别名：api.setttsparams(speed, pitch, volume)。"""
    return settts(speed, pitch, volume)


def setvolume(value=None):
    """设置扬声器音量：api.setvolume(8)。不传参数时使用 config.AUDIO_VOLUME。"""
    global _audio_volume
    if value is None:
        value = getattr(config, "AUDIO_VOLUME", 8)
    try:
        _audio_volume = int(value)
    except Exception:
        _audio_volume = value
    if _audio is not None:
        _apply_audio_settings(_audio)
    return True


def volume(value=None):
    """设置扬声器音量别名：api.volume(8)。"""
    return setvolume(value)


def readvolume():
    """读取当前 easy_api 保存的音量设置。"""
    return _audio_volume


def testaudio():
    from lib.kit.audio_storage import AudioProbe
    probe = AudioProbe(config.AUDIO_RECORD_FILE)
    ok, detail = probe.record_and_play(1500)
    if not ok:
        return _fail("AUDIO", detail)
    ok, detail2 = AudioProbe(config.AUDIO_RECORD_FILE).tts("Quectel test")
    if not ok:
        return _fail("AUDIO", detail2)
    return _pass("AUDIO", detail + "; " + detail2)


