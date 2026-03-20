# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for building DominusPrime Windows executable
Usage: pyinstaller scripts/build_windows_exe.spec
"""
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os
import sys

block_cipher = None

# Get the project root directory
# When running: pyinstaller scripts/build_windows_exe.spec
# The current directory is the project root
PROJECT_ROOT = os.getcwd()
SPEC_DIR = os.path.join(PROJECT_ROOT, 'scripts')

print(f"Project root: {PROJECT_ROOT}")
print(f"SPEC directory: {SPEC_DIR}")

# Collect all dominusprime package data
datas = []
datas += collect_data_files('dominusprime')

# Add console static files
console_path = os.path.join(PROJECT_ROOT, 'src', 'dominusprime', 'console')
if os.path.exists(console_path):
    datas.append((console_path, 'dominusprime/console'))

# Add tokenizer files
tokenizer_path = os.path.join(PROJECT_ROOT, 'src', 'dominusprime', 'tokenizer')
if os.path.exists(tokenizer_path):
    datas.append((tokenizer_path, 'dominusprime/tokenizer'))

# Add agents files
agents_path = os.path.join(PROJECT_ROOT, 'src', 'dominusprime', 'agents')
if os.path.exists(agents_path):
    # Add md_files
    md_files_path = os.path.join(agents_path, 'md_files')
    if os.path.exists(md_files_path):
        datas.append((md_files_path, 'dominusprime/agents/md_files'))
    # Add skills
    skills_path = os.path.join(agents_path, 'skills')
    if os.path.exists(skills_path):
        datas.append((skills_path, 'dominusprime/agents/skills'))

# Collect all submodules
hiddenimports = []
hiddenimports += collect_submodules('dominusprime')
hiddenimports += collect_submodules('agentscope')
hiddenimports += collect_submodules('uvicorn')
hiddenimports += collect_submodules('fastapi')
hiddenimports += collect_submodules('httpx')
hiddenimports += collect_submodules('playwright')
hiddenimports += ['uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto', 
                   'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
                   'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto',
                   'uvicorn.lifespan', 'uvicorn.lifespan.on']

a = Analysis(
    [os.path.join(SPEC_DIR, 'windows_launcher.py')],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'scipy'],
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
    exclude_binaries=True,
    name='DominusPrime',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Keep console window for server logs
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(PROJECT_ROOT, 'console', 'public', 'favicon.ico') if os.path.exists(os.path.join(PROJECT_ROOT, 'console', 'public', 'favicon.ico')) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DominusPrime',
)
