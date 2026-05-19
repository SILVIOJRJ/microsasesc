from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QDialog, QFormLayout, QLineEdit, QComboBox, QTextEdit,
    QMessageBox, QHeaderView, QTabWidget, QDoubleSpinBox, QSpinBox, QCheckBox,
    QFrame, QSplitter,
)
from PyQt6.QtCore import Qt, pyqtSignal
from app.database import db
from app.auth import auth
from app.config import REGIMES
import os


class ClientDialog(QDialog):
    def __init__(self, parent=None, client=None):
        super().__init__(parent)
        self.client = client
        self.setWindowTitle("Novo Cliente" if not client else "Editar Cliente")
        self.setMinimumWidth(640)
        self.setMinimumHeight(600)
        self.setModal(True)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # ── Tab 1: Dados Gerais ──
        tab1 = QWidget()
        f1 = QFormLayout(tab1)
        f1.setSpacing(10)
        f1.setContentsMargins(16, 16, 16, 16)

        self.inp_name = QLineEdit()
        self.inp_fantasy = QLineEdit()
        self.inp_cnpj = QLineEdit()
        self.inp_cnpj.setPlaceholderText("00.000.000/0001-00 ou 000.000.000-00")
        self.cmb_type = QComboBox()
        self.cmb_type.addItem("Pessoa Jurídica", "PJ")
        self.cmb_type.addItem("Pessoa Física", "PF")
        self.inp_email = QLineEdit()
        self.inp_phone = QLineEdit()
        self.inp_mobile = QLineEdit()
        self.inp_contact = QLineEdit()
        self.cmb_regime = QComboBox()
        for r in REGIMES:
            self.cmb_regime.addItem(r)
        self.cmb_dept = QComboBox()
        self.cmb_dept.addItem("— Nenhum —", None)
        for d in db.get_departments(active_only=True):
            self.cmb_dept.addItem(d["name"], d["id"])
        self.chk_active = QCheckBox("Cliente ativo")
        self.chk_active.setChecked(True)

        f1.addRow("Razão Social / Nome *", self.inp_name)
        f1.addRow("Nome Fantasia", self.inp_fantasy)
        f1.addRow("CNPJ / CPF *", self.inp_cnpj)
        f1.addRow("Tipo", self.cmb_type)
        f1.addRow("E-mail", self.inp_email)
        f1.addRow("Telefone", self.inp_phone)
        f1.addRow("Celular", self.inp_mobile)
        f1.addRow("Responsável / Contato", self.inp_contact)
        f1.addRow("Regime Tributário", self.cmb_regime)
        f1.addRow("Departamento", self.cmb_dept)
        f1.addRow("", self.chk_active)
        tabs.addTab(tab1, "Dados Gerais")

        # ── Tab 2: Endereço ──
        tab2 = QWidget()
        f2 = QFormLayout(tab2)
        f2.setSpacing(10)
        f2.setContentsMargins(16, 16, 16, 16)
        self.inp_zip = QLineEdit()
        self.inp_address = QLineEdit()
        self.inp_number = QLineEdit()
        self.inp_complement = QLineEdit()
        self.inp_neighborhood = QLineEdit()
        self.inp_city = QLineEdit()
        self.inp_state = QLineEdit()
        self.inp_state.setMaximumWidth(80)
        f2.addRow("CEP", self.inp_zip)
        f2.addRow("Logradouro", self.inp_address)
        f2.addRow("Número", self.inp_number)
        f2.addRow("Complemento", self.inp_complement)
        f2.addRow("Bairro", self.inp_neighborhood)
        f2.addRow("Cidade", self.inp_city)
        f2.addRow("Estado (UF)", self.inp_state)
        tabs.addTab(tab2, "Endereço")

        # ── Tab 3: Financeiro ──
        tab3 = QWidget()
        f3 = QFormLayout(tab3)
        f3.setSpacing(10)
        f3.setContentsMargins(16, 16, 16, 16)
        self.spin_fee = QDoubleSpinBox()
        self.spin_fee.setPrefix("R$ ")
        self.spin_fee.setMaximum(999999.99)
        self.spin_fee.setDecimals(2)
        self.spin_due = QSpinBox()
        self.spin_due.setMinimum(1)
        self.spin_due.setMaximum(31)
        self.spin_due.setValue(5)
        self.inp_notes = QTextEdit()
        self.inp_notes.setMaximumHeight(120)
        f3.addRow("Honorário mensal (R$)", self.spin_fee)
        f3.addRow("Dia de vencimento", self.spin_due)
        f3.addRow("Observações", self.inp_notes)
        tabs.addTab(tab3, "Financeiro / Obs.")

        # Populate if editing
        if self.client:
            self.inp_name.setText(self.client["name"])
            self.inp_fantasy.setText(self.client["fantasy_name"] or "")
            self.inp_cnpj.setText(self.client["cnpj_cpf"])
            idx = self.cmb_type.findData(self.client["type"])
            if idx >= 0:
                self.cmb_type.setCurrentIndex(idx)
            self.inp_email.setText(self.client["email"] or "")
            self.inp_phone.setText(self.client["phone"] or "")
            self.inp_mobile.setText(self.client["mobile"] or "")
            self.inp_contact.setText(self.client["contact_person"] or "")
            ri = self.cmb_regime.findText(self.client["regime_tributario"] or "")
            if ri >= 0:
                self.cmb_regime.setCurrentIndex(ri)
            if self.client["department_id"]:
                di = self.cmb_dept.findData(self.client["department_id"])
                if di >= 0:
                    self.cmb_dept.setCurrentIndex(di)
            self.chk_active.setChecked(bool(self.client["active"]))
            self.inp_zip.setText(self.client["zip_code"] or "")
            self.inp_address.setText(self.client["address"] or "")
            self.inp_number.setText(self.client["number"] or "")
            self.inp_complement.setText(self.client["complement"] or "")
            self.inp_neighborhood.setText(self.client["neighborhood"] or "")
            self.inp_city.setText(self.client["city"] or "")
            self.inp_state.setText(self.client["state"] or "")
            self.spin_fee.setValue(self.client["monthly_fee"] or 0)
            self.spin_due.setValue(self.client["due_day"] or 5)
            self.inp_notes.setPlainText(self.client["notes"] or "")

        btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Salvar Cliente")
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _collect(self):
        return {
            "name": self.inp_name.text().strip(),
            "fantasy_name": self.inp_fantasy.text().strip(),
            "cnpj_cpf": self.inp_cnpj.text().strip(),
            "type": self.cmb_type.currentData(),
            "email": self.inp_email.text().strip(),
            "phone": self.inp_phone.text().strip(),
            "mobile": self.inp_mobile.text().strip(),
            "contact_person": self.inp_contact.text().strip(),
            "regime_tributario": self.cmb_regime.currentText(),
            "department_id": self.cmb_dept.currentData(),
            "active": 1 if self.chk_active.isChecked() else 0,
            "zip_code": self.inp_zip.text().strip(),
            "address": self.inp_address.text().strip(),
            "number": self.inp_number.text().strip(),
            "complement": self.inp_complement.text().strip(),
            "neighborhood": self.inp_neighborhood.text().strip(),
            "city": self.inp_city.text().strip(),
            "state": self.inp_state.text().strip().upper(),
            "monthly_fee": self.spin_fee.value(),
            "due_day": self.spin_due.value(),
            "notes": self.inp_notes.toPlainText().strip(),
        }

    def _save(self):
        data = self._collect()
        if not data["name"]:
            QMessageBox.warning(self, "Atenção", "Razão Social é obrigatória.")
            return
        if not data["cnpj_cpf"]:
            QMessageBox.warning(self, "Atenção", "CNPJ/CPF é obrigatório.")
            return
        try:
            if self.client:
                db.update_client(self.client["id"], data)
            else:
                cid = db.create_client(data)
                # Create client folder
                from app.config import CLIENTS_DIR
                folder = os.path.join(CLIENTS_DIR, f"{cid}_{data['name'][:30]}")
                os.makedirs(folder, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao salvar", str(e))
            return
        self.accept()


class ClientsWidget(QWidget):
    client_selected = pyqtSignal(int)

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
        self.inp_search.setPlaceholderText("Buscar por nome, CNPJ/CPF...")
        self.inp_search.textChanged.connect(self._load)
        self.cmb_filter = QComboBox()
        self.cmb_filter.addItem("Todos", "")
        self.cmb_filter.addItem("Apenas ativos", "1")
        self.cmb_filter.currentIndexChanged.connect(self._load)
        btn_new = QPushButton("+ Novo Cliente")
        btn_new.clicked.connect(self._new_client)

        toolbar.addWidget(self.inp_search)
        toolbar.addWidget(self.cmb_filter)
        toolbar.addStretch()
        toolbar.addWidget(btn_new)
        layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["#", "Razão Social", "Nome Fantasia", "CNPJ/CPF", "Regime", "Honorário", "Status"]
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._edit_client)
        layout.addWidget(self.table)

        # Action bar
        action_bar = QHBoxLayout()
        btn_view = QPushButton("Ver Detalhes")
        btn_view.setObjectName("btn_secondary")
        btn_view.clicked.connect(self._view_client)
        btn_edit = QPushButton("Editar")
        btn_edit.setObjectName("btn_secondary")
        btn_edit.clicked.connect(self._edit_client)
        action_bar.addStretch()
        action_bar.addWidget(btn_view)
        action_bar.addWidget(btn_edit)
        layout.addLayout(action_bar)

    def _load(self):
        search = self.inp_search.text().strip()
        filter_val = self.cmb_filter.currentData()
        active_only = filter_val == "1"
        clients = db.get_clients(active_only=active_only, search=search)
        self.table.setRowCount(len(clients))
        for i, c in enumerate(clients):
            self.table.setItem(i, 0, QTableWidgetItem(str(c["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(c["name"]))
            self.table.setItem(i, 2, QTableWidgetItem(c["fantasy_name"] or ""))
            self.table.setItem(i, 3, QTableWidgetItem(c["cnpj_cpf"]))
            self.table.setItem(i, 4, QTableWidgetItem(c["regime_tributario"] or ""))
            fee = QTableWidgetItem(f"R$ {c['monthly_fee']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            fee.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 5, fee)
            status = QTableWidgetItem("Ativo" if c["active"] else "Inativo")
            status.setForeground(Qt.GlobalColor.darkGreen if c["active"] else Qt.GlobalColor.red)
            self.table.setItem(i, 6, status)
        self.table.resizeRowsToContents()

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def _new_client(self):
        if not auth.has_role("CONTADOR"):
            QMessageBox.warning(self, "Acesso negado", "Permissão insuficiente.")
            return
        dlg = ClientDialog(self)
        if dlg.exec():
            self._load()

    def _edit_client(self):
        cid = self._selected_id()
        if not cid:
            QMessageBox.information(self, "Selecione", "Selecione um cliente.")
            return
        if not auth.has_role("CONTADOR"):
            QMessageBox.warning(self, "Acesso negado", "Permissão insuficiente.")
            return
        client = db.get_client_by_id(cid)
        dlg = ClientDialog(self, client)
        if dlg.exec():
            self._load()

    def _view_client(self):
        cid = self._selected_id()
        if not cid:
            QMessageBox.information(self, "Selecione", "Selecione um cliente.")
            return
        self.client_selected.emit(cid)
