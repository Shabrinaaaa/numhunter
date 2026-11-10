"""Pengujian otomatis NumHunter. Jalankan:  python test_numhunter.py

Tidak membutuhkan pustaka tambahan. Setiap fungsi test_* menguji satu fitur.
"""
import json
import os
import tempfile
from datetime import date, datetime

import auth
import data_store
import game
import leaderboard
import riwayat
import skor
import soal


def db_baru():
    return data_store.buat_data_awal()


def admin_dari(db):
    return auth.login(db, "admin", "admin123")


def pemain_baru(db, nama="budi"):
    ok, _ = auth.daftar_pemain(db, nama, "rahasia1")
    assert ok
    return auth.login(db, nama, "rahasia1")


def mulai(db, pemain, jawaban_soal_id):
    ok, state = game.mulai_permainan(db, pemain, jawaban_soal_id)
    assert ok, state
    return state


def soal_id_jawaban(db, jawaban):
    for s in db["soal"]:
        if s["jawaban"] == jawaban:
            return s["soal_id"]
    raise AssertionError(f"Soal dengan jawaban {jawaban} tidak ada")


# ------------------------------------------------------------ Kegiatan 3: data
def test_data_awal():
    db = db_baru()
    assert len(db["users"]) == 1 and db["users"][0]["role"] == "admin"
    assert len(db["soal"]) == len(data_store.SOAL_AWAL) >= 5
    for s in db["soal"]:
        assert s["jumlah_digit"] == len(s["jawaban"])
        assert s["jawaban"].isdigit()
    assert db["riwayat"] == []
    assert "admin123" not in json.dumps(db)          # password tidak tersimpan polos


def test_simpan_muat_dan_pemulihan():
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "data", "db.json")
        db = data_store.muat_data(path)               # file belum ada -> dibuat
        assert os.path.exists(path)
        db["soal"].append({"soal_id": "S999", "petunjuk": "x", "jawaban": "12",
                           "jumlah_digit": 2, "dibuat_oleh": "U001"})
        data_store.simpan_data(db, path)
        assert data_store.muat_data(path)["soal"][-1]["soal_id"] == "S999"
        with open(path, "w", encoding="utf-8") as f:   # rusak
            f.write("{bukan json")
        pulih = data_store.muat_data(path)
        assert len(pulih["soal"]) == len(data_store.SOAL_AWAL)
        assert os.path.exists(path + ".rusak")


def test_id_baru():
    assert data_store.id_baru("S", [], "soal_id") == "S001"
    assert data_store.id_baru("S", [{"soal_id": "S003"}, {"soal_id": "S001"}], "soal_id") == "S004"


# ------------------------------------------------------------ Kegiatan 4: login
def test_hash_password():
    a, b = auth.hash_password("abcdef"), auth.hash_password("abcdef")
    assert a != b                                     # garam acak
    assert "abcdef" not in a
    assert auth.cek_password("abcdef", a) and auth.cek_password("abcdef", b)
    assert not auth.cek_password("abcdeg", a)
    assert not auth.cek_password("abcdef", "rusak")


def test_daftar_dan_login():
    db = db_baru()
    assert auth.daftar_pemain(db, "Budi_01", "rahasia1")[0]
    assert not auth.daftar_pemain(db, "budi_01", "rahasia1")[0]      # duplikat (tanpa beda huruf)
    assert not auth.daftar_pemain(db, "ab", "rahasia1")[0]           # terlalu pendek
    assert not auth.daftar_pemain(db, "budi baru", "rahasia1")[0]    # karakter tidak valid
    assert not auth.daftar_pemain(db, "citra", "abc")[0]             # password pendek
    assert auth.login(db, "BUDI_01", "rahasia1")["role"] == "pemain"
    assert auth.login(db, "budi_01", "salah") is None
    assert auth.login(db, "tidak_ada", "rahasia1") is None
    assert auth.login(db, "admin", "admin123")["role"] == "admin"


def test_hak_akses_peran():
    db = db_baru()
    admin, pemain = admin_dari(db), pemain_baru(db)
    assert auth.punya_akses(admin, "admin") and not auth.punya_akses(admin, "pemain")
    assert auth.punya_akses(pemain, "pemain") and not auth.punya_akses(pemain, "admin")
    assert not auth.punya_akses(None, "admin")
    # Pemain tidak boleh mengelola soal
    jumlah = len(db["soal"])
    assert not soal.tambah_soal(db, pemain, "Soal ilegal?", "123")[0]
    assert not soal.ubah_soal(db, pemain, "S001", jawaban="999")[0]
    assert not soal.hapus_soal(db, pemain, "S001")[0]
    assert len(db["soal"]) == jumlah
    # Admin tidak boleh bermain
    assert not game.mulai_permainan(db, admin, "S001")[0]


# ------------------------------------------------------------ Kegiatan 5: kelola soal
def test_tambah_soal():
    db = db_baru()
    admin = admin_dari(db)
    ok, pesan = soal.tambah_soal(db, admin, "  Berapa sisi segitiga ditambah 100?  ", " 103 ")
    assert ok, pesan
    s = soal.cari_soal(db, "s012")
    assert s["petunjuk"] == "Berapa sisi segitiga ditambah 100?" and s["jawaban"] == "103"
    assert s["jumlah_digit"] == 3 and s["dibuat_oleh"] == admin["user_id"]
    assert s["tingkat"] == "mudah"                                  # otomatis dari 3 digit


def test_validasi_soal():
    db = db_baru()
    admin = admin_dari(db)
    n = len(db["soal"])
    assert not soal.tambah_soal(db, admin, "", "123")[0]                      # petunjuk kosong
    assert not soal.tambah_soal(db, admin, "Soal A?", "12a")[0]               # bukan angka
    assert not soal.tambah_soal(db, admin, "Soal A?", "1 2")[0]               # ada spasi
    assert not soal.tambah_soal(db, admin, "Soal A?", "-12")[0]               # tanda minus
    assert not soal.tambah_soal(db, admin, "Soal A?", "5")[0]                 # terlalu pendek
    assert not soal.tambah_soal(db, admin, "Soal A?", "12345678901")[0]       # terlalu panjang
    assert not soal.tambah_soal(db, admin, "Soal A?", "١٢٣")[0]                # angka non-ASCII
    assert not soal.tambah_soal(db, admin, "x" * 151, "123")[0]               # petunjuk terlalu panjang
    assert not soal.tambah_soal(db, admin, "TAHUN BERAPA INDONESIA MERDEKA?", "1945")[0]  # duplikat
    assert len(db["soal"]) == n


def test_tingkat_soal():
    db = db_baru()
    admin = admin_dari(db)
    for t in data_store.TINGKAT:
        assert soal.daftar_soal(db, t), t                              # tiap tingkat punya soal
    assert len(soal.daftar_soal(db)) == len(data_store.SOAL_AWAL)
    assert sum(len(soal.daftar_soal(db, t)) for t in data_store.TINGKAT) == len(db["soal"])
    assert not soal.tambah_soal(db, admin, "Soal tingkat salah?", "123", "ahli")[0]
    assert soal.tambah_soal(db, admin, "Soal sulit manual?", "123", "sulit")[0]   # admin boleh menimpa
    assert soal.daftar_soal(db, "sulit")[-1]["petunjuk"] == "Soal sulit manual?"
    assert soal.ubah_soal(db, admin, "S001", tingkat="sedang")[0]
    assert soal.cari_soal(db, "S001")["tingkat"] == "sedang"
    assert not soal.ubah_soal(db, admin, "S001", tingkat="x")[0]
    pemain = pemain_baru(db)
    ok, state = game.mulai_permainan(db, pemain, "S001")
    assert ok and state["tingkat"] == "sedang"
    assert data_store.tingkat_otomatis(3) == "mudah" and data_store.tingkat_otomatis(4) == "sedang" \
        and data_store.tingkat_otomatis(6) == "sulit"
    # data lama tanpa tingkat dilengkapi saat dimuat
    import tempfile, os, json
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "db.json")
        lama = data_store.buat_data_awal()
        for item in lama["soal"]:
            del item["tingkat"]
        json.dump(lama, open(path, "w"))
        assert all(s["tingkat"] in data_store.TINGKAT for s in data_store.muat_data(path)["soal"])


def test_ubah_dan_hapus_soal():
    db = db_baru()
    admin = admin_dari(db)
    ok, _ = soal.ubah_soal(db, admin, "S001", jawaban="19450817")
    assert ok and soal.cari_soal(db, "S001")["jumlah_digit"] == 8
    ok, _ = soal.ubah_soal(db, admin, "S001", petunjuk="Tanggal proklamasi (tahun+bulan+tanggal)?")
    assert ok and soal.cari_soal(db, "S001")["jawaban"] == "19450817"
    assert not soal.ubah_soal(db, admin, "S001")[0]                       # tidak ada perubahan
    assert not soal.ubah_soal(db, admin, "S001", jawaban="abc")[0]        # tidak valid
    assert soal.cari_soal(db, "S001")["jawaban"] == "19450817"            # tidak berubah
    assert not soal.ubah_soal(db, admin, "S999", jawaban="12")[0]         # tidak ada
    assert not soal.ubah_soal(db, admin, "S001", petunjuk="Berapa menit dalam satu hari?")[0]  # duplikat
    n = len(db["soal"])
    assert soal.hapus_soal(db, admin, "s002")[0]
    assert len(db["soal"]) == n - 1 and soal.cari_soal(db, "S002") is None
    assert not soal.hapus_soal(db, admin, "S002")[0]


# ------------------------------------------------------------ Kegiatan 6: permainan
def test_menang_tanpa_salah():
    db = db_baru()
    state = mulai(db, pemain_baru(db), soal_id_jawaban(db, "1945"))
    assert game.tampilan_jawaban(state) == "_ _ _ _"
    for d in "1945":
        assert game.tebak_digit(state, d)[0] == "benar"
    assert state["status"] == "menang" and state["jumlah_percobaan"] == 4
    assert game.tampilan_jawaban(state) == "1 9 4 5"
    assert game.tebak_digit(state, "2")[0] == "selesai"
    assert state["jumlah_percobaan"] == 4


def test_digit_berulang_terbuka_sekaligus():
    db = db_baru()
    state = mulai(db, pemain_baru(db), soal_id_jawaban(db, "144"))
    hasil, pesan = game.tebak_digit(state, "4")
    assert hasil == "benar" and "2 posisi" in pesan
    assert game.tampilan_jawaban(state) == "_ 4 4"
    game.tebak_digit(state, 1)                        # angka bertipe int juga diterima
    assert state["status"] == "menang" and state["jumlah_percobaan"] == 2


def test_kalah_kesempatan_habis():
    db = db_baru()
    state = mulai(db, pemain_baru(db), soal_id_jawaban(db, "1945"))
    assert game.BATAS_SALAH == 5 and state["batas_salah"] == 5
    for d in "0236":
        assert game.tebak_digit(state, d)[0] == "salah"
    assert state["status"] == "berjalan" and game.sisa_kesempatan(state) == 1
    assert game.tebak_digit(state, "7")[0] == "salah"
    assert state["status"] == "kalah" and game.sisa_kesempatan(state) == 0
    assert game.tampilan_jawaban(state, buka_semua=True) == "1 9 4 5"


def test_input_tidak_dihitung():
    db = db_baru()
    state = mulai(db, pemain_baru(db), soal_id_jawaban(db, "1945"))
    for buruk in ("", " ", "a", "12", "-1", "٣", "1.5", "10"):
        assert game.tebak_digit(state, buruk)[0] == "tidak_valid", buruk
    assert state["jumlah_percobaan"] == 0
    game.tebak_digit(state, "1")
    game.tebak_digit(state, "0")
    assert game.tebak_digit(state, "1")[0] == "sudah_dicoba"
    assert game.tebak_digit(state, "0")[0] == "sudah_dicoba"
    assert state["jumlah_percobaan"] == 2 and state["digit_salah"] == [0]


def test_menyerah():
    db = db_baru()
    state = mulai(db, pemain_baru(db), soal_id_jawaban(db, "1945"))
    game.tebak_digit(state, "1")
    game.menyerah(state)
    assert state["status"] == "kalah"
    assert skor.hitung_skor(state) == 0


# ------------------------------------------------------------ Kegiatan 7: skor
def selesaikan(db, jawaban, urutan):
    nomor = len([u for u in db["users"] if u["role"] == "pemain"]) + 1
    state = mulai(db, pemain_baru(db, f"pemain{nomor}"), soal_id_jawaban(db, jawaban))
    for d in urutan:
        game.tebak_digit(state, d)
    return state


def test_skor_menang():
    db = db_baru()
    assert skor.hitung_skor(selesaikan(db, "1945", "1945")) == 100        # tanpa salah
    assert skor.hitung_skor(selesaikan(db, "1945", "01945")) == 90        # 1 salah
    assert skor.hitung_skor(selesaikan(db, "1945", "0231945")) == 70      # 3 salah
    assert skor.hitung_skor(selesaikan(db, "144", "41")) == 100           # digit berulang: minimum 2
    r = skor.rincian_skor(selesaikan(db, "1945", "0231945"))
    assert r == {"status": "menang", "jumlah_percobaan": 7, "percobaan_minimum": 4,
                 "percobaan_berlebih": 3, "penalti": 30, "skor": 70}


def test_skor_kalah_nol_dan_urutan():
    db = db_baru()
    assert skor.hitung_skor(selesaikan(db, "1945", "02367")) == 0
    assert skor.hitung_skor(selesaikan(db, "1945", "19")) == 0            # belum selesai
    # Semakin sedikit percobaan, semakin tinggi skor
    nilai = [skor.hitung_skor(selesaikan(db, "1945", u)) for u in ("1945", "01945", "0231945")]
    assert nilai == [100, 90, 70] and nilai == sorted(nilai, reverse=True)


def test_skor_terendah_menang_batas_salah():
    db = db_baru()
    # 4 salah (batas 5) lalu menang: 4 digit + 4 salah = 8 percobaan -> penalti 40 -> skor 60
    assert skor.hitung_skor(selesaikan(db, "1945", "0236" + "1945")) == 60
    # kesalahan ke-5 mengakhiri ronde sebagai kalah, tebakan benar sesudahnya tidak berlaku
    assert skor.hitung_skor(selesaikan(db, "1945", "02367" + "1945")) == 0


# ------------------------------------------------------------ Kegiatan 8: riwayat
def test_catat_dan_baca_riwayat():
    db = db_baru()
    budi, sari = pemain_baru(db, "budi"), pemain_baru(db, "sari")
    s1 = mulai(db, budi, soal_id_jawaban(db, "1945"))
    assert riwayat.catat_riwayat(db, s1, 0) is None                  # belum selesai
    for d in "1945":
        game.tebak_digit(s1, d)
    r = riwayat.catat_riwayat(db, s1, skor.hitung_skor(s1), datetime(2026, 11, 3, 8, 0, 0))
    assert r["waktu_main"] == "2026-11-03 08:00:00" and r["status"] == "menang" and r["skor"] == 100
    assert riwayat.catat_riwayat(db, s1, 100) is None                # tidak dicatat dua kali
    s2 = mulai(db, budi, soal_id_jawaban(db, "168"))
    game.menyerah(s2)
    riwayat.catat_riwayat(db, s2, 0, datetime(2026, 11, 4, 9, 30, 0))
    s3 = mulai(db, sari, soal_id_jawaban(db, "144"))
    game.menyerah(s3)
    riwayat.catat_riwayat(db, s3, 0, datetime(2026, 11, 4, 10, 0, 0))

    semua = riwayat.riwayat_pemain(db, budi["user_id"])
    assert [x["soal_id"] for x in semua] == [s2["soal_id"], s1["soal_id"]]   # terbaru dahulu
    assert len(riwayat.riwayat_pemain(db, budi["user_id"], "menang")) == 1
    assert len(riwayat.riwayat_pemain(db, budi["user_id"], "kalah")) == 1
    assert len(riwayat.riwayat_pemain(db, sari["user_id"])) == 1              # tidak tercampur
    assert riwayat.soal_sudah_dimainkan(db, budi["user_id"]) == {s1["soal_id"], s2["soal_id"]}
    assert riwayat.riwayat_pemain(db, "U999") == []
    ids = [x["riwayat_id"] for x in db["riwayat"]]
    assert ids == ["R001", "R002", "R003"]


# ------------------------------------------------------------ Kegiatan 8: leaderboard
def db_leaderboard():
    db = db_baru()
    a, b, c = (pemain_baru(db, n) for n in ("anto", "bela", "cici"))

    def tambah(user, tanggal, nilai, status="menang"):
        db["riwayat"].append({
            "riwayat_id": data_store.id_baru("R", db["riwayat"], "riwayat_id"),
            "user_id": user["user_id"], "soal_id": "S001", "skor": nilai, "status": status,
            "jumlah_percobaan": 4, "waktu_main": tanggal})
    tambah(a, "2026-11-05 10:00:00", 100)
    tambah(a, "2026-11-03 09:00:00", 50)
    tambah(a, "2026-11-01 23:59:59", 80)     # Minggu sebelumnya, masih bulan November
    tambah(a, "2026-10-20 08:00:00", 70)     # bulan lain, tahun sama
    tambah(a, "2025-12-31 12:00:00", 60)     # tahun lain
    tambah(b, "2026-11-05 11:00:00", 100)
    tambah(c, "2026-11-04 15:00:00", 90)
    tambah(c, "2026-11-04 16:00:00", 0, "kalah")
    return db, a, b, c


def ringkas(baris):
    return [(x["peringkat"], x["username"], x["total_skor"]) for x in baris]


def test_rentang_periode():
    kamis = date(2026, 11, 5)
    assert leaderboard.rentang_periode("harian", kamis) == (kamis, kamis)
    assert leaderboard.rentang_periode("mingguan", kamis) == (date(2026, 11, 2), date(2026, 11, 8))
    assert leaderboard.rentang_periode("mingguan", date(2026, 11, 8)) == (date(2026, 11, 2), date(2026, 11, 8))  # Minggu
    assert leaderboard.rentang_periode("mingguan", date(2026, 11, 2)) == (date(2026, 11, 2), date(2026, 11, 8))  # Senin
    assert leaderboard.rentang_periode("mingguan", date(2026, 1, 1)) == (date(2025, 12, 29), date(2026, 1, 4))   # lintas tahun
    assert leaderboard.rentang_periode("bulanan", kamis) == (date(2026, 11, 1), date(2026, 11, 30))
    assert leaderboard.rentang_periode("bulanan", date(2028, 2, 10)) == (date(2028, 2, 1), date(2028, 2, 29))   # kabisat
    assert leaderboard.rentang_periode("bulanan", date(2027, 2, 10)) == (date(2027, 2, 1), date(2027, 2, 28))
    assert leaderboard.rentang_periode("tahunan", kamis) == (date(2026, 1, 1), date(2026, 12, 31))
    assert leaderboard.rentang_periode("harian", datetime(2026, 11, 5, 23, 59)) == (kamis, kamis)
    try:
        leaderboard.rentang_periode("dekade", kamis)
        raise AssertionError("Seharusnya ValueError")
    except ValueError:
        pass


def test_leaderboard_empat_periode():
    db, a, b, c = db_leaderboard()
    acuan = date(2026, 11, 5)
    assert ringkas(leaderboard.hitung_leaderboard(db, "harian", acuan)) == [
        (1, "anto", 100), (1, "bela", 100)]                       # skor sama -> peringkat sama
    assert ringkas(leaderboard.hitung_leaderboard(db, "mingguan", acuan)) == [
        (1, "anto", 150), (2, "bela", 100), (3, "cici", 90)]
    assert ringkas(leaderboard.hitung_leaderboard(db, "bulanan", acuan)) == [
        (1, "anto", 230), (2, "bela", 100), (3, "cici", 90)]
    assert ringkas(leaderboard.hitung_leaderboard(db, "tahunan", acuan)) == [
        (1, "anto", 300), (2, "bela", 100), (3, "cici", 90)]


def test_leaderboard_peringkat_seri_dan_kosong():
    db, a, b, c = db_leaderboard()
    baris = leaderboard.hitung_leaderboard(db, "harian", date(2026, 11, 5))
    assert [x["peringkat"] for x in baris] == [1, 1]
    db["riwayat"].append({"riwayat_id": "R099", "user_id": c["user_id"], "soal_id": "S001", "skor": 100,
                          "status": "menang", "jumlah_percobaan": 4, "waktu_main": "2026-11-05 12:00:00"})
    baris = leaderboard.hitung_leaderboard(db, "harian", date(2026, 11, 5))
    assert [x["peringkat"] for x in baris] == [1, 1, 1]            # tiga pemain seri
    assert leaderboard.hitung_leaderboard(db, "harian", date(2030, 1, 1)) == []
    assert leaderboard.hitung_leaderboard(db_baru(), "tahunan", date(2026, 11, 5)) == []


def test_leaderboard_urutan_peringkat_setelah_seri():
    db, a, b, c = db_leaderboard()
    db["riwayat"].append({"riwayat_id": "R100", "user_id": c["user_id"], "soal_id": "S001", "skor": 60,
                          "status": "menang", "jumlah_percobaan": 5, "waktu_main": "2026-11-06 10:00:00"})
    baris = ringkas(leaderboard.hitung_leaderboard(db, "mingguan", date(2026, 11, 5)))
    # anto 150, cici 150 (seri, urut abjad), bela 100 -> peringkat 1, 1, 3
    assert baris == [(1, "anto", 150), (1, "cici", 150), (3, "bela", 100)]


def test_leaderboard_catatan_rusak_dilewati():
    db, a, b, c = db_leaderboard()
    db["riwayat"].append({"riwayat_id": "R200", "user_id": a["user_id"], "soal_id": "S001", "skor": 999,
                          "status": "menang", "jumlah_percobaan": 1, "waktu_main": "bukan tanggal"})
    assert ringkas(leaderboard.hitung_leaderboard(db, "tahunan", date(2026, 11, 5)))[0] == (1, "anto", 300)


def test_label_periode():
    k = date(2026, 11, 5)
    assert leaderboard.label_periode("harian", k) == "Harian: 5 Nov 2026"
    assert leaderboard.label_periode("mingguan", k) == "Mingguan: 2 Nov 2026 - 8 Nov 2026"
    assert leaderboard.label_periode("bulanan", k) == "Bulanan: November 2026"
    assert leaderboard.label_periode("tahunan", k) == "Tahunan: 2026"


# ------------------------------------------------------------ Satu alur utuh
def test_alur_utuh():
    db = db_baru()
    admin = admin_dari(db)
    assert soal.tambah_soal(db, admin, "Berapa hasil 25 x 4?", "100")[0]
    pemain = pemain_baru(db, "flora")
    state = mulai(db, pemain, soal_id_jawaban(db, "100"))
    for d in "01":
        game.tebak_digit(state, d)
    assert state["status"] == "menang"
    nilai = skor.hitung_skor(state)
    assert nilai == 100 and state["jumlah_percobaan"] == 2
    riwayat.catat_riwayat(db, state, nilai)
    hari_ini = leaderboard.hitung_leaderboard(db, "harian")
    assert ringkas(hari_ini) == [(1, "flora", 100)]
    assert soal.hapus_soal(db, admin, state["soal_id"])[0]            # soal dihapus, riwayat tetap
    assert len(riwayat.riwayat_pemain(db, pemain["user_id"])) == 1


if __name__ == "__main__":
    daftar = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    gagal = 0
    for nama, fungsi in daftar:
        try:
            fungsi()
            print(f"LULUS  {nama}")
        except Exception as e:           # noqa: BLE001 - tampilkan semua kegagalan
            gagal += 1
            print(f"GAGAL  {nama}: {type(e).__name__}: {e}")
    print(f"\n{len(daftar) - gagal} dari {len(daftar)} pengujian lulus.")
    raise SystemExit(1 if gagal else 0)
