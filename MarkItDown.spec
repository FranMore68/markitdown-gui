# -*- mode: python ; coding: utf-8 -*-
import os, sys
from pathlib import Path

# Locate site-packages where our dependencies live
import site
SP = site.getusersitepackages()   # user site-packages
SP_SYS = next(
    (p for p in site.getsitepackages() if 'site-packages' in p or 'dist-packages' in p),
    site.getusersitepackages()   # fallback para Ubuntu/Debian que usan dist-packages
)

def pkg(name, base=None):
    """Return (src_dir, dest_inside_bundle) or None if package not found."""
    if base is None:
        for sp in [SP, SP_SYS]:
            p = os.path.join(sp, name)
            if os.path.isdir(p):
                base = sp
                break
    if base is None:
        print(f"WARNING: package '{name}' not found in site-packages, skipping.")
        return None
    return (os.path.join(base, name), name)

a = Analysis(
    ['gui_app.py'],
    pathex=[],
    binaries=[],
    datas=[x for x in [
        pkg('magika'),       # ONNX model + config for file-type detection
        pkg('ftfy'),         # Unicode data files
        pkg('markitdown'),   # converters package
        pkg('markdownify'),
        pkg('bs4'),
        pkg('pdfminer'),
        pkg('pdfplumber'),
        pkg('mammoth'),
        pkg('openpyxl'),
        pkg('pandas'),
        pkg('pptx'),
        pkg('defusedxml'),
        pkg('olefile'),
        pkg('pydub'),
        pkg('speech_recognition'),
        pkg('youtube_transcript_api'),
    ] if x is not None],
    hiddenimports=[
        # markitdown converters (auto-discovered at runtime)
        'markitdown.converters._pdf_converter',
        'markitdown.converters._docx_converter',
        'markitdown.converters._xlsx_converter',
        'markitdown.converters._csv_converter',
        'markitdown.converters._html_converter',
        'markitdown.converters._image_converter',
        'markitdown.converters._epub_converter',
        'markitdown.converters._ipynb_converter',
        'markitdown.converters._audio_converter',
        'markitdown.converters._outlook_msg_converter',
        'olefile',
        'xlrd',
        'pydub',
        'speech_recognition',
        'youtube_transcript_api',
        # pdfminer internals
        'pdfminer.high_level',
        'pdfminer.layout',
        'pdfminer.converter',
        'pdfminer.pdfpage',
        'pdfminer.pdfinterp',
        'pdfminer.pdfdevice',
        # onnxruntime (used by magika)
        'onnxruntime',
        'onnxruntime.capi._pybind_state',
        # misc
        'charset_normalizer',
        'charset_normalizer.md__mypyc',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'ftfy',
        'ftfy.fixes',
        'ftfy.chardata',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'notebook', 'IPython', 'PIL._imagingtk'],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,   # onedir: binaries/datas go to COLLECT, not inside the exe
    name='MarkItDown',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,           # no black console window behind the GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='MarkItDown',       # output folder: dist/MarkItDown/
)
