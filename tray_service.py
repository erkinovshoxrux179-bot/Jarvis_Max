"""System tray service for JARVIS - always-on background presence."""

import os
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


class TrayService:
    """Manages the system tray icon and global hotkey for JARVIS."""

    def __init__(self, window: 'MainWindow', overlay=None):
        self._window = window
        self._overlay = overlay
        self._tray: QSystemTrayIcon | None = None
        self._hotkey_registered = False
        self._create_tray_icon()

    def _create_tray_icon(self):
        icon_path = _base_dir() / "ico.ico"
        icon = QIcon(str(icon_path))

        self._tray = QSystemTrayIcon(icon, self._window)
        self._tray.setToolTip("J.A.R.V.I.S - MARK XXXIX")
        self._tray.activated.connect(self._on_tray_activated)

        menu = self._create_context_menu()
        self._tray.setContextMenu(menu)
        self._tray.show()

    def _create_context_menu(self) -> QMenu:
        menu = QMenu()

        activate_action = QAction("Activate JARVIS", menu)
        activate_action.triggered.connect(self._activate_jarvis)
        menu.addAction(activate_action)

        show_action = QAction("Show/Hide JARVIS", menu)
        show_action.triggered.connect(self._toggle_window)
        menu.addAction(show_action)

        mute_action = QAction("Mute/Unmute", menu)
        mute_action.triggered.connect(self._toggle_mute)
        menu.addAction(mute_action)

        menu.addSeparator()

        settings_action = QAction("Settings", menu)
        settings_action.triggered.connect(self._show_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        exit_action = QAction("Exit JARVIS", menu)
        exit_action.triggered.connect(QApplication.quit)
        menu.addAction(exit_action)

        return menu

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._toggle_window()

    def _toggle_window(self):
        if self._window.isVisible():
            self._window.hide()
        else:
            self._window.show_from_tray()

    def _activate_jarvis(self):
        """Show the overlay widget to activate JARVIS."""
        self._window.show_from_tray()
        if self._overlay:
            self._overlay.show_overlay()
            self._overlay.set_state("LISTENING")

    def set_overlay(self, overlay):
        """Set or update the overlay reference."""
        self._overlay = overlay

    def _toggle_mute(self):
        self._window._toggle_mute()

    def _show_settings(self):
        self._window.show_from_tray()

    def show_notification(self, title: str, message: str, duration: int = 3000):
        """Show a system tray balloon notification."""
        if self._tray and self._tray.isVisible():
            self._tray.showMessage(
                title,
                message,
                QSystemTrayIcon.MessageIcon.Information,
                duration,
            )

    def setup_global_hotkey(self):
        """Register Win+J global hotkey to toggle JARVIS window visibility."""
        try:
            import keyboard
            keyboard.add_hotkey("win+j", self._toggle_window)
            self._hotkey_registered = True
        except Exception:
            # keyboard library may not work without root/admin or on non-Windows
            self._hotkey_registered = False

    def cleanup(self):
        """Clean up tray icon and hotkey on shutdown."""
        if self._hotkey_registered:
            try:
                import keyboard
                keyboard.unhook_all()
            except Exception:
                pass
        if self._tray:
            self._tray.hide()
            self._tray = None
