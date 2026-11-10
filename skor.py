"""skor.py - Kegiatan 7: sistem skor berbasis jumlah percobaan dan hasil ronde.

Aturan:
  - Kalah (termasuk menyerah) -> skor 0.
  - Menang -> skor awal 100, dikurangi 10 untuk setiap percobaan yang melebihi
    percobaan minimum. Percobaan minimum = banyak digit berbeda pada jawaban
    (semua tebakan langsung benar).
Semakin sedikit percobaan yang dipakai, semakin tinggi skor.
"""
SKOR_AWAL = 100
PENALTI_PER_PERCOBAAN = 10


def percobaan_minimum(jawaban):
    """Percobaan paling sedikit untuk membuka jawaban (satu per digit berbeda)."""
    return len(set(jawaban))


def rincian_skor(state):
    """Hitung skor ronde dan rinciannya dalam bentuk dictionary."""
    minimum = percobaan_minimum(state["jawaban"])
    berlebih = max(0, state["jumlah_percobaan"] - minimum)
    penalti = berlebih * PENALTI_PER_PERCOBAAN
    if state["status"] == "menang":
        nilai = max(0, SKOR_AWAL - penalti)
    else:
        nilai = 0
    return {
        "status": state["status"],
        "jumlah_percobaan": state["jumlah_percobaan"],
        "percobaan_minimum": minimum,
        "percobaan_berlebih": berlebih,
        "penalti": penalti,
        "skor": nilai,
    }


def hitung_skor(state):
    return rincian_skor(state)["skor"]
