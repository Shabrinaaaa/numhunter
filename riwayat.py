"""riwayat.py - Kegiatan 8 (bagian 1): riwayat soal yang pernah dimainkan pemain."""
from datetime import datetime

import data_store
import game

FORMAT_WAKTU = "%Y-%m-%d %H:%M:%S"


def catat_riwayat(db, state, skor, waktu=None):
    """Catat ronde yang sudah selesai. Mengembalikan catatan, atau None bila
    ronde belum selesai atau sudah pernah dicatat."""
    if state["status"] == game.STATUS_BERJALAN or state.get("tercatat"):
        return None
    waktu = waktu or datetime.now()
    catatan = {
        "riwayat_id": data_store.id_baru("R", db["riwayat"], "riwayat_id"),
        "user_id": state["user_id"],
        "soal_id": state["soal_id"],
        "skor": skor,
        "status": state["status"],
        "jumlah_percobaan": state["jumlah_percobaan"],
        "waktu_main": waktu.strftime(FORMAT_WAKTU),
    }
    db["riwayat"].append(catatan)
    state["tercatat"] = True
    return catatan


def riwayat_pemain(db, user_id, status=None):
    """Riwayat milik satu pemain, terbaru lebih dulu. status: None/'menang'/'kalah'."""
    hasil = []
    for r in db["riwayat"]:
        if r["user_id"] == user_id and (status is None or r["status"] == status):
            hasil.append(r)
    hasil.sort(key=lambda r: (r["waktu_main"], r["riwayat_id"]), reverse=True)
    return hasil


def soal_sudah_dimainkan(db, user_id):
    """Kumpulan soal_id yang pernah dimainkan pemain."""
    return {r["soal_id"] for r in db["riwayat"] if r["user_id"] == user_id}
