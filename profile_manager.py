"""
User profile manager for Smart Flashcards.
Each user has their own config, stats, and active topics.
"""
import json
from pathlib import Path
from app_paths import get_data_dir

DATA_DIR = get_data_dir()
PROFILES_DIR = DATA_DIR / 'profiles'
LAST_USER_FILE = DATA_DIR / 'last_user.txt'


def ensure_profiles_dir():
    """Ensures the profiles directory exists."""
    PROFILES_DIR.mkdir(parents=True, exist_ok=True)


def get_all_profiles():
    """Returns list of all profile names."""
    ensure_profiles_dir()
    profiles = []
    for p in PROFILES_DIR.iterdir():
        if p.is_dir():
            profiles.append(p.name)
    return sorted(profiles)


def get_last_user():
    """Returns the last used profile name, or None."""
    if LAST_USER_FILE.exists():
        return LAST_USER_FILE.read_text(encoding='utf-8').strip()
    return None


def set_last_user(username):
    """Saves the last used profile name."""
    DATA_DIR.mkdir(exist_ok=True)
    LAST_USER_FILE.write_text(username, encoding='utf-8')


def get_profile_path(username):
    """Returns the path to a user's profile directory."""
    ensure_profiles_dir()
    return PROFILES_DIR / username


def create_profile(username):
    """Creates a new user profile directory."""
    profile_path = get_profile_path(username)
    profile_path.mkdir(exist_ok=True)
    # Create default config
    config_file = profile_path / 'config.json'
    if not config_file.exists():
        default_config = {
            'timer_interval': 10,
            'hotkey': 'shift_r',
            'active_topics': [],
            'show_notifications': True,
            'semantic_grading': False,
        }
        config_file.write_text(json.dumps(default_config, indent=2), encoding='utf-8')
    # Create empty stats
    stats_file = profile_path / 'stats.json'
    if not stats_file.exists():
        stats_file.write_text('{}', encoding='utf-8')
    return profile_path


def profile_exists(username):
    """Checks if a profile exists."""
    return get_profile_path(username).exists()


def delete_profile(username):
    """Deletes a profile and all its data. Returns True if something was removed."""
    import shutil
    path = get_profile_path(username)
    if not path.exists():
        return False
    shutil.rmtree(path, ignore_errors=True)
    # If we just deleted the remembered profile, forget it too.
    if get_last_user() == username:
        set_last_user("")
    return True
