# backend/locked_files_store.py

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# Maximum files a user can link in Manage Files
MAX_LOCKED_FILES = 20


# ---------- Paths ----------

def _backend_dir() -> str:
    """Absolute path to the backend folder (this file's directory)."""
    return os.path.dirname(os.path.abspath(__file__))

def _users_json_path() -> str:
    """Absolute path to backend/users.json."""
    return os.path.join(_backend_dir(), "users.json")


# ---------- JSON I/O (robust to old/new shapes) ----------

def _load_users_db() -> Dict[str, Any]:
    """
    Load users.json and normalize it to a dict keyed by username.
    Older versions may have stored a list containing a single dict; this handles that.
    """
    path = _users_json_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}

    # Normalize: if it's a list like [ { ...users... } ], unwrap it
    if isinstance(data, list) and data and isinstance(data[0], dict):
        data = data[0]
    if not isinstance(data, dict):
        data = {}
    return data

def _save_users_db(db: Dict[str, Any]) -> None:
    """
    Save users.json in normalized dict form (not a list wrapper).
    Preserves any unrelated user fields (full_name, email, etc.).
    """
    path = _users_json_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

def _ensure_user_node(db: Dict[str, Any], username: str) -> Dict[str, Any]:
    """
    Make sure db[username] exists and has a 'locked_files' list.
    """
    if username not in db or not isinstance(db[username], dict):
        db[username] = {}
    user = db[username]
    if "locked_files" not in user or not isinstance(user["locked_files"], list):
        user["locked_files"] = []
    return user


# ---------- Public API used by UI ----------

def load_locked_files(username: str) -> List[Dict[str, Any]]:
    """
    Return the user's locked files list (may be empty).
    Each item is a dict like:
      {
        "name": "<filename.ext>",
        "path": "C:/full/original/path/filename.ext",
        "added_at": "UTC_ISO_TIMESTAMP",
        "size_bytes": <int or None>
      }
    """
    db = _load_users_db()
    user = db.get(username)
    if not isinstance(user, dict):
        return []
    lf = user.get("locked_files")
    return lf if isinstance(lf, list) else []

def save_locked_files(username: str, items: List[Dict[str, Any]]) -> None:
    """
    Overwrite the user's locked_files with 'items'.
    """
    db = _load_users_db()
    user = _ensure_user_node(db, username)
    user["locked_files"] = list(items or [])
    db[username] = user
    _save_users_db(db)

def append_locked_file(username: str, meta: Dict[str, Any]) -> None:
    """
    Append one file meta to the user's locked_files, respecting MAX_LOCKED_FILES.
    """
    db = _load_users_db()
    user = _ensure_user_node(db, username)
    if len(user["locked_files"]) >= MAX_LOCKED_FILES:
        raise ValueError(f"Limit reached ({MAX_LOCKED_FILES}) for user {username}")
    user["locked_files"].append(meta)
    db[username] = user
    _save_users_db(db)

def remove_locked_file_by_index(username: str, idx: int) -> Optional[Dict[str, Any]]:
    """
    Remove and return the file meta at 'idx'. Returns None if out of range.
    """
    db = _load_users_db()
    user = _ensure_user_node(db, username)
    items = user["locked_files"]
    if 0 <= idx < len(items):
        removed = items.pop(idx)
        db[username] = user
        _save_users_db(db)
        return removed
    return None

def build_meta_for_existing_path(src_path: str) -> Dict[str, Any]:
    """
    Validate and describe an existing file on disk; DO NOT copy it.
    Returns the metadata dict stored in users.json.
    """
    if not src_path or not os.path.isfile(src_path):
        raise ValueError("Selected path is not an existing file.")
    apath = os.path.abspath(src_path)
    try:
        size_bytes = os.path.getsize(apath)
    except Exception:
        size_bytes = None
    return {
        "name": os.path.basename(apath),
        "path": apath,
        "added_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "size_bytes": size_bytes,
    }

def relink_locked_file(username: str, idx: int, new_path: str) -> Dict[str, Any]:
    """
    Replace the file at index 'idx' with metadata built from 'new_path'.
    Useful if a linked file was moved/renamed outside the app.
    Returns the new meta.
    """
    db = _load_users_db()
    user = _ensure_user_node(db, username)
    items = user["locked_files"]
    if not (0 <= idx < len(items)):
        raise IndexError("Index out of range.")

    meta = build_meta_for_existing_path(new_path)
    items[idx] = meta
    db[username] = user
    _save_users_db(db)
    return meta


__all__ = [
    "MAX_LOCKED_FILES",
    "load_locked_files",
    "save_locked_files",
    "append_locked_file",
    "remove_locked_file_by_index",
    "build_meta_for_existing_path",
    "relink_locked_file",
]
