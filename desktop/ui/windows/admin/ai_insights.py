# ============================================
# Author: Himal Acharya
# Student ID: 22085619
# Last Edited: 2026-04-25
# ============================================

"""
desktop/ui/windows/admin/ai_insights.py
implements the AI Insights analytics dashboard, featuring a chat interface and conversational data analysis tools.
"""

import re
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
    BG_CARD,
    BG_DARK,
    BG_DARKEST,
    BORDER,
    HERO_BG,
    SPACING_MD,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WHITE,
    body_font,
)
from desktop.ui.widgets import heading_label, separator

# Markdown -> HTML processing utilities


def _inline_md(text: str) -> str:
    """Convert inline markdown (bold, italic, code) to HTML spans."""
    # Bold: **text** or __text__
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)
    # Italic: *text* — but not the ** already turned into <b>
    text = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"(?<!_)_([^_\n]+?)_(?!_)", r"<i>\1</i>", text)
    # Inline code: `code`
    text = re.sub(
        r"`([^`]+?)`",
        r'<code style="background:#F1F1EF; padding:1px 4px; border-radius:3px; font-family:monospace;">\1</code>',
        text,
    )
    return text


def _md_to_html(text: str) -> str:
    """
    Convert a basic subset of Markdown to Qt-compatible HTML for QLabel RichText.
    Handles: headings, bullet lists, numbered lists, bold, italic, inline code,
    paragraph breaks. Passes through content that is already HTML unchanged.
    """
    # If the text is already HTML (e.g. error messages like "<b>Error:</b> …"),
    # pass it straight through.
    if text.lstrip().startswith("<"):
        return text

    lines = text.split("\n")
    out: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Blank line -> paragraph spacer
        if not line.strip():
            # Avoid stacking more than one break
            if out and out[-1] != "<br>":
                out.append("<br>")
            i += 1
            continue

        # ATX Heading:  # / ## / ###
        m = re.match(r"^(#{1,3})\s+(.+)$", line)
        if m:
            sizes = {1: "13pt", 2: "12pt", 3: "11pt"}
            size = sizes[len(m.group(1))]
            inner = _inline_md(m.group(2))
            out.append(f'<b style="font-size:{size};">{inner}</b><br>')
            i += 1
            continue

        # Unordered list:  - / * / +
        if re.match(r"^[-*+]\s+", line):
            items: list[str] = []
            while i < len(lines) and re.match(r"^[-*+]\s+", lines[i]):
                content = re.sub(r"^[-*+]\s+", "", lines[i])
                items.append(f"<li>{_inline_md(content)}</li>")
                i += 1
            out.append(
                '<ul style="margin:2px 0 4px 0; padding-left:18px;">' + "".join(items) + "</ul>"
            )
            continue

        # Ordered list:  1. / 2. / …
        if re.match(r"^\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i]):
                content = re.sub(r"^\d+\.\s+", "", lines[i])
                items.append(f"<li>{_inline_md(content)}</li>")
                i += 1
            out.append(
                '<ol style="margin:2px 0 4px 0; padding-left:18px;">' + "".join(items) + "</ol>"
            )
            continue

        # Normal paragraph line
        out.append(_inline_md(line) + "<br>")
        i += 1

    html = "".join(out)
    # Collapse 3+ consecutive <br> tags down to two (one blank line)
    html = re.sub(r"(<br>){3,}", "<br><br>", html)
    # Strip any trailing line breaks
    html = re.sub(r"(<br>\s*)+$", "", html)
    return html


class SuggestionChip(QPushButton):
    """a compact, clickable button used for quick analytical queries."""

    def __init__(self, text: str, callback: callable):
        super().__init__(text)
        self.setFont(body_font(9))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(lambda: callback(text))
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {BG_DARKEST};
                color: {TEXT_SECONDARY};
                border: 1.5px solid {BORDER};
                border-radius: 14px;
                padding: 5px 14px;
                margin-right: 8px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                border-color: {ACCENT};
                color: {WHITE};
                background-color: {ACCENT};
            }}
        """)


class SessionButton(QPushButton):
    """a specialized button in the sidebar representing an individual chat session."""

    rename_requested = pyqtSignal(int)
    delete_requested = pyqtSignal(int)

    def __init__(self, session_id: int, title: str, callback: callable):
        self.full_title = title
        display_title = title if len(title) < 28 else title[:25] + "..."
        super().__init__(f"  {display_title}")
        self.session_id = session_id
        self.setCheckable(True)
        self.setFixedHeight(32)  # ← reduced from 40
        self.setFont(body_font(9))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(lambda: callback(self.session_id))
        self._update_style(False)

    def _update_style(self, checked: bool):
        if checked:
            self.setStyleSheet(f"""
                QPushButton {{
                    text-align: left;
                    background-color: {BG_CARD};
                    color: {TEXT_PRIMARY};
                    border: none;
                    border-radius: 6px;
                    font-weight: 700;
                    padding-left: 10px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    text-align: left;
                    background-color: transparent;
                    color: {TEXT_PRIMARY};
                    border: none;
                    border-radius: 6px;
                    font-weight: 400;
                    padding-left: 10px;
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
        """triggers a context menu for session renaming and deletion."""
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
    """a message container for the chat interface that supports RichText via HTML."""

    def __init__(self, text: str, is_ai: bool = True):
        super().__init__()
        self.setFrameShape(QFrame.Shape.NoFrame)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(4)

        source_name = "HORIZON" if is_ai else "YOU"
        source = QLabel(source_name)
        source.setFont(body_font(8, bold=True))
        source.setStyleSheet(f"color: {ACCENT if is_ai else '#9CA3AF'}; background: transparent;")
        layout.addWidget(source)

        # convert AI-generated Markdown to HTML; keep user input as plain text
        display_text = _md_to_html(text) if is_ai else text
        text_color = TEXT_PRIMARY if is_ai else WHITE

        self.content = QLabel(display_text)
        self.content.setWordWrap(True)
        self.content.setFont(body_font(10))
        self.content.setTextFormat(Qt.TextFormat.RichText)
        self.content.setStyleSheet(
            f"color: {text_color}; background: transparent; line-height: 1.6;"
        )
        self.content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.content)

        if is_ai:
            self.setStyleSheet(f"""
                ChatBubble {{
                    background-color: {BG_CARD};
                    border: 1.5px solid {BORDER};
                    border-radius: 10px;
                    margin: 4px 0px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                ChatBubble {{
                    background-color: #1E2025;
                    border: 1.5px solid {BORDER};
                    border-radius: 10px;
                    margin: 4px 32px 4px 0px;
                }}
            """)

    def set_text(self, text: str, is_ai: bool = True):
        """updates the bubble content, applying Markdown conversion for AI responses."""
        self.content.setText(_md_to_html(text) if is_ai else text)


class AIWorker(QThread):
    """a worker thread that manages asynchronous communication with the AI analytics API."""

    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, query: str, history: List[Dict[str, str]], session_id: Optional[int]):
        super().__init__()
        self.query = query
        self.history = history
        self.session_id = session_id

    def run(self):
        """executes the AI query on a background thread to prevent UI locking."""
        try:
            result = api.post_ai_query(self.query, self.history, self.session_id)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class AIInsightsView(QWidget):
    """the primary analytics dashboard view combining session management and chat interaction."""

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
        # delay session loading slightly to ensure UI stability
        QTimer.singleShot(100, self._load_sessions)

    def _build_ui(self):
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # left sidebar: conversation history and session search
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        # only the right border separates the sidebar from the chat interface
        sidebar.setStyleSheet(
            f"background-color: {BG_DARK}; border: none; border-right: 1px solid {BORDER};"
        )
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 14, 12, 12)
        sidebar_layout.setSpacing(10)

        # session search bar for filtering past conversations
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search chats...")
        self.search_field.setFont(body_font(9))
        self.search_field.setFixedHeight(28)
        self.search_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {BG_DARKEST};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 0px 10px;
                min-height: 28px;
                max-height: 28px;
            }}
            QLineEdit:focus {{
                border-color: {ACCENT};
            }}
        """)
        self.search_field.textChanged.connect(self._on_search_changed)
        sidebar_layout.addWidget(self.search_field)

        past_lbl = QLabel("Past conversations")
        past_lbl.setFont(body_font(9))
        past_lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; background: transparent; padding: 2px 2px 0px 2px;"
        )
        sidebar_layout.addWidget(past_lbl)

        # scrollable list of historical chat sessions
        self.session_scroll = QScrollArea()
        self.session_scroll.setWidgetResizable(True)
        self.session_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.session_scroll.setFrameShadow(QFrame.Shadow.Plain)
        self.session_scroll.setLineWidth(0)
        self.session_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.session_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.session_scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            "QScrollArea > QWidget { border: none; background: transparent; }"
        )
        # remove borders from the inner viewport widget
        self.session_scroll.viewport().setStyleSheet("background: transparent; border: none;")

        self.session_list_widget = QWidget()
        self.session_list_widget.setStyleSheet("background: transparent; border: none;")
        self.session_list_layout = QVBoxLayout(self.session_list_widget)
        self.session_list_layout.setContentsMargins(0, 0, 0, 0)
        self.session_list_layout.setSpacing(2)
        self.session_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.session_scroll.setWidget(self.session_list_widget)
        sidebar_layout.addWidget(self.session_scroll, 1)

        root_layout.addWidget(sidebar)

        # central chat interface area
        chat_area = QWidget()
        chat_area.setStyleSheet(f"background-color: {BG_DARKEST};")
        chat_vbox = QVBoxLayout(chat_area)
        chat_vbox.setContentsMargins(SPACING_MD, SPACING_MD, SPACING_MD, SPACING_MD)
        chat_vbox.setSpacing(SPACING_MD)

        # chat header featuring title and descriptive subtitle
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 4)
        header_layout.setSpacing(4)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        self.title_label = heading_label("Horizon Assistant")
        title_col.addWidget(self.title_label)
        subtitle = QLabel("AI-powered analytics and operational decision support")
        subtitle.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10pt; background: transparent;")
        title_col.addWidget(subtitle)

        title_row.addLayout(title_col)
        title_row.addStretch()

        # circular button to initialize a fresh chat session
        new_chat_btn = QPushButton("+")
        new_chat_btn.setFixedSize(32, 32)
        new_chat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_chat_btn.setToolTip("New Chat")
        new_chat_btn.setFont(body_font(16, bold=True))
        new_chat_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {HERO_BG};
                color: {WHITE};
                border: none;
                border-radius: 16px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: #2E2C28;
            }}
        """)
        new_chat_btn.clicked.connect(self._start_new_chat)
        title_row.addWidget(new_chat_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        header_layout.addLayout(title_row)
        header_layout.addWidget(separator())
        chat_vbox.addWidget(header)

        # scrollable container for the conversational message history
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setSpacing(12)

        self.scroll.setWidget(self.chat_container)
        chat_vbox.addWidget(self.scroll, 1)

        # horizontal row of analytical suggestion chips
        self.suggestions_row = QHBoxLayout()
        self.suggestions_row.setSpacing(0)
        self.suggestions_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._set_suggestion_chips(
            ["Weekly Revenue", "Staff Performance", "Occupancy Rate", "Top Films"]
        )
        chat_vbox.addLayout(self.suggestions_row)

        # message input bar for user queries
        # fixed-height container with integrated send button
        input_frame = QFrame()
        input_frame.setFixedHeight(52)
        input_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1.5px solid {BORDER};
                border-radius: 12px;
            }}
            QFrame:focus-within {{
                border-color: {ACCENT};
                background-color: {WHITE};
            }}
        """)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(16, 0, 10, 0)  # tighter right margin
        input_layout.setSpacing(10)
        input_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask about bookings, revenue, staff, films...")
        self.input_field.setFont(body_font(11))
        self.input_field.setStyleSheet(
            "QLineEdit { border: none; background: transparent; color: #0A0908; }"
        )
        self.input_field.returnPressed.connect(self._send_query)
        input_layout.addWidget(self.input_field, 1)

        # send button styled to fit within the input frame
        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedSize(72, 32)  # 32px tall fits easily inside 52px frame
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setFont(body_font(9, bold=True))
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #3A0A0A;
                color: {WHITE};
                border-radius: 10px;
                border: none;
                padding: 0px;
            }}
            QPushButton:hover {{ background-color: #5C1212; }}
            QPushButton:disabled {{ background-color: #1A0505; color: #5A3030; }}
        """)
        self.send_btn.clicked.connect(self._send_query)
        input_layout.addWidget(self.send_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        chat_vbox.addWidget(input_frame)
        root_layout.addWidget(chat_area, 1)

    # session and query logic

    def _load_sessions(self):
        """fetches all available chat sessions from the api and populates the sidebar."""
        try:
            sessions = api.get_ai_sessions()

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
        """creates a fresh AI session and switches the view to it."""
        try:
            session = api.create_ai_session()
            self.current_session_id = session["session_id"]
            self._on_session_selected(self.current_session_id)
            self._load_sessions()
        except Exception:
            pass

    def _on_session_selected(self, session_id: int):
        """clears the current chat and loads message history for the selected session."""
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.history = []

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
        """displays a welcome message and instructions for new chat sessions."""
        welcome = QLabel(
            "<b style='font-size:14pt; color:black;'>How can I help?</b><br><br>"
            "<span style='color:#9CA3AF;font-size:10.5pt;'>"
            "I can analyze your cinema's performance, suggest listing optimizations, <br>"
            "or summarize recent booking trends. Just ask below."
            "</span>"
        )
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.setTextFormat(Qt.TextFormat.RichText)
        welcome.setWordWrap(True)
        welcome.setStyleSheet("background: transparent; padding: 60px;")
        self.chat_layout.addWidget(welcome)

    def _on_suggestion_clicked(self, text: str):
        self.input_field.setText(text)
        self._send_query()

    def _on_search_changed(self, text: str):
        """filters the session sidebar list based on user search input."""
        search_text = text.lower()
        for btn in self.session_buttons:
            btn.setVisible(search_text in btn.full_title.lower())

    def _handle_rename(self, session_id: int):
        """displays a rename dialog and updates the session title via the api."""
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
        """confirms and processes the deletion of a specific chat session."""
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
                    self._on_session_selected(-1)
                self._load_sessions()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {str(e)}")

    def _send_query(self):
        """submits the user's input query to the AI worker for processing."""
        query = self.input_field.text().strip()
        if not query:
            return

        if self.current_session_id is None:
            self._start_new_chat()
            if self.current_session_id is None:
                return

        self.input_field.clear()
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)

        self._add_message(query, False)
        self._show_thinking()

        self.worker = AIWorker(query, self.history, self.current_session_id)
        self.worker.finished.connect(self._on_query_finished)
        self.worker.error.connect(self._on_query_error)
        self.worker.start()

    def _on_query_finished(self, result: dict):
        """handles the completion of an AI query and updates the chat history."""
        self._hide_thinking()
        answer = result.get("answer", "No response received.")
        self._add_message(answer, True)
        self.history.append({"role": "user", "content": self.worker.query})
        self.history.append({"role": "assistant", "content": answer})

        if len(self.history) <= 2:
            self._load_sessions()

        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input_field.setFocus()
        self._fetch_suggestions()

    def _on_query_error(self, error: str):
        self._hide_thinking()
        self._add_message(f"<b>Error:</b> {error}", True)
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)

    def _fetch_suggestions(self):
        """periodically fetches fresh analytical suggestions from the api."""
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
        """updates the suggestion row with a new set of chip widgets."""
        while self.suggestions_row.count():
            item = self.suggestions_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for s in suggestions[:4]:
            chip = SuggestionChip(s, self._on_suggestion_clicked)
            self.suggestions_row.addWidget(chip)

    # layout and animation helpers

    def _add_message(self, text: str, is_ai: bool):
        """adds a new ChatBubble to the interface and auto-scrolls to the bottom."""
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
        """displays a temporary 'thinking' indicator while waiting for the AI response."""
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
        """updates the animation state of the 'thinking' dots."""
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
