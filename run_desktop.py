"""
run_desktop.py
Launch the Horizon Cinemas PyQt6 desktop application.

Usage:
    1. Start the API server: python run_server.py
    2. In another terminal:   python run_desktop.py
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget # type: ignore
from PyQt6.QtCore import Qt, QSize # type: ignore
from PyQt6.QtGui import QIcon # type: ignore

from desktop.ui.theme import load_fonts, GLOBAL_QSS
from desktop.ui.windows.login_window import LoginWindow
from desktop.ui.windows.main_window import MainWindow


class HCBSApp(QMainWindow):
    """
    Root window that switches between Login and Main views.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Horizon Cinemas Booking System")
        self.setMinimumSize(QSize(1100, 700))
        self.resize(1280, 800)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self._show_login()

    def _show_login(self):
        # Remove old widgets
        while self.stack.count():
            w = self.stack.widget(0)
            self.stack.removeWidget(w)
            w.deleteLater()

        login = LoginWindow(on_login_success=self._show_main)
        self.stack.addWidget(login)
        self.stack.setCurrentWidget(login)

    def _show_main(self):
        while self.stack.count():
            w = self.stack.widget(0)
            self.stack.removeWidget(w)
            w.deleteLater()

        main = MainWindow(on_logout=self._show_login)
        self.stack.addWidget(main)
        self.stack.setCurrentWidget(main)


def main():
    app = QApplication(sys.argv)

    # Load custom fonts
    load_fonts()

    # Apply global stylesheet
    app.setStyleSheet(GLOBAL_QSS)

    window = HCBSApp()
    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()