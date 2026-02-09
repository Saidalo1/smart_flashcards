"""
Utility to resolve the correct data directory path.
When running as a PyInstaller .exe, data is stored next to the .exe file.
When running as a script, data is stored in the project directory.
"""
import sys
from pathlib import Path


def get_app_dir():
    """Returns the directory where the application is running from."""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller .exe — use the directory containing the .exe
        return Path(sys.executable).parent
    else:
        # Running as a Python script
        return Path(__file__).parent


def get_data_dir():
    """Returns the path to the data directory."""
    return get_app_dir() / 'data'
