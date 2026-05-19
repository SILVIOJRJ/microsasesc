from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QDialog, QFormLayout, QLineEdit, QComboBox, QCheckBox,
    QMessageBox, QHeaderView, QFrame,
)
from PyQt6.QtCore import Qt
from app.database import db
from app.auth import auth
from app.config import ROLE_LABELS


class UserDialog(QDialog):
    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("Novo Usuário" if not user else "Editar Usuário")
        self.setMinimumWidth(420)
        self.setModal(True)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Usuário" if not self.user else "Editar Usuário")
        title.setObjectName("section_label")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.inp_name = QLineEdit()
        self.inp_username = QLineEdit()
        self.inp_email = QLineEdit()
        self.inp_pw = QLineEdit()
        self.inp_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_pw2 = QLineEdit()
        self.inp_pw2.setEchoMode(QLineEdit.EchoMode.Password)
        self.cmb_role = QComboBox()
        for key, label in ROLE_LABELS.items():
            self.cmb_role.addItem(label, key)
        self.chk_active = QCheckBox("Ativo")
        self.chk_active.setChecked(True)

        form.addRow("Nome completo *", self.inp_name)
        form.addRow("Usuário (login) *", self.inp_username)
        form.addRow("E-mail", self.inp_email)
        form.addRow("Perfil *", self.cmb_role)
        form.addRow("Senha *", self.inp_pw)
        form.addRow("Confirmar senha *", self.inp_pw2)
        form.addRow("", self.chk_active)

        layout.addLayout(form)

        if self.user:
            self.inp_name.setText(self.user["name"])
            self.inp_username.setText(self.user["username"])
            self.inp_username.setEnabled(False)
            self.inp_email.setText(self.user["email"] or "")
            idx = self.cmb_role.findData(self.user["role"])
            if idx >= 0:
                self.cmb_role.setCurrentIndex(idx)
            self.chk_active.setChecked(bool(self.user["active"]))
            self.inp_pw.setPlaceholderText("Deixe em branco para manter")
            self.inp_pw2.setPlaceholderText("Deixe em branco para manter")

        note = QLabel("* Campos obrigatórios")
        note.setStyleSheet("color: #7F8C8D; font-size: 11px;")
        layout.addWidget(note)

        btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Salvar")
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _save(self):
        name = self.inp_name.text().strip()
        username = self.inp_username.text().strip()
        email = self.inp_email.text().strip()
        role = self.cmb_role.currentData()
        pw = self.inp_pw.text()
        pw2 = self.inp_pw2.text()
        active = self.chk_active.isChecked()

        if not name or not username:
            QMessageBox.warning(self, "Atenção", "Nome e usuário são obrigatórios.")
            return

        if not self.user and not pw:
            QMessageBox.warning(self, "Atenção", "Informe uma senha.")
            return

        if pw and pw != pw2:
            QMessageBox.warning(self, "Atenção", "As senhas não conferem.")
            return

        if pw and len(pw) < 6:
            QMessageBox.warning(self, "Atenção", "A senha deve ter ao menos 6 caracteres.")
            return

        try:
            if self.user:
                db.update_user(self.user["id"], name, role, email, 1 if active else 0)
                if pw:
                    db.update_user_password(self.user["id"], auth.hash_password(pw))
            else:
                existing = db.get_user_by_username(username)
                if existing:
                    QMessageBox.warning(self, "Atenção", "Usuário já cadastrado.")
                    return
                db.create_user(username, auth.hash_password(pw), name, role, email)
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))
            return
        self.accept()


class UsersWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._build()
        self._load()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Toolbar
        toolbar = QHBoxLayout()
        self.inp_search = QLineEdit()
        self.inp_search.setObjectName("search_bar")
        self.inp_search.setPlaceholderText("Buscar usuário...")
        self.inp_search.textChanged.connect(self._load)

        btn_new = QPushButton("+ Novo Usuário")
        btn_new.clicked.connect(self._new_user)
        if not auth.has_role("ADMIN"):
            btn_new.setEnabled(False)

        toolbar.addWidget(self.inp_search)
        toolbar.addStretch()
        toolbar.addWidget(btn_new)
        layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["#", "Nome", "Usuário", "Perfil", "E-mail", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._edit_user)
        layout.addWidget(self.table)

        # Bottom action bar
        action_bar = QHBoxLayout()
        self.btn_edit = QPushButton("Editar")
        self.btn_edit.setObjectName("btn_secondary")
        self.btn_edit.clicked.connect(self._edit_user)
        action_bar.addStretch()
        action_bar.addWidget(self.btn_edit)
        layout.addLayout(action_bar)

    def _load(self):
        search = self.inp_search.text().strip()
        users = db.get_users()
        if search:
            s = search.lower()
            users = [u for u in users if s in u["name"].lower() or s in u["username"].lower()]

        self.table.setRowCount(len(users))
        for i, u in enumerate(users):
            self.table.setItem(i, 0, QTableWidgetItem(str(u["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(u["name"]))
            self.table.setItem(i, 2, QTableWidgetItem(u["username"]))
            from app.config import ROLE_LABELS
            self.table.setItem(i, 3, QTableWidgetItem(ROLE_LABELS.get(u["role"], u["role"])))
            self.table.setItem(i, 4, QTableWidgetItem(u["email"] or ""))
            status = QTableWidgetItem("Ativo" if u["active"] else "Inativo")
            status.setForeground(
                Qt.GlobalColor.darkGreen if u["active"] else Qt.GlobalColor.red
            )
            self.table.setItem(i, 5, status)
        self.table.resizeRowsToContents()

    def _selected_user_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def _new_user(self):
        if not auth.has_role("ADMIN"):
            QMessageBox.warning(self, "Acesso negado", "Apenas administradores podem criar usuários.")
            return
        dlg = UserDialog(self)
        if dlg.exec():
            self._load()

    def _edit_user(self):
        uid = self._selected_user_id()
        if not uid:
            QMessageBox.information(self, "Selecione", "Selecione um usuário.")
            return
        if not auth.has_role("ADMIN"):
            QMessageBox.warning(self, "Acesso negado", "Apenas administradores podem editar usuários.")
            return
        user = db.get_user_by_id(uid)
        dlg = UserDialog(self, user)
        if dlg.exec():
            self._load()
