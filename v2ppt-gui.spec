# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Get the project root directory
project_root = Path(SPECPATH)

# Define data files to include
datas = [
    # Include all source modules
    (str(project_root / 'src'), 'src'),
    (str(project_root / 'config'), 'config'),
    (str(project_root / 'ui'), 'ui'),
    
    # Include main processing files
    (str(project_root / 'main.py'), '.'),
    (str(project_root / 'improved_processing.py'), '.'),
    
    # Include documentation
    (str(project_root / 'README.md'), '.'),
    (str(project_root / 'BUILD_GUIDE.md'), '.'),
]

# Hidden imports for modules that might not be detected automatically
hiddenimports = [
    'cv2',
    'numpy',
    'PIL',
    'PIL.Image',
    'pptx',
    'pptx.presentation',
    'pptx.slide',
    'pptx.util',
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'pathlib',
    'threading',
    'queue',
    'datetime',
    'logging',
    'json',
    'hashlib',
    # Optional dependencies - only include if available
    # 'imagehash',
    # 'skimage',
    # 'skimage.metrics',
    # 'scipy',
    # 'scipy.spatial',
    # 'scipy.spatial.distance',
]

# Analysis configuration
a = Analysis(
    ['gui_main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# Remove duplicate files
pyz = PYZ(a.pure)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='v2ppt-gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to False for windowed app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path if you have one
)
