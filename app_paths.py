"""Resolves where the app reads/writes its files.

Installed build (.exe): user data lives in a per-user app-data folder OUTSIDE the
install directory, so it (a) never ships one user's words/profile to another,
(b) survives uninstall and updates, and (c) is always writable. Big,
re-downloadable files (the ML model) go in a device-local cache folder.

Dev (running from source): everything stays in the project's ./data folder, so
the developer's own vocabulary/profiles are untouched.
"""
import os
import sys
from pathlib import Path

APP_FOLDER = 'SmartFlashcards'


def _is_frozen():
    return getattr(sys, 'frozen', False)


def get_app_dir():
    """Directory the application runs from (the .exe folder, or the source dir)."""
    if _is_frozen():
        return Path(sys.executable).parent
    return Path(__file__).parent


def get_data_dir():
    """Per-user writable data: vocabulary, profiles, config, logs.

    Installed: %APPDATA%\\SmartFlashcards (Windows) / ~/.local/share/SmartFlashcards.
    Dev: <project>/data.
    """
    if _is_frozen():
        if os.name == 'nt':
            base = os.environ.get('APPDATA') or (Path.home() / 'AppData' / 'Roaming')
        else:
            base = os.environ.get('XDG_DATA_HOME') or (Path.home() / '.local' / 'share')
        path = Path(base) / APP_FOLDER
    else:
        path = get_app_dir() / 'data'
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_cache_dir():
    """Per-user cache for large, re-downloadable files (the similarity model).

    Installed: %LOCALAPPDATA%\\SmartFlashcards (Windows) / ~/.cache/SmartFlashcards.
    Dev: <project>/data (same place as before, so nothing changes locally).
    """
    if _is_frozen():
        if os.name == 'nt':
            base = os.environ.get('LOCALAPPDATA') or (Path.home() / 'AppData' / 'Local')
        else:
            base = os.environ.get('XDG_CACHE_HOME') or (Path.home() / '.cache')
        path = Path(base) / APP_FOLDER
    else:
        path = get_app_dir() / 'data'
    path.mkdir(parents=True, exist_ok=True)
    return path
