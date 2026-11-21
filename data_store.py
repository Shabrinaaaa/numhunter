"""data_store.py - Penghubung NumHunter dengan PostgreSQL.

Data aplikasi disimpan di PostgreSQL melalui konfigurasi pada db.py.
Dictionary tetap dipakai oleh modul logika agar alur program tidak berubah.
"""
from datetime import datetime

import db as database

TINGKAT = ("mudah", "sedang", "sulit")
SOAL_AWAL = [
    ("Berapa nomor telepon darurat polisi di Indonesia", "110", "mudah"),
    ("Berapa hasil dari dua belas dikali dua belas", "144", "mudah"),
    ("Berapa jumlah jam dalam satu minggu", "168", "mudah"),
    ("Berapa jumlah hari dalam satu tahun biasa bukan kabisat", "365", "mudah"),
    ("Tahun berapa Indonesia merdeka", "1945", "sedang"),
    ("Tahun berapa Sumpah Pemuda diikrarkan", "1928", "sedang"),
    ("Berapa menit dalam satu hari", "1440", "sedang"),
    ("Berapa detik dalam satu jam", "3600", "sedang"),
    ("Berapa detik dalam satu hari", "86400", "sulit"),
    ("Berapa hasil dari dua pangkat enam belas", "65536", "sulit"),
    ("Berapa hasil dari sembilan ratus sembilan puluh sembilan dikali sembilan ratus sembilan puluh sembilan",
     "998001", "sulit"),
]
USERNAME_ADMIN_AWAL = "admin"
PASSWORD_ADMIN_AWAL = "admin123"


def tingkat_otomatis(jumlah_digit):
    if jumlah_digit <= 3:
        return "mudah"
    if jumlah_digit == 4:
        return "sedang"
    return "sulit"


def id_baru(prefix, daftar, kunci):
    terbesar = 0
    for item in daftar:
        angka = str(item[kunci])[len(prefix):]
        if angka.isdigit() and int(angka) > terbesar:
            terbesar = int(angka)
    return f"{prefix}{terbesar + 1:03d}"


def buat_data_awal():
    """Data lokal untuk pengujian logika; bukan penyimpanan aplikasi."""
    import auth
    data = {"users": [], "soal": [], "riwayat": []}
    data["users"].append({
        "user_id": "U001", "username": USERNAME_ADMIN_AWAL,
        "password": auth.hash_password(PASSWORD_ADMIN_AWAL), "role": "admin",
    })
    for petunjuk, jawaban, tingkat in SOAL_AWAL:
        data["soal"].append({
            "soal_id": id_baru("S", data["soal"], "soal_id"),
            "petunjuk": petunjuk, "jawaban": jawaban,
            "jumlah_digit": len(jawaban), "tingkat": tingkat,
            "dibuat_oleh": "U001",
        })
    return data


def _ambil_semua():
    database.pastikan_database()
    conn = database.koneksi()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id, username, password, role FROM users ORDER BY user_id")
            users = [dict(x) for x in cur.fetchall()]
            cur.execute(
                "SELECT soal_id, petunjuk, jawaban, jumlah_digit, tingkat, dibuat_oleh "
                "FROM soal ORDER BY soal_id")
            soal = [dict(x) for x in cur.fetchall()]
            cur.execute(
                "SELECT riwayat_id, user_id, soal_id, skor, status, jumlah_percobaan, waktu_main "
                "FROM riwayat ORDER BY waktu_main, riwayat_id")
            riwayat = []
            for item in cur.fetchall():
                baris = dict(item)
                waktu = baris["waktu_main"]
                if isinstance(waktu, datetime):
                    baris["waktu_main"] = waktu.strftime("%Y-%m-%d %H:%M:%S")
                riwayat.append(baris)
        return {"users": users, "soal": soal, "riwayat": riwayat}
    finally:
        conn.close()


def muat_data(path=None):
    """Ambil semua data langsung dari PostgreSQL. Parameter path diabaikan."""
    return _ambil_semua()


def simpan_data(data, path=None):
    """Simpan perubahan dictionary ke PostgreSQL menggunakan UPSERT.

    Data yang sudah ada diperbarui, data baru ditambahkan, dan baris yang
    dihapus dari dictionary dihapus dari tabel terkait.
    """
    conn = database.koneksi()
    try:
        with conn.cursor() as cur:
            # Akun disimpan lebih dulu karena soal dan riwayat memiliki foreign key.
            for u in data["users"]:
                cur.execute(
                    """INSERT INTO users (user_id, username, password, role)
                       VALUES (%s, %s, %s, %s)
                       ON CONFLICT (user_id) DO UPDATE SET
                       username = EXCLUDED.username, password = EXCLUDED.password,
                       role = EXCLUDED.role""",
                    (u["user_id"], u["username"], u["password"], u["role"]))

            for s in data["soal"]:
                cur.execute(
                    """INSERT INTO soal (soal_id, petunjuk, jawaban, tingkat, dibuat_oleh)
                       VALUES (%s, %s, %s, %s, %s)
                       ON CONFLICT (soal_id) DO UPDATE SET
                       petunjuk = EXCLUDED.petunjuk, jawaban = EXCLUDED.jawaban,
                       tingkat = EXCLUDED.tingkat, dibuat_oleh = EXCLUDED.dibuat_oleh""",
                    (s["soal_id"], s["petunjuk"], s["jawaban"], s["tingkat"],
                     s.get("dibuat_oleh")))

            id_soal_tersedia = {s["soal_id"] for s in data["soal"]}
            for r in data["riwayat"]:
                if r.get("soal_id") not in id_soal_tersedia:
                    r["soal_id"] = None
                cur.execute(
                    """INSERT INTO riwayat
                       (riwayat_id, user_id, soal_id, skor, status, jumlah_percobaan, waktu_main)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (riwayat_id) DO UPDATE SET
                       user_id = EXCLUDED.user_id, soal_id = EXCLUDED.soal_id,
                       skor = EXCLUDED.skor, status = EXCLUDED.status,
                       jumlah_percobaan = EXCLUDED.jumlah_percobaan,
                       waktu_main = EXCLUDED.waktu_main""",
                    (r["riwayat_id"], r["user_id"], r.get("soal_id"), r["skor"],
                     r["status"], r["jumlah_percobaan"], r["waktu_main"]))

            # Hapus catatan yang memang sudah dihapus dari data aplikasi.
            for nama, tabel, kolom in (
                ("riwayat", "riwayat", "riwayat_id"),
                ("soal", "soal", "soal_id"),
                ("users", "users", "user_id"),
            ):
                ids = [baris[kolom] for baris in data[nama]]
                if ids:
                    cur.execute(
                        f"DELETE FROM {tabel} WHERE {kolom} <> ALL(%s)", (ids,))
                else:
                    cur.execute(f"DELETE FROM {tabel}")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
