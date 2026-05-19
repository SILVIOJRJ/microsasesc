import os
import subprocess
import sys
import glob
from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QDialog, QFormLayout, QLineEdit, QComboBox, QTextEdit,
    QMessageBox, QHeaderView, QDoubleSpinBox, QSpinBox, QDateEdit, QTabWidget,
    QFrame,
)
from PyQt6.QtCore import Qt, QDate
from app.database import db
from app.auth import auth
from app.config import CONTRACT_TYPES, CONTRACT_STATUS, CLIENTS_DIR
from app.reports.contract_pdf import generate_contract_pdf

CONTRACT_DEFAULT_TEMPLATE = """CLÁUSULA 1 – DO PRAZO
O presente contrato é de prazo indeterminado, com início em {{START_DATE}}.

CLÁUSULA 2 – DOS SERVIÇOS CONTRATADOS
O CONTRATADO prestará ao CONTRATANTE os serviços contábeis, fiscais e de departamento pessoal conforme a necessidade e modalidade específica contratada.

CLÁUSULA 3 – DOS HONORÁRIOS
Os honorários mensais pelos serviços contratados ficam estipulados no valor de R$ {{MONTHLY_FEE}}, com vencimento todo dia {{DUE_DAY}} do mês subsequente ao da prestação dos serviços.
§1. O não pagamento dos honorários na data do vencimento sujeitará o CONTRATANTE ao acréscimo de multa moratória de 2% sobre o valor devido, acrescido de juros de 1% ao mês e correção monetária pelo índice oficial aplicável.
§5. O reajuste anual dos honorários ocorrerá no mês de abril, com base na variação acumulada do INPC/IBGE.

CLÁUSULA 4 – DA INADIMPLÊNCIA
O não pagamento de qualquer parcela dos honorários autoriza o CONTRATADO a suspender a prestação dos serviços e ingressar com ação judicial cabível.

CLÁUSULA 5 – DA ENTREGA DE DOCUMENTOS E INFORMAÇÕES
A execução dos serviços dependerá da entrega, pelo CONTRATANTE, de todos os documentos, extratos bancários (PDF e OFX) e informações necessárias, até o dia 10 do mês subsequente. Penalidades decorrentes da negligência do CONTRATANTE são de sua exclusiva responsabilidade.

CLÁUSULA 6 – DA PARALISAÇÃO DAS ATIVIDADES
Caso a empresa CONTRATANTE permaneça paralisada por mais de 3 (três) meses, será cobrada taxa equivalente a 50% dos honorários mensais.

CLÁUSULA 7 – DOS ENCARGOS ANUAIS
O CONTRATANTE pagará anualmente uma mensalidade extra referente à elaboração da DIRPJ/DEFIS, ressarcimento de despesas com impressos e encerramento do balanço anual.

CLÁUSULA 8 – DA RESCISÃO
No caso de rescisão imotivada por qualquer das partes, será devida multa equivalente a 2 (duas) mensalidades. O prazo de aviso prévio é de 60 (sessenta) dias.

CLÁUSULA 9 – DA PROTEÇÃO DE DADOS (LGPD)
Em cumprimento à Lei nº 13.709/2018 (LGPD), as partes comprometem-se a tratar os dados pessoais obtidos em razão deste contrato com responsabilidade e segurança, não compartilhando-os com terceiros, salvo nos casos exigidos por lei.

CLÁUSULA 10 – DO FORO
Fica eleito o foro da Comarca de {{CITY}}/{{STATE}}, domicílio do CONTRATADO, para dirimir quaisquer controvérsias oriundas do presente contrato."""


class ContractDialog(QDialog):
    def __init__(self, parent=None, contract_id=None, default_client_id=None):
        super().__init__(parent)
        self.contract_id = contract_id
        self.default_client_id = default_client_id
        self.setWindowTitle("Novo Contrato" if not contract_id else "Editar Contrato")
        self.setMinimumWidth(860)
        self.setMinimumHeight(680)
        self.setModal(True)
        self._build()
        if contract_id:
            self._load_contract(contract_id)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        tabs = QTabWidget()
        layout.addWidget(tabs)

        # ── Tab 1: Cabeçalho ──
        tab1 = QWidget()
        t1l = QFormLayout(tab1)
        t1l.setSpacing(10)
        t1l.setContentsMargins(16, 16, 16, 16)

        self.inp_number = QLineEdit()
        self.inp_number.setReadOnly(True)
        if not self.contract_id:
            self.inp_number.setText(db.next_contract_number())
        self.inp_date = QDateEdit()
        self.inp_date.setCalendarPopup(True)
        self.inp_date.setDate(QDate.currentDate())
        self.inp_start = QDateEdit()
        self.inp_start.setCalendarPopup(True)
        self.inp_start.setDate(QDate.currentDate())
        self.cmb_client = QComboBox()
        self.cmb_client.setMinimumWidth(320)
        for c in db.get_clients(active_only=True):
            self.cmb_client.addItem(f"{c['name']}  ({c['cnpj_cpf']})", c["id"])
        if self.default_client_id:
            idx = self.cmb_client.findData(self.default_client_id)
            if idx >= 0:
                self.cmb_client.setCurrentIndex(idx)
        self.cmb_type = QComboBox()
        for key, label in CONTRACT_TYPES.items():
            self.cmb_type.addItem(label, key)
        self.spin_fee = QDoubleSpinBox()
        self.spin_fee.setPrefix("R$ ")
        self.spin_fee.setMaximum(999999.99)
        self.spin_fee.setDecimals(2)
        self.spin_due = QSpinBox()
        self.spin_due.setMinimum(1)
        self.spin_due.setMaximum(31)
        self.spin_due.setValue(5)
        self.cmb_status = QComboBox()
        for key, label in CONTRACT_STATUS.items():
            self.cmb_status.addItem(label, key)

        t1l.addRow("Nº Contrato", self.inp_number)
        t1l.addRow("Data de emissão", self.inp_date)
        t1l.addRow("Data de início", self.inp_start)
        t1l.addRow("Cliente *", self.cmb_client)
        t1l.addRow("Modalidade", self.cmb_type)
        t1l.addRow("Honorário mensal", self.spin_fee)
        t1l.addRow("Dia de vencimento", self.spin_due)
        t1l.addRow("Status", self.cmb_status)
        tabs.addTab(tab1, "Dados do Contrato")

        # ── Tab 2: Cláusulas (editor) ──
        tab2 = QWidget()
        t2l = QVBoxLayout(tab2)
        t2l.setContentsMargins(16, 12, 16, 12)
        t2l.setSpacing(8)

        info = QLabel("Edite as cláusulas do contrato abaixo. As variáveis {{START_DATE}}, {{MONTHLY_FEE}}, {{DUE_DAY}} serão substituídas automaticamente ao gerar o PDF.")
        info.setWordWrap(True)
        info.setStyleSheet("color: #7F8C8D; font-size: 11px;")
        t2l.addWidget(info)

        btn_load_template = QPushButton("Carregar Modelo Padrão")
        btn_load_template.setObjectName("btn_secondary")
        btn_load_template.clicked.connect(self._load_template)
        t2l.addWidget(btn_load_template, alignment=Qt.AlignmentFlag.AlignLeft)

        self.txt_content = QTextEdit()
        self.txt_content.setPlaceholderText("Conteúdo do contrato / cláusulas...")
        self.txt_content.setFont(self.txt_content.font())
        t2l.addWidget(self.txt_content)
        tabs.addTab(tab2, "Cláusulas do Contrato")

        # ── Buttons ──
        btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_draft = QPushButton("Salvar Rascunho")
        btn_draft.setObjectName("btn_warning")
        btn_draft.clicked.connect(lambda: self._save("RASCUNHO"))
        btn_save = QPushButton("Salvar e Ativar")
        btn_save.clicked.connect(lambda: self._save("ATIVO"))
        btns.addWidget(btn_cancel)
        btns.addStretch()
        btns.addWidget(btn_draft)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _load_template(self):
        self.txt_content.setPlainText(CONTRACT_DEFAULT_TEMPLATE)

    def _load_contract(self, cid):
        ct = db.get_contract_by_id(cid)
        if not ct:
            return
        self.inp_number.setText(ct["number"])
        self.inp_date.setDate(QDate.fromString(ct["date"][:10], "yyyy-MM-dd"))
        if ct["start_date"]:
            self.inp_start.setDate(QDate.fromString(ct["start_date"][:10], "yyyy-MM-dd"))
        ci = self.cmb_client.findData(ct["client_id"])
        if ci >= 0:
            self.cmb_client.setCurrentIndex(ci)
        ti = self.cmb_type.findData(ct["type"])
        if ti >= 0:
            self.cmb_type.setCurrentIndex(ti)
        self.spin_fee.setValue(ct["monthly_fee"] or 0)
        self.spin_due.setValue(ct["due_day"] or 5)
        si = self.cmb_status.findData(ct["status"])
        if si >= 0:
            self.cmb_status.setCurrentIndex(si)
        self.txt_content.setPlainText(ct["content"] or "")

    def _collect(self, status):
        content = self.txt_content.toPlainText()
        fee = self.spin_fee.value()
        due = self.spin_due.value()
        start = self.inp_start.date().toString("yyyy-MM-dd")
        # Replace template vars
        content = content.replace("{{START_DATE}}", _fmt_date_br(start))
        content = content.replace("{{MONTHLY_FEE}}", _fmt_money(fee))
        content = content.replace("{{DUE_DAY}}", str(due).zfill(2))
        from app.config import ESCRITORIO
        content = content.replace("{{CITY}}", ESCRITORIO.get("cidade", ""))
        content = content.replace("{{STATE}}", ESCRITORIO.get("estado", ""))
        return {
            "number": self.inp_number.text(),
            "client_id": self.cmb_client.currentData(),
            "type": self.cmb_type.currentData(),
            "date": self.inp_date.date().toString("yyyy-MM-dd"),
            "start_date": start,
            "monthly_fee": fee,
            "due_day": due,
            "content": content,
            "status": status,
        }

    def _save(self, status):
        if not self.cmb_client.currentData():
            QMessageBox.warning(self, "Atenção", "Selecione um cliente.")
            return
        data = self._collect(status)
        try:
            if self.contract_id:
                db.update_contract(self.contract_id, data)
                self._saved_id = self.contract_id
            else:
                cid = db.create_contract(data, auth.current_user()["id"])
                self._saved_id = cid
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))
            return
        self.accept()

    def get_saved_id(self):
        return getattr(self, "_saved_id", None)


class ContractsWidget(QWidget):
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
        self.inp_search.setPlaceholderText("Buscar por cliente, número...")
        self.inp_search.textChanged.connect(self._load)
        self.cmb_status = QComboBox()
        self.cmb_status.addItem("Todos", "")
        for key, label in CONTRACT_STATUS.items():
            self.cmb_status.addItem(label, key)
        self.cmb_status.currentIndexChanged.connect(self._load)
        btn_new = QPushButton("+ Novo Contrato")
        btn_new.clicked.connect(self._new_contract)
        toolbar.addWidget(self.inp_search)
        toolbar.addWidget(self.cmb_status)
        toolbar.addStretch()
        toolbar.addWidget(btn_new)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Nº", "Cliente", "Modalidade", "Data", "Honorário", "Status", "Criado por"]
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._edit_contract)
        layout.addWidget(self.table)

        action_bar = QHBoxLayout()
        btn_edit = QPushButton("Editar")
        btn_edit.setObjectName("btn_secondary")
        btn_edit.clicked.connect(self._edit_contract)
        btn_pdf = QPushButton("Gerar PDF")
        btn_pdf.setObjectName("btn_info")
        btn_pdf.clicked.connect(self._generate_pdf)
        btn_fee = QPushButton("Lançar Honorário")
        btn_fee.setObjectName("btn_warning")
        btn_fee.clicked.connect(self._launch_fee)
        action_bar.addStretch()
        action_bar.addWidget(btn_edit)
        action_bar.addWidget(btn_pdf)
        action_bar.addWidget(btn_fee)
        layout.addLayout(action_bar)

    def _load(self):
        search = self.inp_search.text().strip()
        status = self.cmb_status.currentData()
        contracts = db.get_contracts(search=search, status=status)
        self.table.setRowCount(len(contracts))
        for i, c in enumerate(contracts):
            self.table.setItem(i, 0, QTableWidgetItem(c["number"]))
            self.table.setItem(i, 1, QTableWidgetItem(c["client_name"]))
            self.table.setItem(i, 2, QTableWidgetItem(CONTRACT_TYPES.get(c["type"], c["type"])))
            self.table.setItem(i, 3, QTableWidgetItem(_fmt_date_br(c["date"])))
            fee = QTableWidgetItem(_fmt_money(c["monthly_fee"]))
            fee.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 4, fee)
            self.table.setItem(i, 5, QTableWidgetItem(CONTRACT_STATUS.get(c["status"], c["status"])))
            self.table.setItem(i, 6, QTableWidgetItem(c["creator"] or ""))
            self.table.item(i, 0).setData(Qt.ItemDataRole.UserRole, c["id"])
        self.table.resizeRowsToContents()

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

    def _new_contract(self):
        if not auth.has_role("CONTADOR"):
            QMessageBox.warning(self, "Acesso negado", "Permissão insuficiente.")
            return
        dlg = ContractDialog(self)
        if dlg.exec():
            self._load()
            cid = dlg.get_saved_id()
            if cid:
                reply = QMessageBox.question(
                    self, "Gerar PDF",
                    "Contrato salvo! Deseja gerar o PDF agora?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self._generate_pdf_for(cid)

    def _edit_contract(self):
        cid = self._selected_id()
        if not cid:
            QMessageBox.information(self, "Selecione", "Selecione um contrato.")
            return
        if not auth.has_role("CONTADOR"):
            QMessageBox.warning(self, "Acesso negado", "Permissão insuficiente.")
            return
        dlg = ContractDialog(self, contract_id=cid)
        if dlg.exec():
            self._load()

    def _generate_pdf(self):
        cid = self._selected_id()
        if not cid:
            QMessageBox.information(self, "Selecione", "Selecione um contrato.")
            return
        self._generate_pdf_for(cid)

    def _generate_pdf_for(self, cid):
        ct = db.get_contract_by_id(cid)
        if not ct:
            return
        client = db.get_client_by_id(ct["client_id"])
        client_id = ct["client_id"]
        folders = glob.glob(os.path.join(CLIENTS_DIR, f"{client_id}_*"))
        if folders:
            folder = folders[0]
        else:
            folder = os.path.join(CLIENTS_DIR, f"{client_id}_{ct['client_name'][:30]}")
            os.makedirs(folder, exist_ok=True)
        filename = f"CONTRATO_{ct['number']}_{ct['date'][:10]}.pdf"
        output_path = os.path.join(folder, filename)
        try:
            generate_contract_pdf(dict(ct), dict(client), output_path)
            db.create_client_document(
                client_id, filename, output_path, "CONTRACT", cid, auth.current_user()["id"]
            )
            QMessageBox.information(self, "PDF Gerado", f"PDF salvo em:\n{output_path}")
            _open_file(output_path)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao gerar PDF", str(e))

    def _launch_fee(self):
        cid = self._selected_id()
        if not cid:
            QMessageBox.information(self, "Selecione", "Selecione um contrato.")
            return
        ct = db.get_contract_by_id(cid)
        if not ct:
            return
        from app.ui.commercial.commercial_widget import FeeDialog
        dlg = FeeDialog(
            self,
            client_id=ct["client_id"],
            contract_id=cid,
            default_amount=ct["monthly_fee"],
            default_desc=f"Honorário contábil – Contrato Nº {ct['number']}",
        )
        if dlg.exec():
            QMessageBox.information(self, "Honorário", "Honorário lançado com sucesso!")


def _fmt_date_br(d: str) -> str:
    if not d:
        return ""
    try:
        from datetime import datetime
        return datetime.strptime(d[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return d


def _fmt_money(v) -> str:
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def _open_file(path: str):
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])
    except Exception:
        pass
