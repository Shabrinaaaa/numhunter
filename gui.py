"""gui.py - Antarmuka grafis NumHunter (tkinter, bawaan Python).

Setiap layar adalah satu kelas Frame. Layar hanya mengatur tampilan dan
perpindahan; semua aturan (login, soal, permainan, skor, riwayat, leaderboard)
dipanggil dari modul logika. Layar yang ada mengikuti rancangan Figma:
Login, Menu Pemain, Pilih Soal, Permainan, Hasil Ronde, Riwayat Soal,
Leaderboard, Menu Admin, Kelola Soal (daftar dan form).
"""
import random
import tkinter as tk
from tkinter import messagebox, ttk

import auth
import data_store
import game
import leaderboard
import riwayat
import skor
import soal

# ---------------------------------------------------------------- tema
BG = "#F4F6FB"
KARTU = "#FFFFFF"
UTAMA = "#4F46E5"
UTAMA_GELAP = "#4338CA"
TEKS = "#1F2937"
REDUP = "#6B7280"
GARIS = "#D9DEE8"
BENAR = "#16A34A"
BENAR_MUDA = "#DCFCE7"
SALAH = "#DC2626"
SALAH_MUDA = "#FEE2E2"
WARNA_TINGKAT = {"mudah": "#16A34A", "sedang": "#D97706", "sulit": "#DC2626"}
FONT = "Segoe UI"


def huruf_awal(teks):
    return teks[:1].upper() + teks[1:]


def pasang_gaya(root):
    gaya = ttk.Style(root)
    gaya.theme_use("clam")
    gaya.configure(".", font=(FONT, 11), background=BG, foreground=TEKS)
    gaya.configure("TFrame", background=BG)
    gaya.configure("Kartu.TFrame", background=KARTU, relief="solid", borderwidth=1, bordercolor=GARIS)
    gaya.configure("TLabel", background=BG, foreground=TEKS)
    gaya.configure("Kartu.TLabel", background=KARTU)
    gaya.configure("Judul.TLabel", font=(FONT, 22, "bold"))
    gaya.configure("Sub.TLabel", foreground=REDUP)
    gaya.configure("KartuSub.TLabel", background=KARTU, foreground=REDUP)
    gaya.configure("Galat.TLabel", foreground=SALAH)
    gaya.configure("TButton", padding=(14, 8), background=KARTU, bordercolor=GARIS, focuscolor=KARTU)
    gaya.map("TButton", background=[("active", "#EEF0FB")])
    gaya.configure("Utama.TButton", background=UTAMA, foreground="#FFFFFF", bordercolor=UTAMA, font=(FONT, 11, "bold"))
    gaya.map("Utama.TButton", background=[("active", UTAMA_GELAP), ("disabled", "#A5A8E8")],
             foreground=[("disabled", "#FFFFFF")])
    gaya.configure("Bahaya.TButton", foreground=SALAH)
    gaya.configure("Tombol.TButton", font=(FONT, 16, "bold"), padding=(0, 10))
    gaya.configure("TombolBenar.TButton", font=(FONT, 16, "bold"), padding=(0, 10),
                   background=BENAR_MUDA, foreground=BENAR, bordercolor=BENAR)
    gaya.configure("TombolSalah.TButton", font=(FONT, 16, "bold"), padding=(0, 10),
                   background=SALAH_MUDA, foreground=SALAH, bordercolor=SALAH)
    for nama in ("TombolBenar.TButton", "TombolSalah.TButton"):
        gaya.map(nama, background=[("disabled", gaya.lookup(nama, "background"))],
                 foreground=[("disabled", gaya.lookup(nama, "foreground"))])
    gaya.configure("Tab.TButton", padding=(14, 6))
    gaya.configure("TabAktif.TButton", padding=(14, 6), background=UTAMA, foreground="#FFFFFF", bordercolor=UTAMA)
    gaya.map("TabAktif.TButton", background=[("active", UTAMA_GELAP)])
    gaya.configure("Treeview", rowheight=30, background=KARTU, fieldbackground=KARTU, bordercolor=GARIS)
    gaya.configure("Treeview.Heading", font=(FONT, 10, "bold"), background="#E9ECF6", padding=6)
    gaya.map("Treeview", background=[("selected", "#DDE0FA")], foreground=[("selected", TEKS)])
    gaya.configure("TEntry", padding=6, fieldbackground=KARTU)
    gaya.configure("TCombobox", padding=6, fieldbackground=KARTU)


# ---------------------------------------------------------------- alat bantu
class Layar(ttk.Frame):
    """Dasar semua layar: menyimpan referensi ke aplikasi dan menyediakan kerangka."""

    def __init__(self, app):
        super().__init__(app, padding=24)
        self.app = app
        self.db = app.db

    def bar_judul(self, judul, sub=None, kembali=None):
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 16))
        if kembali:
            ttk.Button(bar, text="← Kembali", command=kembali).pack(side="left", padx=(0, 14))
        kolom = ttk.Frame(bar)
        kolom.pack(side="left")
        ttk.Label(kolom, text=judul, style="Judul.TLabel").pack(anchor="w")
        if sub:
            ttk.Label(kolom, text=sub, style="Sub.TLabel").pack(anchor="w")
        return bar

    def kartu(self, **opsi):
        k = ttk.Frame(self, style="Kartu.TFrame", padding=opsi.pop("padding", 18))
        return k

    def tabel(self, induk, kolom, tinggi=12):
        """kolom: list (id, judul, lebar, rata). Mengembalikan Treeview dengan scrollbar."""
        bungkus = ttk.Frame(induk)
        tree = ttk.Treeview(bungkus, columns=[k[0] for k in kolom], show="headings",
                            height=tinggi, selectmode="browse")
        for id_, judul, lebar, rata in kolom:
            tree.heading(id_, text=judul, anchor=rata)
            tree.column(id_, width=lebar, anchor=rata, stretch=(id_ == kolom[-1][0] or lebar > 200))
        bar = ttk.Scrollbar(bungkus, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=bar.set)
        tree.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")
        tree.tag_configure("menang", foreground=BENAR)
        tree.tag_configure("kalah", foreground=SALAH)
        tree.tag_configure("saya", background="#EEF0FF")
        return bungkus, tree


# ---------------------------------------------------------------- login dan daftar
class LayarLogin(Layar):
    def __init__(self, app):
        super().__init__(app)
        self.mode = "masuk"
        tengah = ttk.Frame(self)
        tengah.place(relx=0.5, rely=0.46, anchor="center")
        ttk.Label(tengah, text="NumHunter", font=(FONT, 34, "bold"), foreground=UTAMA).pack()
        ttk.Label(tengah, text="Tebak angka tersembunyi sebelum kesempatanmu habis",
                  style="Sub.TLabel").pack(pady=(0, 18))

        self.kotak = ttk.Frame(tengah, style="Kartu.TFrame", padding=24)
        self.kotak.pack(ipadx=10)
        tab = ttk.Frame(self.kotak, style="Kartu.TFrame")
        tab.pack(fill="x", pady=(0, 14))
        self.tab_masuk = ttk.Button(tab, text="Masuk", command=lambda: self.ganti("masuk"))
        self.tab_daftar = ttk.Button(tab, text="Daftar pemain", command=lambda: self.ganti("daftar"))
        self.tab_masuk.pack(side="left", expand=True, fill="x")
        self.tab_daftar.pack(side="left", expand=True, fill="x", padx=(6, 0))

        self.var_user, self.var_pw, self.var_pw2 = tk.StringVar(), tk.StringVar(), tk.StringVar()
        ttk.Label(self.kotak, text="Username", style="Kartu.TLabel").pack(anchor="w")
        self.isi_user = ttk.Entry(self.kotak, textvariable=self.var_user, width=34)
        self.isi_user.pack(fill="x", pady=(2, 10))
        ttk.Label(self.kotak, text="Password", style="Kartu.TLabel").pack(anchor="w")
        self.isi_pw = ttk.Entry(self.kotak, textvariable=self.var_pw, show="•", width=34)
        self.isi_pw.pack(fill="x", pady=(2, 10))
        self.label_pw2 = ttk.Label(self.kotak, text="Ulangi password", style="Kartu.TLabel")
        self.isi_pw2 = ttk.Entry(self.kotak, textvariable=self.var_pw2, show="•", width=34)

        self.pesan = ttk.Label(self.kotak, text="", style="Kartu.TLabel", wraplength=300, justify="left")
        self.pesan.pack(anchor="w", pady=(0, 8))
        self.tombol = ttk.Button(self.kotak, text="Masuk", style="Utama.TButton", command=self.kirim)
        self.tombol.pack(fill="x")
        for w in (self.isi_user, self.isi_pw, self.isi_pw2):
            w.bind("<Return>", lambda e: self.kirim())
        self.gagal = 0
        self.ganti("masuk")
        self.isi_user.focus_set()

    def ganti(self, mode):
        self.mode = mode
        self.pesan.configure(text="")
        self.tab_masuk.configure(style="TabAktif.TButton" if mode == "masuk" else "Tab.TButton")
        self.tab_daftar.configure(style="TabAktif.TButton" if mode == "daftar" else "Tab.TButton")
        if mode == "daftar":
            self.label_pw2.pack(anchor="w", before=self.pesan)
            self.isi_pw2.pack(fill="x", pady=(2, 10), before=self.pesan)
            self.tombol.configure(text="Buat akun")
        else:
            self.label_pw2.pack_forget()
            self.isi_pw2.pack_forget()
            self.tombol.configure(text="Masuk")

    def tampil_pesan(self, teks, baik=False):
        self.pesan.configure(text=teks, foreground=BENAR if baik else SALAH)

    def kirim(self):
        username, password = self.var_user.get().strip(), self.var_pw.get()
        if self.mode == "daftar":
            if password != self.var_pw2.get():
                return self.tampil_pesan("Password tidak sama.")
            ok, pesan = auth.daftar_pemain(self.db, username, password)
            if ok:
                data_store.simpan_data(self.db)
                self.var_pw.set("")
                self.var_pw2.set("")
                self.ganti("masuk")
                self.tampil_pesan(pesan + " Silakan masuk.", baik=True)
            else:
                self.tampil_pesan(pesan)
            return
        pengguna = auth.login(self.db, username, password)
        if pengguna is None:
            self.gagal += 1
            self.var_pw.set("")
            return self.tampil_pesan("Username atau password salah." +
                                     (f" ({self.gagal}x gagal)" if self.gagal > 1 else ""))
        self.app.masuk(pengguna)


# ---------------------------------------------------------------- menu pemain dan admin
class LayarMenuPemain(Layar):
    def __init__(self, app):
        super().__init__(app)
        p = app.pengguna
        total, peringkat = 0, "-"
        for b in leaderboard.hitung_leaderboard(self.db, "harian"):
            if b["user_id"] == p["user_id"]:
                total, peringkat = b["total_skor"], f"#{b['peringkat']}"
        self.bar_judul(f"Halo, {p['username']}", "Pilih apa yang ingin kamu lakukan.")
        ringkas = ttk.Frame(self)
        ringkas.pack(fill="x", pady=(0, 18))
        for judul, nilai in (("Skor hari ini", str(total)), ("Peringkat harian", peringkat),
                             ("Soal dimainkan", str(len(riwayat.soal_sudah_dimainkan(self.db, p["user_id"]))))):
            k = ttk.Frame(ringkas, style="Kartu.TFrame", padding=16)
            k.pack(side="left", expand=True, fill="x", padx=(0, 12))
            ttk.Label(k, text=judul, style="KartuSub.TLabel").pack(anchor="w")
            ttk.Label(k, text=nilai, style="Kartu.TLabel", font=(FONT, 24, "bold")).pack(anchor="w")
        menu = ttk.Frame(self)
        menu.pack(fill="x")
        ttk.Button(menu, text="Mulai Bermain", style="Utama.TButton",
                   command=lambda: app.tampil(LayarPilihSoal)).pack(fill="x", pady=5)
        ttk.Button(menu, text="Riwayat Soal", command=lambda: app.tampil(LayarRiwayat)).pack(fill="x", pady=5)
        ttk.Button(menu, text="Leaderboard", command=lambda: app.tampil(LayarLeaderboard)).pack(fill="x", pady=5)
        ttk.Button(menu, text="Keluar", style="Bahaya.TButton", command=app.keluar).pack(fill="x", pady=(18, 5))


class LayarMenuAdmin(Layar):
    def __init__(self, app):
        super().__init__(app)
        self.bar_judul(f"Panel Admin - {app.pengguna['username']}", "Kelola bank soal dan pantau papan peringkat.")
        jumlah = {t: len(soal.daftar_soal(self.db, t)) for t in soal.TINGKAT}
        ringkas = ttk.Frame(self)
        ringkas.pack(fill="x", pady=(0, 18))
        for t in soal.TINGKAT:
            k = ttk.Frame(ringkas, style="Kartu.TFrame", padding=16)
            k.pack(side="left", expand=True, fill="x", padx=(0, 12))
            ttk.Label(k, text=f"Soal {t}", style="KartuSub.TLabel").pack(anchor="w")
            ttk.Label(k, text=str(jumlah[t]), style="Kartu.TLabel", font=(FONT, 24, "bold"),
                      foreground=WARNA_TINGKAT[t]).pack(anchor="w")
        ttk.Button(self, text="Kelola Soal", style="Utama.TButton",
                   command=lambda: app.tampil(LayarKelolaSoal)).pack(fill="x", pady=5)
        ttk.Button(self, text="Leaderboard", command=lambda: app.tampil(LayarLeaderboard)).pack(fill="x", pady=5)
        ttk.Button(self, text="Keluar", style="Bahaya.TButton", command=app.keluar).pack(fill="x", pady=(18, 5))


# ---------------------------------------------------------------- pilih soal
class LayarPilihSoal(Layar):
    def __init__(self, app, tingkat="mudah"):
        super().__init__(app)
        self.tingkat = tingkat
        self.bar_judul("Pilih Soal", "Pilih tingkat, lalu pilih soalnya atau biarkan diacak.",
                       kembali=lambda: app.tampil(LayarMenuPemain))
        baris = ttk.Frame(self)
        baris.pack(fill="x", pady=(0, 12))
        self.tombol_tingkat = {}
        for t in soal.TINGKAT:
            b = ttk.Button(baris, text=huruf_awal(t), command=lambda t=t: self.pilih_tingkat(t))
            b.pack(side="left", padx=(0, 8))
            self.tombol_tingkat[t] = b
        self.info = ttk.Label(baris, text="", style="Sub.TLabel")
        self.info.pack(side="right")
        bungkus, self.tree = self.tabel(self, [
            ("status", "", 110, "center"), ("digit", "Digit", 70, "center"), ("petunjuk", "Petunjuk", 520, "w")], 10)
        bungkus.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self.mainkan_terpilih())
        aksi = ttk.Frame(self)
        aksi.pack(fill="x", pady=(14, 0))
        ttk.Button(aksi, text="Mainkan soal terpilih", style="Utama.TButton",
                   command=self.mainkan_terpilih).pack(side="left")
        ttk.Button(aksi, text="Soal acak", command=self.mainkan_acak).pack(side="left", padx=10)
        self.pesan = ttk.Label(aksi, text="", style="Galat.TLabel")
        self.pesan.pack(side="left", padx=10)
        self.pilih_tingkat(tingkat)

    def pilih_tingkat(self, tingkat):
        self.tingkat = tingkat
        self.pesan.configure(text="")
        for t, b in self.tombol_tingkat.items():
            b.configure(style="TabAktif.TButton" if t == tingkat else "TButton")
        self.sudah = riwayat.soal_sudah_dimainkan(self.db, self.app.pengguna["user_id"])
        self.tree.delete(*self.tree.get_children())
        daftar = soal.daftar_soal(self.db, tingkat)
        for s in daftar:
            self.tree.insert("", "end", iid=s["soal_id"], values=(
                "sudah dimainkan" if s["soal_id"] in self.sudah else "baru", s["jumlah_digit"], s["petunjuk"]))
        belum = sum(1 for s in daftar if s["soal_id"] not in self.sudah)
        self.info.configure(text=f"{len(daftar)} soal, {belum} belum dimainkan")
        if daftar:
            self.tree.selection_set(daftar[0]["soal_id"])

    def mulai(self, soal_id):
        ok, hasil = game.mulai_permainan(self.db, self.app.pengguna, soal_id)
        if not ok:
            return self.pesan.configure(text=hasil)
        self.app.tampil(LayarPermainan, state=hasil)

    def mainkan_terpilih(self):
        pilih = self.tree.selection()
        if not pilih:
            return self.pesan.configure(text="Pilih satu soal dulu.")
        self.mulai(pilih[0])

    def mainkan_acak(self):
        daftar = soal.daftar_soal(self.db, self.tingkat)
        if not daftar:
            return self.pesan.configure(text="Belum ada soal di tingkat ini.")
        belum = [s for s in daftar if s["soal_id"] not in self.sudah]
        self.mulai(random.choice(belum or daftar)["soal_id"])


# ---------------------------------------------------------------- permainan
class LayarPermainan(Layar):
    def __init__(self, app, state):
        super().__init__(app)
        self.state = state
        atas = ttk.Frame(self)
        atas.pack(fill="x")
        ttk.Button(atas, text="Menyerah", style="Bahaya.TButton", command=self.menyerah).pack(side="right")
        t = state["tingkat"]
        ttk.Label(atas, text=f"  {huruf_awal(t)}  ", foreground="#FFFFFF", background=WARNA_TINGKAT[t],
                  font=(FONT, 10, "bold")).pack(side="left")
        self.info = ttk.Label(atas, text="", style="Sub.TLabel")
        self.info.pack(side="left", padx=12)

        ttk.Label(self, text=state["petunjuk"], font=(FONT, 16, "bold"), wraplength=780,
                  justify="center").pack(pady=(22, 14))
        self.papan = ttk.Frame(self)
        self.papan.pack(pady=8)
        self.kotak = []
        for _ in state["jawaban"]:
            lb = tk.Label(self.papan, text="", width=2, font=(FONT, 30, "bold"), bg=KARTU, fg=TEKS,
                          relief="solid", bd=1, highlightthickness=0, pady=8)
            lb.pack(side="left", padx=4)
            self.kotak.append(lb)

        self.nyawa = ttk.Label(self, text="", font=(FONT, 20), foreground=SALAH)
        self.nyawa.pack(pady=(14, 0))
        self.sisa = ttk.Label(self, text="", style="Sub.TLabel")
        self.sisa.pack()
        self.pesan = ttk.Label(self, text="Tekan angka di bawah atau ketik 0-9 di keyboard.", style="Sub.TLabel")
        self.pesan.pack(pady=10)

        pad = ttk.Frame(self)
        pad.pack(pady=4)
        self.tombol = {}
        for d in range(10):
            b = ttk.Button(pad, text=str(d), width=4, style="Tombol.TButton", command=lambda d=d: self.tebak(d))
            b.grid(row=d // 5, column=d % 5, padx=5, pady=5)
            self.tombol[d] = b
        app.bind("<Key>", self.tombol_keyboard)
        self.segarkan()

    def destroy(self):
        self.app.unbind("<Key>")
        super().destroy()

    def tombol_keyboard(self, event):
        if event.char and event.char in "0123456789":
            self.tebak(int(event.char))

    def segarkan(self):
        s = self.state
        buka = s["status"] != game.STATUS_BERJALAN
        for lb, c in zip(self.kotak, s["jawaban"]):
            terbuka = int(c) in s["digit_terbuka"]
            if terbuka:
                lb.configure(text=c, fg=BENAR, bg=BENAR_MUDA)
            elif buka:
                lb.configure(text=c, fg=SALAH, bg=SALAH_MUDA)      # digit yang tidak sempat terbuka
            else:
                lb.configure(text="", bg=KARTU)
        sisa = game.sisa_kesempatan(s)
        self.nyawa.configure(text="● " * sisa + "○ " * (s["batas_salah"] - sisa))
        self.sisa.configure(text=f"Sisa kesempatan salah: {sisa} dari {s['batas_salah']}")
        self.info.configure(text=f"{s['jumlah_digit']} digit  ·  Percobaan: {s['jumlah_percobaan']}")
        for d, b in self.tombol.items():
            if d in s["digit_terbuka"]:
                b.configure(style="TombolBenar.TButton", state="disabled")
            elif d in s["digit_salah"]:
                b.configure(style="TombolSalah.TButton", state="disabled")

    def tebak(self, digit):
        if self.state["status"] != game.STATUS_BERJALAN:
            return
        hasil, pesan = game.tebak_digit(self.state, digit)
        self.pesan.configure(text=pesan, foreground=BENAR if hasil == "benar" else SALAH)
        self.segarkan()
        if self.state["status"] != game.STATUS_BERJALAN:
            self.after(900, self.selesai)

    def menyerah(self):
        if self.state["status"] == game.STATUS_BERJALAN and messagebox.askyesno(
                "Menyerah", "Yakin menyerah? Ronde dihitung kalah dengan skor 0."):
            game.menyerah(self.state)
            self.segarkan()
            self.selesai()

    def selesai(self):
        if self.winfo_exists():
            self.app.tampil(LayarHasil, state=self.state)


class LayarHasil(Layar):
    def __init__(self, app, state):
        super().__init__(app)
        self.state = state
        r = skor.rincian_skor(state)
        riwayat.catat_riwayat(self.db, state, r["skor"])
        data_store.simpan_data(self.db)
        menang = state["status"] == game.STATUS_MENANG
        warna = BENAR if menang else SALAH

        tengah = ttk.Frame(self)
        tengah.place(relx=0.5, rely=0.45, anchor="center")
        ttk.Label(tengah, text="Kamu menang!" if menang else "Kamu kalah", font=(FONT, 30, "bold"),
                  foreground=warna).pack()
        ttk.Label(tengah, text=game.tampilan_jawaban(state, buka_semua=True), font=(FONT, 26, "bold"),
                  foreground=TEKS).pack(pady=(10, 2))
        ttk.Label(tengah, text="jawaban yang benar", style="Sub.TLabel").pack(pady=(0, 16))

        kartu = ttk.Frame(tengah, style="Kartu.TFrame", padding=20)
        kartu.pack(fill="x")
        baris = [("Jumlah percobaan", r["jumlah_percobaan"])]
        if menang:
            baris += [("Percobaan minimum", r["percobaan_minimum"]),
                      ("Percobaan berlebih", r["percobaan_berlebih"]),
                      ("Penalti", f"-{r['penalti']}" if r["penalti"] else "0")]
        for i, (k, v) in enumerate(baris):
            ttk.Label(kartu, text=k, style="Kartu.TLabel").grid(row=i, column=0, sticky="w", pady=2)
            ttk.Label(kartu, text=str(v), style="Kartu.TLabel").grid(row=i, column=1, sticky="e", padx=(60, 0))
        kartu.columnconfigure(1, weight=1)
        ttk.Separator(kartu).grid(row=len(baris), column=0, columnspan=2, sticky="ew", pady=8)
        ttk.Label(kartu, text="Skor ronde ini", style="Kartu.TLabel", font=(FONT, 12, "bold")).grid(
            row=len(baris) + 1, column=0, sticky="w")
        ttk.Label(kartu, text=str(r["skor"]), style="Kartu.TLabel", font=(FONT, 22, "bold"),
                  foreground=warna).grid(row=len(baris) + 1, column=1, sticky="e")

        aksi = ttk.Frame(tengah)
        aksi.pack(pady=(18, 0))
        ttk.Button(aksi, text="Main lagi", style="Utama.TButton",
                   command=lambda: app.tampil(LayarPilihSoal, tingkat=state["tingkat"])).pack(side="left")
        ttk.Button(aksi, text="Leaderboard", command=lambda: app.tampil(LayarLeaderboard)).pack(side="left", padx=8)
        ttk.Button(aksi, text="Menu", command=lambda: app.tampil(LayarMenuPemain)).pack(side="left")


# ---------------------------------------------------------------- riwayat dan leaderboard
class LayarRiwayat(Layar):
    def __init__(self, app):
        super().__init__(app)
        self.bar_judul("Riwayat Soal", "Soal yang pernah kamu mainkan.", kembali=lambda: app.tampil(LayarMenuPemain))
        self.filter = None
        baris = ttk.Frame(self)
        baris.pack(fill="x", pady=(0, 12))
        self.tombol = {}
        for nama, status in (("Semua", None), ("Menang", game.STATUS_MENANG), ("Kalah", game.STATUS_KALAH)):
            b = ttk.Button(baris, text=nama, command=lambda s=status: self.isi(s))
            b.pack(side="left", padx=(0, 8))
            self.tombol[status] = b
        bungkus, self.tree = self.tabel(self, [
            ("waktu", "Waktu", 140, "w"), ("soal", "Soal", 380, "w"), ("tingkat", "Tingkat", 80, "center"),
            ("status", "Status", 80, "center"), ("skor", "Skor", 60, "e")], 12)
        bungkus.pack(fill="both", expand=True)
        self.kosong = ttk.Label(self, text="", style="Sub.TLabel")
        self.kosong.pack(pady=8)
        self.isi(None)

    def isi(self, status):
        for s, b in self.tombol.items():
            b.configure(style="TabAktif.TButton" if s == status else "TButton")
        self.tree.delete(*self.tree.get_children())
        daftar = riwayat.riwayat_pemain(self.db, self.app.pengguna["user_id"], status)
        for r in daftar:
            s = soal.cari_soal(self.db, r["soal_id"])
            self.tree.insert("", "end", tags=(r["status"],), values=(
                r["waktu_main"][:16], s["petunjuk"] if s else "(soal sudah dihapus)",
                huruf_awal(s["tingkat"]) if s else "-", huruf_awal(r["status"]), r["skor"]))
        self.kosong.configure(text="" if daftar else "Belum ada riwayat permainan.")


class LayarLeaderboard(Layar):
    def __init__(self, app):
        super().__init__(app)
        kembali = LayarMenuAdmin if app.pengguna["role"] == auth.PERAN_ADMIN else LayarMenuPemain
        self.bar_judul("Leaderboard", "Total skor tiap pemain pada periode yang dipilih.",
                       kembali=lambda: app.tampil(kembali))
        baris = ttk.Frame(self)
        baris.pack(fill="x", pady=(0, 6))
        self.tombol = {}
        for p in leaderboard.PERIODE:
            b = ttk.Button(baris, text=huruf_awal(p), command=lambda p=p: self.isi(p))
            b.pack(side="left", padx=(0, 8))
            self.tombol[p] = b
        self.label = ttk.Label(self, text="", style="Sub.TLabel")
        self.label.pack(anchor="w", pady=(6, 8))
        bungkus, self.tree = self.tabel(self, [
            ("peringkat", "Peringkat", 90, "center"), ("pemain", "Pemain", 340, "w"),
            ("skor", "Total skor", 110, "e"), ("main", "Main", 70, "e")], 11)
        bungkus.pack(fill="both", expand=True)
        self.kosong = ttk.Label(self, text="", style="Sub.TLabel")
        self.kosong.pack(pady=8)
        self.isi("harian")

    def isi(self, periode):
        for p, b in self.tombol.items():
            b.configure(style="TabAktif.TButton" if p == periode else "TButton")
        self.label.configure(text=leaderboard.label_periode(periode))
        self.tree.delete(*self.tree.get_children())
        baris = leaderboard.hitung_leaderboard(self.db, periode)
        for b in baris:
            saya = b["user_id"] == self.app.pengguna["user_id"]
            self.tree.insert("", "end", tags=("saya",) if saya else (), values=(
                b["peringkat"], b["username"] + ("  (kamu)" if saya else ""), b["total_skor"], b["jumlah_main"]))
        self.kosong.configure(text="" if baris else "Belum ada permainan pada periode ini.")


# ---------------------------------------------------------------- kelola soal (Admin)
class LayarKelolaSoal(Layar):
    def __init__(self, app):
        super().__init__(app)
        self.bar_judul("Kelola Soal", "Tambah, ubah, atau hapus soal hangman angka.",
                       kembali=lambda: app.tampil(LayarMenuAdmin))
        baris = ttk.Frame(self)
        baris.pack(fill="x", pady=(0, 12))
        self.filter = None
        self.tombol = {}
        for nama, t in (("Semua", None),) + tuple((huruf_awal(t), t) for t in soal.TINGKAT):
            b = ttk.Button(baris, text=nama, command=lambda t=t: self.isi(t))
            b.pack(side="left", padx=(0, 8))
            self.tombol[t] = b
        ttk.Button(baris, text="+ Tambah soal", style="Utama.TButton",
                   command=lambda: self.form()).pack(side="right")
        bungkus, self.tree = self.tabel(self, [
            ("id", "ID", 60, "center"), ("tingkat", "Tingkat", 80, "center"), ("digit", "Digit", 60, "center"),
            ("jawaban", "Jawaban", 100, "center"), ("petunjuk", "Petunjuk", 440, "w")], 11)
        bungkus.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self.ubah())
        aksi = ttk.Frame(self)
        aksi.pack(fill="x", pady=(12, 0))
        ttk.Button(aksi, text="Ubah", command=self.ubah).pack(side="left")
        ttk.Button(aksi, text="Hapus", style="Bahaya.TButton", command=self.hapus).pack(side="left", padx=8)
        self.pesan = ttk.Label(aksi, text="", style="Sub.TLabel")
        self.pesan.pack(side="left", padx=10)
        self.isi(None)

    def isi(self, tingkat, pesan=None):
        self.filter = tingkat
        for t, b in self.tombol.items():
            b.configure(style="TabAktif.TButton" if t == tingkat else "TButton")
        self.tree.delete(*self.tree.get_children())
        for s in soal.daftar_soal(self.db, tingkat):
            self.tree.insert("", "end", iid=s["soal_id"], values=(
                s["soal_id"], huruf_awal(s["tingkat"]), s["jumlah_digit"], s["jawaban"], s["petunjuk"]))
        if pesan is not None:
            self.pesan.configure(text=pesan)

    def terpilih(self):
        pilih = self.tree.selection()
        if not pilih:
            self.pesan.configure(text="Pilih satu soal dulu.", foreground=SALAH)
            return None
        return soal.cari_soal(self.db, pilih[0])

    def form(self, s=None):
        FormSoal(self.app, self.db, s, setelah=lambda pesan: self.isi(self.filter, pesan))

    def ubah(self):
        s = self.terpilih()
        if s:
            self.form(s)

    def hapus(self):
        s = self.terpilih()
        if not s:
            return
        if messagebox.askyesno("Hapus soal", f"Hapus soal {s['soal_id']}?\n\n{s['petunjuk']}\n\n"
                               "Riwayat permainan lama tetap tersimpan."):
            ok, pesan = soal.hapus_soal(self.db, self.app.pengguna, s["soal_id"])
            if ok:
                data_store.simpan_data(self.db)
            self.isi(self.filter, pesan)


class FormSoal(tk.Toplevel):
    """Jendela form tambah/ubah soal."""

    def __init__(self, app, db, s, setelah):
        super().__init__(app)
        self.app, self.db, self.s, self.setelah = app, db, s, setelah
        self.title("Ubah soal" if s else "Tambah soal")
        self.configure(bg=BG, padx=22, pady=18)
        self.resizable(False, False)
        self.transient(app)
        ttk.Label(self, text="Ubah soal " + s["soal_id"] if s else "Soal baru", font=(FONT, 16, "bold")).pack(anchor="w")
        ttk.Label(self, text="Jawaban hanya angka 0-9, 2 sampai 10 digit.", style="Sub.TLabel").pack(anchor="w", pady=(0, 12))
        self.var_petunjuk = tk.StringVar(value=s["petunjuk"] if s else "")
        self.var_jawaban = tk.StringVar(value=s["jawaban"] if s else "")
        self.var_tingkat = tk.StringVar(value=huruf_awal(s["tingkat"]) if s else "Otomatis")
        ttk.Label(self, text="Petunjuk soal").pack(anchor="w")
        e1 = ttk.Entry(self, textvariable=self.var_petunjuk, width=52)
        e1.pack(fill="x", pady=(2, 10))
        ttk.Label(self, text="Jawaban (angka)").pack(anchor="w")
        ttk.Entry(self, textvariable=self.var_jawaban, width=20).pack(anchor="w", pady=(2, 10))
        ttk.Label(self, text="Tingkat").pack(anchor="w")
        nilai = [huruf_awal(t) for t in soal.TINGKAT]
        ttk.Combobox(self, textvariable=self.var_tingkat, state="readonly", width=17,
                     values=nilai if s else ["Otomatis"] + nilai).pack(anchor="w", pady=(2, 10))
        self.pesan = ttk.Label(self, text="", style="Galat.TLabel", wraplength=380)
        self.pesan.pack(anchor="w", pady=(0, 8))
        aksi = ttk.Frame(self)
        aksi.pack(fill="x")
        ttk.Button(aksi, text="Simpan", style="Utama.TButton", command=self.simpan).pack(side="left")
        ttk.Button(aksi, text="Batal", command=self.destroy).pack(side="left", padx=8)
        self.bind("<Return>", lambda e: self.simpan())
        self.bind("<Escape>", lambda e: self.destroy())
        e1.focus_set()
        self.grab_set()

    def simpan(self):
        teks = self.var_tingkat.get().lower()
        tingkat = None if teks == "otomatis" else teks
        pengguna = self.app.pengguna
        if self.s:
            ok, pesan = soal.ubah_soal(self.db, pengguna, self.s["soal_id"], self.var_petunjuk.get(),
                                       self.var_jawaban.get(), tingkat)
        else:
            ok, pesan = soal.tambah_soal(self.db, pengguna, self.var_petunjuk.get(), self.var_jawaban.get(), tingkat)
        if not ok:
            return self.pesan.configure(text=pesan)
        data_store.simpan_data(self.db)
        self.destroy()
        self.setelah(pesan)


# ---------------------------------------------------------------- aplikasi
class App(tk.Tk):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.pengguna = None
        self.layar = None
        self.title("NumHunter - Tebak Angka")
        self.configure(bg=BG)
        lebar, tinggi = 900, 680
        self.geometry(f"{lebar}x{tinggi}+{(self.winfo_screenwidth() - lebar) // 2}+"
                      f"{max(0, (self.winfo_screenheight() - tinggi) // 3)}")
        self.minsize(820, 640)
        pasang_gaya(self)
        self.protocol("WM_DELETE_WINDOW", self.tutup)
        self.tampil(LayarLogin)

    def tampil(self, kelas, **opsi):
        if self.layar is not None:
            self.layar.destroy()
        self.layar = kelas(self, **opsi)
        self.layar.pack(fill="both", expand=True)

    def masuk(self, pengguna):
        self.pengguna = pengguna
        self.tampil(LayarMenuAdmin if pengguna["role"] == auth.PERAN_ADMIN else LayarMenuPemain)

    def keluar(self):
        self.pengguna = None
        self.tampil(LayarLogin)

    def tutup(self):
        data_store.simpan_data(self.db)
        self.destroy()

def jalankan():
    db = data_store.muat_data()
    App(db).mainloop()
