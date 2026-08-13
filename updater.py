"""Lightweight self-updater (no third-party deps).

On startup the app checks the PUBLIC releases-only repo for a newer version. The
private source repo is never touched by the app — only compiled installers are
published to the dist repo, so nothing sensitive is exposed. If a newer release
exists, we download its installer and run it; Inno Setup upgrades in place.
"""
import json
import logging
import os
import ssl
import subprocess
import tempfile
import urllib.request
from urllib.error import URLError, HTTPError

from version import __version__

log = logging.getLogger(__name__)


def _ssl_context():
    """SSL context that trusts a bundled CA store (certifi). A frozen build often
    can't find the OS trust store, so plain create_default_context() fails cert
    verification (SSLCertVerificationError). certifi ships a known-good CA bundle."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()

# Public releases-only repo. Source stays private; only installers land here.
RELEASES_API = "https://api.github.com/repos/Saidalo1/smart_flashcards_dist/releases/latest"
_HEADERS = {"User-Agent": "SmartFlashcards-Updater"}


def _parse_version(text):
    """'v1.2.3' / '1.2.3' -> (1, 2, 3). Missing/garbage parts become 0."""
    text = (text or "").lstrip("vV").strip()
    parts = []
    for chunk in text.split("."):
        digits = "".join(ch for ch in chunk if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts) if parts else (0,)


def check_for_update(timeout=8):
    """Return (version_str, installer_url) if a newer release exists, else None.

    Never raises: any network/parse error (including 'no releases yet' -> 404)
    simply means 'no update right now'.
    """
    log.info("Update check: current=%s, querying %s", __version__, RELEASES_API)
    try:
        req = urllib.request.Request(RELEASES_API, headers=_HEADERS)
        ctx = _ssl_context()
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (URLError, HTTPError, ValueError, TimeoutError, OSError) as e:
        log.info("Update check failed (treated as 'no update'): %r", e)
        return None

    tag = data.get("tag_name") or data.get("name") or ""
    log.info("Update check: latest release tag=%r", tag)
    if _parse_version(tag) <= _parse_version(__version__):
        log.info("Update check: already up to date (%s >= %s)", __version__, tag)
        return None

    # Pick the installer asset (the .exe uploaded to the release).
    for asset in data.get("assets", []) or []:
        name = (asset.get("name") or "").lower()
        if name.endswith(".exe"):
            url = asset.get("browser_download_url")
            if url:
                log.info("Update available: %s -> %s", tag, url)
                return (tag.lstrip("vV"), url)
    log.info("Update check: newer tag %r but no .exe asset attached", tag)
    return None


def download_installer(url, timeout=180):
    """Download the installer to a temp .exe and return its path, or None."""
    try:
        req = urllib.request.Request(url, headers=_HEADERS)
        ctx = _ssl_context()
        fd, path = tempfile.mkstemp(prefix="SmartFlashcards_Update_", suffix=".exe")
        with os.fdopen(fd, "wb") as out, \
                urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                out.write(chunk)
        return path
    except (URLError, HTTPError, TimeoutError, OSError):
        return None


def run_installer(path):
    """Launch the downloaded installer (detached). The app must quit right after so
    the installer can replace its files."""
    try:
        subprocess.Popen([path], close_fds=True)
        return True
    except OSError:
        return False
