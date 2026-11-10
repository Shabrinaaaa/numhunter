"""soal.py - Kegiatan 5: kelola soal oleh Admin (tambah, lihat, ubah, hapus).

Soal terdiri dari petunjuk, jawaban berupa angka, dan tingkat (mudah/sedang/sulit).
Jumlah digit dihitung otomatis; bila tingkat tidak diisi, dipilih otomatis dari jumlah digit.
"""
import auth
import data_store

MIN_DIGIT = 2
MAX_DIGIT = 10
MAKS_PETUNJUK = 150
TINGKAT = data_store.TINGKAT
PESAN_DITOLAK = "Akses ditolak: hanya Admin yang dapat mengelola soal."


def validasi_soal(petunjuk, jawaban, tingkat=None):
    """Periksa isi soal. Mengembalikan (valid, pesan_kesalahan)."""
    if not petunjuk.strip():
        return False, "Petunjuk soal tidak boleh kosong."
    if len(petunjuk.strip()) > MAKS_PETUNJUK:
        return False, f"Petunjuk soal maksimal {MAKS_PETUNJUK} karakter."
    jawaban = jawaban.strip()
    if not (jawaban.isascii() and jawaban.isdigit()):
        return False, "Jawaban hanya boleh berisi angka 0-9, tanpa spasi atau huruf."
    if not MIN_DIGIT <= len(jawaban) <= MAX_DIGIT:
        return False, f"Jawaban harus {MIN_DIGIT}-{MAX_DIGIT} digit."
    if tingkat is not None and tingkat not in TINGKAT:
        return False, "Tingkat harus mudah, sedang, atau sulit."
    return True, ""


def daftar_soal(db, tingkat=None):
    """Soal urut berdasarkan soal_id; tingkat=None berarti semua tingkat."""
    hasil = [s for s in db["soal"] if tingkat is None or s["tingkat"] == tingkat]
    return sorted(hasil, key=lambda s: s["soal_id"])


def cari_soal(db, soal_id):
    for s in db["soal"]:
        if s["soal_id"].lower() == soal_id.strip().lower():
            return s
    return None


def _petunjuk_sudah_ada(db, petunjuk, kecuali_id=None):
    for s in db["soal"]:
        if s["soal_id"] != kecuali_id and s["petunjuk"].lower() == petunjuk.strip().lower():
            return True
    return False


def tambah_soal(db, pengguna, petunjuk, jawaban, tingkat=None):
    """Tambah soal baru. Mengembalikan (berhasil, pesan)."""
    if not auth.punya_akses(pengguna, auth.PERAN_ADMIN):
        return False, PESAN_DITOLAK
    valid, pesan = validasi_soal(petunjuk, jawaban, tingkat)
    if not valid:
        return False, pesan
    if _petunjuk_sudah_ada(db, petunjuk):
        return False, "Soal dengan petunjuk yang sama sudah ada."
    soal_baru = {
        "soal_id": data_store.id_baru("S", db["soal"], "soal_id"),
        "petunjuk": petunjuk.strip(),
        "jawaban": jawaban.strip(),
        "jumlah_digit": len(jawaban.strip()),
        "tingkat": tingkat or data_store.tingkat_otomatis(len(jawaban.strip())),
        "dibuat_oleh": pengguna["user_id"],
    }
    db["soal"].append(soal_baru)
    return True, f"Soal {soal_baru['soal_id']} berhasil ditambahkan ({soal_baru['jumlah_digit']} digit, {soal_baru['tingkat']})."


def ubah_soal(db, pengguna, soal_id, petunjuk=None, jawaban=None, tingkat=None):
    """Ubah petunjuk, jawaban, dan/atau tingkat. Nilai None berarti tidak diubah."""
    if not auth.punya_akses(pengguna, auth.PERAN_ADMIN):
        return False, PESAN_DITOLAK
    s = cari_soal(db, soal_id)
    if s is None:
        return False, "Soal tidak ditemukan."
    if petunjuk is None and jawaban is None and tingkat is None:
        return False, "Tidak ada perubahan."
    petunjuk_baru = s["petunjuk"] if petunjuk is None else petunjuk
    jawaban_baru = s["jawaban"] if jawaban is None else jawaban
    valid, pesan = validasi_soal(petunjuk_baru, jawaban_baru, tingkat)
    if not valid:
        return False, pesan
    if _petunjuk_sudah_ada(db, petunjuk_baru, kecuali_id=s["soal_id"]):
        return False, "Soal dengan petunjuk yang sama sudah ada."
    s["petunjuk"] = petunjuk_baru.strip()
    s["jawaban"] = jawaban_baru.strip()
    s["jumlah_digit"] = len(s["jawaban"])
    if tingkat is not None:
        s["tingkat"] = tingkat
    return True, f"Soal {s['soal_id']} berhasil diubah."


def hapus_soal(db, pengguna, soal_id):
    """Hapus soal. Riwayat permainan lama tetap disimpan."""
    if not auth.punya_akses(pengguna, auth.PERAN_ADMIN):
        return False, PESAN_DITOLAK
    s = cari_soal(db, soal_id)
    if s is None:
        return False, "Soal tidak ditemukan."
    db["soal"].remove(s)
    return True, f"Soal {s['soal_id']} berhasil dihapus."
