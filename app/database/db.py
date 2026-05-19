import sqlite3
import os
from app.config import DB_PATH

_conn = None


def get_conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA foreign_keys = ON")
        _create_tables(_conn)
        _seed_admin(_conn)
    return _conn


def _create_tables(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('ADMIN','GERENTE','CONTADOR','ASSISTENTE')),
        email TEXT DEFAULT '',
        active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        fantasy_name TEXT DEFAULT '',
        cnpj_cpf TEXT UNIQUE NOT NULL,
        type TEXT DEFAULT 'PJ' CHECK(type IN ('PJ','PF')),
        email TEXT DEFAULT '',
        phone TEXT DEFAULT '',
        mobile TEXT DEFAULT '',
        address TEXT DEFAULT '',
        number TEXT DEFAULT '',
        complement TEXT DEFAULT '',
        neighborhood TEXT DEFAULT '',
        city TEXT DEFAULT '',
        state TEXT DEFAULT '',
        zip_code TEXT DEFAULT '',
        contact_person TEXT DEFAULT '',
        regime_tributario TEXT DEFAULT '',
        department_id INTEGER REFERENCES departments(id),
        monthly_fee REAL DEFAULT 0,
        due_day INTEGER DEFAULT 5,
        notes TEXT DEFAULT '',
        active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS service_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        number TEXT NOT NULL UNIQUE,
        client_id INTEGER REFERENCES clients(id),
        date TEXT NOT NULL,
        description TEXT DEFAULT '',
        status TEXT DEFAULT 'EMITIDA',
        subtotal REAL DEFAULT 0,
        discount REAL DEFAULT 0,
        total REAL DEFAULT 0,
        notes TEXT DEFAULT '',
        created_by INTEGER REFERENCES users(id),
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS service_order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER REFERENCES service_orders(id) ON DELETE CASCADE,
        description TEXT NOT NULL,
        quantity REAL DEFAULT 1,
        unit_price REAL DEFAULT 0,
        total REAL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        number TEXT NOT NULL UNIQUE,
        client_id INTEGER REFERENCES clients(id),
        type TEXT DEFAULT 'CONTABIL',
        date TEXT NOT NULL,
        start_date TEXT DEFAULT '',
        monthly_fee REAL DEFAULT 0,
        due_day INTEGER DEFAULT 5,
        content TEXT DEFAULT '',
        status TEXT DEFAULT 'ATIVO',
        created_by INTEGER REFERENCES users(id),
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS fees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER REFERENCES clients(id),
        contract_id INTEGER REFERENCES contracts(id),
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        due_date TEXT NOT NULL,
        paid_date TEXT DEFAULT '',
        status TEXT DEFAULT 'PENDENTE',
        reference_month TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS cash_flow (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL CHECK(type IN ('RECEITA','DESPESA')),
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        date TEXT NOT NULL,
        category TEXT DEFAULT '',
        client_id INTEGER REFERENCES clients(id),
        fee_id INTEGER REFERENCES fees(id),
        notes TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS client_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER REFERENCES clients(id),
        name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        doc_type TEXT DEFAULT 'ATTACHMENT',
        reference_id INTEGER DEFAULT 0,
        created_by INTEGER REFERENCES users(id),
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT DEFAULT ''
    );
    """)
    conn.commit()


def _seed_admin(conn):
    import bcrypt
    row = conn.execute("SELECT id FROM users WHERE username='admin'").fetchone()
    if not row:
        pw = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
        conn.execute(
            "INSERT INTO users (username, password_hash, name, role) VALUES (?,?,?,?)",
            ("admin", pw, "Administrador", "ADMIN"),
        )
        conn.commit()


# ── Users ──────────────────────────────────────────────────────────────────────

def get_users(active_only=False):
    q = "SELECT * FROM users"
    if active_only:
        q += " WHERE active=1"
    q += " ORDER BY name"
    return get_conn().execute(q).fetchall()


def get_user_by_id(uid):
    return get_conn().execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()


def get_user_by_username(username):
    return get_conn().execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()


def create_user(username, password_hash, name, role, email=""):
    conn = get_conn()
    conn.execute(
        "INSERT INTO users (username,password_hash,name,role,email) VALUES (?,?,?,?,?)",
        (username, password_hash, name, role, email),
    )
    conn.commit()


def update_user(uid, name, role, email, active):
    conn = get_conn()
    conn.execute(
        "UPDATE users SET name=?,role=?,email=?,active=? WHERE id=?",
        (name, role, email, active, uid),
    )
    conn.commit()


def update_user_password(uid, password_hash):
    conn = get_conn()
    conn.execute("UPDATE users SET password_hash=? WHERE id=?", (password_hash, uid))
    conn.commit()


# ── Departments ────────────────────────────────────────────────────────────────

def get_departments(active_only=False):
    q = "SELECT * FROM departments"
    if active_only:
        q += " WHERE active=1"
    q += " ORDER BY name"
    return get_conn().execute(q).fetchall()


def get_department_by_id(did):
    return get_conn().execute("SELECT * FROM departments WHERE id=?", (did,)).fetchone()


def create_department(name, description=""):
    conn = get_conn()
    conn.execute("INSERT INTO departments (name,description) VALUES (?,?)", (name, description))
    conn.commit()


def update_department(did, name, description, active):
    conn = get_conn()
    conn.execute(
        "UPDATE departments SET name=?,description=?,active=? WHERE id=?",
        (name, description, active, did),
    )
    conn.commit()


# ── Clients ────────────────────────────────────────────────────────────────────

def get_clients(active_only=False, search=""):
    q = "SELECT c.*, d.name as dept_name FROM clients c LEFT JOIN departments d ON c.department_id=d.id"
    conds = []
    params = []
    if active_only:
        conds.append("c.active=1")
    if search:
        conds.append("(c.name LIKE ? OR c.fantasy_name LIKE ? OR c.cnpj_cpf LIKE ?)")
        params += [f"%{search}%", f"%{search}%", f"%{search}%"]
    if conds:
        q += " WHERE " + " AND ".join(conds)
    q += " ORDER BY c.name"
    return get_conn().execute(q, params).fetchall()


def get_client_by_id(cid):
    return get_conn().execute(
        "SELECT c.*, d.name as dept_name FROM clients c LEFT JOIN departments d ON c.department_id=d.id WHERE c.id=?",
        (cid,),
    ).fetchone()


def create_client(data: dict):
    conn = get_conn()
    conn.execute(
        """INSERT INTO clients
        (name,fantasy_name,cnpj_cpf,type,email,phone,mobile,address,number,complement,
         neighborhood,city,state,zip_code,contact_person,regime_tributario,department_id,
         monthly_fee,due_day,notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            data.get("name", ""),
            data.get("fantasy_name", ""),
            data.get("cnpj_cpf", ""),
            data.get("type", "PJ"),
            data.get("email", ""),
            data.get("phone", ""),
            data.get("mobile", ""),
            data.get("address", ""),
            data.get("number", ""),
            data.get("complement", ""),
            data.get("neighborhood", ""),
            data.get("city", ""),
            data.get("state", ""),
            data.get("zip_code", ""),
            data.get("contact_person", ""),
            data.get("regime_tributario", ""),
            data.get("department_id") or None,
            data.get("monthly_fee", 0),
            data.get("due_day", 5),
            data.get("notes", ""),
        ),
    )
    conn.commit()
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def update_client(cid, data: dict):
    conn = get_conn()
    conn.execute(
        """UPDATE clients SET name=?,fantasy_name=?,cnpj_cpf=?,type=?,email=?,phone=?,mobile=?,
           address=?,number=?,complement=?,neighborhood=?,city=?,state=?,zip_code=?,
           contact_person=?,regime_tributario=?,department_id=?,monthly_fee=?,due_day=?,notes=?,active=?
           WHERE id=?""",
        (
            data.get("name", ""),
            data.get("fantasy_name", ""),
            data.get("cnpj_cpf", ""),
            data.get("type", "PJ"),
            data.get("email", ""),
            data.get("phone", ""),
            data.get("mobile", ""),
            data.get("address", ""),
            data.get("number", ""),
            data.get("complement", ""),
            data.get("neighborhood", ""),
            data.get("city", ""),
            data.get("state", ""),
            data.get("zip_code", ""),
            data.get("contact_person", ""),
            data.get("regime_tributario", ""),
            data.get("department_id") or None,
            data.get("monthly_fee", 0),
            data.get("due_day", 5),
            data.get("notes", ""),
            data.get("active", 1),
            cid,
        ),
    )
    conn.commit()


# ── Service Orders ─────────────────────────────────────────────────────────────

def next_os_number():
    row = get_conn().execute("SELECT MAX(CAST(number AS INTEGER)) FROM service_orders").fetchone()
    return str((row[0] or 0) + 1).zfill(4)


def get_orders(search="", status=""):
    q = """SELECT o.*, c.name as client_name, c.cnpj_cpf, u.name as creator
           FROM service_orders o
           JOIN clients c ON o.client_id=c.id
           LEFT JOIN users u ON o.created_by=u.id"""
    conds = []
    params = []
    if search:
        conds.append("(c.name LIKE ? OR o.number LIKE ?)")
        params += [f"%{search}%", f"%{search}%"]
    if status:
        conds.append("o.status=?")
        params.append(status)
    if conds:
        q += " WHERE " + " AND ".join(conds)
    q += " ORDER BY o.created_at DESC"
    return get_conn().execute(q, params).fetchall()


def get_order_by_id(oid):
    return get_conn().execute(
        """SELECT o.*, c.name as client_name, c.cnpj_cpf, c.email, c.phone,
                  c.address, c.number as addr_number, c.complement, c.neighborhood,
                  c.city, c.state, c.zip_code, c.contact_person, c.regime_tributario,
                  u.name as creator
           FROM service_orders o
           JOIN clients c ON o.client_id=c.id
           LEFT JOIN users u ON o.created_by=u.id
           WHERE o.id=?""",
        (oid,),
    ).fetchone()


def get_order_items(oid):
    return get_conn().execute(
        "SELECT * FROM service_order_items WHERE order_id=? ORDER BY id", (oid,)
    ).fetchall()


def create_order(data: dict, items: list, user_id: int):
    conn = get_conn()
    subtotal = sum(it["total"] for it in items)
    discount = data.get("discount", 0)
    total = subtotal - discount
    conn.execute(
        """INSERT INTO service_orders
           (number,client_id,date,description,status,subtotal,discount,total,notes,created_by)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (
            data["number"],
            data["client_id"],
            data["date"],
            data.get("description", ""),
            data.get("status", "EMITIDA"),
            subtotal,
            discount,
            total,
            data.get("notes", ""),
            user_id,
        ),
    )
    oid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    for it in items:
        conn.execute(
            "INSERT INTO service_order_items (order_id,description,quantity,unit_price,total) VALUES (?,?,?,?,?)",
            (oid, it["description"], it["quantity"], it["unit_price"], it["total"]),
        )
    conn.commit()
    return oid


def update_order_status(oid, status):
    conn = get_conn()
    conn.execute("UPDATE service_orders SET status=? WHERE id=?", (status, oid))
    conn.commit()


def update_order(oid, data: dict, items: list):
    conn = get_conn()
    subtotal = sum(it["total"] for it in items)
    discount = data.get("discount", 0)
    total = subtotal - discount
    conn.execute(
        """UPDATE service_orders SET client_id=?,date=?,description=?,status=?,
           subtotal=?,discount=?,total=?,notes=? WHERE id=?""",
        (
            data["client_id"],
            data["date"],
            data.get("description", ""),
            data.get("status", "EMITIDA"),
            subtotal,
            discount,
            total,
            data.get("notes", ""),
            oid,
        ),
    )
    conn.execute("DELETE FROM service_order_items WHERE order_id=?", (oid,))
    for it in items:
        conn.execute(
            "INSERT INTO service_order_items (order_id,description,quantity,unit_price,total) VALUES (?,?,?,?,?)",
            (oid, it["description"], it["quantity"], it["unit_price"], it["total"]),
        )
    conn.commit()


# ── Contracts ──────────────────────────────────────────────────────────────────

def next_contract_number():
    row = get_conn().execute("SELECT MAX(CAST(number AS INTEGER)) FROM contracts").fetchone()
    return str((row[0] or 0) + 1).zfill(4)


def get_contracts(search="", status=""):
    q = """SELECT ct.*, c.name as client_name, c.cnpj_cpf, u.name as creator
           FROM contracts ct
           JOIN clients c ON ct.client_id=c.id
           LEFT JOIN users u ON ct.created_by=u.id"""
    conds = []
    params = []
    if search:
        conds.append("(c.name LIKE ? OR ct.number LIKE ?)")
        params += [f"%{search}%", f"%{search}%"]
    if status:
        conds.append("ct.status=?")
        params.append(status)
    if conds:
        q += " WHERE " + " AND ".join(conds)
    q += " ORDER BY ct.created_at DESC"
    return get_conn().execute(q, params).fetchall()


def get_contract_by_id(cid):
    return get_conn().execute(
        """SELECT ct.*, c.name as client_name, c.cnpj_cpf, c.email, c.phone,
                  c.address, c.number as addr_number, c.complement, c.neighborhood,
                  c.city, c.state, c.zip_code, c.contact_person, c.type as client_type,
                  u.name as creator
           FROM contracts ct
           JOIN clients c ON ct.client_id=c.id
           LEFT JOIN users u ON ct.created_by=u.id
           WHERE ct.id=?""",
        (cid,),
    ).fetchone()


def create_contract(data: dict, user_id: int):
    conn = get_conn()
    conn.execute(
        """INSERT INTO contracts
           (number,client_id,type,date,start_date,monthly_fee,due_day,content,status,created_by)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (
            data["number"],
            data["client_id"],
            data.get("type", "CONTABIL"),
            data["date"],
            data.get("start_date", ""),
            data.get("monthly_fee", 0),
            data.get("due_day", 5),
            data.get("content", ""),
            data.get("status", "ATIVO"),
            user_id,
        ),
    )
    cid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    return cid


def update_contract(cid, data: dict):
    conn = get_conn()
    conn.execute(
        """UPDATE contracts SET client_id=?,type=?,date=?,start_date=?,monthly_fee=?,
           due_day=?,content=?,status=? WHERE id=?""",
        (
            data["client_id"],
            data.get("type", "CONTABIL"),
            data["date"],
            data.get("start_date", ""),
            data.get("monthly_fee", 0),
            data.get("due_day", 5),
            data.get("content", ""),
            data.get("status", "ATIVO"),
            cid,
        ),
    )
    conn.commit()


# ── Fees ───────────────────────────────────────────────────────────────────────

def get_fees(client_id=None, status="", search=""):
    q = """SELECT f.*, c.name as client_name
           FROM fees f JOIN clients c ON f.client_id=c.id"""
    conds = []
    params = []
    if client_id:
        conds.append("f.client_id=?")
        params.append(client_id)
    if status:
        conds.append("f.status=?")
        params.append(status)
    if search:
        conds.append("(c.name LIKE ? OR f.description LIKE ?)")
        params += [f"%{search}%", f"%{search}%"]
    if conds:
        q += " WHERE " + " AND ".join(conds)
    q += " ORDER BY f.due_date DESC"
    return get_conn().execute(q, params).fetchall()


def get_fee_by_id(fid):
    return get_conn().execute("SELECT * FROM fees WHERE id=?", (fid,)).fetchone()


def create_fee(data: dict):
    conn = get_conn()
    conn.execute(
        """INSERT INTO fees (client_id,contract_id,description,amount,due_date,status,reference_month,notes)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            data["client_id"],
            data.get("contract_id") or None,
            data["description"],
            data["amount"],
            data["due_date"],
            data.get("status", "PENDENTE"),
            data.get("reference_month", ""),
            data.get("notes", ""),
        ),
    )
    fid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    return fid


def update_fee(fid, data: dict):
    conn = get_conn()
    conn.execute(
        """UPDATE fees SET client_id=?,description=?,amount=?,due_date=?,paid_date=?,
           status=?,reference_month=?,notes=? WHERE id=?""",
        (
            data["client_id"],
            data["description"],
            data["amount"],
            data["due_date"],
            data.get("paid_date", ""),
            data.get("status", "PENDENTE"),
            data.get("reference_month", ""),
            data.get("notes", ""),
            fid,
        ),
    )
    conn.commit()


def pay_fee(fid, paid_date):
    conn = get_conn()
    conn.execute(
        "UPDATE fees SET status='PAGO', paid_date=? WHERE id=?", (paid_date, fid)
    )
    conn.commit()


# ── Cash Flow ──────────────────────────────────────────────────────────────────

def get_cash_flow(date_from="", date_to="", flow_type=""):
    q = """SELECT cf.*, c.name as client_name
           FROM cash_flow cf LEFT JOIN clients c ON cf.client_id=c.id"""
    conds = []
    params = []
    if date_from:
        conds.append("cf.date >= ?")
        params.append(date_from)
    if date_to:
        conds.append("cf.date <= ?")
        params.append(date_to)
    if flow_type:
        conds.append("cf.type=?")
        params.append(flow_type)
    if conds:
        q += " WHERE " + " AND ".join(conds)
    q += " ORDER BY cf.date DESC"
    return get_conn().execute(q, params).fetchall()


def create_cash_flow(data: dict):
    conn = get_conn()
    conn.execute(
        """INSERT INTO cash_flow (type,description,amount,date,category,client_id,fee_id,notes)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            data["type"],
            data["description"],
            data["amount"],
            data["date"],
            data.get("category", ""),
            data.get("client_id") or None,
            data.get("fee_id") or None,
            data.get("notes", ""),
        ),
    )
    conn.commit()


def get_balance(date_from="", date_to=""):
    q = "SELECT type, SUM(amount) as total FROM cash_flow"
    conds = []
    params = []
    if date_from:
        conds.append("date >= ?")
        params.append(date_from)
    if date_to:
        conds.append("date <= ?")
        params.append(date_to)
    if conds:
        q += " WHERE " + " AND ".join(conds)
    q += " GROUP BY type"
    rows = get_conn().execute(q, params).fetchall()
    result = {"RECEITA": 0.0, "DESPESA": 0.0}
    for r in rows:
        result[r["type"]] = r["total"] or 0.0
    result["SALDO"] = result["RECEITA"] - result["DESPESA"]
    return result


# ── Client Documents ───────────────────────────────────────────────────────────

def get_client_documents(client_id):
    return get_conn().execute(
        """SELECT cd.*, u.name as creator_name FROM client_documents cd
           LEFT JOIN users u ON cd.created_by=u.id
           WHERE cd.client_id=? ORDER BY cd.created_at DESC""",
        (client_id,),
    ).fetchall()


def create_client_document(client_id, name, file_path, doc_type, reference_id, user_id):
    conn = get_conn()
    conn.execute(
        """INSERT INTO client_documents (client_id,name,file_path,doc_type,reference_id,created_by)
           VALUES (?,?,?,?,?,?)""",
        (client_id, name, file_path, doc_type, reference_id, user_id),
    )
    conn.commit()


def delete_client_document(doc_id):
    conn = get_conn()
    conn.execute("DELETE FROM client_documents WHERE id=?", (doc_id,))
    conn.commit()


# ── Settings ───────────────────────────────────────────────────────────────────

def get_setting(key, default=""):
    row = get_conn().execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row[0] if row else default


def set_setting(key, value):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (key, value))
    conn.commit()
