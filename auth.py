"""auth.py - Kegiatan 4: login dan hak akses peran (Admin / Pemain)."""
import hashlib
import hmac
import os
import re




import data_store

ITERASI_HASH = 100_000
POLA_USERNAME = re.compile(r"[A-Za-z0-9_]{3,20}")
MIN_PASSWORD = 6
PERAN_ADMIN = "admin"
PERAN_PEMAIN = "pemain"


def hash_password(password, garam=None):
    """Kembalikan 'garam$hash' (hex). Password asli tidak pernah disimpan."""
    if garam is None:
        garam = os.urandom(16)
    hasil = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), garam, ITERASI_HASH)
    return garam.hex() + "$" + hasil.hex()


def cek_password(password, tersimpan):
    """True bila password cocok dengan nilai 'garam$hash' yang tersimpan."""
    try:
        garam_hex, hash_hex = tersimpan.split("$")
        garam = bytes.fromhex(garam_hex)
    except ValueError:
        return False
    hasil = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), garam, ITERASI_HASH)
    return hmac.compare_digest(hasil.hex(), hash_hex)


def cari_user(db, username):
    """Cari akun berdasarkan username (tidak membedakan huruf besar/kecil)."""
    for user in db["users"]:
        if user["username"].lower() == username.strip().lower():
            return user
    return None


def cari_user_id(db, user_id):
    for user in db["users"]:
        if user["user_id"] == user_id:
            return user
    return None


def daftar_pemain(db, username, password):
    """Daftarkan akun Pemain baru. Mengembalikan (berhasil, pesan)."""
    username = username.strip()
    if not POLA_USERNAME.fullmatch(username):
        return False, "Username harus 3-20 karakter: huruf, angka, atau garis bawah (_)."
    if len(password) < MIN_PASSWORD:
        return False, f"Password minimal {MIN_PASSWORD} karakter."
    if cari_user(db, username) is not None:
        return False, "Username sudah dipakai. Pilih username lain."
    db["users"].append({
        "user_id": data_store.id_baru("U", db["users"], "user_id"),
        "username": username,
        "password": hash_password(password),
        "role": PERAN_PEMAIN,
    })
    return True, f"Akun pemain '{username}' berhasil dibuat. Silakan masuk."


def login(db, username, password):
    """Kembalikan data akun bila username dan password benar, selain itu None."""
    user = cari_user(db, username)
    if user is not None and cek_password(password, user["password"]):
        return user
    return None


def punya_akses(pengguna, peran):
    """True bila pengguna sudah login dan perannya sesuai."""
    return pengguna is not None and pengguna.get("role") == peran
