import PyInstaller.__main__
import os

# Build the exe
PyInstaller.__main__.run([
    'main.py',
    '--onefile',  # Single exe file
    '--windowed',  # No console window
    '--icon=ico.ico',  # Icon
    '--name=Mark_XXXIX',  # Name
    '--add-data=core;core',  # Include core folder
    '--add-data=actions;actions',
    '--add-data=agent;agent',
    '--add-data=memory;memory',
    '--add-data=config;config',
    '--hidden-import=google.generativeai',
    '--hidden-import=sounddevice',
    '--hidden-import=pyautogui',
    # Add other hidden imports as needed
])

print("Exe built in dist/ folder")