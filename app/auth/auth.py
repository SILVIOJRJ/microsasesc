import bcrypt
from app.database import db
from app.config import ROLES

_current_user = None


def login(username: str, password: str):
    global _current_user
    user = db.get_user_by_username(username)
    if not user or not user["active"]:
        return False
    if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        _current_user = dict(user)
        return True
    return False


def logout():
    global _current_user
    _current_user = None


def current_user():
    return _current_user


def has_role(min_role: str) -> bool:
    if not _current_user:
        return False
    return ROLES.get(_current_user["role"], 0) >= ROLES.get(min_role, 0)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
