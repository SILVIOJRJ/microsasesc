import os
import subprocess
import sys
from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QDialog, QFormLayout, QLineEdit, QComboBox, QTextEdit,
    QMessageBox, QHeaderView, QDoubleSpinBox, QSpinBox, QDateEdit,
    QDialogButtonBox, QSplitter, QFrame, QAbstractItemView,
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from app.database import db
from app.auth import auth
from app.config import OS_STATUS, CLIENTS_DIR
from app.reports.service_order_pdf import generate_os_pdf


class ItemsTable(QWidget):
    total_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        toolbar = QHBoxLayout()
        btn_add = QPushButton("+ Adicionar Item")
        btn_add.setObjectName("btn_success")
        btn_add.clicked.connect(self._add_row)
        btn_del = QPushButton("Remover")
        btn_del.setObjectName("btn_danger")
        btn_del.clicked.connect(self._del_row)
        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_del)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Descrição do Serviço/Item", "Qtd.", "Valor Unit. (R$)", "Total (R$)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setMinimumHeight(180)
        self.table.itemChanged.connect(self._recalc)
        layout.addWidget(self.table)

    def _add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(""))
        self.table.setItem(row, 1, QTableWidgetItem("1"))
        self.table.setItem(row, 2, QTableWidgetItem("0,00"))
        total_item = QTableWidgetItem("R$ 0,00")
        total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 3, total_item)

    def _del_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            self._emit_total()

    def _recalc(self, item):
        if item.column() in (1, 2):
            row = item.row()
            try:
                qty = float(self.table.item(row, 1).text().replace(",", "."))
                price = float(self.table.item(row, 2).text().replace(",", "."))
                total = qty * price
                t_item = self.table.item(row, 3)
                if t_item:
                    t_item.setText(f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            except (ValueError, AttributeError):
                pass
        self._emit_total()

    def _emit_total(self):
        total = self._get_total()
        self.total_changed.emit(total)

    def _get_total(self):
        total = 0.0
        for row in range(self.table.rowCount()):
            try:
                qty = float(self.table.item(row, 1).text().replace(",", "."))
                price = float(self.table.item(row, 2).text().replace(",", "."))
                total += qty * price
            except (ValueError, AttributeError):
                pass
        return total

    def get_items(self):
        items = []
        for row in range(self.table.rowCount()):
            try:
                desc = self.table.item(row, 0).text().strip()
                if not desc:
                    continue
                qty = float(self.table.item(row, 1).text().replace(",", "."))
                price = float(self.table.item(row, 2).text().replace(",", "."))
                total = qty * price
                items.append({"description": desc, "quantity": qty, "unit_price": price, "total": total})
            except (ValueError, AttributeError):
                pass
        return items

    def set_items(self, items):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        for it in items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(it["description"]))
            self.table.setItem(row, 1, QTableWidgetItem(str(it["quantity"]).replace(".", ",")))
            self.table.setItem(row, 2, QTableWidgetItem(f"{it['unit_price']:.2f}".replace(".", ",")))
            t_item = QTableWidgetItem(f"R$ {it['total']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            t_item.setFlags(t_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, t_item)
        self.table.blockSignals(False)
        self._emit_total()


class OrderDialog(QDialog):
    def __init__(self, parent=None, order_id=None):
        super().__init__(parent)
        self.order_id = order_id
        self.setWindowTitle("Nova Ordem de Serviço" if not order_id else "Editar Ordem de Serviço")
        self.setMinimumWidth(800)
        self.setMinimumHeight(700)
        self.setModal(True)
        self._build()
        if order_id:
            self._load_order(order_id)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header row
        header = QHBoxLayout()
        num_label = QLabel("Nº OS:")
        num_label.setStyleSheet("font-weight: bold;")
        self.inp_number = QLineEdit()
        self.inp_number.setReadOnly(True)
        self.inp_number.setFixedWidth(100)
        if not self.order_id:
            self.inp_number.setText(db.next_os_number())

        date_label = QLabel("Data:")
        date_label.setStyleSheet("font-weight: bold;")
        self.inp_date = QDateEdit()
        self.inp_date.setCalendarPopup(True)
        self.inp_date.setDate(QDate.currentDate())
        self.inp_date.setFixedWidth(130)

        status_label = QLabel("Status:")
        status_label.setStyleSheet("font-weight: bold;")
        self.cmb_status = QComboBox()
        for key, label in OS_STATUS.items():
            self.cmb_status.addItem(label, key)
        self.cmb_status.setFixedWidth(130)

        header.addWidget(num_label)
        header.addWidget(self.inp_number)
        header.addWidget(date_label)
        header.addWidget(self.inp_date)
        header.addWidget(status_label)
        header.addWidget(self.cmb_status)
        header.addStretch()
        layout.addLayout(header)

        # Client
        client_row = QHBoxLayout()
        client_lbl = QLabel("Cliente: *")
        client_lbl.setStyleSheet("font-weight: bold;")
        self.cmb_client = QComboBox()
        self.cmb_client.setMinimumWidth(350)
        for c in db.get_clients(active_only=True):
            self.cmb_client.addItem(f"{c['name']}  ({c['cnpj_cpf']})", c["id"])
        client_row.addWidget(client_lbl)
        client_row.addWidget(self.cmb_client)
        client_row.addStretch()
        layout.addLayout(client_row)

        # Description
        desc_lbl = QLabel("Descrição geral do serviço:")
        desc_lbl.setStyleSheet("font-weight: bold;")
        layout.addWidget(desc_lbl)
        self.inp_desc = QTextEdit()
        self.inp_desc.setMaximumHeight(70)
        self.inp_desc.setPlaceholderText("Descreva o serviço prestado...")
        layout.addWidget(self.inp_desc)

        # Items table
        items_lbl = QLabel("Itens / Serviços:")
        items_lbl.setStyleSheet("font-weight: bold;")
        layout.addWidget(items_lbl)
        self.items_table = ItemsTable()
        self.items_table.total_changed.connect(self._update_total)
        layout.addWidget(self.items_table)

        # Totals row
        totals = QHBoxLayout()
        self.spin_discount = QDoubleSpinBox()
        self.spin_discount.setPrefix("Desconto R$ ")
        self.spin_discount.setMaximum(999999.99)
        self.spin_discount.setDecimals(2)
        self.spin_discount.valueChanged.connect(self._update_total)
        self.lbl_subtotal = QLabel("Subtotal: R$ 0,00")
        self.lbl_total = QLabel("TOTAL: R$ 0,00")
        self.lbl_total.setStyleSheet("font-size: 16px; font-weight: bold; color: #1B2A3B;")
        totals.addWidget(self.spin_discount)
        totals.addStretch()
        totals.addWidget(self.lbl_subtotal)
        totals.addWidget(self.lbl_total)
        layout.addLayout(totals)

        # Notes
        notes_lbl = QLabel("Observações / Termos:")
        notes_lbl.setStyleSheet("font-weight: bold;")
        layout.addWidget(notes_lbl)
        self.inp_notes = QTextEdit()
        self.inp_notes.setMaximumHeight(60)
        layout.addWidget(self.inp_notes)

        # Buttons
        btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        self.btn_save_draft = QPushButton("Salvar Rascunho")
        self.btn_save_draft.setObjectName("btn_warning")
        self.btn_save_draft.clicked.connect(lambda: self._save("RASCUNHO"))
        self.btn_save = QPushButton("Emitir OS")
        self.btn_save.clicked.connect(lambda: self._save("EMITIDA"))
        btns.addWidget(btn_cancel)
        btns.addStretch()
        btns.addWidget(self.btn_save_draft)
        btns.addWidget(self.btn_save)
        layout.addLayout(btns)

    def _update_total(self, subtotal=None):
        if subtotal is None:
            subtotal = self.items_table._get_total()
        discount = self.spin_discount.value()
        total = max(0, subtotal - discount)
        self.lbl_subtotal.setText(f"Subtotal: {_fmt_money(subtotal)}")
        self.lbl_total.setText(f"TOTAL: {_fmt_money(total)}")

    def _load_order(self, oid):
        order = db.get_order_by_id(oid)
        if not order:
            return
        self.inp_number.setText(order["number"])
        try:
            d = QDate.fromString(order["date"][:10], "yyyy-MM-dd")
            self.inp_date.setDate(d)
        except Exception:
            pass
        idx = self.cmb_status.findData(order["status"])
        if idx >= 0:
            self.cmb_status.setCurrentIndex(idx)
        ci = self.cmb_client.findData(order["client_id"])
        if ci >= 0:
            self.cmb_client.setCurrentIndex(ci)
        self.inp_desc.setPlainText(order["description"] or "")
        self.inp_notes.setPlainText(order["notes"] or "")
        self.spin_discount.setValue(order["discount"] or 0)
        items = db.get_order_items(oid)
        self.items_table.set_items([dict(it) for it in items])
        self._update_total()

    def _save(self, status_override=None):
        client_id = self.cmb_client.currentData()
        if not client_id:
            QMessageBox.warning(self, "Atenção", "Selecione um cliente.")
            return
        items = self.items_table.get_items()
        if not items:
            QMessageBox.warning(self, "Atenção", "Adicione ao menos um item.")
            return
        status = status_override or self.cmb_status.currentData()
        data = {
            "number": self.inp_number.text(),
            "client_id": client_id,
            "date": self.inp_date.date().toString("yyyy-MM-dd"),
            "description": self.inp_desc.toPlainText().strip(),
            "status": status,
            "discount": self.spin_discount.value(),
            "notes": self.inp_notes.toPlainText().strip(),
        }
        try:
            if self.order_id:
                db.update_order(self.order_id, data, items)
                self._saved_id = self.order_id
            else:
                oid = db.create_order(data, items, auth.current_user()["id"])
                self._saved_id = oid
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))
            return
        self.accept()

    def get_saved_id(self):
        return getattr(self, "_saved_id", None)


class OrdersWidget(QWidget):
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
        self.inp_search.setPlaceholderText("Buscar por cliente, número...")
        self.inp_search.textChanged.connect(self._load)
        self.cmb_status = QComboBox()
        self.cmb_status.addItem("Todos os status", "")
        for key, label in OS_STATUS.items():
            self.cmb_status.addItem(label, key)
        self.cmb_status.currentIndexChanged.connect(self._load)
        btn_new = QPushButton("+ Nova OS")
        btn_new.clicked.connect(self._new_order)
        toolbar.addWidget(self.inp_search)
        toolbar.addWidget(self.cmb_status)
        toolbar.addStretch()
        toolbar.addWidget(btn_new)
        layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Nº", "Cliente", "Data", "Descrição", "Total", "Status", "Criado por"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._edit_order)
        layout.addWidget(self.table)

        # Actions
        action_bar = QHBoxLayout()
        btn_edit = QPushButton("Editar")
        btn_edit.setObjectName("btn_secondary")
        btn_edit.clicked.connect(self._edit_order)
        btn_pdf = QPushButton("Gerar PDF")
        btn_pdf.setObjectName("btn_info")
        btn_pdf.clicked.connect(self._generate_pdf)
        btn_print = QPushButton("Imprimir")
        btn_print.setObjectName("btn_secondary")
        btn_print.clicked.connect(self._print_order)
        btn_fee = QPushButton("Lançar Honorário")
        btn_fee.setObjectName("btn_warning")
        btn_fee.clicked.connect(self._launch_fee)
        action_bar.addStretch()
        action_bar.addWidget(btn_edit)
        action_bar.addWidget(btn_pdf)
        action_bar.addWidget(btn_print)
        action_bar.addWidget(btn_fee)
        layout.addLayout(action_bar)

    def _load(self):
        search = self.inp_search.text().strip()
        status = self.cmb_status.currentData()
        orders = db.get_orders(search=search, status=status)
        self.table.setRowCount(len(orders))
        for i, o in enumerate(orders):
            self.table.setItem(i, 0, QTableWidgetItem(o["number"]))
            self.table.setItem(i, 1, QTableWidgetItem(o["client_name"]))
            self.table.setItem(i, 2, QTableWidgetItem(_fmt_date_br(o["date"])))
            self.table.setItem(i, 3, QTableWidgetItem((o["description"] or "")[:60]))
            total_item = QTableWidgetItem(_fmt_money(o["total"]))
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(i, 4, total_item)
            self.table.setItem(i, 5, QTableWidgetItem(OS_STATUS.get(o["status"], o["status"])))
            self.table.setItem(i, 6, QTableWidgetItem(o["creator"] or ""))
            # Store id in row
            self.table.item(i, 0).setData(Qt.ItemDataRole.UserRole, o["id"])
        self.table.resizeRowsToContents()

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)

    def _new_order(self):
        if not auth.has_role("CONTADOR"):
            QMessageBox.warning(self, "Acesso negado", "Permissão insuficiente.")
            return
        dlg = OrderDialog(self)
        if dlg.exec():
            self._load()
            oid = dlg.get_saved_id()
            if oid:
                reply = QMessageBox.question(
                    self, "Gerar PDF",
                    "OS criada com sucesso! Deseja gerar o PDF agora?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self._generate_pdf_for(oid)

    def _edit_order(self):
        oid = self._selected_id()
        if not oid:
            QMessageBox.information(self, "Selecione", "Selecione uma OS.")
            return
        if not auth.has_role("CONTADOR"):
            QMessageBox.warning(self, "Acesso negado", "Permissão insuficiente.")
            return
        dlg = OrderDialog(self, order_id=oid)
        if dlg.exec():
            self._load()

    def _generate_pdf(self):
        oid = self._selected_id()
        if not oid:
            QMessageBox.information(self, "Selecione", "Selecione uma OS.")
            return
        self._generate_pdf_for(oid)

    def _generate_pdf_for(self, oid):
        order = db.get_order_by_id(oid)
        items = db.get_order_items(oid)
        if not order:
            return
        client_id = order["client_id"]
        # Find client folder
        import glob
        folders = glob.glob(os.path.join(CLIENTS_DIR, f"{client_id}_*"))
        if folders:
            folder = folders[0]
        else:
            folder = os.path.join(CLIENTS_DIR, f"{client_id}_{order['client_name'][:30]}")
            os.makedirs(folder, exist_ok=True)

        filename = f"OS_{order['number']}_{order['date'][:10]}.pdf"
        output_path = os.path.join(folder, filename)
        try:
            generate_os_pdf(dict(order), [dict(it) for it in items], output_path)
            # Register document
            db.create_client_document(
                client_id, filename, output_path, "OS", oid, auth.current_user()["id"]
            )
            QMessageBox.information(self, "PDF Gerado", f"PDF salvo em:\n{output_path}")
            _open_file(output_path)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao gerar PDF", str(e))

    def _print_order(self):
        oid = self._selected_id()
        if not oid:
            QMessageBox.information(self, "Selecione", "Selecione uma OS.")
            return
        self._generate_pdf_for(oid)

    def _launch_fee(self):
        oid = self._selected_id()
        if not oid:
            QMessageBox.information(self, "Selecione", "Selecione uma OS.")
            return
        order = db.get_order_by_id(oid)
        if not order:
            return
        from app.ui.commercial.commercial_widget import FeeDialog
        dlg = FeeDialog(
            self,
            client_id=order["client_id"],
            default_amount=order["total"],
            default_desc=f"OS Nº {order['number']} – {order['client_name']}",
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
