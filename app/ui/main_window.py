from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QStackedWidget, QFrame, QSizePolicy, QMessageBox, QDialog, QFormLayout,
    QLineEdit, QTabWidget, QSpinBox,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPixmap, QIcon
from app.auth import auth
from app.config import APP_NAME, LOGO_PATH, COLORS, ESCRITORIO, ROLE_LABELS
from app.ui.styles import MAIN_STYLE
from app.ui.users.users_widget import UsersWidget
from app.ui.clients.clients_widget import ClientsWidget
from app.ui.departments.departments_widget import DepartmentsWidget
from app.ui.service_orders.orders_widget import OrdersWidget
from app.ui.contracts.contracts_widget import ContractsWidget
from app.ui.commercial.commercial_widget import CommercialWidget
from app.ui.documents.documents_widget import DocumentsWidget
from app.database import db
import os


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações do Escritório")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._build()
        self._load()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)
        self.inp_nome = QLineEdit()
        self.inp_cnpj = QLineEdit()
        self.inp_crc = QLineEdit()
        self.inp_responsavel = QLineEdit()
        self.inp_endereco = QLineEdit()
        self.inp_cidade = QLineEdit()
        self.inp_estado = QLineEdit()
        self.inp_estado.setMaximumWidth(60)
        self.inp_cep = QLineEdit()
        self.inp_telefone = QLineEdit()
        self.inp_email = QLineEdit()
        form.addRow("Nome do escritório", self.inp_nome)
        form.addRow("CNPJ", self.inp_cnpj)
        form.addRow("CRC", self.inp_crc)
        form.addRow("Contador responsável", self.inp_responsavel)
        form.addRow("Endereço", self.inp_endereco)
        form.addRow("Cidade", self.inp_cidade)
        form.addRow("Estado (UF)", self.inp_estado)
        form.addRow("CEP", self.inp_cep)
        form.addRow("Telefone", self.inp_telefone)
        form.addRow("E-mail", self.inp_email)
        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Salvar")
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _load(self):
        fields = ["nome", "cnpj", "crc", "responsavel", "endereco", "cidade", "estado", "cep", "telefone", "email"]
        for f in fields:
            val = db.get_setting(f"escritorio_{f}", ESCRITORIO.get(f, ""))
            getattr(self, f"inp_{f}").setText(val)

    def _save(self):
        fields = ["nome", "cnpj", "crc", "responsavel", "endereco", "cidade", "estado", "cep", "telefone", "email"]
        for f in fields:
            val = getattr(self, f"inp_{f}").text().strip()
            db.set_setting(f"escritorio_{f}", val)
            ESCRITORIO[f] = val
        QMessageBox.information(self, "Salvo", "Configurações salvas com sucesso.")
        self.accept()


def _load_escritorio_settings():
    fields = ["nome", "cnpj", "crc", "responsavel", "endereco", "cidade", "estado", "cep", "telefone", "email"]
    for f in fields:
        val = db.get_setting(f"escritorio_{f}", "")
        if val:
            ESCRITORIO[f] = val


class NavButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setObjectName("nav_btn")
        self.setCheckable(True)
        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        _load_escritorio_settings()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1200, 700)
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()
        self._nav_buttons[0].setChecked(True)
        self.stack.setCurrentIndex(0)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ──
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(0)

        # Logo/header
        header = QFrame()
        header.setObjectName("sidebar_header")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(12, 16, 12, 16)
        hl.setSpacing(4)

        if os.path.exists(LOGO_PATH):
            try:
                logo_lbl = QLabel()
                px = QPixmap(LOGO_PATH).scaledToWidth(48, Qt.TransformationMode.SmoothTransformation)
                logo_lbl.setPixmap(px)
                logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                hl.addWidget(logo_lbl)
            except Exception:
                pass

        title = QLabel(APP_NAME)
        title.setObjectName("sidebar_title")
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #C8A951; font-size: 12px; font-weight: bold;")
        hl.addWidget(title)
        sl.addWidget(header)

        # Navigation
        nav_container = QWidget()
        nav_container.setStyleSheet("background: transparent;")
        nl = QVBoxLayout(nav_container)
        nl.setContentsMargins(0, 8, 0, 8)
        nl.setSpacing(2)

        self._nav_buttons = []
        nav_items = self._get_nav_items()
        for i, (icon, label, _) in enumerate(nav_items):
            btn = NavButton(f"  {icon}  {label}")
            btn.clicked.connect(lambda checked, idx=i: self._switch_page(idx))
            nl.addWidget(btn)
            self._nav_buttons.append(btn)

        nl.addStretch()
        sl.addWidget(nav_container, 1)

        # User info at bottom of sidebar
        user_frame = QFrame()
        user_frame.setStyleSheet("background: #0D1B2A; padding: 10px;")
        uf = QVBoxLayout(user_frame)
        uf.setContentsMargins(12, 8, 12, 8)
        uf.setSpacing(4)
        user = auth.current_user()
        lbl_name = QLabel(user["name"])
        lbl_name.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        lbl_role = QLabel(ROLE_LABELS.get(user["role"], user["role"]))
        lbl_role.setStyleSheet("color: #C8A951; font-size: 11px;")
        btn_settings = QPushButton("⚙ Configurações")
        btn_settings.setObjectName("nav_btn")
        btn_settings.setFixedHeight(32)
        btn_settings.setStyleSheet("font-size: 11px; margin: 0;")
        btn_settings.clicked.connect(self._open_settings)
        btn_logout = QPushButton("↩ Sair")
        btn_logout.setObjectName("nav_btn")
        btn_logout.setFixedHeight(32)
        btn_logout.setStyleSheet("font-size: 11px; margin: 0;")
        btn_logout.clicked.connect(self._logout)
        uf.addWidget(lbl_name)
        uf.addWidget(lbl_role)
        uf.addWidget(btn_settings)
        uf.addWidget(btn_logout)
        sl.addWidget(user_frame)

        root.addWidget(sidebar)

        # ── Content area ──
        content_area = QWidget()
        cal = QVBoxLayout(content_area)
        cal.setContentsMargins(0, 0, 0, 0)
        cal.setSpacing(0)

        # Header bar
        self.header_bar = QFrame()
        self.header_bar.setObjectName("header")
        hbl = QHBoxLayout(self.header_bar)
        hbl.setContentsMargins(24, 0, 24, 0)
        self.lbl_page_title = QLabel("Dashboard")
        self.lbl_page_title.setObjectName("page_title")
        hbl.addWidget(self.lbl_page_title)
        hbl.addStretch()
        cal.addWidget(self.header_bar)

        # Pages stack
        self.stack = QStackedWidget()
        cal.addWidget(self.stack, 1)
        root.addWidget(content_area, 1)

        # Build pages
        self._pages = []
        for _, _, widget_factory in self._get_nav_items():
            w = widget_factory()
            self.stack.addWidget(w)
            self._pages.append(w)

        # Connect client_selected signal from clients page to documents page
        clients_page = self._pages[self._get_page_index("Clientes")]
        docs_page = self._pages[self._get_page_index("Documentos")]
        if hasattr(clients_page, "client_selected"):
            clients_page.client_selected.connect(self._navigate_to_docs)

    def _get_nav_items(self):
        user = auth.current_user()
        role = user["role"] if user else "ASSISTENTE"
        items = [
            ("🏠", "Clientes", ClientsWidget),
            ("📋", "Ordens de Serviço", OrdersWidget),
            ("📄", "Contratos", ContractsWidget),
            ("💰", "Comercial / Caixa", CommercialWidget),
            ("📁", "Documentos", DocumentsWidget),
            ("🏢", "Departamentos", DepartmentsWidget),
        ]
        if auth.has_role("ADMIN"):
            items.append(("👥", "Usuários", UsersWidget))
        return items

    def _get_page_index(self, label):
        for i, (_, lbl, _) in enumerate(self._get_nav_items()):
            if lbl == label:
                return i
        return 0

    def _switch_page(self, idx):
        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == idx)
        self.stack.setCurrentIndex(idx)
        label = self._get_nav_items()[idx][1]
        self.lbl_page_title.setText(label)

    def _navigate_to_docs(self, client_id: int):
        docs_idx = self._get_page_index("Documentos")
        self._switch_page(docs_idx)
        docs_page = self._pages[docs_idx]
        if hasattr(docs_page, "select_client"):
            docs_page.select_client(client_id)

    def _open_settings(self):
        if not auth.has_role("GERENTE"):
            QMessageBox.warning(self, "Acesso negado", "Apenas gerentes e administradores podem alterar as configurações.")
            return
        dlg = SettingsDialog(self)
        dlg.exec()

    def _logout(self):
        reply = QMessageBox.question(
            self, "Sair",
            "Deseja realmente sair do sistema?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            auth.logout()
            self.close()
            from app.ui.login_window import LoginWindow
            self._login_window = LoginWindow()
            self._login_window.login_success.connect(self._reopen)
            self._login_window.show()

    def _reopen(self):
        self._login_window.hide()
        new_main = MainWindow()
        new_main.show()
        self._login_window = None
