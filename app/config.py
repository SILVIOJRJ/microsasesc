import os

APP_NAME = "Nascente Soluções Contábeis"
APP_VERSION = "1.0.0"
APP_SHORT = "NSC"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "nascente.db")
CLIENTS_DIR = os.path.join(DATA_DIR, "clientes")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.png")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CLIENTS_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

ROLES = {
    "ADMIN": 4,
    "GERENTE": 3,
    "CONTADOR": 2,
    "ASSISTENTE": 1,
}

ROLE_LABELS = {
    "ADMIN": "Administrador",
    "GERENTE": "Gerente",
    "CONTADOR": "Contador",
    "ASSISTENTE": "Assistente",
}

REGIMES = ["Simples Nacional", "Lucro Presumido", "Lucro Real", "MEI", "Autônomo", "Outro"]

CONTRACT_TYPES = {
    "CONTABIL": "Serviços Contábeis",
    "PESSOAL": "Departamento Pessoal",
    "FISCAL": "Serviços Fiscais",
    "BPO": "BPO Financeiro",
    "ASSESSORIA": "Assessoria Empresarial",
}

OS_STATUS = {
    "RASCUNHO": "Rascunho",
    "EMITIDA": "Emitida",
    "ACEITA": "Aceita",
    "CANCELADA": "Cancelada",
}

CONTRACT_STATUS = {
    "RASCUNHO": "Rascunho",
    "ATIVO": "Ativo",
    "ENCERRADO": "Encerrado",
    "CANCELADO": "Cancelado",
}

FEE_STATUS = {
    "PENDENTE": "Pendente",
    "PAGO": "Pago",
    "VENCIDO": "Vencido",
    "CANCELADO": "Cancelado",
}

COLORS = {
    "gold": "#C8A951",
    "gold_dark": "#9E7D2B",
    "navy": "#1B2A3B",
    "navy_light": "#243447",
    "sidebar_hover": "#2E4057",
    "sidebar_active": "#C8A951",
    "bg": "#F4F6F8",
    "card": "#FFFFFF",
    "border": "#DDE1E7",
    "text": "#2C3E50",
    "text_light": "#7F8C8D",
    "success": "#27AE60",
    "warning": "#F39C12",
    "danger": "#E74C3C",
    "info": "#2980B9",
}

ESCRITORIO = {
    "nome": "Nascente Soluções Contábeis",
    "cnpj": "",
    "crc": "",
    "endereco": "",
    "cidade": "",
    "estado": "PR",
    "cep": "",
    "telefone": "",
    "email": "",
    "responsavel": "",
}
