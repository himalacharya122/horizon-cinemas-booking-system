import time
from typing import Dict, List, Optional

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal  # type: ignore
from PyQt6.QtGui import QAction  # type: ignore
from PyQt6.QtWidgets import (  # type: ignore
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from desktop.api_client import api
from desktop.ui.theme import (
    ACCENT,
    ACCENT_HOVER,
    BG_CARD,
    BG_DARK,
    BG_DARKEST,
    BORDER,
    BORDER_LIGHT,
    RADIUS,
    SPACING_MD,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WHITE,
    body_font,
)
from desktop.ui.widgets import heading_label, separator


class SuggestionChip(QPushButton):
    """A small clickable chip for quick queries."""

    def __init__(self, text: str, callback: callable):
        super().__init__(text)
        self.setFont(body_font(9))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(lambda: callback(text))
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG_CARD};
                color: {TEXT_SECONDARY};
                border: 1px solid {BORDER};
                border-radius: 12px;
                padding: 4px 12px;
                margin-right: 6px;
            }}
            QPushButton:hover {{
                border-color: {ACCENT};
                color: {ACCENT};
                background-color: #1A2A2B;
            }}
        """)


class SessionButton(QPushButton):
    """A button in the sidebar representing a chat session."""

    rename_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)

    def __init__(self, session_id: int, title: str, callback: callable):
        self.full_title = title
        display_title = title if len(title) < 28 else title[:25] + "..."
        super().__init__(f"  {display_title}")
        self.session_id = session_id
        self.setCheckable(True)
        self.setFixedHeight(40)
        self.setFont(body_font(9))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(lambda: callback(self.session_id))
        self._update_style(False)

    def _update_style(self, checked: bool):
        if checked:
            self.setStyleSheet(f"""
                QPushButton {{
                    text-align: left;
                    background-color: {ACCENT};
                    color: {WHITE};
                    border: none;
                    border-radius: 6px;
                    font-weight: 600;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    text-align: left;
                    background-color: transparent;
                    color: {TEXT_SECONDARY};
                    border: none;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background-color: {BG_CARD};
                    color: {TEXT_PRIMARY};
                }}
            """)

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self._update_style(checked)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(
            f"background-color: {BG_CARD}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER};"
        )

        rename_act = QAction("Rename", self)
        rename_act.triggered.connect(lambda: self.rename_requested.emit(self.session_id))
        menu.addAction(rename_act)

        delete_act = QAction("Delete", self)
        delete_act.triggered.connect(lambda: self.delete_requested.emit(self.session_id))
        menu.addAction(delete_act)

        menu.exec(event.globalPos())


class ChatBubble(QFrame):
    """A message bubble for the chat interface. Supports RichText (HTML)."""

    def __init__(self, text: str, is_ai: bool = True):
        super().__init__()
        self.setFrameShape(QFrame.Shape.NoFrame)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(4)

        source_name = "HORIZON" if is_ai else "YOU"
        source = QLabel(source_name)
        source.setFont(body_font(8, bold=True))
        source.setStyleSheet(
            f"color: {ACCENT if is_ai else TEXT_MUTED}; letter-spacing: 1.8px; background: transparent;"
        )
        layout.addWidget(source)

        self.content = QLabel(text)
        self.content.setWordWrap(True)
        self.content.setFont(body_font(10))
        self.content.setTextFormat(Qt.TextFormat.RichText)
        self.content.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent; line-height: 1.5;")
        self.content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.content)

        if is_ai:
            self.setStyleSheet(f"""
                ChatBubble {{
                    background-color: #16171A;
                    border: 1px solid {BORDER};
                    border-left: 3px solid {ACCENT};
                    border-radius: {RADIUS};
                    margin: 2px 0px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                ChatBubble {{
                    background-color: #1E2025;
                    border: 1px solid {BORDER_LIGHT};
                    border-radius: {RADIUS};
                    margin: 2px 32px 2px 0px;
                }}
            """)

    def set_text(self, text: str):
        self.content.setText(text)


class AIWorker(QThread):
    """Worker thread to perform AI queries asynchronously."""

    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, query: str, history: List[Dict[str, str]], session_id: Optional[int]):
        super().__init__()
        self.query = query
        self.history = history
        self.session_id = session_id

    def run(self):
        try:
            result = api.post_ai_query(self.query, self.history, self.session_id)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class AIInsightsView(QWidget):
    """The main AI Analytics view with Session Sidebar and Chat History."""

    def __init__(self):
        super().__init__()
        self.current_session_id: Optional[int] = None
        self.history: List[Dict[str, str]] = []
        self.session_buttons: List[SessionButton] = []

        self.thinking_bubble: Optional[ChatBubble] = None
        self.thinking_timer = QTimer()
        self.thinking_timer.timeout.connect(self._update_thinking_dots)
        self.dot_count = 0
        self._last_suggestions_fetch: float = 0.0

        self._build_ui()
        # Load sessions on startup
        QTimer.singleShot(100, self._load_sessions)

    def _build_ui(self):
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Sidebar Area
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"background-color: {BG_DARK}; border-right: 1px solid {BORDER};")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        sidebar_layout.setSpacing(12)

        # New Chat Button
        new_chat_btn = QPushButton("+  New Chat")
        new_chat_btn.setFixedHeight(44)
        new_chat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_chat_btn.setFont(body_font(10, bold=True))
        new_chat_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG_DARKEST};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {BG_CARD};
                border-color: {ACCENT};
            }}
        """)
        new_chat_btn.clicked.connect(self._start_new_chat)
        sidebar_layout.addWidget(new_chat_btn)

        # Search Bar
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search chats...")
        self.search_field.setFont(body_font(9))
        self.search_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BG_DARKEST};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 4px 8px;
            }}
        """)
        self.search_field.textChanged.connect(self._on_search_changed)
        sidebar_layout.addWidget(self.search_field)

        # Session List
        sidebar_layout.addWidget(QLabel("PAST CONVERSATIONS"), 0, Qt.AlignmentFlag.AlignLeft)

        self.session_scroll = QScrollArea()
        self.session_scroll.setWidgetResizable(True)
        self.session_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.session_list_widget = QWidget()
        self.session_list_layout = QVBoxLayout(self.session_list_widget)
        self.session_list_layout.setContentsMargins(0, 0, 0, 0)
        self.session_list_layout.setSpacing(4)
        self.session_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.session_scroll.setWidget(self.session_list_widget)
        sidebar_layout.addWidget(self.session_scroll, 1)

        root_layout.addWidget(sidebar)

        # ─── Chat Logic Area ───
        chat_area = QWidget()
        chat_area.setStyleSheet(f"background-color: {BG_DARKEST};")
        chat_vbox = QVBoxLayout(chat_area)
        chat_vbox.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        chat_vbox.setSpacing(SPACING_MD)

        # Header
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        self.title_label = heading_label("Horizon Assistant")
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(separator())
        chat_vbox.addWidget(header)

        # Chat Scroll
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(12)

        self.scroll.setWidget(self.chat_container)
        chat_vbox.addWidget(self.scroll, 1)

        # Suggestions
        self.suggestions_row = QHBoxLayout()
        self.suggestions_row.setSpacing(0)
        self.suggestions_row.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Initial chips (will be dynamic)
        self._set_suggestion_chips(
            ["Weekly Revenue", "Staff Performance", "Occupancy Rate", "Top Films"]
        )

        chat_vbox.addLayout(self.suggestions_row)

        # Input
        input_frame = QFrame()
        input_frame.setFixedHeight(60)
        input_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_LIGHT};
                border-radius: 8px;
            }}
            QFrame:focus-within {{
                border-color: {ACCENT};
            }}
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(14, 10, 10, 10)
        input_layout.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask about bookings, revenue, staff, films...")
        self.input_field.setFont(body_font(11))
        self.input_field.setStyleSheet(
            "QLineEdit { border: none; background: transparent; color: white; }"
        )
        self.input_field.returnPressed.connect(self._send_query)
        input_layout.addWidget(self.input_field, 1)

        self.send_btn = QPushButton("Send →")
        self.send_btn.setFixedSize(90, 38)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setFont(body_font(10, bold=True))
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                color: {WHITE};
                border-radius: 6px;
                border: none;
            }}
            QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}
            QPushButton:disabled {{ background-color: #4A1010; color: #7A4040; }}
        """)
        self.send_btn.clicked.connect(self._send_query)
        input_layout.addWidget(self.send_btn)

        chat_vbox.addWidget(input_frame)
        root_layout.addWidget(chat_area, 1)

    # Data Logic

    def _load_sessions(self):
        """Fetch all sessions for the user and populate the sidebar."""
        try:
            sessions = api.get_ai_sessions()

            # Clear old buttons
            for btn in self.session_buttons:
                btn.deleteLater()
            self.session_buttons.clear()

            for s in sessions:
                btn = SessionButton(s["session_id"], s["title"], self._on_session_selected)
                btn.rename_requested.connect(self._handle_rename)
                btn.delete_requested.connect(self._handle_delete)
                self.session_list_layout.addWidget(btn)
                self.session_buttons.append(btn)

            if sessions and self.current_session_id is None:
                self._on_session_selected(sessions[0]["session_id"])
            elif self.current_session_id:
                for btn in self.session_buttons:
                    btn.setChecked(btn.session_id == self.current_session_id)
            elif not sessions:
                self._on_session_selected(0)
        except Exception:
            pass

    def _start_new_chat(self):
        """Create a new session via API."""
        try:
            session = api.create_ai_session()
            self.current_session_id = session["session_id"]
            self._on_session_selected(self.current_session_id)
            self._load_sessions()  # Refresh list
        except Exception:
            pass

    def _on_session_selected(self, session_id: int):
        """Load history for a specific session."""
        # Clear chat container
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.history = []

        # Invalid/deleted session — show empty state
        if session_id <= 0:
            self.current_session_id = None
            self.title_label.setText("Horizon Assistant")
            self._show_empty_state()
            return

        self.current_session_id = session_id
        for btn in self.session_buttons:
            btn.setChecked(btn.session_id == session_id)
            if btn.session_id == session_id:
                self.title_label.setText(btn.full_title)

        # Load messages
        try:
            messages = api.get_ai_session_messages(session_id)
            if not messages:
                self._show_empty_state()
            else:
                for msg in messages:
                    self._add_message(msg["content"], msg["role"] == "assistant")
                    self.history.append({"role": msg["role"], "content": msg["content"]})

        except Exception:
            self._add_message("Failed to load conversation history.", True)

    def _show_empty_state(self):
        """Show a welcome prompt in an empty chat."""
        welcome = QLabel(
            "<b style='font-size:13pt;'>How can I help?</b><br>"
            "<span style='color:#9CA3AF;font-size:10pt;'>"
            "Ask me anything about your cinema — bookings, revenue, staff, films."
            "</span>"
        )
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.setTextFormat(Qt.TextFormat.RichText)
        welcome.setWordWrap(True)
        welcome.setStyleSheet("color: white; background: transparent; padding: 40px;")
        self.chat_layout.addWidget(welcome)

    def _on_suggestion_clicked(self, text: str):
        self.input_field.setText(text)
        self._send_query()

    def _on_search_changed(self, text: str):
        search_text = text.lower()
        for btn in self.session_buttons:
            btn.setVisible(search_text in btn.full_title.lower())

    def _handle_rename(self, session_id: int):
        # find current title
        current_title = ""
        for btn in self.session_buttons:
            if btn.session_id == session_id:
                current_title = btn.full_title
                break

        new_title, ok = QInputDialog.getText(
            self, "Rename Chat", "Enter new title:", text=current_title
        )
        if ok and new_title.strip():
            try:
                api.rename_ai_session(session_id, new_title.strip())
                self._load_sessions()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to rename: {str(e)}")

    def _handle_delete(self, session_id: int):
        confirm = QMessageBox.question(
            self,
            "Delete Chat",
            "Are you sure you want to delete this conversation?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                api.delete_ai_session(session_id)
                if self.current_session_id == session_id:
                    self.current_session_id = None
                    self.history = []
                    # Clear chat UI
                    self._on_session_selected(-1)  # Trigger empty state
                self._load_sessions()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {str(e)}")

    def _send_query(self):
        query = self.input_field.text().strip()
        if not query:
            return

        if self.current_session_id is None:
            # Need a session first
            self._start_new_chat()
            if self.current_session_id is None:
                return

        self.input_field.clear()
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)

        # UI Update
        self._add_message(query, False)
        self._show_thinking()

        # API Call
        self.worker = AIWorker(query, self.history, self.current_session_id)
        self.worker.finished.connect(self._on_query_finished)
        self.worker.error.connect(self._on_query_error)
        self.worker.start()

    def _on_query_finished(self, result: dict):
        self._hide_thinking()
        answer = result.get("answer", "No response received.")

        self._add_message(answer, True)
        self.history.append({"role": "user", "content": self.worker.query})
        self.history.append({"role": "assistant", "content": answer})

        # If it was the first message, the title might have changed in DB
        if len(self.history) <= 2:
            self._load_sessions()

        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input_field.setFocus()

        # Refresh dynamic suggestions after each turn
        self._fetch_suggestions()

    def _on_query_error(self, error: str):
        self._hide_thinking()
        self._add_message(f"<b>Error:</b> {error}", True)
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)

    def _fetch_suggestions(self):
        """Fetch dynamic suggestions — at most once every 20 seconds."""
        if time.time() - self._last_suggestions_fetch < 20:
            return
        self._last_suggestions_fetch = time.time()
        QTimer.singleShot(300, self._do_fetch_suggestions)

    def _do_fetch_suggestions(self):
        try:
            suggestions = api.get_ai_suggestions(self.current_session_id)
            if suggestions:
                self._set_suggestion_chips(suggestions)
        except Exception:
            pass

    def _set_suggestion_chips(self, suggestions: List[str]):
        # Clear row
        while self.suggestions_row.count():
            item = self.suggestions_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for s in suggestions[:4]:
            chip = SuggestionChip(s, self._on_suggestion_clicked)
            self.suggestions_row.addWidget(chip)

    # ─── Helpers ───

    def _add_message(self, text: str, is_ai: bool):
        if not text:
            return
        bubble = ChatBubble(text, is_ai)
        self.chat_layout.addWidget(bubble)
        QTimer.singleShot(
            50,
            lambda: self.scroll.verticalScrollBar().setValue(
                self.scroll.verticalScrollBar().maximum()
            ),
        )

    def _show_thinking(self):
        self.thinking_bubble = ChatBubble("Thinking...", True)
        self.chat_layout.addWidget(self.thinking_bubble)
        QTimer.singleShot(
            50,
            lambda: self.scroll.verticalScrollBar().setValue(
                self.scroll.verticalScrollBar().maximum()
            ),
        )
        self.dot_count = 0
        self.thinking_timer.start(500)

    def _update_thinking_dots(self):
        if self.thinking_bubble:
            self.dot_count = (self.dot_count + 1) % 3
            dots = "." * (self.dot_count + 1)
            self.thinking_bubble.set_text(f"Thinking{dots}")

    def _hide_thinking(self):
        self.thinking_timer.stop()
        if self.thinking_bubble:
            self.chat_layout.removeWidget(self.thinking_bubble)
            self.thinking_bubble.deleteLater()
            self.thinking_bubble = None
