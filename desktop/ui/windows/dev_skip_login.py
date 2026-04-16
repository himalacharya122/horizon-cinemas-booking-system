# ============================================
# Author: Himal Acharya
# Student ID: 22085619
# Last Edited: 2026-04-25
# ============================================

# ======================================================================================
# Use this in the login window to add skip buttons for development/testing purposes.
# ======================================================================================

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QWidget

from desktop.api_client import api


def add_dev_skip_button(layout, on_login_success):
    """
    Adds skip buttons for different roles.
    This file can be safely removed or commented out before production.
    """
    container = QWidget()
    hlayout = QHBoxLayout(container)
    hlayout.setContentsMargins(0, 0, 0, 0)
    hlayout.setSpacing(8)

    roles = [("Admin", "ewilson"), ("Manager", "jcarter"), ("Staff", "akhan")]

    def make_btn(role_name, username):
        btn = QPushButton(f"Skip as {role_name}")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #ff5555; "
            "border: 1px dashed #ff5555; border-radius: 6px; padding: 10px 5px; "
            "font-weight: bold; font-size: 10pt; }"
            "QPushButton:hover { background-color: rgba(255, 85, 85, 25); }"
            "QPushButton:disabled { color: #888; border-color: #888; }"
        )

        def do_skip():
            btn.setText("...")
            btn.setEnabled(False)
            try:
                try:
                    # Try seed hashtag password
                    api.login(username, "Password123#")
                except Exception:
                    # Try seed exclamation password
                    api.login(username, "Password123!")
                on_login_success()
            except Exception as e:
                btn.setText("Error")
                btn.setEnabled(True)
                print(f"Dev Skip Error ({role_name}): {e}")

        btn.clicked.connect(do_skip)
        return btn

    for r_name, u_name in roles:
        hlayout.addWidget(make_btn(r_name, u_name))

    layout.addWidget(container)
