"""leaderboard.py - Kegiatan 8 (bagian 2): leaderboard harian, mingguan, bulanan, tahunan.

Leaderboard tidak disimpan terpisah. Setiap kali dibuka, total skor tiap pemain
dihitung ulang dari riwayat yang tanggalnya berada dalam periode yang dipilih.
"""
import calendar
from datetime import date, datetime, timedelta

import auth

PERIODE = ("harian", "mingguan", "bulanan", "tahunan")
FORMAT_WAKTU = "%Y-%m-%d %H:%M:%S"
BULAN_SINGKAT = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
BULAN_PENUH = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
               "Agustus", "September", "Oktober", "November", "Desember"]


def _ke_tanggal(acuan):
    if acuan is None:
        return date.today()
    if isinstance(acuan, datetime):
        return acuan.date()
    return acuan


def format_tanggal(tgl):
    return f"{tgl.day} {BULAN_SINGKAT[tgl.month - 1]} {tgl.year}"


def rentang_periode(periode, acuan=None):
    """Kembalikan (tanggal_awal, tanggal_akhir) periode yang memuat tanggal acuan.

    Minggu dihitung Senin sampai Minggu; bulan dan tahun menurut kalender.
    """
    acuan = _ke_tanggal(acuan)
    if periode == "harian":
        return acuan, acuan
    if periode == "mingguan":
        senin = acuan - timedelta(days=acuan.weekday())
        return senin, senin + timedelta(days=6)
    if periode == "bulanan":
        hari_terakhir = calendar.monthrange(acuan.year, acuan.month)[1]
        return date(acuan.year, acuan.month, 1), date(acuan.year, acuan.month, hari_terakhir)
    if periode == "tahunan":
        return date(acuan.year, 1, 1), date(acuan.year, 12, 31)
    raise ValueError(f"Periode tidak dikenal: {periode}")


def label_periode(periode, acuan=None):
    """Teks judul periode untuk ditampilkan."""
    awal, akhir = rentang_periode(periode, acuan)
    if periode == "harian":
        return f"Harian: {format_tanggal(awal)}"
    if periode == "mingguan":
        return f"Mingguan: {format_tanggal(awal)} - {format_tanggal(akhir)}"
    if periode == "bulanan":
        return f"Bulanan: {BULAN_PENUH[awal.month - 1]} {awal.year}"
    return f"Tahunan: {awal.year}"


def hitung_leaderboard(db, periode, acuan=None):
    """Susun peringkat pemain pada periode tertentu.

    Mengembalikan list dictionary (peringkat, user_id, username, total_skor,
    jumlah_main), urut dari total skor tertinggi. Skor yang sama mendapat
    peringkat yang sama (mis. 1, 1, 3).
    """
    awal, akhir = rentang_periode(periode, acuan)

    total = {}   # user_id -> [total_skor, jumlah_main]
    for r in db["riwayat"]:
        try:
            tgl = datetime.strptime(r["waktu_main"], FORMAT_WAKTU).date()
        except (ValueError, KeyError, TypeError):
            continue   # lewati catatan dengan waktu rusak
        if awal <= tgl <= akhir:
            if r["user_id"] not in total:
                total[r["user_id"]] = [0, 0]
            total[r["user_id"]][0] += r["skor"]
            total[r["user_id"]][1] += 1

    baris = []
    for user_id, (jumlah_skor, jumlah_main) in total.items():
        user = auth.cari_user_id(db, user_id)
        baris.append({
            "peringkat": 0,
            "user_id": user_id,
            "username": user["username"] if user else "(akun dihapus)",
            "total_skor": jumlah_skor,
            "jumlah_main": jumlah_main,
        })

    baris.sort(key=lambda b: (-b["total_skor"], b["username"].lower()))
    for i, b in enumerate(baris):
        if i > 0 and b["total_skor"] == baris[i - 1]["total_skor"]:
            b["peringkat"] = baris[i - 1]["peringkat"]
        else:
            b["peringkat"] = i + 1
    return baris
