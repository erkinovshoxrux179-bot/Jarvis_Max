import PyInstaller.__main__
import os

# Build the exe
PyInstaller.__main__.run([
    'main.py',
    '--onefile',
    '--windowed',
    '--name=Mark_XXXIX',
    '--icon=ico.ico',
    '--add-data=core;core',
    '--add-data=actions;actions',
    '--add-data=agent;agent',
    '--add-data=memory;memory',
    '--add-data=config;config',
    '--add-data=ico.ico;.',
    '--add-data=tray_service.py;.',
    '--add-data=wake_word.py;.',
    '--hidden-import=google',
    '--hidden-import=sounddevice',
    '--hidden-import=PyQt6',
    '--hidden-import=PyQt6.QtWidgets',
    '--hidden-import=PyQt6.QtGui',
    '--hidden-import=PyQt6.QtCore',
    '--hidden-import=pystray',
    '--hidden-import=plyer',
    '--hidden-import=plyer.platforms.win.notification',
    '--hidden-import=keyboard',
    '--hidden-import=audioop',
])

print("Exe built in dist/ folder")
print("Next: Open installer/markxxxix.iss in Inno Setup to create the installer.")
