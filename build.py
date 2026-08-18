"""One-shot release build for Smart Flashcards.

    python build.py

Steps:
  1. Compile the app to a standalone folder with Nuitka (nuitka_build/main.dist).
  2. Wrap that folder into a Windows installer with Inno Setup (ISCC).
  3. Print the installer path, size and SHA-256 (the SHA the updater verifies).

The version is the single source of truth in version.py — it flows into the exe
metadata and the installer. No need to touch installer.iss for a version bump.
This replaces the manual "run Nuitka, then Ctrl+F9" dance.
"""
import hashlib
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable  # the .venv python running this script

# --- version (single source of truth) ---
sys.path.insert(0, ROOT)
from app.version import __version__ as VERSION  # noqa: E402

# Packages no app module imports — excluded purely so an optional/transitive
# import inside a dependency can never drag them in and bloat the build.
EXCLUDE = [
    "torch", "tensorflow", "matplotlib", "scipy", "sklearn", "scikit_learn",
    "pandas", "transformers", "PyQt6", "PyQt5", "IPython", "tkinter",
    # Semantic grading is disabled at runtime (RapidFuzz only) and its heavy
    # sentence-transformers stack is imported lazily inside a function that never
    # runs — so these only leaked into the build as dead weight. Safe to drop.
    "sentence_transformers", "tokenizers", "huggingface_hub", "safetensors",
    "sympy", "networkx",
]

NUITKA = [
    PY, "-m", "nuitka", "main.py",
    "--standalone",
    "--assume-yes-for-downloads",
    "--enable-plugin=pyside6",
    "--windows-console-mode=disable",
    "--windows-icon-from-ico=app_icon.ico",
    "--company-name=Smart Flashcards",
    "--product-name=Smart Flashcards",
    "--file-description=Smart Flashcards",
    f"--file-version={VERSION}",
    f"--product-version={VERSION}",
    # CA bundle so the frozen build can verify TLS (auto-update + cloud catalog).
    "--include-package-data=certifi",
    # PortAudio DLL for sounddevice (lives in the _sounddevice_data package).
    "--include-package-data=_sounddevice_data",
    f"--nofollow-import-to={','.join(EXCLUDE)}",
    "--output-dir=nuitka_build",
    "--output-filename=SmartFlashcards.exe",
]

ISCC_CANDIDATES = [
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"),
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
]


def find_iscc():
    for p in ISCC_CANDIDATES:
        if os.path.exists(p):
            return p
    found = shutil.which("ISCC")
    if found:
        return found
    sys.exit("ISCC.exe (Inno Setup 6) not found. Install it or edit ISCC_CANDIDATES.")


def run(cmd, **kw):
    print("\n>>>", " ".join(cmd) if isinstance(cmd, list) else cmd, flush=True)
    r = subprocess.run(cmd, cwd=ROOT, **kw)
    if r.returncode != 0:
        sys.exit(f"Step failed (exit {r.returncode}).")


def main():
    print(f"=== Building Smart Flashcards v{VERSION} ===", flush=True)

    # 1) clean previous Nuitka output so nothing stale leaks into the build
    for d in ("nuitka_build/main.dist", "nuitka_build/main.build"):
        p = os.path.join(ROOT, *d.split("/"))
        if os.path.isdir(p):
            print("cleaning", d, flush=True)
            shutil.rmtree(p, ignore_errors=True)

    # 2) Nuitka standalone build
    run(NUITKA)
    exe = os.path.join(ROOT, "nuitka_build", "main.dist", "SmartFlashcards.exe")
    if not os.path.exists(exe):
        sys.exit("Nuitka finished but SmartFlashcards.exe is missing.")

    # 3) Inno Setup installer
    iscc = find_iscc()
    run([iscc, f"/DAppVer={VERSION}", "installer.iss"])

    installer = os.path.join(ROOT, "installer_output", "SmartFlashcards_Setup.exe")
    if not os.path.exists(installer):
        sys.exit("ISCC finished but the installer is missing.")

    # 4) report
    data = open(installer, "rb").read()
    sha = hashlib.sha256(data).hexdigest()
    print("\n=== DONE ===")
    print("Installer:", installer)
    print("Size:     ", f"{len(data) / 1_048_576:.1f} MB")
    print("Version:  ", VERSION)
    print("SHA-256:  ", sha)
    print("\nNext: create a GitHub Release on smart_flashcards_dist tagged")
    print(f"  v{VERSION}  and upload this installer as an asset.")


if __name__ == "__main__":
    main()
