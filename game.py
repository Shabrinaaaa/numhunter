"""game.py - Kegiatan 6: logika permainan hangman angka.

Jawaban soal berupa deretan angka yang awalnya tersembunyi. Pemain menebak satu
digit (0-9) per percobaan. Digit benar terbuka di semua posisinya, digit salah
dicatat dan mengurangi kesempatan. Menang bila semua digit terbuka, kalah bila
kesempatan salah habis. Keadaan satu ronde disimpan di memori (dictionary `state`).
"""
import uuid




import auth
import soal as modul_soal

BATAS_SALAH = 5
STATUS_BERJALAN = "berjalan"
STATUS_MENANG = "menang"
STATUS_KALAH = "kalah"


def mulai_permainan(db, pemain, soal_id, batas_salah=BATAS_SALAH):
    """Buat ronde baru. Mengembalikan (True, state) atau (False, pesan)."""
    if not auth.punya_akses(pemain, auth.PERAN_PEMAIN):
        return False, "Hanya akun Pemain yang dapat bermain."
    s = modul_soal.cari_soal(db, soal_id)
    if s is None:
        return False, "Soal tidak ditemukan."
    state = {
        "game_id": "G" + uuid.uuid4().hex[:8],
        "soal_id": s["soal_id"],
        "user_id": pemain["user_id"],
        "petunjuk": s["petunjuk"],
        "jawaban": s["jawaban"],
        "jumlah_digit": s["jumlah_digit"],
        "tingkat": s["tingkat"],
        "batas_salah": batas_salah,
        "digit_terbuka": [],      # digit yang sudah benar ditebak
        "digit_salah": [],        # digit yang salah ditebak
        "jumlah_percobaan": 0,
        "status": STATUS_BERJALAN,
    }
    return True, state


def tebak_digit(state, masukan):
    """Proses satu tebakan digit.

    Mengembalikan (hasil, pesan); hasil salah satu dari:
    'benar', 'salah', 'sudah_dicoba', 'tidak_valid', 'selesai'.
    Hanya 'benar' dan 'salah' yang dihitung sebagai percobaan.
    """
    if state["status"] != STATUS_BERJALAN:
        return "selesai", "Permainan sudah selesai."
    masukan = str(masukan).strip()
    if len(masukan) != 1 or masukan not in "0123456789":
        return "tidak_valid", "Masukkan satu digit angka (0-9)."
    digit = int(masukan)
    if digit in state["digit_terbuka"] or digit in state["digit_salah"]:
        return "sudah_dicoba", f"Digit {digit} sudah pernah ditebak."

    state["jumlah_percobaan"] += 1
    if masukan in state["jawaban"]:
        state["digit_terbuka"].append(digit)
        posisi = state["jawaban"].count(masukan)
        hasil, pesan = "benar", f"Benar! Digit {digit} ada pada {posisi} posisi."
    else:
        state["digit_salah"].append(digit)
        hasil, pesan = "salah", f"Salah. Digit {digit} tidak ada pada jawaban."
    perbarui_status(state)
    return hasil, pesan


def perbarui_status(state):
    """Tentukan menang atau kalah setelah setiap tebakan."""
    digit_jawaban = {int(c) for c in state["jawaban"]}
    if digit_jawaban.issubset(state["digit_terbuka"]):
        state["status"] = STATUS_MENANG
    elif len(state["digit_salah"]) >= state["batas_salah"]:
        state["status"] = STATUS_KALAH


def menyerah(state):
    """Hentikan ronde yang sedang berjalan dan hitung sebagai kalah."""
    if state["status"] == STATUS_BERJALAN:
        state["status"] = STATUS_KALAH


def tampilan_jawaban(state, buka_semua=False):
    """Contoh: '1 9 _ _'."""
    bagian = []
    for c in state["jawaban"]:
        if buka_semua or int(c) in state["digit_terbuka"]:
            bagian.append(c)
        else:
            bagian.append("_")
    return " ".join(bagian)


def sisa_kesempatan(state):
    return state["batas_salah"] - len(state["digit_salah"])
