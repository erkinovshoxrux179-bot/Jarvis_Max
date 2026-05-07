import PyInstaller.__main__
import os

# Build the exe
PyInstaller.__main__.run([
    'main.py',
    '--onefile',  # Single exe file
    '--windowed',  # No console window
    '--name=Mark_XXXIX',  # Name
    '--add-data=core;core',  # Include core folder
    '--add-data=actions;actions',
    '--add-data=agent;agent',
    '--add-data=memory;memory',
    '--add-data=config;config',
    '--hidden-import=google',
    '--hidden-import=sounddevice',
    '--hidden-import=PyQt6',
])

print("Exe built in dist/ folder")