"""data_store.py - Kegiatan 3: struktur data dan data awal.

"Database aplikasi" berupa satu file JSON (data/db.json) yang berisi tiga daftar:
    users    : akun Admin dan Pemain
    soal     : bank soal hangman angka
    riwayat  : catatan setiap ronde permainan yang sudah selesai
Seluruh modul lain bekerja pada dictionary `db` di memori; hanya modul ini
(dan main.py) yang membaca atau menulis file.
"""
import json
import os






FOLDER_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
PATH_DB = os.path.join(FOLDER_DATA, "db.json")

# Tingkatan soal. Bukan level bertahap: pemain bebas memilih tingkat mana saja.
TINGKAT = ("mudah", "sedang", "sulit")


def tingkat_otomatis(jumlah_digit):
    """Saran tingkat dari jumlah digit: sampai 3 mudah, 4 sedang, 5 ke atas sulit."""
    if jumlah_digit <= 3:
        return "mudah"
    if jumlah_digit == 4:
        return "sedang"
    return "sulit"


# Contoh soal awal: (petunjuk, jawaban berupa angka, tingkat)
SOAL_AWAL = [
    ("Berapa nomor telepon darurat Polisi di Indonesia?", "110", "mudah"),
    ("Berapa hasil dari 12 dikali 12?", "144", "mudah"),
    ("Berapa jumlah jam dalam satu minggu?", "168", "mudah"),
    ("Berapa jumlah hari dalam satu tahun biasa (bukan kabisat)?", "365", "mudah"),
    ("Tahun berapa Indonesia merdeka?", "1945", "sedang"),
    ("Tahun berapa Sumpah Pemuda diikrarkan?", "1928", "sedang"),
    ("Berapa menit dalam satu hari?", "1440", "sedang"),
    ("Berapa detik dalam satu jam?", "3600", "sedang"),
    ("Berapa detik dalam satu hari?", "86400", "sulit"),
    ("Berapa hasil dari 2 pangkat 16?", "65536", "sulit"),
    ("Berapa hasil dari 999 dikali 999?", "998001", "sulit"),
]

USERNAME_ADMIN_AWAL = "admin"
PASSWORD_ADMIN_AWAL = "admin123"


def id_baru(prefix, daftar, kunci):
    """Buat id berurutan (mis. S001, S002, ...) dari id terbesar yang sudah ada."""
    terbesar = 0
    for item in daftar:
        angka = item[kunci][len(prefix):]
        if angka.isdigit() and int(angka) > terbesar:
            terbesar = int(angka)
    return f"{prefix}{terbesar + 1:03d}"


def buat_data_awal():
    """Data awal: satu akun Admin dan beberapa contoh soal."""
    # Diimpor di sini agar tidak terjadi impor melingkar (auth memakai id_baru).
    import auth

    db = {"users": [], "soal": [], "riwayat": []}
    db["users"].append({
        "user_id": "U001",
        "username": USERNAME_ADMIN_AWAL,
        "password": auth.hash_password(PASSWORD_ADMIN_AWAL),
        "role": "admin",
    })
    for petunjuk, jawaban, tingkat in SOAL_AWAL:
        db["soal"].append({
            "soal_id": id_baru("S", db["soal"], "soal_id"),
            "petunjuk": petunjuk,
            "jawaban": jawaban,
            "jumlah_digit": len(jawaban),
            "tingkat": tingkat,
            "dibuat_oleh": "U001",
        })
    return db


def simpan_data(db, path=PATH_DB):
    """Simpan db ke file. Ditulis ke file sementara dulu agar data tidak rusak bila terhenti."""
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    sementara = path + ".tmp"
    with open(sementara, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    os.replace(sementara, path)


def muat_data(path=PATH_DB):
    """Muat db dari file. Jika file belum ada atau rusak, dibuat ulang dari data awal."""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                db = json.load(f)
            for kunci in ("users", "soal", "riwayat"):
                if not isinstance(db.get(kunci), list):
                    raise ValueError(f"Bagian '{kunci}' tidak valid")
            for item in db["soal"]:   # data lama tanpa tingkat
                item.setdefault("tingkat", tingkat_otomatis(len(item["jawaban"])))
            return db
        except (json.JSONDecodeError, ValueError, AttributeError, OSError):
            # Simpan file rusak sebagai cadangan, lalu mulai dari data awal.
            try:
                os.replace(path, path + ".rusak")
            except OSError:
                pass
    db = buat_data_awal()
    simpan_data(db, path)
    return db
