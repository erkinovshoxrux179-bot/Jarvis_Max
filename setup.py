from cx_Freeze import setup, Executable

# Dependencies to include
build_exe_options = {
    "packages": [
        "google.generativeai",
        "sounddevice",
        "PIL",
        "requests",
        "bs4",
        "duckduckgo_search",
        "playwright",
        "pyautogui",
        "pyperclip",
        "pygetwindow",
        "cv2",
        "numpy",
        "mss",
        "psutil",
        "comtypes",
        "pycaw",
        "win10toast",
        "send2trash",
        "youtube_transcript_api",
        "pywinauto",
        "pptx",
        "PyQt6",
        "cx_Freeze",
    ],
    "include_files": [
        ("core/", "core/"),
        ("actions/", "actions/"),
        ("agent/", "agent/"),
        ("memory/", "memory/"),
        ("config/", "config/"),
        ("icon.ico", "icon.ico"),  # Include the icon
    ],
    "excludes": [],
    "include_msvcr": True,
}

# MSI options for installer
bdist_msi_options = {
    "upgrade_code": "{12345678-1234-1234-1234-123456789012}",  # Unique GUID
    "add_to_path": False,
    "initial_target_dir": r"[ProgramFilesFolder]\Mark XXXIX",
    "install_icon": "icon.ico",
    "target_name": "Mark XXXIX",
    "shortcuts": [
        (
            "DesktopShortcut",  # Shortcut name
            "DesktopFolder",  # Location
            "Mark XXXIX.exe",  # Target
            "TARGETDIR",  # Start in
            None,  # Parameters
            None,  # Description
            None,  # Icon
            0,  # IconIndex
            None,  # ShowCmd
            "TARGETDIR",  # WkDir
        ),
        (
            "StartMenuShortcut",  # Shortcut name
            "StartMenuFolder",  # Location
            "Mark XXXIX.exe",  # Target
            "TARGETDIR",  # Start in
            None,  # Parameters
            None,  # Description
            None,  # Icon
            0,  # IconIndex
            None,  # ShowCmd
            "TARGETDIR",  # WkDir
        ),
    ],
}

executables = [
    Executable(
        "main.py",
        base=None,  # Use None for console app, "Win32GUI" for GUI without console
        icon="icon.ico",
        shortcut_name="Mark XXXIX",
        shortcut_dir="StartMenuFolder",
    )
]

setup(
    name="Mark XXXIX",
    version="1.0.0",
    description="The Ultimate Cross-Platform Personal AI Assistant",
    author="Jarvis_Max",
    author_email="erkinovshoxrux179@gmail.com",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
    },
    executables=executables,
)

