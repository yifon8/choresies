# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for macOS — produces dist/ChoreWheel.app
# Run from the project root: pyinstaller build/build_mac.spec

from pathlib import Path

ROOT = Path(SPECPATH).parent

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "data"), "data"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="ChoreWheel",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,    # required for macOS .app bundles
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "assets" / "icon.icns"),
)

app = BUNDLE(
    exe,
    name="ChoreWheel.app",
    icon=str(ROOT / "assets" / "icon.icns"),
    bundle_identifier="com.choresies.chorewheel",
    info_plist={
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "10.13.0",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleName": "Chore Wheel",
    },
)
