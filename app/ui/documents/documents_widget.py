import os
import sys
import subprocess
import shutil
import glob
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QComboBox, QLineEdit, QMessageBox, QHeaderView,
    QFileDialog, QFrame, QSplitter,
)
from PyQt6.QtCore import Qt
from app.database import db
from app.auth import auth
from app.config import CLIENTS_DIR


class DocumentsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._current_client_id = None
        self._build()
        self._load_clients()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Client selector
        top = QHBoxLayout()
        top.addWidget(QLabel("Cliente:"))
        self.cmb_client = QComboBox()
        self.cmb_client.setMinimumWidth(350)
        self.cmb_client.currentIndexChanged.connect(self._client_changed)
        top.addWidget(self.cmb_client)
        top.addStretch()
        btn_folder = QPushButton("Abrir Pasta")
        btn_folder.setObjectName("btn_secondary")
        btn_folder.clicked.connect(self._open_folder)
        top.addWidget(btn_folder)
        layout.addLayout(top)

        # Actions bar
        action_bar = QHBoxLayout()
        btn_attach = QPushButton("Anexar Documento")
        btn_attach.clicked.connect(self._attach_doc)
        btn_delete = QPushButton("Remover")
        btn_delete.setObjectName("btn_danger")
        btn_delete.clicked.connect(self._delete_doc)
        btn_open = QPushButton("Abrir Arquivo")
        btn_open.setObjectName("btn_info")
        btn_open.clicked.connect(self._open_doc)
        action_bar.addWidget(btn_attach)
        action_bar.addWidget(btn_open)
        action_bar.addWidget(btn_delete)
        action_bar.addStretch()
        layout.addLayout(action_bar)

        # Documents table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["#", "Nome", "Tipo", "Adicionado por", "Data"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._open_doc)
        layout.addWidget(self.table)

        # Info
        info = QLabel("Dica: Faça duplo clique em um arquivo para abri-lo. Os documentos gerados (OS e Contratos) são salvos automaticamente aqui.")
        info.setStyleSheet("color: #7F8C8D; font-size: 11px;")
        info.setWordWrap(True)
        layout.addWidget(info)

    def _load_clients(self):
        self.cmb_client.blockSignals(True)
        self.cmb_client.clear()
        self.cmb_client.addItem("— Selecione um cliente —", None)
        for c in db.get_clients(active_only=True):
            self.cmb_client.addItem(f"{c['name']}  ({c['cnpj_cpf']})", c["id"])
        self.cmb_client.blockSignals(False)

    def select_client(self, client_id: int):
        idx = self.cmb_client.findData(client_id)
        if idx >= 0:
            self.cmb_client.setCurrentIndex(idx)

    def _client_changed(self):
        self._current_client_id = self.cmb_client.currentData()
        self._load_docs()

    def _load_docs(self):
        if not self._current_client_id:
            self.table.setRowCount(0)
            return
        docs = db.get_client_documents(self._current_client_id)
        self.table.setRowCount(len(docs))
        type_labels = {"OS": "Ordem de Serviço", "CONTRACT": "Contrato", "ATTACHMENT": "Anexo"}
        for i, d in enumerate(docs):
            self.table.setItem(i, 0, QTableWidgetItem(str(d["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(d["name"]))
            self.table.setItem(i, 2, QTableWidgetItem(type_labels.get(d["doc_type"], d["doc_type"])))
            self.table.setItem(i, 3, QTableWidgetItem(d["creator_name"] or ""))
            self.table.setItem(i, 4, QTableWidgetItem(_fmt_datetime(d["created_at"])))
            self.table.item(i, 0).setData(Qt.ItemDataRole.UserRole, d["file_path"])
        self.table.resizeRowsToContents()

    def _selected_path(self):
        row = self.table.currentRow()
        if row < 0:
            return None, None
        doc_id = int(self.table.item(row, 0).text())
        path = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        return doc_id, path

    def _attach_doc(self):
        if not self._current_client_id:
            QMessageBox.information(self, "Selecione", "Selecione um cliente primeiro.")
            return
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Selecionar arquivo(s)", "",
            "Documentos (*.pdf *.doc *.docx *.xls *.xlsx *.png *.jpg *.jpeg *.txt);;Todos (*)",
        )
        if not paths:
            return

        # Get or create client folder
        folders = glob.glob(os.path.join(CLIENTS_DIR, f"{self._current_client_id}_*"))
        if folders:
            folder = folders[0]
        else:
            client = db.get_client_by_id(self._current_client_id)
            folder = os.path.join(CLIENTS_DIR, f"{self._current_client_id}_{client['name'][:30]}")
            os.makedirs(folder, exist_ok=True)

        for src_path in paths:
            filename = os.path.basename(src_path)
            dest_path = os.path.join(folder, filename)
            if os.path.abspath(src_path) != os.path.abspath(dest_path):
                shutil.copy2(src_path, dest_path)
            db.create_client_document(
                self._current_client_id,
                filename,
                dest_path,
                "ATTACHMENT",
                0,
                auth.current_user()["id"],
            )
        self._load_docs()
        QMessageBox.information(self, "Anexado", f"{len(paths)} arquivo(s) anexado(s) com sucesso.")

    def _delete_doc(self):
        doc_id, path = self._selected_path()
        if not doc_id:
            QMessageBox.information(self, "Selecione", "Selecione um documento.")
            return
        reply = QMessageBox.question(
            self, "Confirmar",
            "Remover este documento do sistema?\n(O arquivo físico não será deletado.)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_client_document(doc_id)
            self._load_docs()

    def _open_doc(self):
        _, path = self._selected_path()
        if not path:
            QMessageBox.information(self, "Selecione", "Selecione um documento.")
            return
        if not os.path.exists(path):
            QMessageBox.warning(self, "Arquivo não encontrado", f"O arquivo não foi encontrado:\n{path}")
            return
        _open_file(path)

    def _open_folder(self):
        if not self._current_client_id:
            QMessageBox.information(self, "Selecione", "Selecione um cliente.")
            return
        folders = glob.glob(os.path.join(CLIENTS_DIR, f"{self._current_client_id}_*"))
        if folders:
            folder = folders[0]
        else:
            client = db.get_client_by_id(self._current_client_id)
            folder = os.path.join(CLIENTS_DIR, f"{self._current_client_id}_{client['name'][:30]}")
            os.makedirs(folder, exist_ok=True)
        _open_file(folder)


def _fmt_datetime(dt: str) -> str:
    if not dt:
        return ""
    try:
        from datetime import datetime
        return datetime.strptime(dt[:19], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
    except Exception:
        return dt[:10]


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
