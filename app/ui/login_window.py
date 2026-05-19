from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont
from app.auth import auth
from app.config import APP_NAME, LOGO_PATH
from app.ui.styles import LOGIN_STYLE
import os


class LoginWindow(QWidget):
    login_success = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Login — {APP_NAME}")
        self.setMinimumSize(900, 600)
        self.setStyleSheet(LOGIN_STYLE)
        self._build_ui()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Left panel — branding
        left = QFrame()
        left.setObjectName("left_panel")
        left.setStyleSheet("background: transparent;")
        left.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        ll = QVBoxLayout(left)
        ll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ll.setSpacing(12)

        if os.path.exists(LOGO_PATH):
            logo_lbl = QLabel()
            px = QPixmap(LOGO_PATH).scaledToWidth(200, Qt.TransformationMode.SmoothTransformation)
            logo_lbl.setPixmap(px)
            logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ll.addWidget(logo_lbl)

        title = QLabel(APP_NAME)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #C8A951; font-size: 20px; font-weight: bold;")
        ll.addWidget(title)

        sub = QLabel("Sistema de Gestão Contábil")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #8899AA; font-size: 13px;")
        ll.addWidget(sub)

        root.addWidget(left, 1)

        # Right panel — login card
        right = QFrame()
        right.setStyleSheet("background: #F4F6F8;")
        right.setFixedWidth(420)
        rl = QVBoxLayout(right)
        rl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("login_card")
        card.setFixedWidth(360)
        card.setStyleSheet("""
            QFrame#login_card {
                background: white;
                border-radius: 12px;
                border: 1px solid #DDE1E7;
            }
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(32, 36, 32, 36)
        cl.setSpacing(16)

        # Card header
        card_title = QLabel("Bem-vindo!")
        card_title.setObjectName("login_title")
        card_title.setStyleSheet("color: #1B2A3B; font-size: 22px; font-weight: bold;")
        cl.addWidget(card_title)

        card_sub = QLabel("Faça login para continuar")
        card_sub.setStyleSheet("color: #7F8C8D; font-size: 13px; margin-bottom: 8px;")
        cl.addWidget(card_sub)

        # Username
        lbl_user = QLabel("Usuário")
        lbl_user.setStyleSheet("color: #2C3E50; font-size: 12px; font-weight: bold;")
        cl.addWidget(lbl_user)
        self.inp_user = QLineEdit()
        self.inp_user.setPlaceholderText("Digite seu usuário")
        self.inp_user.setStyleSheet("""
            QLineEdit { background: #F4F6F8; border: 1px solid #DDE1E7; border-radius: 6px;
                        padding: 8px 12px; font-size: 14px; min-height: 36px; color: #2C3E50; }
            QLineEdit:focus { border: 2px solid #C8A951; background: white; }
        """)
        cl.addWidget(self.inp_user)

        # Password
        lbl_pw = QLabel("Senha")
        lbl_pw.setStyleSheet("color: #2C3E50; font-size: 12px; font-weight: bold;")
        cl.addWidget(lbl_pw)
        self.inp_pw = QLineEdit()
        self.inp_pw.setPlaceholderText("Digite sua senha")
        self.inp_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_pw.setStyleSheet("""
            QLineEdit { background: #F4F6F8; border: 1px solid #DDE1E7; border-radius: 6px;
                        padding: 8px 12px; font-size: 14px; min-height: 36px; color: #2C3E50; }
            QLineEdit:focus { border: 2px solid #C8A951; background: white; }
        """)
        self.inp_pw.returnPressed.connect(self._do_login)
        cl.addWidget(self.inp_pw)

        # Error
        self.lbl_error = QLabel("")
        self.lbl_error.setObjectName("error_label")
        self.lbl_error.setStyleSheet("color: #E74C3C; font-size: 12px;")
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(self.lbl_error)

        # Button
        self.btn_login = QPushButton("Entrar")
        self.btn_login.setObjectName("btn_login")
        self.btn_login.setStyleSheet("""
            QPushButton { background: #C8A951; color: white; border: none; border-radius: 6px;
                          padding: 10px; font-size: 15px; font-weight: bold; min-height: 42px; }
            QPushButton:hover { background: #9E7D2B; }
        """)
        self.btn_login.clicked.connect(self._do_login)
        cl.addWidget(self.btn_login)

        rl.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
        root.addWidget(right)

    def _do_login(self):
        username = self.inp_user.text().strip()
        password = self.inp_pw.text()
        if not username or not password:
            self.lbl_error.setText("Preencha usuário e senha.")
            return
        if auth.login(username, password):
            self.login_success.emit()
        else:
            self.lbl_error.setText("Usuário ou senha incorretos.")
            self.inp_pw.clear()
