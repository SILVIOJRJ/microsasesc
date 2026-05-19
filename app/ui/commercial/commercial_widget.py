from datetime import date, datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QDialog, QFormLayout, QLineEdit, QComboBox, QTextEdit,
    QMessageBox, QHeaderView, QDoubleSpinBox, QDateEdit, QTabWidget, QFrame,
    QSplitter, QGridLayout,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont
from app.database import db
from app.auth import auth
from app.config import FEE_STATUS, COLORS


class FeeDialog(QDialog):
    def __init__(self, parent=None, client_id=None, contract_id=None,
                 default_amount=0.0, default_desc="", fee=None):
        super().__init__(parent)
        self.fee = fee
        self.setWindowTitle("Lançar Honorário" if not fee else "Editar Honorário")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._default_client_id = client_id
        self._default_contract_id = contract_id
        self._default_amount = default_amount
        self._default_desc = default_desc
        self._build()
        if fee:
            self._populate(fee)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        self.cmb_client = QComboBox()
        self.cmb_client.setMinimumWidth(280)
        for c in db.get_clients(active_only=True):
            self.cmb_client.addItem(f"{c['name']}", c["id"])
        if self._default_client_id:
            idx = self.cmb_client.findData(self._default_client_id)
            if idx >= 0:
                self.cmb_client.setCurrentIndex(idx)

        self.inp_desc = QLineEdit()
        self.inp_desc.setText(self._default_desc)
        self.spin_amount = QDoubleSpinBox()
        self.spin_amount.setPrefix("R$ ")
        self.spin_amount.setMaximum(9999999.99)
        self.spin_amount.setDecimals(2)
        self.spin_amount.setValue(self._default_amount)
        self.inp_due = QDateEdit()
        self.inp_due.setCalendarPopup(True)
        self.inp_due.setDate(QDate.currentDate())
        self.inp_ref = QLineEdit()
        self.inp_ref.setPlaceholderText("Ex: 2025-04")
        today = date.today()
        self.inp_ref.setText(f"{today.year}-{today.month:02d}")
        self.cmb_status = QComboBox()
        for key, label in FEE_STATUS.items():
            self.cmb_status.addItem(label, key)
        self.inp_paid = QDateEdit()
        self.inp_paid.setCalendarPopup(True)
        self.inp_paid.setDate(QDate.currentDate())
        self.inp_paid.setEnabled(False)
        self.cmb_status.currentIndexChanged.connect(
            lambda: self.inp_paid.setEnabled(self.cmb_status.currentData() == "PAGO")
        )
        self.inp_notes = QTextEdit()
        self.inp_notes.setMaximumHeight(60)

        form.addRow("Cliente *", self.cmb_client)
        form.addRow("Descrição *", self.inp_desc)
        form.addRow("Valor (R$) *", self.spin_amount)
        form.addRow("Vencimento *", self.inp_due)
        form.addRow("Mês referência", self.inp_ref)
        form.addRow("Status", self.cmb_status)
        form.addRow("Data pagamento", self.inp_paid)
        form.addRow("Observações", self.inp_notes)
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

    def _populate(self, fee):
        idx = self.cmb_client.findData(fee["client_id"])
        if idx >= 0:
            self.cmb_client.setCurrentIndex(idx)
        self.inp_desc.setText(fee["description"])
        self.spin_amount.setValue(fee["amount"])
        if fee["due_date"]:
            self.inp_due.setDate(QDate.fromString(fee["due_date"][:10], "yyyy-MM-dd"))
        self.inp_ref.setText(fee["reference_month"] or "")
        si = self.cmb_status.findData(fee["status"])
        if si >= 0:
            self.cmb_status.setCurrentIndex(si)
        if fee["paid_date"]:
            self.inp_paid.setDate(QDate.fromString(fee["paid_date"][:10], "yyyy-MM-dd"))
            self.inp_paid.setEnabled(True)
        self.inp_notes.setPlainText(fee["notes"] or "")

    def _save(self):
        client_id = self.cmb_client.currentData()
        desc = self.inp_desc.text().strip()
        if not client_id or not desc:
            QMessageBox.warning(self, "Atenção", "Cliente e descrição são obrigatórios.")
            return
        amount = self.spin_amount.value()
        if amount <= 0:
            QMessageBox.warning(self, "Atenção", "Valor deve ser maior que zero.")
            return
        status = self.cmb_status.currentData()
        paid_date = self.inp_paid.date().toString("yyyy-MM-dd") if status == "PAGO" else ""
        data = {
            "client_id": client_id,
            "contract_id": self._default_contract_id,
            "description": desc,
            "amount": amount,
            "due_date": self.inp_due.date().toString("yyyy-MM-dd"),
            "paid_date": paid_date,
            "status": status,
            "reference_month": self.inp_ref.text().strip(),
            "notes": self.inp_notes.toPlainText().strip(),
        }
        try:
            if self.fee:
                db.update_fee(self.fee["id"], data)
            else:
                fid = db.create_fee(data)
                # If paid, also register in cash flow
                if status == "PAGO":
                    db.create_cash_flow({
                        "type": "RECEITA",
                        "description": desc,
                        "amount": amount,
                        "date": paid_date or date.today().isoformat(),
                        "category": "Honorários",
                        "client_id": client_id,
                        "fee_id": fid,
                    })
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))
            return
        self.accept()


class CashFlowDialog(QDialog):
    def __init__(self, parent=None, flow_type="RECEITA"):
        super().__init__(parent)
        self.setWindowTitle("Lançar " + ("Receita" if flow_type == "RECEITA" else "Despesa"))
        self.setMinimumWidth(420)
        self.setModal(True)
        self._flow_type = flow_type
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        self.inp_desc = QLineEdit()
        self.spin_amount = QDoubleSpinBox()
        self.spin_amount.setPrefix("R$ ")
        self.spin_amount.setMaximum(9999999.99)
        self.spin_amount.setDecimals(2)
        self.inp_date = QDateEdit()
        self.inp_date.setCalendarPopup(True)
        self.inp_date.setDate(QDate.currentDate())
        self.inp_category = QLineEdit()
        self.inp_category.setPlaceholderText("Ex: Aluguel, Salários, Material...")
        self.cmb_client = QComboBox()
        self.cmb_client.addItem("— Sem cliente —", None)
        for c in db.get_clients(active_only=True):
            self.cmb_client.addItem(c["name"], c["id"])
        self.inp_notes = QTextEdit()
        self.inp_notes.setMaximumHeight(60)

        form.addRow("Descrição *", self.inp_desc)
        form.addRow("Valor *", self.spin_amount)
        form.addRow("Data *", self.inp_date)
        form.addRow("Categoria", self.inp_category)
        form.addRow("Cliente (opcional)", self.cmb_client)
        form.addRow("Observações", self.inp_notes)
        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        lbl = "Lançar Receita" if self._flow_type == "RECEITA" else "Lançar Despesa"
        btn_save = QPushButton(lbl)
        btn_save.setObjectName("btn_success" if self._flow_type == "RECEITA" else "btn_danger")
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _save(self):
        desc = self.inp_desc.text().strip()
        if not desc:
            QMessageBox.warning(self, "Atenção", "Descrição é obrigatória.")
            return
        amount = self.spin_amount.value()
        if amount <= 0:
            QMessageBox.warning(self, "Atenção", "Valor deve ser maior que zero.")
            return
        data = {
            "type": self._flow_type,
            "description": desc,
            "amount": amount,
            "date": self.inp_date.date().toString("yyyy-MM-dd"),
            "category": self.inp_category.text().strip(),
            "client_id": self.cmb_client.currentData(),
            "notes": self.inp_notes.toPlainText().strip(),
        }
        try:
            db.create_cash_flow(data)
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))
            return
        self.accept()


class CommercialWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._build()
        self._load()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # ── Tab 1: Honorários ──
        fee_tab = QWidget()
        fl = QVBoxLayout(fee_tab)
        fl.setContentsMargins(12, 12, 12, 12)
        fl.setSpacing(10)

        fee_toolbar = QHBoxLayout()
        self.inp_fee_search = QLineEdit()
        self.inp_fee_search.setObjectName("search_bar")
        self.inp_fee_search.setPlaceholderText("Buscar cliente, descrição...")
        self.inp_fee_search.textChanged.connect(self._load_fees)
        self.cmb_fee_status = QComboBox()
        self.cmb_fee_status.addItem("Todos", "")
        for key, label in FEE_STATUS.items():
            self.cmb_fee_status.addItem(label, key)
        self.cmb_fee_status.currentIndexChanged.connect(self._load_fees)
        btn_new_fee = QPushButton("+ Novo Honorário")
        btn_new_fee.clicked.connect(self._new_fee)
        btn_pay = QPushButton("Marcar Pago")
        btn_pay.setObjectName("btn_success")
        btn_pay.clicked.connect(self._pay_fee)
        btn_edit_fee = QPushButton("Editar")
        btn_edit_fee.setObjectName("btn_secondary")
        btn_edit_fee.clicked.connect(self._edit_fee)
        fee_toolbar.addWidget(self.inp_fee_search)
        fee_toolbar.addWidget(self.cmb_fee_status)
        fee_toolbar.addStretch()
        fee_toolbar.addWidget(btn_edit_fee)
        fee_toolbar.addWidget(btn_pay)
        fee_toolbar.addWidget(btn_new_fee)
        fl.addLayout(fee_toolbar)

        self.fee_table = QTableWidget()
        self.fee_table.setColumnCount(7)
        self.fee_table.setHorizontalHeaderLabels(
            ["#", "Cliente", "Descrição", "Valor", "Vencimento", "Ref.", "Status"]
        )
        self.fee_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.fee_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.fee_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.fee_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.fee_table.setAlternatingRowColors(True)
        fl.addWidget(self.fee_table)
        tabs.addTab(fee_tab, "Honorários")

        # ── Tab 2: Fluxo de Caixa ──
        cf_tab = QWidget()
        cl = QVBoxLayout(cf_tab)
        cl.setContentsMargins(12, 12, 12, 12)
        cl.setSpacing(10)

        # Summary cards
        self.cards_layout = QHBoxLayout()
        self.lbl_receitas = self._stat_card("Receitas", "R$ 0,00", COLORS["success"])
        self.lbl_despesas = self._stat_card("Despesas", "R$ 0,00", COLORS["danger"])
        self.lbl_saldo = self._stat_card("Saldo", "R$ 0,00", COLORS["navy"])
        self.cards_layout.addWidget(self.lbl_receitas[0])
        self.cards_layout.addWidget(self.lbl_despesas[0])
        self.cards_layout.addWidget(self.lbl_saldo[0])
        cl.addLayout(self.cards_layout)

        cf_toolbar = QHBoxLayout()
        self.inp_cf_from = QDateEdit()
        self.inp_cf_from.setCalendarPopup(True)
        today = QDate.currentDate()
        self.inp_cf_from.setDate(QDate(today.year(), today.month(), 1))
        self.inp_cf_to = QDateEdit()
        self.inp_cf_to.setCalendarPopup(True)
        self.inp_cf_to.setDate(today)
        self.inp_cf_from.dateChanged.connect(self._load_cash_flow)
        self.inp_cf_to.dateChanged.connect(self._load_cash_flow)
        self.cmb_cf_type = QComboBox()
        self.cmb_cf_type.addItem("Todas", "")
        self.cmb_cf_type.addItem("Receitas", "RECEITA")
        self.cmb_cf_type.addItem("Despesas", "DESPESA")
        self.cmb_cf_type.currentIndexChanged.connect(self._load_cash_flow)
        btn_receita = QPushButton("+ Receita")
        btn_receita.setObjectName("btn_success")
        btn_receita.clicked.connect(self._new_receita)
        btn_despesa = QPushButton("+ Despesa")
        btn_despesa.setObjectName("btn_danger")
        btn_despesa.clicked.connect(self._new_despesa)
        cf_toolbar.addWidget(QLabel("De:"))
        cf_toolbar.addWidget(self.inp_cf_from)
        cf_toolbar.addWidget(QLabel("Até:"))
        cf_toolbar.addWidget(self.inp_cf_to)
        cf_toolbar.addWidget(self.cmb_cf_type)
        cf_toolbar.addStretch()
        cf_toolbar.addWidget(btn_receita)
        cf_toolbar.addWidget(btn_despesa)
        cl.addLayout(cf_toolbar)

        self.cf_table = QTableWidget()
        self.cf_table.setColumnCount(6)
        self.cf_table.setHorizontalHeaderLabels(["Data", "Tipo", "Descrição", "Categoria", "Cliente", "Valor"])
        self.cf_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.cf_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.cf_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.cf_table.setAlternatingRowColors(True)
        cl.addWidget(self.cf_table)
        tabs.addTab(cf_tab, "Fluxo de Caixa")

        self.tabs = tabs

    def _stat_card(self, title, value, color):
        frame = QFrame()
        frame.setObjectName("stat_card")
        frame.setStyleSheet(f"""
            QFrame#stat_card {{
                background: white;
                border-left: 4px solid {color};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        fl = QVBoxLayout(frame)
        fl.setSpacing(4)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #7F8C8D; font-size: 12px;")
        lbl_val = QLabel(value)
        lbl_val.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
        fl.addWidget(lbl_title)
        fl.addWidget(lbl_val)
        return frame, lbl_val

    def _load(self):
        self._load_fees()
        self._load_cash_flow()

    def _load_fees(self):
        search = self.inp_fee_search.text().strip()
        status = self.cmb_fee_status.currentData()
        fees = db.get_fees(status=status, search=search)
        self.fee_table.setRowCount(len(fees))
        for i, f in enumerate(fees):
            self.fee_table.setItem(i, 0, QTableWidgetItem(str(f["id"])))
            self.fee_table.setItem(i, 1, QTableWidgetItem(f["client_name"]))
            self.fee_table.setItem(i, 2, QTableWidgetItem(f["description"]))
            val = QTableWidgetItem(_fmt_money(f["amount"]))
            val.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.fee_table.setItem(i, 3, val)
            self.fee_table.setItem(i, 4, QTableWidgetItem(_fmt_date_br(f["due_date"])))
            self.fee_table.setItem(i, 5, QTableWidgetItem(f["reference_month"] or ""))
            status_item = QTableWidgetItem(FEE_STATUS.get(f["status"], f["status"]))
            colors_map = {"PAGO": Qt.GlobalColor.darkGreen, "VENCIDO": Qt.GlobalColor.red,
                          "PENDENTE": Qt.GlobalColor.darkYellow, "CANCELADO": Qt.GlobalColor.gray}
            status_item.setForeground(colors_map.get(f["status"], Qt.GlobalColor.black))
            self.fee_table.setItem(i, 6, status_item)
        self.fee_table.resizeRowsToContents()

    def _load_cash_flow(self):
        date_from = self.inp_cf_from.date().toString("yyyy-MM-dd")
        date_to = self.inp_cf_to.date().toString("yyyy-MM-dd")
        flow_type = self.cmb_cf_type.currentData()
        entries = db.get_cash_flow(date_from=date_from, date_to=date_to, flow_type=flow_type)
        self.cf_table.setRowCount(len(entries))
        for i, e in enumerate(entries):
            self.cf_table.setItem(i, 0, QTableWidgetItem(_fmt_date_br(e["date"])))
            type_item = QTableWidgetItem("Receita" if e["type"] == "RECEITA" else "Despesa")
            type_item.setForeground(
                Qt.GlobalColor.darkGreen if e["type"] == "RECEITA" else Qt.GlobalColor.red
            )
            self.cf_table.setItem(i, 1, type_item)
            self.cf_table.setItem(i, 2, QTableWidgetItem(e["description"]))
            self.cf_table.setItem(i, 3, QTableWidgetItem(e["category"] or ""))
            self.cf_table.setItem(i, 4, QTableWidgetItem(e["client_name"] or ""))
            val = QTableWidgetItem(_fmt_money(e["amount"]))
            val.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            val.setForeground(
                Qt.GlobalColor.darkGreen if e["type"] == "RECEITA" else Qt.GlobalColor.red
            )
            self.cf_table.setItem(i, 5, val)
        self.cf_table.resizeRowsToContents()

        # Update summary
        balance = db.get_balance(date_from=date_from, date_to=date_to)
        self.lbl_receitas[1].setText(_fmt_money(balance["RECEITA"]))
        self.lbl_despesas[1].setText(_fmt_money(balance["DESPESA"]))
        saldo = balance["SALDO"]
        self.lbl_saldo[1].setText(_fmt_money(saldo))
        saldo_color = COLORS["success"] if saldo >= 0 else COLORS["danger"]
        self.lbl_saldo[1].setStyleSheet(f"color: {saldo_color}; font-size: 20px; font-weight: bold;")

    def _fee_selected_id(self):
        row = self.fee_table.currentRow()
        if row < 0:
            return None
        return int(self.fee_table.item(row, 0).text())

    def _new_fee(self):
        dlg = FeeDialog(self)
        if dlg.exec():
            self._load()

    def _edit_fee(self):
        fid = self._fee_selected_id()
        if not fid:
            QMessageBox.information(self, "Selecione", "Selecione um honorário.")
            return
        fee = db.get_fee_by_id(fid)
        dlg = FeeDialog(self, fee=fee)
        if dlg.exec():
            self._load()

    def _pay_fee(self):
        fid = self._fee_selected_id()
        if not fid:
            QMessageBox.information(self, "Selecione", "Selecione um honorário.")
            return
        fee = db.get_fee_by_id(fid)
        if not fee:
            return
        if fee["status"] == "PAGO":
            QMessageBox.information(self, "Já pago", "Este honorário já está marcado como pago.")
            return
        today = date.today().isoformat()
        db.pay_fee(fid, today)
        # Register in cash flow
        db.create_cash_flow({
            "type": "RECEITA",
            "description": fee["description"],
            "amount": fee["amount"],
            "date": today,
            "category": "Honorários",
            "client_id": fee["client_id"],
            "fee_id": fid,
        })
        QMessageBox.information(self, "Pago", "Honorário marcado como pago e lançado no caixa!")
        self._load()

    def _new_receita(self):
        dlg = CashFlowDialog(self, "RECEITA")
        if dlg.exec():
            self._load_cash_flow()

    def _new_despesa(self):
        dlg = CashFlowDialog(self, "DESPESA")
        if dlg.exec():
            self._load_cash_flow()


def _fmt_date_br(d: str) -> str:
    if not d:
        return ""
    try:
        return datetime.strptime(d[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return d


def _fmt_money(v) -> str:
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"
