"""Siri-like floating animated overlay widget for JARVIS."""

import math
import random

from PyQt6.QtCore import (
    QPropertyAnimation, QEasingCurve, QRectF, QTimer, Qt, pyqtSignal,
)
from PyQt6.QtGui import (
    QColor, QFont, QPainter, QPen, QRadialGradient, QBrush,
)
from PyQt6.QtWidgets import QApplication, QWidget


# Color palette (mirrors class C in ui.py)
class _C:
    PRI = "#00d4ff"
    PRI_DIM = "#007a99"
    ACC = "#ff6b00"
    ACC2 = "#ffcc00"
    GREEN = "#00ff88"
    BG = "#00060a"


def _qcol(h: str, a: int = 255) -> QColor:
    c = QColor(h)
    c.setAlpha(a)
    return c


class _Particle:
    """A simple particle for the SPEAKING state effect."""

    def __init__(self, cx: float, cy: float):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.5, 4.0)
        self.x = cx
        self.y = cy
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = 1.0
        self.decay = random.uniform(0.02, 0.05)
        self.size = random.uniform(2.0, 5.0)

    def step(self) -> bool:
        """Advance particle. Returns False when dead."""
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay
        return self.life > 0


_MAX_PARTICLES = 60


class SiriOverlay(QWidget):
    """Frameless, always-on-top animated overlay widget.

    States: LISTENING, SPEAKING, THINKING, IDLE
    """

    # Signals for thread-safe calls from non-GUI threads
    _state_signal = pyqtSignal(str)
    _show_signal = pyqtSignal()
    _hide_signal = pyqtSignal()
    _delayed_hide_signal = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(300, 300)

        # Animation state
        self._state = "IDLE"
        self._tick = 0
        self._particles: list[_Particle] = []
        self._arc_angle = 0.0

        # Generation counter to guard against stale delayed hides
        self._generation = 0

        # Animation timer (16ms ~ 60fps) - starts stopped, activated on show
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._step)

        # Fade animations
        self._fade_in_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_in_anim.setDuration(300)
        self._fade_in_anim.setStartValue(0.0)
        self._fade_in_anim.setEndValue(1.0)
        self._fade_in_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._fade_out_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_out_anim.setDuration(500)
        self._fade_out_anim.setStartValue(1.0)
        self._fade_out_anim.setEndValue(0.0)
        self._fade_out_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fade_out_anim.finished.connect(self._on_fade_out_done)

        # Connect signals for thread safety
        self._state_signal.connect(self._apply_state)
        self._show_signal.connect(self._do_show)
        self._hide_signal.connect(self._do_hide)
        self._delayed_hide_signal.connect(self._schedule_delayed_hide_on_gui)

    # ------------------------------------------------------------------
    # Public API (thread-safe - can be called from any thread)
    # ------------------------------------------------------------------

    def show_overlay(self):
        """Thread-safe: position at screen bottom-center, fade in, and start animating."""
        self._show_signal.emit()

    def hide_overlay(self):
        """Thread-safe: fade out, then hide the widget."""
        self._hide_signal.emit()

    def set_state(self, state: str):
        """Thread-safe state change. Emits signal so UI updates on main thread."""
        self._state_signal.emit(state)

    # ------------------------------------------------------------------
    # Internal (always runs on GUI thread via signals)
    # ------------------------------------------------------------------

    def _do_show(self):
        """Actually show the overlay - runs on GUI thread."""
        self._generation += 1
        self._position_bottom_center()
        self.setWindowOpacity(0.0)
        self.show()
        self._fade_out_anim.stop()
        self._fade_in_anim.start()
        if not self._timer.isActive():
            self._timer.start(16)

    def _do_hide(self):
        """Actually hide the overlay - runs on GUI thread.
        
        Guards against stale hides: no-op if the overlay is in an active state.
        """
        if self._state in ("SPEAKING", "LISTENING", "THINKING"):
            return
        self._fade_in_anim.stop()
        self._fade_out_anim.start()

    def schedule_delayed_hide(self, delay_ms: int = 2000):
        """Thread-safe: schedule a hide after delay_ms.
        
        Uses generation counter so that if the state changes before the
        timer fires, the hide is effectively cancelled.
        """
        self._delayed_hide_signal.emit(delay_ms)

    def _schedule_delayed_hide_on_gui(self, delay_ms: int):
        """Runs on GUI thread: sets up the QTimer.singleShot with generation guard."""
        gen = self._generation

        def _maybe_hide():
            if self._generation == gen and self._state not in ("SPEAKING", "LISTENING", "THINKING"):
                self._do_hide_force()

        QTimer.singleShot(delay_ms, _maybe_hide)

    def _apply_state(self, state: str):
        """Apply state on the GUI thread."""
        self._state = state
        # Bump generation on any active state to invalidate pending delayed hides
        if state in ("SPEAKING", "LISTENING", "THINKING"):
            self._generation += 1
        if state == "IDLE":
            self._do_hide_force()
        self._particles.clear()

    def _do_hide_force(self):
        """Unconditional hide (used by IDLE state transition)."""
        self._fade_in_anim.stop()
        self._fade_out_anim.start()

    def _on_fade_out_done(self):
        self.hide()
        # Stop the animation timer when hidden to save CPU
        self._timer.stop()

    def _position_bottom_center(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geom = screen.availableGeometry()
        x = geom.x() + (geom.width() - self.width()) // 2
        y = geom.y() + geom.height() - self.height() - 50
        self.move(x, y)

    def _step(self):
        """Animation tick - advance state, request repaint."""
        if not self.isVisible():
            return
        self._tick += 1
        self._arc_angle += 4.0

        # Update particles
        self._particles = [p for p in self._particles if p.step()]

        # Spawn new particles in SPEAKING state (capped)
        if self._state == "SPEAKING" and self._tick % 3 == 0:
            if len(self._particles) < _MAX_PARTICLES:
                cx = self.width() / 2.0
                cy = self.height() / 2.0 - 15
                self._particles.append(_Particle(cx, cy))

        self.update()

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self.width() / 2.0
        cy = self.height() / 2.0 - 15  # offset up for status text below

        if self._state == "LISTENING":
            self._paint_listening(p, cx, cy)
        elif self._state == "SPEAKING":
            self._paint_speaking(p, cx, cy)
        elif self._state == "THINKING":
            self._paint_thinking(p, cx, cy)

        # Status text
        self._paint_status_text(p)
        p.end()

    def _paint_listening(self, p: QPainter, cx: float, cy: float):
        """Pulsating breathing orb with radial gradient, cyan/blue."""
        t = self._tick * 0.04
        pulse = 0.85 + 0.15 * math.sin(t)
        radius = 50.0 * pulse

        # Outer glow
        grad = QRadialGradient(cx, cy, radius * 1.8)
        grad.setColorAt(0.0, _qcol(_C.PRI, 80))
        grad.setColorAt(0.5, _qcol(_C.PRI_DIM, 30))
        grad.setColorAt(1.0, _qcol(_C.PRI, 0))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(cx - radius * 1.8), int(cy - radius * 1.8),
                      int(radius * 3.6), int(radius * 3.6))

        # Core orb
        grad2 = QRadialGradient(cx, cy, radius)
        grad2.setColorAt(0.0, _qcol(_C.PRI, 220))
        grad2.setColorAt(0.6, _qcol(_C.PRI_DIM, 160))
        grad2.setColorAt(1.0, _qcol(_C.PRI, 40))
        p.setBrush(QBrush(grad2))
        p.drawEllipse(int(cx - radius), int(cy - radius),
                      int(radius * 2), int(radius * 2))

    def _paint_speaking(self, p: QPainter, cx: float, cy: float):
        """Energetic orb with waveform bars and particles, orange accent."""
        t = self._tick * 0.06
        base_radius = 45.0 + 8.0 * math.sin(t * 1.3) + random.uniform(-2, 2)

        # Outer glow (orange)
        grad = QRadialGradient(cx, cy, base_radius * 2.0)
        grad.setColorAt(0.0, _qcol(_C.ACC, 100))
        grad.setColorAt(0.5, _qcol(_C.ACC, 30))
        grad.setColorAt(1.0, _qcol(_C.ACC, 0))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(cx - base_radius * 2), int(cy - base_radius * 2),
                      int(base_radius * 4), int(base_radius * 4))

        # Core orb
        grad2 = QRadialGradient(cx, cy, base_radius)
        grad2.setColorAt(0.0, _qcol(_C.ACC, 240))
        grad2.setColorAt(0.5, _qcol(_C.PRI, 140))
        grad2.setColorAt(1.0, _qcol(_C.ACC, 50))
        p.setBrush(QBrush(grad2))
        p.drawEllipse(int(cx - base_radius), int(cy - base_radius),
                      int(base_radius * 2), int(base_radius * 2))

        # Waveform bars around the orb
        num_bars = 24
        for i in range(num_bars):
            angle = (2 * math.pi / num_bars) * i + t * 0.5
            bar_h = 8.0 + 12.0 * abs(math.sin(t * 2 + i * 0.5))
            bx = cx + math.cos(angle) * (base_radius + 8)
            by = cy + math.sin(angle) * (base_radius + 8)
            ex = cx + math.cos(angle) * (base_radius + 8 + bar_h)
            ey = cy + math.sin(angle) * (base_radius + 8 + bar_h)
            alpha = int(180 + 75 * math.sin(t + i))
            p.setPen(QPen(_qcol(_C.ACC, alpha), 2.5))
            p.drawLine(int(bx), int(by), int(ex), int(ey))

        # Particles
        for part in self._particles:
            alpha = int(part.life * 200)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(_qcol(_C.ACC, alpha)))
            p.drawEllipse(int(part.x - part.size / 2),
                          int(part.y - part.size / 2),
                          int(part.size), int(part.size))

    def _paint_thinking(self, p: QPainter, cx: float, cy: float):
        """Rotating arc/loading indicator, yellow accent."""
        t = self._tick * 0.05
        radius = 50.0

        # Subtle glow
        grad = QRadialGradient(cx, cy, radius * 1.5)
        grad.setColorAt(0.0, _qcol(_C.ACC2, 50))
        grad.setColorAt(0.6, _qcol(_C.ACC2, 15))
        grad.setColorAt(1.0, _qcol(_C.ACC2, 0))
        p.setBrush(QBrush(grad))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(cx - radius * 1.5), int(cy - radius * 1.5),
                      int(radius * 3), int(radius * 3))

        # Small core dot
        grad2 = QRadialGradient(cx, cy, 15)
        grad2.setColorAt(0.0, _qcol(_C.ACC2, 200))
        grad2.setColorAt(1.0, _qcol(_C.ACC2, 40))
        p.setBrush(QBrush(grad2))
        p.drawEllipse(int(cx - 15), int(cy - 15), 30, 30)

        # Rotating arcs
        p.setPen(QPen(_qcol(_C.ACC2, 200), 3.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)

        rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
        start_angle = int(self._arc_angle * 16) % 5760
        p.drawArc(rect, start_angle, 90 * 16)

        # Second arc (opposite)
        p.setPen(QPen(_qcol(_C.ACC2, 120), 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        rect2 = QRectF(cx - radius * 0.7, cy - radius * 0.7,
                       radius * 1.4, radius * 1.4)
        start_angle2 = int((self._arc_angle * 1.5 + 180) * 16) % 5760
        p.drawArc(rect2, start_angle2, 70 * 16)

    def _paint_status_text(self, p: QPainter):
        """Render status text below the orb."""
        text_map = {
            "LISTENING": "Listening...",
            "SPEAKING": "Speaking...",
            "THINKING": "Jarvis is thinking...",
        }
        text = text_map.get(self._state, "")
        if not text:
            return

        color_map = {
            "LISTENING": _C.PRI,
            "SPEAKING": _C.ACC,
            "THINKING": _C.ACC2,
        }

        font = QFont("Courier New", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        p.setFont(font)
        p.setPen(QPen(_qcol(color_map.get(self._state, _C.PRI), 200)))

        text_y = self.height() - 30
        rect = QRectF(0, text_y, self.width(), 30)
        p.drawText(rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, text)
