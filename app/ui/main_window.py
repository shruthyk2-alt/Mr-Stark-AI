from __future__ import annotations

import math
import os
import threading
import time
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
import google.genai as genai
from google.genai.errors import APIError
from PySide6.QtCore import QEvent, QObject, QPoint, QRect, QSize, QTimer, Qt, QThread, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QFont
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QStackedWidget,
)

try:
    import pyttsx3
except Exception:  # pragma: no cover - optional dependency
    pyttsx3 = None

try:
    import speech_recognition as sr
except Exception:  # pragma: no cover - optional dependency
    sr = None

from app.personality.voice import StarkVoice


class VoiceCaptureWorker(QObject):
    """Continuous voice capture worker that runs in a background thread."""
    
    utterance_captured = Signal(str)  # Emitted when a complete utterance is recognized
    error = Signal(str)                # Emitted for errors that don't stop the worker
    worker_stopped = Signal()          # Emitted when worker stops (user pressed Stop)
    listening = Signal()               # Emitted when ready to listen
    wake_word_detected = Signal()      # Emitted when "Hey Mr. Stark" is detected (standby mode)
    mode_changed = Signal(str)         # Emitted with mode: "standby" or "active"

    def __init__(self, recognizer, microphone, stop_event, main_window, start_in_standby=False):
        super().__init__()
        self.recognizer = recognizer
        self.microphone = microphone
        self.stop_event = stop_event
        self.main_window = main_window  # Reference to check suppression flag
        self.is_running = True
        self.standby_mode = start_in_standby  # True = listening for wake word only
        self.last_activity_time = time.time()  # Track last successful utterance

    def run(self) -> None:
        """
        Continuous listening loop.
        Keeps listening for utterances until stop_event is set.
        Handles errors gracefully without exiting the loop.
        Suppresses listening while TTS is speaking.
        """
        if self.recognizer is None or self.microphone is None:
            self.error.emit("Voice input is not available in this environment.")
            self.worker_stopped.emit()
            return

        # Configure recognizer for complete utterances
        # These parameters help capture full sentences, not fragments
        self.recognizer.energy_threshold = 4000        # Adjust sensitivity
        self.recognizer.dynamic_energy_threshold = True # Auto-adjust for ambient noise
        self.recognizer.pause_threshold = 0.8          # Seconds of silence to detect end of utterance
        self.recognizer.phrase_threshold = 0.3         # Min confidence for a phrase
        self.recognizer.non_speaking_duration = 0.5    # Seconds of silence between phrases

        print("[VOICE] Worker started - continuous listening loop active")
        initial_mode = "standby" if self.standby_mode else "active"
        print(f"[VOICE] Starting in {initial_mode} mode")
        self.mode_changed.emit(initial_mode)
        
        try:
            with self.microphone as source:
                # Adjust once at startup
                print("[VOICE] Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                
                # Continuous listening loop
                while self.is_running and not self.stop_event.is_set():
                    # Check for inactivity timeout (30 seconds in active mode)
                    if not self.standby_mode:
                        if time.time() - self.last_activity_time > 30:
                            print("[VOICE] Inactivity timeout - returning to standby")
                            self.standby_mode = True
                            self.mode_changed.emit("standby")
                            self.append_console_safe("Returning to standby. Say 'Hey Mr. Stark' to activate.")
                    
                    # Check if microphone is suppressed (MR. STARK is speaking)
                    if self.main_window and self.main_window.microphone_suppressed:
                        print("[VOICE] Microphone suppressed (TTS active) - sleeping...")
                        time.sleep(0.1)  # Brief sleep to avoid busy-waiting
                        continue
                    
                    try:
                        self.listening.emit()
                        mode_label = "standby" if self.standby_mode else "active"
                        print(f"[VOICE] Listening for utterance ({mode_label})...")
                        
                        # Listen for a complete utterance
                        # timeout: max time to wait for speech to start (12 seconds)
                        # phrase_time_limit: max length of an utterance (15 seconds)
                        audio = self.recognizer.listen(
                            source,
                            timeout=12,
                            phrase_time_limit=15,
                            snowboy_configuration=None
                        )
                        
                        # Check if stop was requested while listening
                        if self.stop_event.is_set():
                            print("[VOICE] Stop requested during listen")
                            break
                        
                        # Recognize the speech
                        print("[VOICE] Recognizing speech...")
                        try:
                            text = self.recognizer.recognize_google(audio)
                            
                            if text and text.strip():
                                print(f"[VOICE] Captured complete utterance: '{text}'")
                                
                                # Check for wake word if in standby mode
                                if self.standby_mode:
                                    if self._is_wake_word(text):
                                        print("[VOICE] Wake word detected! Activating...")
                                        self.standby_mode = False
                                        self.last_activity_time = time.time()
                                        self.mode_changed.emit("active")
                                        self.wake_word_detected.emit()
                                        self.append_console_safe("Listening for commands...")
                                        # Do NOT emit utterance_captured for wake word
                                        print("[VOICE] Wake word not sent to Gemini")
                                    else:
                                        # Still in standby, ignore this utterance
                                        print(f"[VOICE] Standby mode - ignoring: '{text}'")
                                        self.error.emit(f"(Standby) Say 'Hey Mr. Stark' to activate.")
                                else:
                                    # In active mode, process the utterance normally
                                    self.last_activity_time = time.time()
                                    self.utterance_captured.emit(text.strip())
                            else:
                                print("[VOICE] Empty text recognized")
                                self.error.emit("No speech detected. Try again.")
                                
                        except sr.UnknownValueError:
                            # Google Speech Recognition could not understand audio
                            print("[VOICE] UnknownValueError: Speech not understood")
                            self.error.emit("Didn't catch that. Please repeat.")
                            
                        except sr.RequestError as e:
                            # Network or API error
                            print(f"[VOICE] RequestError: {e}")
                            self.error.emit(f"Connection issue: {str(e)[:50]}")
                    
                    except sr.WaitTimeoutError:
                        # Timeout waiting for speech to start
                        print("[VOICE] WaitTimeoutError: No speech detected within timeout")
                        self.error.emit("No speech detected. Still listening...")
                        # Continue listening, don't exit
                    
                    except Exception as e:
                        # Other recognition errors
                        print(f"[VOICE] Recognition error: {e}")
                        self.error.emit(f"Voice error: {str(e)[:50]}")
                        # Continue listening, don't exit
                        
        except Exception as exc:
            print(f"[VOICE] Fatal worker error: {exc}")
            self.error.emit(f"Voice worker error: {str(exc)[:50]}")
        
        print("[VOICE] Worker stopped")
        self.worker_stopped.emit()
    
    def _is_wake_word(self, text: str) -> bool:
        """
        Detect if the text contains the wake word "Hey Mr. Stark".
        Uses fuzzy matching to handle variations and slight mishearings.
        Returns True if wake word is detected, False otherwise.
        """
        text_lower = text.lower().strip()
        wake_phrases = [
            "hey mr stark",
            "hey mr. stark",
            "hey mister stark",
            "hello mr stark",
            "hello mr. stark",
            "hey stark",
            "mr stark",
            "Yoo Mr Stark",
        ]
        
        # Exact substring match (most reliable)
        for phrase in wake_phrases:
            if phrase in text_lower:
                return True
        
        # Fuzzy match: check if key words are present
        words = set(text_lower.split())
        if ("mr" in words or "mister" in words or "stark" in words) and ("hey" in words or "hello" in words):
            return True
        
        # Levenshtein-like check: if the text is very close to "hey mr stark"
        # This helps with common mishearings like "hey mister stark" or "hey mr starch"
        if len(text_lower) < 25:  # Wake word shouldn't be too long
            main_phrase = "hey mr stark"
            # Simple char-by-char similarity (if >70% similar, it's likely a wake word)
            matches = sum(1 for a, b in zip(text_lower, main_phrase) if a == b)
            if len(text_lower) > 5 and matches / len(main_phrase) > 0.7:
                print(f"[VOICE] Wake word fuzzy match: '{text_lower}' similar to '{main_phrase}'")
                return True
        
        return False
    
    def append_console_safe(self, text: str) -> None:
        """
        Safely append text to console from worker thread.
        """
        if self.main_window and hasattr(self.main_window, 'append_console'):
            self.main_window.append_console(text)


class EnhancedArcReactorWidget(QWidget):
    """
    Enhanced Arc Reactor widget with sophisticated animations for different states.
    Represents the central computational core of MR. STARK.
    """
    def __init__(self, parent: Optional[QWidget] = None, compact: bool = False) -> None:
        super().__init__(parent)
        self.state = "idle"
        self.phase = 0.0
        self.compact = compact
        self.size_multiplier = 1.0
        self._ticker = QTimer(self)
        self._ticker.timeout.connect(self._animate)
        self._ticker.start(16)  # Higher refresh rate for smoother animation
        
        if compact:
            self.setMinimumSize(160, 160)
        else:
            self.setMinimumSize(280, 280)

    def _animate(self) -> None:
        self.phase += 0.06
        if self.phase > 360:
            self.phase -= 360
        self.update()

    def set_state(self, state: str) -> None:
        self.state = state
        self.update()

    def set_size_multiplier(self, mult: float) -> None:
        self.size_multiplier = mult
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        rect = self.rect().adjusted(10, 10, -10, -10)
        cx = rect.center().x()
        cy = rect.center().y()

        # Define state parameters
        if self.state == "listening":
            primary_color = QColor(116, 214, 255)  # Cyan
            secondary_color = QColor(75, 180, 255)  # Darker cyan
            glow_strength = 0.95
            pulse_speed = 1.2
            rotation_speed = 0.0
        elif self.state == "processing":
            primary_color = QColor(255, 190, 90)  # Orange
            secondary_color = QColor(255, 150, 50)  # Darker orange
            glow_strength = 0.85
            pulse_speed = 1.8
            rotation_speed = 2.5
        elif self.state == "speaking":
            primary_color = QColor(113, 255, 172)  # Green
            secondary_color = QColor(70, 220, 140)  # Darker green
            glow_strength = 1.0
            pulse_speed = 2.2
            rotation_speed = 0.0
        else:  # idle/standby
            primary_color = QColor(110, 190, 255)  # Light blue
            secondary_color = QColor(75, 150, 255)  # Darker blue
            glow_strength = 0.65
            pulse_speed = 0.8
            rotation_speed = 0.5

        # Draw outer pulsing rings
        pulse = 0.5 + abs(math.sin(self.phase * pulse_speed * 0.02)) * 0.5
        for i in range(6):
            ring_size = 70 + i * 24 + pulse * 18
            alpha = max(20, int(70 + i * 20 * glow_strength))
            ring_color = QColor(primary_color.red(), primary_color.green(), primary_color.blue(), alpha)
            pen = QPen(ring_color, 1.2 + i * 0.25)
            painter.setPen(pen)
            painter.drawEllipse(
                cx - ring_size // 2,
                cy - ring_size // 2,
                ring_size,
                ring_size,
            )

        # Draw rotating internal ring (when processing)
        if self.state == "processing":
            rotation = (self.phase * rotation_speed) % 360
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(rotation)
            
            ring_rad = 80
            painter.setPen(QPen(QColor(255, 190, 90, 120), 2))
            for angle in range(0, 360, 30):
                rad = math.radians(angle)
                x1 = ring_rad * math.cos(rad)
                y1 = ring_rad * math.sin(rad)
                x2 = (ring_rad + 15) * math.cos(rad)
                y2 = (ring_rad + 15) * math.sin(rad)
                painter.drawLine(int(x1), int(y1), int(x2), int(y2))
            
            painter.restore()

        # Draw solid outer ring
        outer_ring_radius = min(self.width(), self.height()) * 0.38
        painter.setPen(QPen(QColor(primary_color.red(), primary_color.green(), primary_color.blue(), 200), 2.5))
        painter.drawEllipse(cx - outer_ring_radius, cy - outer_ring_radius, outer_ring_radius * 2, outer_ring_radius * 2)

        # Draw center sphere with glow
        center_radius = 30 + abs(math.sin(self.phase * 0.03)) * 10
        
        # Glow effect (multiple circles with decreasing opacity)
        for j in range(3, 0, -1):
            glow_radius = center_radius + j * 6
            glow_alpha = int(60 / j)
            glow_color = QColor(primary_color.red(), primary_color.green(), primary_color.blue(), glow_alpha)
            painter.setBrush(glow_color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(cx - glow_radius, cy - glow_radius, glow_radius * 2, glow_radius * 2)

        # Draw center core
        painter.setBrush(QColor(primary_color.red(), primary_color.green(), primary_color.blue(), 220))
        painter.setPen(QPen(QColor(primary_color.red(), primary_color.green(), primary_color.blue(), 255), 2))
        painter.drawEllipse(cx - center_radius, cy - center_radius, center_radius * 2, center_radius * 2)

        # Draw internal cross pattern
        cross_size = center_radius * 0.6
        painter.setPen(QPen(QColor(255, 255, 255, 150), 1.5))
        painter.drawLine(cx - cross_size, cy, cx + cross_size, cy)
        painter.drawLine(cx, cy - cross_size, cx, cy + cross_size)

        # Draw triangular energy indicators (3 triangles pointing outward)
        if self.state != "idle":
            indicator_dist = outer_ring_radius + 20
            for idx in range(3):
                angle = (self.phase * 0.05 + idx * 120) * math.pi / 180
                x = cx + indicator_dist * math.cos(angle)
                y = cy + indicator_dist * math.sin(angle)
                
                triangle_size = 8
                painter.setBrush(primary_color)
                painter.setPen(QPen(primary_color, 1))
                
                # Simple triangle pointing outward
                points = [
                    QPoint(int(x), int(y - triangle_size)),
                    QPoint(int(x - triangle_size), int(y + triangle_size)),
                    QPoint(int(x + triangle_size), int(y + triangle_size)),
                ]
                painter.drawPolygon(points)


# Keep the old class name for backward compatibility
class ArcReactorWidget(EnhancedArcReactorWidget):
    pass


class StartupSplash(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(540, 320)

        self._pulse = 0.0
        self._progress = 0
        self._ticker = QTimer(self)
        self._ticker.timeout.connect(self._animate)
        self._ticker.start(30)

        self.message = QLabel("INITIALIZING MR. STARK")
        self.message.setAlignment(Qt.AlignCenter)
        self.message.setStyleSheet(
            "color: #EAF7FF; font: 700 18px 'Segoe UI'; letter-spacing: 3px;"
        )

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(8)
        self.progress.setStyleSheet(
            "QProgressBar { border: none; background: rgba(255,255,255,0.08); border-radius: 4px; }"
            "QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #89d5ff, stop:1 #5d8cff); border-radius: 4px; }"
        )

        self.subtext = QLabel("Loading profile, tools, and secure access layers...")
        self.subtext.setAlignment(Qt.AlignCenter)
        self.subtext.setStyleSheet("color: #9CC5D9; font: 500 11px 'Segoe UI';")

        container = QVBoxLayout(self)
        container.setContentsMargins(30, 30, 30, 30)
        container.addStretch()
        container.addWidget(self.message)
        container.addSpacing(12)
        container.addWidget(self.progress)
        container.addSpacing(10)
        container.addWidget(self.subtext)
        container.addStretch()

    def _animate(self) -> None:
        self._pulse += 0.08
        self._progress = min(self._progress + 1, 100)
        self.progress.setValue(self._progress)

        if self._progress >= 100:
            self._ticker.stop()
            QTimer.singleShot(450, self.close)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        glow = abs(math.sin(self._pulse)) * 0.35 + 0.2
        bg = QColor(7, 17, 32)
        border = QColor(104, 177, 255)
        glow_color = QColor(91, 136, 255, int(255 * glow))

        painter.fillRect(self.rect(), bg)
        painter.setPen(QPen(border, 1.5))
        painter.drawRoundedRect(QRect(10, 10, self.width() - 20, self.height() - 20), 20, 20)

        for i in range(3):
            alpha = int(80 + i * 40 + glow * 100)
            pen = QPen(QColor(130, 200, 255, alpha), 2)
            painter.setPen(pen)
            radius = 90 + i * 24 + abs(math.sin(self._pulse + i)) * 10
            painter.drawEllipse(
                self.width() // 2 - radius // 2,
                self.height() // 2 - radius // 2,
                radius,
                radius,
            )

        painter.setPen(QPen(glow_color, 3))
        painter.drawEllipse(self.width() // 2 - 46, self.height() // 2 - 46, 92, 92)
        painter.setPen(QPen(QColor(209, 236, 255), 2))
        painter.drawLine(self.width() // 2 - 28, self.height() // 2, self.width() // 2 + 28, self.height() // 2)
        painter.drawLine(self.width() // 2, self.height() // 2 - 28, self.width() // 2, self.height() // 2 + 28)


class StarkMainWindow(QMainWindow):
    """
    MR. STARK Main Window with Redesigned Sophisticated UI.
    Features left sidebar navigation, central Arc Reactor, right-side panels, and enhanced styling.
    """
    def __init__(self) -> None:
        super().__init__()
        
        # Initialize backend systems
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        load_dotenv(os.path.join(project_root, ".env"))
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            self.gemini_client = genai.Client(api_key=self.api_key)
            self.chat_session = None
        else:
            self.gemini_client = None
            self.chat_session = None
        
        self.conversation_history = []
        self.stark_voice = StarkVoice(mode="focused")
        self.voice_state = "idle"
        self.voice_enabled = False
        self.voice_engine = None
        self.recognizer = None
        self.microphone = None
        self.microphone_suppressed = False
        self.voice_stop_requested = False
        self.voice_thread = None
        self.voice_worker = None
        self.voice_stop_event = None
        self.wake_word_enabled = True
        self.voice_in_standby = False
        self.inactivity_timeout_seconds = 30
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.setSingleShot(True)
        self.inactivity_timer.timeout.connect(self._on_inactivity_timeout)
        self.gemini_request_in_flight = False
        self._max_history_messages = 8
        self.ui_mode = "voice"
        self._init_voice_system()

        # Window setup
        self.setWindowTitle("MR. STARK — ONLINE")
        self.resize(1400, 900)
        self.setMinimumSize(1200, 700)

        # Apply global stylesheet
        self._apply_stylesheet()

        # Build UI
        self._build_ui()

        self.set_mode("voice")

    def _apply_stylesheet(self) -> None:
        """Apply global stylesheet for the application."""
        stylesheet = """
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                stop:0 #050d15, stop:0.45 #0a1723, stop:1 #050b12);
        }
        QWidget {
            color: #EAF7FF;
            background: transparent;
        }
        QTextEdit, QLineEdit {
            background: rgba(13, 23, 33, 0.85);
            color: #EAF7FF;
            border: 1px solid rgba(124, 213, 255, 0.2);
            border-radius: 8px;
            padding: 8px;
            selection-background-color: rgba(124, 213, 255, 0.4);
        }
        QPushButton {
            color: #EAF7FF;
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 700;
            border: 1px solid rgba(124, 213, 255, 0.3);
        }
        QPushButton:hover {
            background: rgba(124, 213, 255, 0.15);
        }
        QPushButton:pressed {
            background: rgba(124, 213, 255, 0.25);
        }
        """
        self.setStyleSheet(stylesheet)

    def _build_ui(self) -> None:
        """Build the complete UI with sidebar, main content, and right panels."""
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ========== LEFT SIDEBAR ==========
        sidebar = self._build_sidebar()
        main_layout.addWidget(sidebar, 0)

        # ========== CENTER CONTENT ==========
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        # Top header with status
        header = self._build_header()
        center_layout.addWidget(header, 0)

        # Main content area
        self.content_area = QStackedWidget()
        self.voice_page = self._build_voice_mode()
        self.text_page = self._build_text_mode()
        self.content_area.addWidget(self.voice_page)
        self.content_area.addWidget(self.text_page)
        self.content_area.setCurrentWidget(self.voice_page)
        center_layout.addWidget(self.content_area, 1)

        # Bottom control bar
        control_bar = self._build_control_bar()
        center_layout.addWidget(control_bar, 0)

        main_layout.addWidget(center_container, 1)

        # ========== RIGHT SIDEBAR ==========
        right_panel = self._build_right_panel()
        main_layout.addWidget(right_panel, 0)

    def _build_sidebar(self) -> QFrame:
        """Build the left navigation sidebar."""
        sidebar = QFrame()
        sidebar.setStyleSheet(
            "QFrame { background: rgba(7, 17, 32, 0.95); border-right: 1px solid rgba(116, 214, 255, 0.15); }"
        )
        sidebar.setFixedWidth(180)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(8)

        # STARK branding
        brand = QLabel("⬤ STARK")
        brand.setStyleSheet("font: 700 14px 'Segoe UI'; color: #74d6ff; letter-spacing: 2px;")
        layout.addWidget(brand)

        layout.addSpacing(16)

        # Navigation items
        nav_items = [
            ("Home", self._on_nav_home),
            ("Chat", lambda: self.set_mode("text")),
            ("Projects", self._on_nav_projects),
            ("Tools", self._on_nav_tools),
            ("Memory", self._on_nav_memory),
            ("Settings", self._on_nav_settings),
        ]

        for label, callback in nav_items:
            btn = QPushButton(label)
            btn.setStyleSheet(
                "QPushButton { background: transparent; color: #b8d9ff; border: none; padding: 10px 12px; text-align: left; font: 600 11px 'Segoe UI'; }"
                "QPushButton:hover { background: rgba(116, 214, 255, 0.1); color: #74d6ff; }"
            )
            btn.clicked.connect(callback)
            layout.addWidget(btn)

        layout.addStretch()

        # User info at bottom
        user_label = QLabel("User: Shruthy")
        user_label.setStyleSheet("color: #7cb5ff; font: 500 10px 'Segoe UI'; padding: 8px;")
        user_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(user_label)

        return sidebar

    def _build_header(self) -> QFrame:
        """Build the top header with status."""
        header = QFrame()
        header.setStyleSheet(
            "QFrame { background: rgba(13, 23, 33, 0.6); border-bottom: 1px solid rgba(116, 214, 255, 0.15); }"
        )
        header.setFixedHeight(60)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(0)

        # Title
        title = QLabel("MR. STARK")
        title.setStyleSheet("font: 700 24px 'Segoe UI'; color: #74d6ff; letter-spacing: 2px;")
        layout.addWidget(title, 0)

        layout.addSpacing(16)

        # Status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #74d6ff; font: 700 20px; margin: 0px 4px;")
        self.status_label = QLabel("ONLINE")
        self.status_label.setStyleSheet("color: #b8d9ff; font: 600 12px 'Segoe UI'; letter-spacing: 1px;")
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(6)
        status_layout.addWidget(self.status_indicator, 0)
        status_layout.addWidget(self.status_label, 0)
        status_frame = QFrame()
        status_frame.setLayout(status_layout)
        layout.addWidget(status_frame, 0)

        layout.addStretch()

        # Mode toggle buttons
        self.text_mode_button = QPushButton("TEXT")
        self.text_mode_button.setStyleSheet(
            "QPushButton { background: rgba(255,255,255,0.05); color: #EAF7FF; border: 1px solid rgba(124, 213, 255, 0.3); "
            "border-radius: 6px; padding: 6px 14px; font: 600 10px 'Segoe UI'; } "
            "QPushButton:hover { background: rgba(124, 213, 255, 0.12); }"
        )
        self.text_mode_button.clicked.connect(lambda: self.set_mode("text"))
        self.text_mode_button.setVisible(True)
        layout.addWidget(self.text_mode_button, 0)

        self.voice_mode_button = QPushButton("VOICE")
        self.voice_mode_button.setStyleSheet(
            "QPushButton { background: rgba(116, 214, 255, 0.15); color: #74d6ff; border: 1px solid rgba(124, 213, 255, 0.5); "
            "border-radius: 6px; padding: 6px 14px; font: 600 10px 'Segoe UI'; } "
            "QPushButton:hover { background: rgba(124, 213, 255, 0.25); }"
        )
        self.voice_mode_button.clicked.connect(lambda: self.set_mode("voice"))
        self.voice_mode_button.setVisible(False)
        layout.addWidget(self.voice_mode_button, 0)

        return header

    def _build_voice_mode(self) -> QWidget:
        """Build the voice mode main content area."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        # Reactor + info in center
        center_layout = QHBoxLayout()
        center_layout.setSpacing(40)

        # Left: Arc Reactor
        reactor_frame = QFrame()
        reactor_frame.setStyleSheet("background: transparent;")
        reactor_layout = QVBoxLayout(reactor_frame)
        reactor_layout.setAlignment(Qt.AlignCenter)
        reactor_layout.setContentsMargins(0, 0, 0, 0)

        self.reactor_widget = ArcReactorWidget()
        self.reactor_widget.setFixedSize(360, 360)
        self.reactor_widget.set_state(self.voice_state)
        reactor_layout.addWidget(self.reactor_widget, alignment=Qt.AlignCenter)

        center_layout.addWidget(reactor_frame, 0, Qt.AlignCenter)

        # Right: System info and quick actions
        info_frame = QFrame()
        info_frame.setStyleSheet(
            "QFrame { background: rgba(13, 23, 33, 0.7); border: 1px solid rgba(116, 214, 255, 0.15); border-radius: 12px; }"
        )
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(20, 16, 20, 16)
        info_layout.setSpacing(12)

        # Voice status label
        info_label = QLabel("VOICE ASSISTANT")
        info_label.setStyleSheet("color: #74d6ff; font: 700 12px 'Segoe UI'; letter-spacing: 1px;")
        info_layout.addWidget(info_label)

        # Status text
        self.voice_status = QLabel("Ready")
        self.voice_status.setStyleSheet("color: #b8d9ff; font: 500 11px 'Segoe UI'; line-height: 1.5;")
        self.voice_status.setWordWrap(True)
        info_layout.addWidget(self.voice_status)

        info_layout.addSpacing(12)

        # Quick action buttons
        action_label = QLabel("QUICK ACTIONS")
        action_label.setStyleSheet("color: #74d6ff; font: 700 11px 'Segoe UI'; letter-spacing: 1px;")
        info_layout.addWidget(action_label)

        for action_name in ["Run Scan", "Open Console", "Guard Review"]:
            btn = QPushButton(action_name)
            btn.setStyleSheet(
                "QPushButton { background: rgba(116, 214, 255, 0.1); color: #b8d9ff; border: 1px solid rgba(116, 214, 255, 0.25); "
                "border-radius: 6px; padding: 8px 12px; font: 500 10px 'Segoe UI'; } "
                "QPushButton:hover { background: rgba(116, 214, 255, 0.2); color: #74d6ff; }"
            )
            btn.clicked.connect(lambda checked, n=action_name: self.handle_action(n))
            info_layout.addWidget(btn)

        info_layout.addStretch()
        center_layout.addWidget(info_frame, 1)

        layout.addLayout(center_layout, 1)
        return container

    def _build_text_mode(self) -> QWidget:
        """Build the text/chat mode main content area."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Chat area
        chat_frame = QFrame()
        chat_frame.setStyleSheet(
            "QFrame { background: rgba(13, 23, 33, 0.7); border: 1px solid rgba(116, 214, 255, 0.15); border-radius: 12px; }"
        )
        chat_layout = QVBoxLayout(chat_frame)
        chat_layout.setContentsMargins(16, 16, 16, 16)
        chat_layout.setSpacing(10)

        # Console output
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setPlainText("Welcome to MR. STARK. Ready for interaction.\n")
        self.console_output.setStyleSheet(
            "QTextEdit { background: rgba(7, 17, 32, 0.8); color: #EAF7FF; border: 1px solid rgba(116, 214, 255, 0.15); "
            "border-radius: 8px; padding: 12px; font: 500 11px 'Courier New'; }"
        )
        chat_layout.addWidget(self.console_output, 1)

        # Input area
        input_frame = QFrame()
        input_frame.setStyleSheet("background: transparent;")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Ask MR. STARK...")
        self.command_input.returnPressed.connect(self.send_console_prompt)
        input_layout.addWidget(self.command_input, 1)

        send_button = QPushButton("SEND")
        send_button.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            "stop:0 #3a8dff, stop:1 #6cb5ff); color: #061420; border: none; "
            "border-radius: 6px; padding: 9px 20px; font: 700 11px 'Segoe UI'; } "
            "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            "stop:0 #4a9dff, stop:1 #7cc5ff); }"
        )
        send_button.clicked.connect(self.send_console_prompt)
        input_layout.addWidget(send_button, 0)

        chat_layout.addWidget(input_frame, 0)
        layout.addWidget(chat_frame, 1)

        return container

    def _build_control_bar(self) -> QFrame:
        """Build the bottom control bar."""
        bar = QFrame()
        bar.setStyleSheet(
            "QFrame { background: rgba(13, 23, 33, 0.6); border-top: 1px solid rgba(116, 214, 255, 0.15); }"
        )
        bar.setFixedHeight(70)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(12)

        # Primary activation button
        self.primary_button = QPushButton("ACTIVATE CORE")
        self.primary_button.setStyleSheet(
            "QPushButton { background: rgba(116, 214, 255, 0.15); color: #74d6ff; border: 1px solid rgba(116, 214, 255, 0.35); "
            "border-radius: 8px; padding: 12px 20px; font: 700 11px 'Segoe UI'; } "
            "QPushButton:hover { background: rgba(116, 214, 255, 0.25); }"
        )
        self.primary_button.clicked.connect(self.on_activate)
        layout.addWidget(self.primary_button)

        layout.addSpacing(12)

        # Voice toggle
        self.voice_toggle_button = QPushButton("🎤 Voice: OFF")
        self.voice_toggle_button.setStyleSheet(
            "QPushButton { background: rgba(255,255,255,0.05); color: #b8d9ff; border: 1px solid rgba(125,152,180,0.28); "
            "border-radius: 8px; padding: 10px 16px; font: 600 10px 'Segoe UI'; } "
            "QPushButton:hover { background: rgba(255,255,255,0.1); }"
        )
        self.voice_toggle_button.clicked.connect(self.toggle_voice_activation)
        layout.addWidget(self.voice_toggle_button)

        # Stop button
        self.stop_voice_button = QPushButton("⏹ STOP")
        self.stop_voice_button.setStyleSheet(
            "QPushButton { background: rgba(255,100,100,0.15); color: #ffc0c0; border: 1px solid rgba(255,100,100,0.35); "
            "border-radius: 8px; padding: 10px 16px; font: 700 10px 'Segoe UI'; } "
            "QPushButton:hover { background: rgba(255,100,100,0.25); }"
        )
        self.stop_voice_button.clicked.connect(self.interrupt_voice)
        self.stop_voice_button.setEnabled(False)
        layout.addWidget(self.stop_voice_button)

        layout.addStretch()

        return bar

    def _build_right_panel(self) -> QFrame:
        """Build the right-side information panel."""
        panel = QFrame()
        panel.setStyleSheet(
            "QFrame { background: rgba(7, 17, 32, 0.95); border-left: 1px solid rgba(116, 214, 255, 0.15); }"
        )
        panel.setFixedWidth(200)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(12)

        # System status title
        title = QLabel("SYSTEM STATUS")
        title.setStyleSheet("color: #74d6ff; font: 700 11px 'Segoe UI'; letter-spacing: 1px;")
        layout.addWidget(title)

        # Status items (non-functional display)
        status_items = [
            ("Voice Pipeline", "READY"),
            ("Gemini API", "ACTIVE"),
            ("Permissions", "ALLOWED"),
            ("Memory Buffer", "OPTIMAL"),
        ]

        for label, value in status_items:
            item_layout = QVBoxLayout()
            item_layout.setContentsMargins(0, 0, 0, 0)
            item_layout.setSpacing(2)
            
            label_w = QLabel(label)
            label_w.setStyleSheet("color: #9cc5d9; font: 500 10px 'Segoe UI';")
            item_layout.addWidget(label_w)
            
            value_w = QLabel(value)
            value_w.setStyleSheet("color: #74d6ff; font: 600 10px 'Segoe UI'; margin-left: 8px;")
            item_layout.addWidget(value_w)
            
            layout.addLayout(item_layout)

        layout.addSpacing(12)

        # Recent actions title
        recent_title = QLabel("RECENT ACTIVITY")
        recent_title.setStyleSheet("color: #74d6ff; font: 700 11px 'Segoe UI'; letter-spacing: 1px;")
        layout.addWidget(recent_title)

        # Activity log
        self.activity_log = QTextEdit()
        self.activity_log.setReadOnly(True)
        self.activity_log.setPlainText("System initialized.\n")
        self.activity_log.setFixedHeight(120)
        self.activity_log.setStyleSheet(
            "QTextEdit { background: rgba(13, 23, 33, 0.7); color: #7cb5ff; border: 1px solid rgba(116, 214, 255, 0.15); "
            "border-radius: 6px; padding: 6px; font: 500 9px 'Courier New'; }"
        )
        layout.addWidget(self.activity_log)

        layout.addStretch()

        return panel

    def _init_voice_system(self) -> None:
        """Initialize voice and speech recognition systems."""
        if pyttsx3 is not None:
            try:
                self.voice_engine = pyttsx3.init()
                self.voice_engine.setProperty("rate", 170)
                self.voice_engine.setProperty("volume", 1.0)
                
                voices = self.voice_engine.getProperty('voices')
                male_voice = None
                for voice in voices:
                    if hasattr(voice, 'gender') and voice.gender.lower() == 'male':
                        male_voice = voice.id
                        break
                
                if male_voice:
                    self.voice_engine.setProperty('voice', male_voice)
                    print(f"[TTS] Selected male voice: {male_voice}")
                else:
                    print(f"[TTS] No male voice found, using default. Available voices: {len(voices)}")
            except Exception as e:
                self.voice_engine = None
                print(f"[TTS] Error initializing voice engine: {e}")

        if sr is not None:
            try:
                self.microphone = sr.Microphone()
                self.recognizer = sr.Recognizer()
            except Exception:
                self.recognizer = None
                self.microphone = None

    def set_mode(self, mode: str) -> None:
        """Switch between voice and text modes."""
        self.ui_mode = mode
        if mode == "voice":
            self.content_area.setCurrentWidget(self.voice_page)
            self.voice_mode_button.setVisible(False)
            self.text_mode_button.setVisible(True)
        else:
            self.content_area.setCurrentWidget(self.text_page)
            self.voice_mode_button.setVisible(True)
            self.text_mode_button.setVisible(False)
            if hasattr(self, "command_input"):
                self.command_input.setFocus()

    def update_voice_state(self, state: str) -> None:
        """Update the visual representation of voice state."""
        self.voice_state = state
        if hasattr(self, "voice_status"):
            state_map = {
                "idle": "Ready to assist",
                "standby": "Listening for wake word 'Hey Mr. Stark'",
                "listening": "Actively listening...",
                "processing": "Processing your request...",
                "speaking": "Speaking response...",
            }
            self.voice_status.setText(state_map.get(state, "Ready to assist"))
        
        if hasattr(self, "reactor_widget"):
            if state == "standby":
                self.reactor_widget.set_state("idle")
            elif state == "listening":
                self.reactor_widget.set_state("listening")
            elif state == "processing":
                self.reactor_widget.set_state("processing")
            elif state == "speaking":
                self.reactor_widget.set_state("speaking")
            else:
                self.reactor_widget.set_state("idle")

    def append_console(self, text: str) -> None:
        """Append text to the console output."""
        if hasattr(self, "console_output"):
            self.console_output.append(text)
            self.console_output.ensureCursorVisible()
        if hasattr(self, "activity_log"):
            self.activity_log.append(text)
            self.activity_log.ensureCursorVisible()

    def toggle_voice_activation(self) -> None:
        """Toggle voice input on/off."""
        if self.voice_enabled:
            self.interrupt_voice()
            return

        if self.recognizer is None or self.microphone is None:
            self.append_console("Voice input is not available in this environment.")
            return

        self.voice_enabled = True
        self.voice_toggle_button.setText("🎤 Voice: ON")
        self.stop_voice_button.setEnabled(True)
        self.voice_stop_requested = False
        self.voice_stop_event = threading.Event()
        
        initial_state = "standby" if self.wake_word_enabled else "listening"
        self.voice_in_standby = self.wake_word_enabled
        self.update_voice_state(initial_state)
        
        if self.wake_word_enabled:
            self.append_console("[Voice] Say 'Hey Mr. Stark' to activate.")
        else:
            self.append_console("[Voice] Listening... Speak when ready.")

        self.voice_thread = QThread(self)
        self.voice_worker = VoiceCaptureWorker(
            self.recognizer, 
            self.microphone, 
            self.voice_stop_event,
            self,
            start_in_standby=self.wake_word_enabled
        )
        self.voice_worker.moveToThread(self.voice_thread)
        
        self.voice_thread.started.connect(self.voice_worker.run)
        self.voice_worker.utterance_captured.connect(self._handle_voice_utterance)
        self.voice_worker.wake_word_detected.connect(self._on_wake_word_detected)
        self.voice_worker.mode_changed.connect(self._on_mode_changed)
        self.voice_worker.error.connect(self._handle_voice_error)
        self.voice_worker.worker_stopped.connect(self.voice_thread.quit)
        self.voice_worker.listening.connect(self._on_worker_listening)
        
        self.voice_thread.start()

    def _handle_voice_utterance(self, text: str) -> None:
        """Handle a captured voice utterance."""
        if not text.strip():
            return

        print(f"[VOICE] Utterance recognized: '{text}'")
        
        if self.inactivity_timer:
            self.inactivity_timer.stop()
            self.inactivity_timer.start(self.inactivity_timeout_seconds * 1000)
        
        self.append_console(f"You (voice): {text}")
        self.command_input.setText(text.strip())
        self.update_voice_state("processing")
        self.send_console_prompt()

    def _handle_voice_error(self, message: str) -> None:
        """Handle voice errors gracefully."""
        print(f"[VOICE] Error: {message}")
        self.append_console(f"[Voice] {message}")

    def interrupt_voice(self) -> None:
        """Stop voice mode."""
        print("[VOICE] Interrupt requested")
        
        self.voice_stop_requested = True
        if self.voice_stop_event is not None:
            self.voice_stop_event.set()
        
        if self.voice_engine is not None:
            try:
                self.voice_engine.stop()
                print("[TTS] Interrupted speech")
            except Exception:
                pass
        
        if self.voice_thread is not None and self.voice_thread.isRunning():
            print("[VOICE] Waiting for worker to stop...")
            self.voice_thread.quit()
            self.voice_thread.wait(timeout=3000)
        
        self.voice_enabled = False
        self.update_voice_state("idle")
        self.voice_toggle_button.setText("🎤 Voice: OFF")
        self.stop_voice_button.setEnabled(False)
        self.append_console("[Voice] Capture stopped.")
        print("[VOICE] Voice mode stopped")

    def _on_wake_word_detected(self) -> None:
        """Handle wake-word detection."""
        print("[VOICE] Wake word activation signal received")
        self.inactivity_timer.stop()
        self.voice_in_standby = False

    def _on_mode_changed(self, mode: str) -> None:
        """Handle mode changes from the voice worker."""
        print(f"[VOICE] Mode changed: {mode}")
        if mode == "active":
            self.voice_in_standby = False
            self.inactivity_timer.stop()
            self.update_voice_state("listening")
            self.inactivity_timer.start(self.inactivity_timeout_seconds * 1000)
        elif mode == "standby":
            self.voice_in_standby = True
            self.inactivity_timer.stop()
            self.update_voice_state("standby")

    def _on_worker_listening(self) -> None:
        """Update listening state from worker."""
        if not self.voice_in_standby:
            self.update_voice_state("listening")

    def _on_inactivity_timeout(self) -> None:
        """Handle inactivity timeout."""
        if self.voice_worker and self.voice_worker.isRunning():
            print("[VOICE] Inactivity timeout triggered - requesting standby mode")
            self.voice_in_standby = True
            self.update_voice_state("standby")
            self.append_console("[Voice] Returning to standby. Say 'Hey Mr. Stark' to activate.")

    def speak_response(self, text: str) -> None:
        """Speak the response using TTS."""
        if self.voice_engine is None or not text:
            return
        try:
            self.update_voice_state("speaking")
            
            self.microphone_suppressed = True
            print("[TTS] Microphone suppressed - speaking")
            
            self.voice_engine.stop()
            self.voice_engine.say(text)
            self.voice_engine.runAndWait()
            
            print("[TTS] Speech complete")
            
        except Exception as e:
            print(f"[TTS] Error speaking: {e}")
        finally:
            self.microphone_suppressed = False
            print("[TTS] Microphone restored - resuming listening")
            
            if self.inactivity_timer and not self.voice_in_standby:
                self.inactivity_timer.stop()
                self.inactivity_timer.start(self.inactivity_timeout_seconds * 1000)
            
            if self.voice_enabled:
                if not self.voice_in_standby:
                    self.update_voice_state("listening")
                print("[TTS] Returning to listening state")
            else:
                self.update_voice_state("idle")

    def send_console_prompt(self) -> None:
        """Send a message through the Gemini pipeline."""
        prompt = self.command_input.text().strip() if hasattr(self, "command_input") else ""
        if not prompt:
            self.append_console("Please enter a message.")
            if hasattr(self, "command_input"):
                self.command_input.setFocus()
            return

        if self.gemini_request_in_flight:
            self.append_console("MR. STARK is already processing a request.")
            return

        self.append_console(f"You: {prompt}")
        self.command_input.clear()
        self.command_input.setEnabled(False)

        if self.gemini_client is None:
            self.append_console("Gemini configuration missing. Add GEMINI_API_KEY to .env file.")
            self.command_input.setEnabled(True)
            self.command_input.setFocus()
            return

        self.gemini_request_in_flight = True
        try:
            self.conversation_history.append({"role": "user", "parts": [{"text": prompt}]})
            recent_history = self.conversation_history[-self._max_history_messages:]

            request_config = genai.types.GenerateContentConfig(
                system_instruction=self.stark_voice.system_instructions(current_datetime=datetime.now()),
            )

            response = self.gemini_client.models.generate_content(
                model="gemini-3.6-flash",
                contents=recent_history,
                config=request_config,
            )

            answer = response.text
            if not answer:
                answer = "No response received from Gemini."

            self.conversation_history.append({"role": "model", "parts": [{"text": answer}]})
            self.conversation_history = self.conversation_history[-(self._max_history_messages * 2):]

            self.append_console(f"MR. STARK: {answer}")
            self.speak_response(answer)
        except APIError as exc:
            self.append_console(f"Gemini API error: {exc}")
        except Exception as exc:
            self.append_console(f"Unable to contact Gemini API: {exc}")
        finally:
            self.gemini_request_in_flight = False
            self.command_input.setEnabled(True)
            self.command_input.setFocus()

    def handle_action(self, name: str) -> None:
        """Handle action button clicks."""
        if name == "Run Scan":
            message = "System scan initiated...\n\nAll core systems checked and operational."
            QMessageBox.information(self, "MR. STARK", message)
            self.append_console("[Action] System scan completed. All systems nominal.")
        elif name == "Open Console":
            self.set_mode("text")
            self.append_console("[Action] Console opened. Ready for input.")
            if hasattr(self, "command_input"):
                self.command_input.setFocus()
        elif name == "Guard Review":
            message = "Guard review complete. Security posture within policy."
            QMessageBox.information(self, "MR. STARK", message)
            self.append_console("[Action] Guard review complete. Security status: ALLOWED.")
        else:
            self.append_console(f"[Action] {name}")

    def on_activate(self) -> None:
        """Handle core activation button."""
        QMessageBox.information(self, "MR. STARK", "Core systems are online and ready for operation.")
        self.append_console("[Core] All systems activated and operational.")

    def _on_nav_home(self) -> None:
        """Navigate to home."""
        self.set_mode("voice")
        self.append_console("[Navigation] Home selected.")

    def _on_nav_projects(self) -> None:
        """Navigate to projects."""
        self.append_console("[Navigation] Projects page (demo).")

    def _on_nav_tools(self) -> None:
        """Navigate to tools."""
        self.append_console("[Navigation] Tools page (demo).")

    def _on_nav_memory(self) -> None:
        """Navigate to memory."""
        self.append_console("[Navigation] Memory page (demo).")

    def _on_nav_settings(self) -> None:
        """Navigate to settings."""
        self.append_console("[Navigation] Settings page (demo).")


def render_startup_animation() -> None:
    """Render the startup splash screen and main window."""
    app = QApplication.instance() or QApplication([])
    splash = StartupSplash()
    splash.show()
    splash.move(
        (app.primaryScreen().availableGeometry().width() - splash.width()) // 2,
        (app.primaryScreen().availableGeometry().height() - splash.height()) // 2,
    )
    app.processEvents()
    time.sleep(1.3)
    window = StarkMainWindow()
    window.show()
    splash.close()
    return window


if __name__ == "__main__":
    app = QApplication([])
    window = StarkMainWindow()
    window.show()
    app.exec()
