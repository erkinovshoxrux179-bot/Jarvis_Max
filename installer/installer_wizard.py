from __future__ import annotations

import os
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)


APP_TITLE = "MARK XXXIX Setup"


def _base_dir() -> Path:
    # If frozen, the installer exe sits next to payload folder (recommended).
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


BASE_DIR = _base_dir()
PAYLOAD_DIR = (BASE_DIR / "payload").resolve()


def _default_install_dir() -> Path:
    local = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return Path(local) / "Mark-XXXIX"


def _safe_rel(p: Path, root: Path) -> str:
    try:
        return str(p.resolve().relative_to(root.resolve()))
    except Exception:
        return p.name


def _load_license_text() -> str:
    # If you ship a license file into payload, show it; else show a template.
    for cand in ("LICENSE", "LICENSE.txt", "license.txt", "readme.md"):
        fp = (PAYLOAD_DIR / cand)
        if fp.exists():
            try:
                return fp.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                pass
    return (
        "License information not found.\n\n"
        "You can replace this text by adding LICENSE or LICENSE.txt into installer/payload/.\n"
    )


@dataclass
class InstallPlan:
    source: Path
    target: Path
    create_desktop_shortcut: bool


class InstallerWorker(QObject):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, plan: InstallPlan):
        super().__init__()
        self.plan = plan

    def run(self):
        try:
            src = self.plan.source
            dst = self.plan.target
            if not src.exists() or not src.is_dir():
                raise RuntimeError(f"Payload folder not found: {src}")

            dst.mkdir(parents=True, exist_ok=True)

            files: list[Path] = []
            for p in src.rglob("*"):
                if p.is_file():
                    files.append(p)

            total = max(1, len(files))
            copied = 0
            self.status.emit("Copying files…")

            for f in files:
                rel = f.relative_to(src)
                out = dst / rel
                out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, out)
                copied += 1
                if copied % 5 == 0 or copied == total:
                    pct = int(copied / total * 100)
                    self.progress.emit(pct)
                    self.status.emit(f"Copied {copied}/{total}: {_safe_rel(rel, Path('.'))}")

            # Optional: desktop shortcut (skipped if we can't create safely without extra deps)
            if self.plan.create_desktop_shortcut:
                self.status.emit("Skipping desktop shortcut (optional).")

            time.sleep(0.3)
            self.progress.emit(100)
            self.status.emit("Install completed.")
            self.finished.emit(True, f"Installed to: {dst}")
        except Exception as e:
            self.finished.emit(False, str(e))


class SetupWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.setFixedSize(780, 520)

        self._page = 0  # 0 welcome, 1 license, 2 dir, 3 install, 4 finish
        self._accepted_license = False
        self._install_ok = False
        self._install_result = ""

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        header = QLabel(APP_TITLE)
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(header)

        sub = QLabel("This wizard will install MARK XXXIX on your computer.")
        sub.setFont(QFont("Segoe UI", 9))
        sub.setStyleSheet("color: #666;")
        layout.addWidget(sub)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #ddd;")
        layout.addWidget(line)

        self.stack = QWidget()
        self.stack_layout = QVBoxLayout(self.stack)
        self.stack_layout.setContentsMargins(0, 0, 0, 0)
        self.stack_layout.setSpacing(0)
        layout.addWidget(self.stack, stretch=1)

        self._pages: list[QWidget] = [
            self._welcome_page(),
            self._license_page(),
            self._dir_page(),
            self._install_page(),
            self._finish_page(),
        ]
        for p in self._pages:
            p.setVisible(False)
            self.stack_layout.addWidget(p)

        self._buttons = self._button_row()
        layout.addWidget(self._buttons)

        self._show_page(0)

    def _button_row(self) -> QWidget:
        w = QWidget()
        row = QHBoxLayout(w)
        row.setContentsMargins(0, 0, 0, 0)
        row.addStretch()

        self.btn_back = QPushButton("< Back")
        self.btn_next = QPushButton("Next >")
        self.btn_cancel = QPushButton("Cancel")
        for b in (self.btn_back, self.btn_next, self.btn_cancel):
            b.setFixedHeight(30)

        self.btn_back.clicked.connect(self._back)
        self.btn_next.clicked.connect(self._next)
        self.btn_cancel.clicked.connect(self.close)

        row.addWidget(self.btn_back)
        row.addWidget(self.btn_next)
        row.addWidget(self.btn_cancel)
        return w

    def _welcome_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 18, 0, 0)
        t = QLabel("Welcome to the MARK XXXIX Setup Wizard")
        t.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lay.addWidget(t)
        p = QLabel(
            "This installer will copy the application files to your computer.\n"
            "Click Next to continue."
        )
        p.setFont(QFont("Segoe UI", 10))
        p.setStyleSheet("color: #333;")
        p.setWordWrap(True)
        lay.addWidget(p)
        lay.addStretch()
        return w

    def _license_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 14, 0, 0)

        t = QLabel("License Agreement")
        t.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lay.addWidget(t)

        self.license_box = QTextEdit()
        self.license_box.setReadOnly(True)
        self.license_box.setText(_load_license_text())
        self.license_box.setFont(QFont("Consolas", 9))
        lay.addWidget(self.license_box, stretch=1)

        self.chk_accept = QCheckBox("I accept the terms in the License Agreement")
        self.chk_accept.stateChanged.connect(lambda _: self._update_buttons())
        lay.addWidget(self.chk_accept)
        return w

    def _dir_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 14, 0, 0)

        t = QLabel("Choose Install Location")
        t.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lay.addWidget(t)

        row = QHBoxLayout()
        self.install_path = QLineEdit(str(_default_install_dir()))
        self.install_path.setMinimumHeight(28)
        btn_browse = QPushButton("Browse…")
        btn_browse.clicked.connect(self._browse_install_dir)
        row.addWidget(self.install_path, stretch=1)
        row.addWidget(btn_browse)
        lay.addLayout(row)

        self.chk_shortcut = QCheckBox("Create a Desktop shortcut (optional)")
        self.chk_shortcut.setChecked(False)
        lay.addWidget(self.chk_shortcut)

        hint = QLabel("Click Next to start installation.")
        hint.setStyleSheet("color: #666;")
        lay.addWidget(hint)
        lay.addStretch()
        return w

    def _install_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 14, 0, 0)

        t = QLabel("Installing…")
        t.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lay.addWidget(t)

        self.lbl_status = QLabel("Preparing…")
        self.lbl_status.setStyleSheet("color: #333;")
        self.lbl_status.setWordWrap(True)
        lay.addWidget(self.lbl_status)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        lay.addWidget(self.progress)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Consolas", 9))
        lay.addWidget(self.log, stretch=1)
        return w

    def _finish_page(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 18, 0, 0)

        self.finish_title = QLabel("Setup Complete")
        self.finish_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lay.addWidget(self.finish_title)

        self.finish_text = QLabel("")
        self.finish_text.setWordWrap(True)
        self.finish_text.setStyleSheet("color: #333;")
        lay.addWidget(self.finish_text)

        lay.addStretch()
        return w

    def _browse_install_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select install folder", str(_default_install_dir()))
        if d:
            self.install_path.setText(d)

    def _show_page(self, idx: int):
        for i, p in enumerate(self._pages):
            p.setVisible(i == idx)
        self._page = idx
        self._update_buttons()

    def _update_buttons(self):
        self.btn_back.setEnabled(self._page > 0 and self._page < 3)
        self.btn_cancel.setEnabled(self._page < 3)

        if self._page == 0:
            self.btn_next.setEnabled(True)
            self.btn_next.setText("Next >")
        elif self._page == 1:
            self.btn_next.setText("Next >")
            self.btn_next.setEnabled(self.chk_accept.isChecked())
        elif self._page == 2:
            self.btn_next.setText("Install")
            self.btn_next.setEnabled(True)
        elif self._page == 3:
            self.btn_next.setEnabled(False)
            self.btn_next.setText("Installing…")
        elif self._page == 4:
            self.btn_back.setEnabled(False)
            self.btn_cancel.setEnabled(False)
            self.btn_next.setEnabled(True)
            self.btn_next.setText("Finish")

    def _back(self):
        if self._page > 0:
            self._show_page(self._page - 1)

    def _next(self):
        if self._page == 0:
            self._show_page(1)
            return
        if self._page == 1:
            self._show_page(2)
            return
        if self._page == 2:
            self._start_install()
            return
        if self._page == 4:
            self.close()

    def _start_install(self):
        if not PAYLOAD_DIR.exists():
            QMessageBox.critical(
                self,
                "Missing payload",
                f"Payload folder not found:\n{PAYLOAD_DIR}\n\n"
                "Build the installer with payload first.",
            )
            return

        target = Path(self.install_path.text().strip() or str(_default_install_dir()))
        plan = InstallPlan(
            source=PAYLOAD_DIR,
            target=target,
            create_desktop_shortcut=self.chk_shortcut.isChecked(),
        )

        self._show_page(3)
        self.progress.setValue(0)
        self.log.clear()

        self.worker_thread = QThread(self)
        self.worker = InstallerWorker(plan)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.status.connect(self._on_status)
        self.worker.finished.connect(self._on_finished)
        self.worker.finished.connect(lambda *_: self.worker_thread.quit())
        self.worker_thread.start()

    def _on_status(self, text: str):
        self.lbl_status.setText(text)
        self.log.append(text)

    def _on_finished(self, ok: bool, msg: str):
        self._install_ok = ok
        self._install_result = msg
        self.finish_title.setText("Setup Complete" if ok else "Setup Failed")
        self.finish_text.setText(msg)
        self._show_page(4)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = SetupWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

