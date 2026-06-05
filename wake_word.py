"""
wake_word.py - Wake word detection module for JARVIS.

Uses sounddevice for audio capture and energy-based voice activity detection.
When sustained audio energy is detected (indicating speech directed at the assistant),
the configured callback is triggered.

NOTE: For production use, integrate vosk or a dedicated keyword spotting model
for actual keyword matching (e.g., "Jarvis", "Hey Jarvis", "Salom Jarvis").
This implementation uses energy-based detection as a lightweight trigger.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, List, Optional


class WakeWordDetector:
    """
    Listens for wake word activation using energy-based voice activity detection.

    The detector continuously monitors audio input. When the RMS energy exceeds
    the configured threshold for a sustained period, it triggers the callback,
    indicating the user is likely speaking to the assistant.

    Parameters
    ----------
    callback : Callable
        Function to call when wake word / speech is detected.
    keywords : list of str, optional
        Keywords to detect (for future model-based detection).
        Default: ["jarvis", "hey jarvis", "salom jarvis"]
    energy_threshold : int
        RMS energy threshold for voice activity detection. Default: 500.
    sample_rate : int
        Audio sample rate in Hz. Default: 16000.
    channels : int
        Number of audio channels. Default: 1 (mono).
    frame_duration_ms : int
        Duration of each audio frame in milliseconds. Default: 30.
    sustained_frames : int
        Number of consecutive frames above threshold to trigger. Default: 10.
    cooldown_seconds : float
        Minimum seconds between consecutive triggers. Default: 3.0.
    """

    def __init__(
        self,
        callback: Callable,
        keywords: Optional[List[str]] = None,
        energy_threshold: int = 500,
        sample_rate: int = 16000,
        channels: int = 1,
        frame_duration_ms: int = 30,
        sustained_frames: int = 10,
        cooldown_seconds: float = 3.0,
    ):
        self._callback = callback
        self._keywords = keywords or ["jarvis", "hey jarvis", "salom jarvis"]
        self._energy_threshold = energy_threshold
        self._sample_rate = sample_rate
        self._channels = channels
        self._frame_duration_ms = frame_duration_ms
        self._sustained_frames = sustained_frames
        self._cooldown_seconds = cooldown_seconds

        # Internal state
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_trigger_time: float = 0.0

        # Frame size in samples
        self._frame_size = int(self._sample_rate * self._frame_duration_ms / 1000)

    def start(self) -> None:
        """Start background listening thread."""
        if self._running:
            return

        self._stop_event.clear()
        self._running = True
        self._thread = threading.Thread(
            target=self._listen_loop,
            daemon=True,
            name="WakeWordDetector",
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the listening thread."""
        if not self._running:
            return

        self._stop_event.set()
        self._running = False

        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None

    def is_running(self) -> bool:
        """Return whether the detector is currently running."""
        return self._running and not self._stop_event.is_set()

    @property
    def energy_threshold(self) -> int:
        """Get current energy threshold."""
        return self._energy_threshold

    @energy_threshold.setter
    def energy_threshold(self, value: int) -> None:
        """Set energy threshold dynamically."""
        self._energy_threshold = max(0, int(value))

    @property
    def keywords(self) -> List[str]:
        """Get configured keywords."""
        return list(self._keywords)

    def _listen_loop(self) -> None:
        """Main listening loop running in background thread."""
        try:
            import sounddevice as sd
        except ImportError:
            self._running = False
            return

        consecutive_active = 0
        block_size = self._frame_size

        def audio_callback(indata, frames, time_info, status):
            nonlocal consecutive_active

            if self._stop_event.is_set():
                raise sd.CallbackAbort()

            # Compute RMS directly from the numpy float32 array
            try:
                import numpy as np
                rms = int(np.sqrt(np.mean(indata[:, 0] ** 2)) * 32767)
            except Exception:
                consecutive_active = 0
                return

            if rms >= self._energy_threshold:
                consecutive_active += 1
            else:
                consecutive_active = 0

            # Check if we have sustained activity
            if consecutive_active >= self._sustained_frames:
                now = time.time()
                if now - self._last_trigger_time >= self._cooldown_seconds:
                    self._last_trigger_time = now
                    consecutive_active = 0
                    # Call the callback in a separate thread to avoid blocking audio
                    threading.Thread(
                        target=self._safe_callback,
                        daemon=True,
                    ).start()

        try:
            with sd.InputStream(
                samplerate=self._sample_rate,
                channels=self._channels,
                dtype="float32",
                blocksize=block_size,
                callback=audio_callback,
            ):
                # Keep the stream alive until stop is requested
                while not self._stop_event.is_set():
                    self._stop_event.wait(timeout=0.5)
        except Exception:
            pass
        finally:
            self._running = False

    def _safe_callback(self) -> None:
        """Call the user callback with error handling."""
        try:
            self._callback()
        except Exception:
            pass


# Convenience function for quick testing
def create_detector(
    callback: Callable,
    keywords: Optional[List[str]] = None,
    energy_threshold: int = 500,
) -> WakeWordDetector:
    """
    Create and return a WakeWordDetector instance.

    Parameters
    ----------
    callback : Callable
        Function to call on wake word detection.
    keywords : list of str, optional
        Wake words to listen for.
    energy_threshold : int
        Energy level that triggers detection. Default: 500.

    Returns
    -------
    WakeWordDetector
        Configured detector instance (call .start() to begin).
    """
    return WakeWordDetector(
        callback=callback,
        keywords=keywords,
        energy_threshold=energy_threshold,
    )
