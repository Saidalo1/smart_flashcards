# -*- mode: python ; coding: utf-8 -*-
"""
FRIENDS build of Smart Flashcards — a SINGLE self-contained .exe (onefile).

- Excludes the heavy ML stack (torch/sentence-transformers) → RapidFuzz-only
  grading, small size. The app imports sentence-transformers lazily and falls
  back to RapidFuzz when absent, so excluding it is safe.
- onefile: everything (Python + PySide6 + rapidfuzz) is packed into ONE .exe.
  The friend just double-clicks it — nothing to install, no folder, no archive.

Build:  .venv\\Scripts\\python.exe -m PyInstaller smart_flashcards_lite.spec --noconfirm
Output: dist/SmartFlashcards.exe
"""

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'rapidfuzz',
        'pynput',
        'pynput.keyboard',
        'pynput.keyboard._win32',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # heavy ML stack (semantic grading) — app falls back to RapidFuzz.
        # (Unused Qt modules like QtWebEngine/QtQuick are NOT listed: PyInstaller
        # already skips them because the app never imports them.)
        'torch', 'torchvision', 'torchaudio', 'torchgen',
        'sentence_transformers', 'transformers', 'huggingface_hub',
        'tokenizers', 'safetensors', 'scipy', 'sklearn', 'matplotlib',
        # The app uses PySide6; PyQt6 may also be present in the venv. Exclude the
        # other Qt bindings so PyInstaller never bundles two Qt stacks.
        'PyQt6', 'PyQt5', 'PySide2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SmartFlashcards',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='app_icon.ico',
)
