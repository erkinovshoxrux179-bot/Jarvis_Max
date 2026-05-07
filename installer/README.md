# MARK XXXIX — Windows Setup Builder

This folder contains a **wizard-style installer** (like the screenshot) and build scripts.

## What you get
- `installer_wizard.py`: PyQt6 Setup Wizard (License → Path → Progress → Finish)
- `build_installer.ps1`: builds `MarkXXXIX-Setup.exe` using PyInstaller
- `markxxxix.iss`: optional Inno Setup packager (creates a `setup.exe` if Inno Setup is installed)

## Build (Windows)
Prereqs:
- Python **3.11+** (either `python` or `py -3.11` must work)
- `pip` available

From repo root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\installer\build_installer.ps1 -PayloadSource ".." -OutDir .\installer_out
```

Output:
- `installer_out\MarkXXXIX-Setup.exe`

## (Optional) Package with Inno Setup
Install Inno Setup, then run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\installer\build_installer.ps1 -PayloadSource ".." -OutDir .\installer_out -MakeInnoSetup
```

If `iscc.exe` is found, it will package the output into a `setup.exe` inside `installer_out`.

## Customizing the License page
Put a `LICENSE` or `LICENSE.txt` file into `installer\payload\` before building.

