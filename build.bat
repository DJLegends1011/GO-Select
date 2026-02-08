@echo off
echo ========================================
echo Building GO-Select.exe
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install dependencies if needed
echo Installing dependencies...
pip install customtkinter pyinstaller --quiet

REM Get CustomTkinter path
for /f "delims=" %%i in ('python -c "import customtkinter; print(customtkinter.__path__[0])"') do set CTK_PATH=%%i

echo CustomTkinter found at: %CTK_PATH%

REM Create spec file with dynamic CTK path
echo Creating build spec...
python -c "
ctk_path = r'%CTK_PATH%'
spec_content = '''# -*- mode: python ; coding: utf-8 -*-

ctk_path = r\"''' + ctk_path + '''\"

block_cipher = None

a = Analysis(
    ['GO_Select.py'],
    pathex=[],
    binaries=[],
    datas=[
        (ctk_path, 'customtkinter'),
    ],
    hiddenimports=['customtkinter', 'darkdetect'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='GO-Select',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
with open('GO_Select.spec', 'w') as f:
    f.write(spec_content)
print('Spec file created.')
"

REM Build the executable
echo.
echo Building executable...
python -m PyInstaller GO_Select.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build complete!
echo Executable: dist\GO-Select.exe
echo Size: 
for %%A in (dist\GO-Select.exe) do echo   %%~zA bytes (%%~zA / 1048576 MB approx)
echo ========================================
pause