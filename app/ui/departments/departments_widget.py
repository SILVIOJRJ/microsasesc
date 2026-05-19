from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QDialog, QFormLayout, QLineEdit, QTextEdit, QCheckBox,
    QMessageBox, QHeaderView,
)
from PyQt6.QtCore import Qt
from app.database import db
from app.auth import auth


class DeptDialog(QDialog):
    def __init__(self, parent=None, dept=None):
        super().__init__(parent)
        self.dept = dept
        self.setWindowTitle("Departamento")
        self.setMinimumWidth(380)
        self.setModal(True)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)
        self.inp_name = QLineEdit()
        self.inp_desc = QTextEdit()
        self.inp_desc.setMaximumHeight(80)
        self.chk_active = QCheckBox("Ativo")
        self.chk_active.setChecked(True)
        form.addRow("Nome *", self.inp_name)
        form.addRow("Descrição", self.inp_desc)
        form.addRow("", self.chk_active)
        layout.addLayout(form)

        if self.dept:
            self.inp_name.setText(self.dept["name"])
            self.inp_desc.setPlainText(self.dept["description"] or "")
            self.chk_active.setChecked(bool(self.dept["active"]))

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
        if not name:
            QMessageBox.warning(self, "Atenção", "Nome é obrigatório.")
            return
        desc = self.inp_desc.toPlainText().strip()
        active = 1 if self.chk_active.isChecked() else 0
        if self.dept:
            db.update_department(self.dept["id"], name, desc, active)
        else:
            db.create_department(name, desc)
        self.accept()


class DepartmentsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._build()
        self._load()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        toolbar = QHBoxLayout()
        self.inp_search = QLineEdit()
        self.inp_search.setObjectName("search_bar")
        self.inp_search.setPlaceholderText("Buscar departamento...")
        self.inp_search.textChanged.connect(self._load)

        btn_new = QPushButton("+ Novo Departamento")
        btn_new.clicked.connect(self._new_dept)

        toolbar.addWidget(self.inp_search)
        toolbar.addStretch()
        toolbar.addWidget(btn_new)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["#", "Nome", "Descrição", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._edit_dept)
        layout.addWidget(self.table)

        action_bar = QHBoxLayout()
        btn_edit = QPushButton("Editar")
        btn_edit.setObjectName("btn_secondary")
        btn_edit.clicked.connect(self._edit_dept)
        action_bar.addStretch()
        action_bar.addWidget(btn_edit)
        layout.addLayout(action_bar)

    def _load(self):
        search = self.inp_search.text().strip().lower()
        depts = db.get_departments()
        if search:
            depts = [d for d in depts if search in d["name"].lower()]
        self.table.setRowCount(len(depts))
        for i, d in enumerate(depts):
            self.table.setItem(i, 0, QTableWidgetItem(str(d["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(d["name"]))
            self.table.setItem(i, 2, QTableWidgetItem(d["description"] or ""))
            status = QTableWidgetItem("Ativo" if d["active"] else "Inativo")
            status.setForeground(Qt.GlobalColor.darkGreen if d["active"] else Qt.GlobalColor.red)
            self.table.setItem(i, 3, status)
        self.table.resizeRowsToContents()

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def _new_dept(self):
        if not auth.has_role("GERENTE"):
            QMessageBox.warning(self, "Acesso negado", "Permissão insuficiente.")
            return
        dlg = DeptDialog(self)
        if dlg.exec():
            self._load()

    def _edit_dept(self):
        did = self._selected_id()
        if not did:
            QMessageBox.information(self, "Selecione", "Selecione um departamento.")
            return
        if not auth.has_role("GERENTE"):
            QMessageBox.warning(self, "Acesso negado", "Permissão insuficiente.")
            return
        dept = db.get_department_by_id(did)
        dlg = DeptDialog(self, dept)
        if dlg.exec():
            self._load()
