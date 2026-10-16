from __future__ import annotations

import html
import math
import os
import re
import threading
import time
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
import google.genai as genai
from google.genai.errors import APIError
from PySide6.QtCore import QEvent, QObject, QPoint, QRect, QSize, QTimer, Qt, QThread, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QFont, QClipboard
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
from app.personality.engine import ToneMode, StarkVault


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
    MR. STARK Main Window — Futuristic Cinematic AI Command Centre.
    Unified workspace featuring interactive chat cards, dynamic sarcastic personality,
    live tone switching, prominent Arc Reactor, and continuous voice interaction.
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

        # Personality & Vault
        self.vault = StarkVault()
        self.stark_voice = StarkVoice(mode="focused", user_name="Shruthy")
        self.last_assistant_response = ""
        self.conversation_history = []

        # Voice Pipeline States
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
        self.ui_mode = "unified"

        self._init_voice_system()

        # Window setup
        self.setWindowTitle("MR. STARK // CINEMATIC COMMAND CENTRE")
        self.resize(1440, 920)
        self.setMinimumSize(1240, 750)

        # Apply global stylesheet
        self._apply_stylesheet()

        # Build UI
        self._build_ui()

        # Generate and display initial dynamic greeting
        QTimer.singleShot(400, self.generate_startup_greeting)

    def _apply_stylesheet(self) -> None:
        """Apply cinematic futuristic stylesheet."""
        stylesheet = """
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                stop:0 #040911, stop:0.4 #081422, stop:1 #040810);
        }
        QWidget {
            color: #EAF7FF;
            background: transparent;
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
        }
        QTextEdit, QLineEdit {
            background: rgba(7, 18, 30, 0.9);
            color: #EAF7FF;
            border: 1px solid rgba(116, 214, 255, 0.25);
            border-radius: 8px;
            padding: 10px;
            selection-background-color: rgba(116, 214, 255, 0.35);
        }
        QLineEdit:focus {
            border: 1px solid #74d6ff;
            background: rgba(10, 24, 40, 0.95);
        }
        QPushButton {
            color: #EAF7FF;
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 600;
            border: 1px solid rgba(116, 214, 255, 0.28);
            background: rgba(116, 214, 255, 0.08);
        }
        QPushButton:hover {
            background: rgba(116, 214, 255, 0.2);
            border: 1px solid #74d6ff;
        }
        QPushButton:pressed {
            background: rgba(116, 214, 255, 0.3);
        }
        QScrollBar:vertical {
            border: none;
            background: rgba(5, 12, 20, 0.6);
            width: 8px;
            border-radius: 4px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: rgba(116, 214, 255, 0.35);
            min-height: 24px;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical:hover {
            background: #74d6ff;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        """
        self.setStyleSheet(stylesheet)

    def _build_ui(self) -> None:
        """Build the complete 3-panel command centre."""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. LEFT SIDEBAR: Navigation & Active Projects
        sidebar = self._build_sidebar()
        main_layout.addWidget(sidebar, 0)

        # 2. CENTER CONTENT: Unified Chat Workspace
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        header = self._build_header()
        center_layout.addWidget(header, 0)

        unified_workspace = self._build_center_workspace()
        center_layout.addWidget(unified_workspace, 1)

        main_layout.addWidget(center_container, 1)

        # 3. RIGHT PANEL: Holographic Intelligence & Arc Reactor
        right_panel = self._build_right_panel()
        main_layout.addWidget(right_panel, 0)

    def _build_sidebar(self) -> QFrame:
        """Build the left navigation & projects sidebar."""
        sidebar = QFrame()
        sidebar.setStyleSheet(
            "QFrame { background: rgba(5, 13, 23, 0.96); border-right: 1px solid rgba(116, 214, 255, 0.18); }"
        )
        sidebar.setFixedWidth(200)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 18, 14, 18)
        layout.setSpacing(10)

        # Brand header
        brand = QLabel("◈ STARK // AI")
        brand.setStyleSheet("font: 800 15px 'Segoe UI'; color: #74d6ff; letter-spacing: 2px;")
        layout.addWidget(brand)

        subtitle = QLabel("Command Node v2.0")
        subtitle.setStyleSheet("color: rgba(184, 217, 255, 0.5); font: 500 10px 'Segoe UI'; margin-bottom: 8px;")
        layout.addWidget(subtitle)

        # Navigation items
        nav_items = [
            ("⚡ Command Deck", lambda: self.command_input.setFocus() if hasattr(self, "command_input") else None),
            ("📁 Project Vault", self._on_nav_projects),
            ("🛠 Engineering Tools", self._on_nav_tools),
            ("🧠 Memory Index", self._on_nav_memory),
            ("⚙ System Settings", self._on_nav_settings),
        ]

        for label, callback in nav_items:
            btn = QPushButton(label)
            btn.setStyleSheet(
                "QPushButton { background: transparent; color: #b8d9ff; border: none; padding: 9px 10px; text-align: left; font: 600 11px 'Segoe UI'; border-radius: 6px; }"
                "QPushButton:hover { background: rgba(116, 214, 255, 0.12); color: #74d6ff; }"
            )
            btn.clicked.connect(callback)
            layout.addWidget(btn)

        layout.addSpacing(14)

        # Active Projects section
        proj_label = QLabel("ACTIVE PROJECTS")
        proj_label.setStyleSheet("color: #74d6ff; font: 700 10px 'Segoe UI'; letter-spacing: 1.5px;")
        layout.addWidget(proj_label)

        projects = self.vault.get_projects()
        for proj in projects:
            p_btn = QPushButton(f"● {proj['name']}")
            p_btn.setToolTip(f"Status: {proj['status']}\n{proj['notes']}")
            p_btn.setStyleSheet(
                "QPushButton { background: rgba(116, 214, 255, 0.04); color: #9cc5d9; border: 1px solid rgba(116, 214, 255, 0.15); "
                "padding: 6px 8px; text-align: left; font: 500 10px 'Segoe UI'; border-radius: 5px; margin-bottom: 2px; }"
                "QPushButton:hover { background: rgba(116, 214, 255, 0.15); color: #74d6ff; border: 1px solid rgba(116, 214, 255, 0.4); }"
            )
            p_btn.clicked.connect(lambda ch, p=proj: self._on_select_project(p))
            layout.addWidget(p_btn)

        layout.addStretch()

        # User profile badge
        user_card = QFrame()
        user_card.setStyleSheet("background: rgba(116, 214, 255, 0.06); border: 1px solid rgba(116, 214, 255, 0.15); border-radius: 8px; padding: 8px;")
        user_layout = QVBoxLayout(user_card)
        user_layout.setContentsMargins(6, 6, 6, 6)
        user_layout.setSpacing(2)

        user_tag = QLabel("USER IDENTITY")
        user_tag.setStyleSheet("color: #74d6ff; font: 700 9px 'Segoe UI'; letter-spacing: 1px;")
        user_name = QLabel("Shruthy (ECE)")
        user_name.setStyleSheet("color: #ffffff; font: 600 11px 'Segoe UI';")
        user_layout.addWidget(user_tag)
        user_layout.addWidget(user_name)
        layout.addWidget(user_card)

        return sidebar

    def _build_header(self) -> QFrame:
        """Build the top header with status and Tone Switcher."""
        header = QFrame()
        header.setStyleSheet(
            "QFrame { background: rgba(7, 18, 30, 0.85); border-bottom: 1px solid rgba(116, 214, 255, 0.18); }"
        )
        header.setFixedHeight(64)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(22, 0, 22, 0)
        layout.setSpacing(14)

        # Title & Online status
        title = QLabel("MR. STARK")
        title.setStyleSheet("font: 800 20px 'Segoe UI'; color: #74d6ff; letter-spacing: 2px;")
        layout.addWidget(title, 0)

        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #74d6ff; font: 700 18px; margin: 0px 4px;")
        self.status_label = QLabel("ONLINE")
        self.status_label.setStyleSheet("color: #b8d9ff; font: 600 11px 'Segoe UI'; letter-spacing: 1px;")

        status_box = QHBoxLayout()
        status_box.setContentsMargins(0, 0, 0, 0)
        status_box.setSpacing(4)
        status_box.addWidget(self.status_indicator)
        status_box.addWidget(self.status_label)
        status_widget = QWidget()
        status_widget.setLayout(status_box)
        layout.addWidget(status_widget, 0)

        layout.addSpacing(20)

        # TONE SWITCHER: Sarcastic, Serious, Supportive
        tone_box = QFrame()
        tone_box.setStyleSheet(
            "QFrame { background: rgba(5, 13, 23, 0.85); border: 1px solid rgba(116, 214, 255, 0.22); border-radius: 8px; padding: 2px; }"
        )
        tone_layout = QHBoxLayout(tone_box)
        tone_layout.setContentsMargins(4, 3, 4, 3)
        tone_layout.setSpacing(4)

        tone_tag = QLabel("PERSONA:")
        tone_tag.setStyleSheet("color: rgba(184, 217, 255, 0.6); font: 700 9px 'Segoe UI'; margin-right: 4px;")
        tone_layout.addWidget(tone_tag)

        self.btn_tone_sarcastic = QPushButton("⚡ SARCASTIC")
        self.btn_tone_sarcastic.setToolTip("Stark's default mode: Witty, blunt, playfully rude, challenging, brilliant.")
        self.btn_tone_sarcastic.clicked.connect(lambda: self.set_active_tone(ToneMode.SARCASTIC))

        self.btn_tone_serious = QPushButton("📐 SERIOUS")
        self.btn_tone_serious.setToolTip("Pure technical mode: Direct, mathematically rigorous, zero sarcasm.")
        self.btn_tone_serious.clicked.connect(lambda: self.set_active_tone(ToneMode.SERIOUS))

        self.btn_tone_supportive = QPushButton("🛡️ SUPPORTIVE")
        self.btn_tone_supportive.setToolTip("Attentive mentor mode: Empathetic, supportive, listening first.")
        self.btn_tone_supportive.clicked.connect(lambda: self.set_active_tone(ToneMode.SUPPORTIVE))

        for b in [self.btn_tone_sarcastic, self.btn_tone_serious, self.btn_tone_supportive]:
            b.setFixedHeight(28)
            tone_layout.addWidget(b)

        self._refresh_tone_button_styles()
        layout.addWidget(tone_box, 0)

        layout.addStretch()

        # Telemetry chip
        model_chip = QLabel("◈ GEMINI 3.6 / 3.8 FLASH")
        model_chip.setStyleSheet(
            "background: rgba(116, 214, 255, 0.08); color: #74d6ff; border: 1px solid rgba(116, 214, 255, 0.25); "
            "border-radius: 6px; padding: 5px 10px; font: 600 10px 'Courier New'; letter-spacing: 1px;"
        )
        layout.addWidget(model_chip, 0)

        return header

    def _build_center_workspace(self) -> QWidget:
        """Build the unified conversational engineering workspace."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        # Chat stream panel
        chat_frame = QFrame()
        chat_frame.setStyleSheet(
            "QFrame { background: rgba(6, 15, 26, 0.7); border: 1px solid rgba(116, 214, 255, 0.16); border-radius: 12px; }"
        )
        chat_layout = QVBoxLayout(chat_frame)
        chat_layout.setContentsMargins(16, 14, 16, 14)
        chat_layout.setSpacing(10)

        # Chat stream header
        stream_header = QHBoxLayout()
        stream_title = QLabel("◈ CONVERSATION STREAM // ACTIVE SESSION")
        stream_title.setStyleSheet("color: #74d6ff; font: 700 10px 'Segoe UI'; letter-spacing: 1.5px;")
        stream_header.addWidget(stream_title)
        stream_header.addStretch()

        btn_copy = QPushButton("📋 Copy Last Answer")
        btn_copy.setStyleSheet(
            "QPushButton { background: transparent; color: #9cc5d9; border: 1px solid rgba(116, 214, 255, 0.2); "
            "padding: 4px 10px; font: 600 10px 'Segoe UI'; border-radius: 5px; }"
            "QPushButton:hover { background: rgba(116, 214, 255, 0.15); color: #74d6ff; }"
        )
        btn_copy.clicked.connect(self.copy_last_response)
        stream_header.addWidget(btn_copy)
        chat_layout.addLayout(stream_header)

        # Rich Chat Display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet(
            "QTextEdit { background: rgba(4, 11, 20, 0.9); color: #EAF7FF; border: 1px solid rgba(116, 214, 255, 0.18); "
            "border-radius: 8px; padding: 14px; font: 500 11px 'Segoe UI'; }"
        )
        chat_layout.addWidget(self.chat_display, 1)

        # QUICK ACTION CHIPS
        chips_frame = QFrame()
        chips_frame.setStyleSheet("background: transparent;")
        chips_layout = QHBoxLayout(chips_frame)
        chips_layout.setContentsMargins(0, 0, 0, 0)
        chips_layout.setSpacing(8)

        chips_label = QLabel("QUICK ACTIONS:")
        chips_label.setStyleSheet("color: rgba(116, 214, 255, 0.7); font: 700 9px 'Segoe UI'; letter-spacing: 1px;")
        chips_layout.addWidget(chips_label)

        chips = [
            ("⚡ Explain Circuit", "Stark, explain how this circuit works and calculate the component values: "),
            ("🛠 Debug Code", "Stark, critique this code and tell me why it will fail: "),
            ("💡 Exosuit Actuator", "Stark, let's analyze torque and actuator specs for the exosuit elbow joint: "),
            ("🎯 Challenge My Idea", "Stark, tear apart my engineering assumptions on this concept: "),
        ]

        for label, prompt_prefix in chips:
            btn_chip = QPushButton(label)
            btn_chip.setStyleSheet(
                "QPushButton { background: rgba(116, 214, 255, 0.06); color: #b8d9ff; border: 1px solid rgba(116, 214, 255, 0.2); "
                "border-radius: 6px; padding: 4px 10px; font: 600 10px 'Segoe UI'; }"
                "QPushButton:hover { background: rgba(116, 214, 255, 0.18); color: #74d6ff; border: 1px solid #74d6ff; }"
            )
            btn_chip.clicked.connect(lambda ch, p=prompt_prefix: self._insert_chip_prompt(p))
            chips_layout.addWidget(btn_chip)

        chips_layout.addStretch()
        chat_layout.addWidget(chips_frame)

        # COMMAND INPUT BAR
        input_container = QFrame()
        input_container.setStyleSheet(
            "QFrame { background: rgba(5, 14, 24, 0.95); border: 1px solid rgba(116, 214, 255, 0.3); border-radius: 10px; padding: 4px; }"
        )
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(6, 4, 6, 4)
        input_layout.setSpacing(8)

        # Integrated Voice Toggle
        self.voice_toggle_button = QPushButton("🎤 Voice: OFF")
        self.voice_toggle_button.setFixedHeight(38)
        self.voice_toggle_button.setStyleSheet(
            "QPushButton { background: rgba(255,255,255,0.04); color: #b8d9ff; border: 1px solid rgba(116, 214, 255, 0.2); "
            "border-radius: 6px; padding: 8px 14px; font: 600 10px 'Segoe UI'; }"
            "QPushButton:hover { background: rgba(116, 214, 255, 0.12); color: #74d6ff; }"
        )
        self.voice_toggle_button.clicked.connect(self.toggle_voice_activation)
        input_layout.addWidget(self.voice_toggle_button)

        # Text input
        self.command_input = QLineEdit()
        self.command_input.setFixedHeight(38)
        self.command_input.setPlaceholderText("Ask MR. STARK or say 'Hey Mr. Stark'...")
        self.command_input.returnPressed.connect(self.send_console_prompt)
        input_layout.addWidget(self.command_input, 1)

        # Send button
        self.send_button = QPushButton("SEND ➜")
        self.send_button.setFixedHeight(38)
        self.send_button.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1a75ff, stop:1 #52b8ff); "
            "color: #030a12; border: none; border-radius: 6px; padding: 8px 22px; font: 800 11px 'Segoe UI'; letter-spacing: 1px; }"
            "QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2b84ff, stop:1 #6eccff); }"
        )
        self.send_button.clicked.connect(self.send_console_prompt)
        input_layout.addWidget(self.send_button)

        # Stop button
        self.stop_voice_button = QPushButton("⏹ STOP")
        self.stop_voice_button.setFixedHeight(38)
        self.stop_voice_button.setStyleSheet(
            "QPushButton { background: rgba(255, 75, 75, 0.15); color: #ffb4b4; border: 1px solid rgba(255, 75, 75, 0.35); "
            "border-radius: 6px; padding: 8px 14px; font: 700 10px 'Segoe UI'; }"
            "QPushButton:hover { background: rgba(255, 75, 75, 0.28); color: #ffffff; }"
        )
        self.stop_voice_button.clicked.connect(self.interrupt_voice)
        self.stop_voice_button.setEnabled(False)
        input_layout.addWidget(self.stop_voice_button)

        chat_layout.addWidget(input_container)
        layout.addWidget(chat_frame, 1)

        return container

    def _build_right_panel(self) -> QFrame:
        """Build the right-side holographic panel with Arc Reactor & Telemetry."""
        panel = QFrame()
        panel.setStyleSheet(
            "QFrame { background: rgba(5, 13, 23, 0.96); border-left: 1px solid rgba(116, 214, 255, 0.18); }"
        )
        panel.setFixedWidth(330)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 18, 16, 18)
        layout.setSpacing(12)

        # Reactor title
        reactor_header = QLabel("◈ HOLOGRAPHIC CORE // TELEMETRY")
        reactor_header.setStyleSheet("color: #74d6ff; font: 700 10px 'Segoe UI'; letter-spacing: 1.5px;")
        layout.addWidget(reactor_header)

        # PROMINENT ARC REACTOR
        reactor_frame = QFrame()
        reactor_frame.setStyleSheet(
            "QFrame { background: rgba(7, 18, 30, 0.7); border: 1px solid rgba(116, 214, 255, 0.2); border-radius: 12px; }"
        )
        reactor_layout = QVBoxLayout(reactor_frame)
        reactor_layout.setContentsMargins(10, 14, 10, 14)
        reactor_layout.setAlignment(Qt.AlignCenter)

        self.reactor_widget = ArcReactorWidget(compact=True)
        self.reactor_widget.setFixedSize(240, 240)
        self.reactor_widget.set_state(self.voice_state)
        reactor_layout.addWidget(self.reactor_widget, alignment=Qt.AlignCenter)

        # Voice status badge
        self.voice_status = QLabel("Ready to assist")
        self.voice_status.setAlignment(Qt.AlignCenter)
        self.voice_status.setStyleSheet("color: #b8d9ff; font: 600 11px 'Segoe UI'; padding-top: 4px;")
        reactor_layout.addWidget(self.voice_status)

        layout.addWidget(reactor_frame)

        # Real System Telemetry Card
        telem_card = QFrame()
        telem_card.setStyleSheet(
            "QFrame { background: rgba(7, 18, 30, 0.7); border: 1px solid rgba(116, 214, 255, 0.16); border-radius: 10px; padding: 10px; }"
        )
        telem_layout = QVBoxLayout(telem_card)
        telem_layout.setContentsMargins(10, 10, 10, 10)
        telem_layout.setSpacing(6)

        telem_title = QLabel("SYSTEM METRICS")
        telem_title.setStyleSheet("color: #74d6ff; font: 700 9px 'Segoe UI'; letter-spacing: 1px;")
        telem_layout.addWidget(telem_title)

        self.telemetry_labels = {}
        metrics = [
            ("Persona Mode", "SARCASTIC [DEFAULT]"),
            ("Voice Pipeline", "CONTINUOUS WAKE-WORD"),
            ("TTS Voice", "SAPI5 David (Male)"),
            ("Local Vault", "stark_vault.db [ONLINE]"),
        ]

        for k, v in metrics:
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            lbl_k = QLabel(k)
            lbl_k.setStyleSheet("color: rgba(184, 217, 255, 0.6); font: 500 10px 'Segoe UI';")
            lbl_v = QLabel(v)
            lbl_v.setStyleSheet("color: #74d6ff; font: 700 10px 'Segoe UI';")
            row.addWidget(lbl_k)
            row.addStretch()
            row.addWidget(lbl_v)
            telem_layout.addLayout(row)
            self.telemetry_labels[k] = lbl_v

        layout.addWidget(telem_card)

        # Live Activity Log
        log_header = QLabel("LIVE EVENT LOG")
        log_header.setStyleSheet("color: #74d6ff; font: 700 9px 'Segoe UI'; letter-spacing: 1px;")
        layout.addWidget(log_header)

        self.activity_log = QTextEdit()
        self.activity_log.setReadOnly(True)
        self.activity_log.setPlainText("System online.\nStark Personality Engine loaded.\n")
        self.activity_log.setFixedHeight(110)
        self.activity_log.setStyleSheet(
            "QTextEdit { background: rgba(4, 11, 20, 0.85); color: #7cb5ff; border: 1px solid rgba(116, 214, 255, 0.15); "
            "border-radius: 6px; padding: 6px; font: 500 9px 'Consolas', monospace; }"
        )
        layout.addWidget(self.activity_log)

        return panel

    def _refresh_tone_button_styles(self) -> None:
        """Update active visual state for tone buttons."""
        active = self.stark_voice.get_tone()
        active_style = (
            "QPushButton { background: rgba(116, 214, 255, 0.25); color: #74d6ff; border: 1px solid #74d6ff; "
            "border-radius: 6px; font: 700 10px 'Segoe UI'; padding: 4px 10px; }"
        )
        inactive_style = (
            "QPushButton { background: transparent; color: rgba(184, 217, 255, 0.7); border: 1px solid transparent; "
            "border-radius: 6px; font: 600 10px 'Segoe UI'; padding: 4px 10px; }"
            "QPushButton:hover { background: rgba(116, 214, 255, 0.1); color: #b8d9ff; }"
        )

        self.btn_tone_sarcastic.setStyleSheet(active_style if active == ToneMode.SARCASTIC else inactive_style)
        self.btn_tone_serious.setStyleSheet(active_style if active == ToneMode.SERIOUS else inactive_style)
        self.btn_tone_supportive.setStyleSheet(active_style if active == ToneMode.SUPPORTIVE else inactive_style)

    def set_active_tone(self, tone: str) -> None:
        """Switch active personality tone."""
        self.stark_voice.set_tone(tone)
        self._refresh_tone_button_styles()

        tone_names = {
            ToneMode.SARCASTIC: "SIGNATURE SARCASTIC (Default)",
            ToneMode.SERIOUS: "SERIOUS ENGINEERING (Pure Rigor)",
            ToneMode.SUPPORTIVE: "SUPPORTIVE MENTOR (Empathy)",
        }
        name = tone_names.get(tone, tone.upper())
        if "Persona Mode" in self.telemetry_labels:
            self.telemetry_labels["Persona Mode"].setText(tone.upper())

        self.append_system_message(f"Tone shifted to [{name}]. Directives updated.")
        self.append_activity_log(f"Tone switched to {tone}")

    def generate_startup_greeting(self) -> None:
        """Generate and display dynamic context-aware startup greeting."""
        greeting = self.stark_voice.greeting(self.gemini_client)
        self.append_chat_message("model", greeting, tone=self.stark_voice.get_tone())
        self.vault.save_message("model", greeting, tone=self.stark_voice.get_tone())
        self.last_assistant_response = greeting
        self.append_activity_log("Dynamic greeting dispatched")

    def _insert_chip_prompt(self, prefix: str) -> None:
        """Insert quick action chip text into input field."""
        self.command_input.setText(prefix)
        self.command_input.setFocus()
        self.command_input.setCursorPosition(len(prefix))

    def copy_last_response(self) -> None:
        """Copy Mr. Stark's latest response to clipboard."""
        if self.last_assistant_response:
            QApplication.clipboard().setText(self.last_assistant_response)
            self.append_system_message("Copied last response to clipboard.")
            self.append_activity_log("Response copied to clipboard")
        else:
            self.append_system_message("No recent response to copy.")

    def _format_markdown_to_html(self, text: str) -> str:
        """Converts markdown bold, italic, code blocks, and math into rich HTML."""
        escaped = html.escape(text)

        # Fenced code blocks ```lang ... ```
        def _code_repl(m):
            code = m.group(1).strip()
            return (
                f'<div style="background-color: #03080e; border: 1px solid rgba(116, 214, 255, 0.35); '
                f'border-radius: 6px; padding: 10px 12px; margin: 8px 0; font-family: \'Consolas\', monospace; '
                f'color: #a8d5ff; font-size: 11px; white-space: pre-wrap;">{code}</div>'
            )
        escaped = re.sub(r'```(?:[a-zA-Z0-9_-]+)?\n(.*?)```', _code_repl, escaped, flags=re.DOTALL)

        # Inline code `code`
        escaped = re.sub(
            r'`([^`]+)`',
            r'<code style="background-color: rgba(116, 214, 255, 0.16); color: #74d6ff; padding: 1px 5px; '
            r'border-radius: 3px; font-family: \'Consolas\', monospace;">\1</code>',
            escaped
        )

        # Bold **text**
        escaped = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color: #ffffff;">\1</strong>', escaped)

        # Italic *text*
        escaped = re.sub(r'\*(.+?)\*', r'<em>\1</em>', escaped)

        # Linebreaks
        escaped = escaped.replace('\n', '<br>')
        return escaped

    def append_chat_message(self, role: str, text: str, tone: Optional[str] = None) -> None:
        """Appends a styled HTML chat bubble into the conversation stream."""
        now_str = datetime.now().strftime("%I:%M %p")
        formatted = self._format_markdown_to_html(text)
        active_tone = tone or self.stark_voice.get_tone()

        if role == "user":
            card = f"""
            <div style="margin: 8px 0px 8px 50px; padding: 12px 16px; background-color: rgba(16, 38, 62, 0.88); 
                        border: 1px solid rgba(116, 214, 255, 0.3); border-radius: 12px 12px 2px 12px;">
                <div style="color: #74d6ff; font-size: 10px; font-weight: 700; margin-bottom: 4px; letter-spacing: 1px;">
                    SHRUTHY (kiddo) <span style="color: rgba(184, 217, 255, 0.5); font-weight: normal; margin-left: 8px;">{now_str}</span>
                </div>
                <div style="color: #eaf7ff; font-size: 12px; line-height: 1.5;">{formatted}</div>
            </div>
            """
        elif role == "model":
            badge = f"MR. STARK [{active_tone.upper()}]"
            card = f"""
            <div style="margin: 8px 50px 8px 0px; padding: 14px 18px; background-color: rgba(6, 17, 29, 0.92); 
                        border-left: 3px solid #74d6ff; border-top: 1px solid rgba(116, 214, 255, 0.2); 
                        border-right: 1px solid rgba(116, 214, 255, 0.15); border-bottom: 1px solid rgba(116, 214, 255, 0.2); 
                        border-radius: 2px 12px 12px 12px;">
                <div style="color: #74d6ff; font-size: 11px; font-weight: 700; margin-bottom: 6px; letter-spacing: 1.5px;">
                    ◈ {badge} <span style="color: rgba(184, 217, 255, 0.45); font-size: 10px; font-weight: normal; margin-left: 10px;">{now_str}</span>
                </div>
                <div style="color: #d8eeff; font-size: 12px; line-height: 1.55;">{formatted}</div>
            </div>
            """
        else:
            card = f"""
            <div style="margin: 6px 30px; padding: 6px 12px; background-color: rgba(116, 214, 255, 0.08); 
                        border: 1px dashed rgba(116, 214, 255, 0.28); border-radius: 6px; text-align: center;">
                <span style="color: #74d6ff; font-size: 10px; font-weight: 600; letter-spacing: 1px;">{formatted}</span>
            </div>
            """

        self.chat_display.append(card)
        self.chat_display.ensureCursorVisible()

    def append_system_message(self, text: str) -> None:
        """Display a subtle system announcement in the chat."""
        self.append_chat_message("system", text)

    def append_console(self, text: str) -> None:
        """Backwards compatibility helper for existing worker/action logs."""
        self.append_system_message(text)
        self.append_activity_log(text)

    def append_activity_log(self, text: str) -> None:
        """Add entry to right panel activity log."""
        if hasattr(self, "activity_log"):
            self.activity_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {text}")
            self.activity_log.ensureCursorVisible()

    def send_console_prompt(self) -> None:
        """Send a message through the Gemini pipeline with active personality and persistence."""
        prompt = self.command_input.text().strip() if hasattr(self, "command_input") else ""
        if not prompt:
            self.append_system_message("Please enter a message.")
            if hasattr(self, "command_input"):
                self.command_input.setFocus()
            return

        if self.gemini_request_in_flight:
            self.append_system_message("MR. STARK is already calculating a response.")
            return

        # Render user message
        self.append_chat_message("user", prompt)
        self.vault.save_message("user", prompt, tone=self.stark_voice.get_tone())
        self.command_input.clear()
        self.command_input.setEnabled(False)
        self.update_voice_state("processing")
        self.append_activity_log(f"Request: '{prompt[:30]}...'")

        if self.gemini_client is None:
            self.append_chat_message("model", "Gemini configuration missing. Check your GEMINI_API_KEY in the .env file.", tone="serious")
            self.command_input.setEnabled(True)
            self.command_input.setFocus()
            self.update_voice_state("idle")
            return

        self.gemini_request_in_flight = True
        try:
            self.conversation_history.append({"role": "user", "parts": [{"text": prompt}]})
            recent_history = self.conversation_history[-self._max_history_messages:]

            request_config = genai.types.GenerateContentConfig(
                system_instruction=self.stark_voice.system_instructions(current_datetime=datetime.now()),
            )

            # Try primary active model, fallback to 3.8 if needed
            try:
                response = self.gemini_client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=recent_history,
                    config=request_config,
                )
            except Exception:
                response = self.gemini_client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=recent_history,
                    config=request_config,
                )

            answer = response.text if (response and response.text) else "No response received from Gemini."
            self.last_assistant_response = answer

            self.conversation_history.append({"role": "model", "parts": [{"text": answer}]})
            self.conversation_history = self.conversation_history[-(self._max_history_messages * 2):]

            # Render assistant message
            self.append_chat_message("model", answer, tone=self.stark_voice.get_tone())
            self.vault.save_message("model", answer, tone=self.stark_voice.get_tone())
            self.append_activity_log("Response received from Gemini")

            # Speak response
            self.speak_response(answer)

        except APIError as exc:
            self.append_system_message(f"Gemini API error: {exc}")
            self.append_activity_log(f"API Error: {exc}")
        except Exception as exc:
            self.append_system_message(f"Unable to reach Gemini API: {exc}")
            self.append_activity_log(f"Connection Error: {exc}")
        finally:
            self.gemini_request_in_flight = False
            self.command_input.setEnabled(True)
            self.command_input.setFocus()

    def update_voice_state(self, state: str) -> None:
        """Update visual representation across Arc Reactor and status labels."""
        self.voice_state = state
        state_map = {
            "idle": "Ready to assist",
            "standby": "Listening for 'Hey Mr. Stark'",
            "listening": "Actively listening...",
            "processing": "Calculating with Gemini...",
            "speaking": "Speaking response...",
        }
        if hasattr(self, "voice_status"):
            self.voice_status.setText(state_map.get(state, "Ready to assist"))

        if hasattr(self, "reactor_widget"):
            self.reactor_widget.set_state(state)

    def _init_voice_system(self) -> None:
        """Initialize TTS engine and SpeechRecognizer."""
        if pyttsx3 is not None:
            try:
                self.voice_engine = pyttsx3.init()
                self.voice_engine.setProperty("rate", 175)
                self.voice_engine.setProperty("volume", 1.0)

                voices = self.voice_engine.getProperty("voices")
                male_voice = None
                for voice in voices:
                    if hasattr(voice, "gender") and str(voice.gender).lower() == "male":
                        male_voice = voice.id
                        break
                    if "david" in voice.id.lower() or "david" in getattr(voice, "name", "").lower():
                        male_voice = voice.id
                        break

                if male_voice:
                    self.voice_engine.setProperty("voice", male_voice)
                    print(f"[TTS] Selected voice: {male_voice}")
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

    def toggle_voice_activation(self) -> None:
        """Toggle continuous voice input on/off."""
        if self.voice_enabled:
            self.interrupt_voice()
            return

        if self.recognizer is None or self.microphone is None:
            self.append_system_message("Voice input is not available on this device.")
            return

        self.voice_enabled = True
        self.voice_toggle_button.setText("🎤 Voice: ON")
        self.voice_toggle_button.setStyleSheet(
            "QPushButton { background: rgba(116, 214, 255, 0.25); color: #74d6ff; border: 1px solid #74d6ff; "
            "border-radius: 6px; padding: 8px 14px; font: 700 10px 'Segoe UI'; }"
        )
        self.stop_voice_button.setEnabled(True)
        self.voice_stop_requested = False
        self.voice_stop_event = threading.Event()

        initial_state = "standby" if self.wake_word_enabled else "listening"
        self.voice_in_standby = self.wake_word_enabled
        self.update_voice_state(initial_state)

        if self.wake_word_enabled:
            self.append_system_message("Voice active. Say 'Hey Mr. Stark' to summon.")
        else:
            self.append_system_message("Listening continuously... Speak when ready.")

        self.voice_thread = QThread(self)
        self.voice_worker = VoiceCaptureWorker(
            self.recognizer,
            self.microphone,
            self.voice_stop_event,
            self,
            start_in_standby=self.wake_word_enabled,
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
        """Handle captured speech utterance."""
        if not text.strip():
            return

        if self.inactivity_timer:
            self.inactivity_timer.stop()
            self.inactivity_timer.start(self.inactivity_timeout_seconds * 1000)

        self.command_input.setText(text.strip())
        self.send_console_prompt()

    def _handle_voice_error(self, message: str) -> None:
        """Handle non-fatal voice loop messages."""
        self.append_activity_log(f"Voice: {message}")

    def interrupt_voice(self) -> None:
        """Interrupt active TTS speech or voice listening."""
        self.voice_stop_requested = True
        if self.voice_stop_event is not None:
            self.voice_stop_event.set()

        if self.voice_engine is not None:
            try:
                self.voice_engine.stop()
            except Exception:
                pass

        if self.voice_thread is not None and self.voice_thread.isRunning():
            self.voice_thread.quit()
            self.voice_thread.wait(timeout=3000)

        self.voice_enabled = False
        self.update_voice_state("idle")
        self.voice_toggle_button.setText("🎤 Voice: OFF")
        self.voice_toggle_button.setStyleSheet(
            "QPushButton { background: rgba(255,255,255,0.04); color: #b8d9ff; border: 1px solid rgba(116, 214, 255, 0.2); "
            "border-radius: 6px; padding: 8px 14px; font: 600 10px 'Segoe UI'; }"
        )
        self.stop_voice_button.setEnabled(False)
        self.append_system_message("Voice capture stopped.")

    def _on_wake_word_detected(self) -> None:
        """Wake word triggered."""
        self.inactivity_timer.stop()
        self.voice_in_standby = False
        self.append_system_message("Wake-word detected! Mr. Stark is listening...")

    def _on_mode_changed(self, mode: str) -> None:
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
        if not self.voice_in_standby:
            self.update_voice_state("listening")

    def _on_inactivity_timeout(self) -> None:
        if self.voice_worker and getattr(self.voice_worker, "is_running", False):
            self.voice_in_standby = True
            self.update_voice_state("standby")
            self.append_system_message("Returning to standby. Say 'Hey Mr. Stark' to wake.")

    def speak_response(self, text: str) -> None:
        """Speak the response using TTS with echo suppression."""
        if self.voice_engine is None or not text:
            self.update_voice_state("idle" if not self.voice_enabled else ("standby" if self.voice_in_standby else "listening"))
            return

        try:
            self.update_voice_state("speaking")
            self.microphone_suppressed = True
            self.stop_voice_button.setEnabled(True)

            # Strip code blocks and markdown symbols before TTS speaking for natural audio
            clean_speech = re.sub(r'```.*?```', ' Code block omitted for voice playback. ', text, flags=re.DOTALL)
            clean_speech = re.sub(r'[*_#`]', '', clean_speech)

            self.voice_engine.stop()
            self.voice_engine.say(clean_speech)
            self.voice_engine.runAndWait()
        except Exception as e:
            print(f"[TTS] Speech error: {e}")
        finally:
            self.microphone_suppressed = False
            if self.voice_enabled:
                state = "standby" if self.voice_in_standby else "listening"
                self.update_voice_state(state)
            else:
                self.update_voice_state("idle")
                self.stop_voice_button.setEnabled(False)

    def _on_select_project(self, project: dict) -> None:
        """Select a project to set active working context."""
        name = project.get("name", "Unknown")
        notes = project.get("notes", "")
        self.command_input.setText(f"Stark, let's work on '{name}'. Context: {notes}")
        self.command_input.setFocus()
        self.append_system_message(f"Selected project: [{name}]. Context ready.")

    def set_mode(self, mode: str) -> None:
        """Retained for backward compatibility with external scripts."""
        self.ui_mode = mode

    def handle_action(self, name: str) -> None:
        """Retained for backward compatibility."""
        self.append_system_message(f"System Diagnostic: '{name}' check nominal.")

    def on_activate(self) -> None:
        self.append_system_message("Core arc reactor running at optimal resonance.")

    def _on_nav_home(self) -> None:
        self.command_input.setFocus()

    def _on_nav_projects(self) -> None:
        self.append_system_message("Project Vault loaded: Check sidebar for active modules.")

    def _on_nav_tools(self) -> None:
        self.append_system_message("Engineering Tools active: Use quick action chips above input.")

    def _on_nav_memory(self) -> None:
        count = len(self.vault.get_recent_messages(limit=100))
        self.append_system_message(f"Memory Vault: {count} messages indexed in stark_vault.db.")

    def _on_nav_settings(self) -> None:
        self.append_system_message(f"Active Tone: [{self.stark_voice.get_tone().upper()}]. Voice: [{'ON' if self.voice_enabled else 'OFF'}].")


def render_startup_animation() -> StarkMainWindow:
    """Render startup splash screen and main command centre."""
    app = QApplication.instance() or QApplication([])
    splash = StartupSplash()
    splash.show()
    splash.move(
        (app.primaryScreen().availableGeometry().width() - splash.width()) // 2,
        (app.primaryScreen().availableGeometry().height() - splash.height()) // 2,
    )
    app.processEvents()
    time.sleep(1.2)
    window = StarkMainWindow()
    window.show()
    splash.close()
    return window


if __name__ == "__main__":
    app = QApplication([])
    window = StarkMainWindow()
    window.show()
    app.exec()

