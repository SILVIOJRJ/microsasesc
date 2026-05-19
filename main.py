import sys
import os

# Ensure the app directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt
from app.config import APP_NAME, LOGO_PATH
from app.database.db import get_conn


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("Nascente")

    # Set app icon
    if os.path.exists(LOGO_PATH):
        app.setWindowIcon(QIcon(LOGO_PATH))

    # Default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Initialize database
    get_conn()

    # Show login
    from app.ui.login_window import LoginWindow
    login = LoginWindow()

    main_window_ref = [None]

    def on_login_success():
        login.hide()
        from app.ui.main_window import MainWindow
        mw = MainWindow()
        mw.show()
        main_window_ref[0] = mw

    login.login_success.connect(on_login_success)
    login.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
