"""Cloud vocabulary catalog — fetches curated topic sets from the public content
repo via the jsDelivr CDN. Read-only: users browse the catalog and download topics
into their LOCAL vocabulary; nothing is ever uploaded. Same trust model as the
auto-updater (a public repo of JSON, no auth, no server to run).
"""
import json
import logging
import ssl
import urllib.request
from urllib.error import URLError, HTTPError

log = logging.getLogger(__name__)

# jsDelivr serves the content repo's files from a global CDN (fast + cached, no auth).
# catalog.json lives at the repo root; each topic's words at topics/<id>.json.
CDN_BASE = "https://cdn.jsdelivr.net/gh/Saidalo1/smart_flashcards_dist@main"
_HEADERS = {"User-Agent": "SmartFlashcards-Catalog"}


def _ssl_context():
    """CA bundle via certifi (a frozen build can't find the OS trust store)."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _fetch_json(url, timeout):
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_catalog(timeout=10):
    """Return the list of categories, or None on any error (offline / missing /
    malformed). Shape: [{"name": str, "topics": [{"id","name","words"}, ...]}, ...]."""
    try:
        data = _fetch_json(f"{CDN_BASE}/catalog.json", timeout)
        cats = data.get("categories") if isinstance(data, dict) else None
        return cats if isinstance(cats, list) else None
    except (URLError, HTTPError, ValueError, TimeoutError, OSError) as e:
        log.info("Catalog fetch failed: %r", e)
        return None


def fetch_topic(topic_id, timeout=15):
    """Return the list of word dicts for a topic id, or None on error.
    Each word: {"english","uzbek", optional "hint"/"definition"/...}."""
    try:
        data = _fetch_json(f"{CDN_BASE}/topics/{topic_id}.json", timeout)
        return data if isinstance(data, list) else None
    except (URLError, HTTPError, ValueError, TimeoutError, OSError) as e:
        log.info("Topic %r fetch failed: %r", topic_id, e)
        return None
