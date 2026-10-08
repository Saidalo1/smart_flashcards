"""Word pronunciation (text-to-speech) for the flashcards.

Strategy — natural, correct English pronunciation that also works offline after
first use:

1. Fetch an MP3 from Google Translate's TTS endpoint (free, no API key, natural
   voice, handles single words AND phrases like "To give smb a hand"). The MP3
   is cached on disk, so each word is downloaded at most once and replays
   instantly (and offline) afterwards.
2. Play it with Qt Multimedia (QMediaPlayer) — cross-platform (GStreamer on
   Linux, Media Foundation on Windows).
3. If the network and the cache both fail, fall back to the OS speech engine via
   QtTextToSpeech so the button still does *something* offline.

Public API: ``pronounce(text)`` — say an English word/phrase out loud.
"""
import hashlib
import threading
import urllib.parse
import urllib.request

from PySide6.QtCore import QObject, Signal, QUrl

from .app_paths import get_data_dir

_GOOGLE_TTS = "https://translate.google.com/translate_tts"
_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
# Sentinel prefix: tell the GUI thread to use the offline engine instead of a file.
_OFFLINE = "\0offline\0"


class _Pronouncer(QObject):
    # Emitted from the download thread; carries a local file path OR the offline
    # sentinel. Connected to a GUI-thread slot so playback happens on the UI thread.
    _ready = Signal(str)

    def __init__(self):
        super().__init__()
        self._cache_dir = get_data_dir() / "tts_cache"
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        self._player = None   # created lazily on first use (GUI thread)
        self._audio = None
        self._tts = None      # offline QtTextToSpeech fallback, lazy
        self._text_for_file = {}   # mp3 path -> word (so a playback error can speak it)
        self._last_file_text = ""
        self._ready.connect(self._on_ready)

    # ---- public ----
    def say(self, text):
        text = (text or "").strip()
        if not text:
            return
        path = self._cache_dir / (hashlib.md5(text.lower().encode("utf-8")).hexdigest() + ".mp3")
        self._text_for_file[str(path)] = text
        if path.exists() and path.stat().st_size > 512:
            self._on_ready(str(path))
            return
        threading.Thread(target=self._download, args=(text, path), daemon=True).start()

    # ---- download (background thread) ----
    def _download(self, text, path):
        try:
            url = _GOOGLE_TTS + "?" + urllib.parse.urlencode(
                {"ie": "UTF-8", "q": text, "tl": "en", "client": "tw-ob"}
            )
            req = urllib.request.Request(url, headers={"User-Agent": _UA})
            data = urllib.request.urlopen(req, timeout=10).read()
            if len(data) > 512:
                tmp = path.with_suffix(".part")
                tmp.write_bytes(data)
                tmp.replace(path)
                self._ready.emit(str(path))
                return
        except Exception as e:
            print(f"[TTS] download failed for {text!r}: {e}")
        # Couldn't get audio — ask the GUI thread to use the offline engine.
        self._ready.emit(_OFFLINE + text)

    # ---- playback (GUI thread) ----
    def _on_ready(self, payload):
        if payload.startswith(_OFFLINE):
            self._speak_offline(payload[len(_OFFLINE):])
            return
        self._last_file_text = self._text_for_file.get(payload, "")
        try:
            if self._player is None:
                from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
                self._audio = QAudioOutput()
                self._audio.setVolume(1.0)
                self._player = QMediaPlayer()
                self._player.setAudioOutput(self._audio)
                # If Qt Multimedia can't play (backend/plugin missing in a frozen
                # build), speak the word with the OS engine so the button still works.
                self._player.errorOccurred.connect(
                    lambda *a: (print(f"[TTS] player error: {a}"),
                                self._speak_offline(self._last_file_text))
                )
            self._player.stop()
            self._player.setSource(QUrl.fromLocalFile(payload))
            self._player.play()
        except Exception as e:
            print(f"[TTS] playback failed ({e}); using OS engine")
            self._speak_offline(self._last_file_text)

    def _speak_offline(self, text):
        # 1) Qt's speech engine (needs the QtTextToSpeech plugin — may be absent in a
        #    frozen build). 2) On Windows, fall back to the built-in SAPI voice via
        #    PowerShell, which needs NO bundled plugin and always works offline.
        try:
            if self._tts is None:
                from PySide6.QtTextToSpeech import QTextToSpeech
                self._tts = QTextToSpeech()
            # If no engine/voice is available, QtTextToSpeech is silent — detect and
            # fall through to the OS engine instead of doing nothing.
            from PySide6.QtTextToSpeech import QTextToSpeech as _QTTS
            if self._tts.state() == _QTTS.State.Error or not self._tts.availableEngines():
                raise RuntimeError("QtTextToSpeech has no engine")
            self._tts.say(text)
            return
        except Exception as e:
            print(f"[TTS] Qt offline engine unavailable ({e}); trying OS SAPI")
        self._speak_windows_sapi(text)

    def _speak_windows_sapi(self, text):
        """Last-resort offline speech on Windows via the built-in SAPI voice (no Qt
        plugin, no network). Runs detached so it never blocks the UI."""
        import sys
        if sys.platform != 'win32':
            print("[TTS] no offline speech backend on this OS")
            return
        try:
            import subprocess
            safe = text.replace("'", "''")
            ps = ("Add-Type -AssemblyName System.Speech; "
                  "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                  f"$s.Speak('{safe}')")
            CREATE_NO_WINDOW = 0x08000000
            subprocess.Popen(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                creationflags=CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            print(f"[TTS] Windows SAPI fallback failed: {e}")


_instance = None


def _get():
    global _instance
    if _instance is None:
        _instance = _Pronouncer()
    return _instance


def pronounce(text):
    """Say an English word or phrase out loud (cached MP3, offline fallback)."""
    _get().say(text)
