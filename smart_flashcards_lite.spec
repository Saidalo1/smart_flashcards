# -*- mode: python ; coding: utf-8 -*-
"""
Lightweight PyInstaller spec for the FRIENDS build of Smart Flashcards.

Excludes the heavy ML stack (torch / sentence-transformers / transformers), so
grading runs on RapidFuzz only (strict string match — no synonyms, no ~470 MB
model download). The app imports sentence-transformers lazily and falls back to
RapidFuzz when it's absent, so excluding it is safe. Result: a small, fully
self-contained install — the end user needs nothing preinstalled.

Build:  .venv\\Scripts\\python.exe -m PyInstaller smart_flashcards_lite.spec --clean --noconfirm
Output: dist/SmartFlashcards/  (SmartFlashcards.exe + _internal/)
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
        'torch', 'torchvision', 'torchaudio', 'torchgen',
        'sentence_transformers', 'transformers', 'huggingface_hub',
        'tokenizers', 'safetensors', 'scipy', 'sklearn', 'matplotlib',
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
    [],
    exclude_binaries=True,  # onedir mode (fast startup)
    name='SmartFlashcards',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SmartFlashcards',
)
