# NumHunter - Game Tebak Angka (Hangman Angka) dengan Sistem Skor

Aplikasi desktop (GUI) Python berbasis tkinter dan PostgreSQL.
Di Linux, jika `import tkinter` gagal, pasang dulu paket `python3-tk`.

## Menjalankan
```
python main.py              # jalankan aplikasi (jendela GUI)
python test_numhunter.py    # jalankan pengujian otomatis
```
Akun Admin awal: `admin` / `admin123`. Akun pemain dibuat lewat menu **Daftar pemain**.
Data akun, soal, riwayat, skor, dan leaderboard tersimpan di PostgreSQL.

## Cara bermain
Pemain memilih soal berupa petunjuk, jawabannya deretan angka yang tersembunyi (`_ _ _ _`).
Tebak satu digit (0-9) per percobaan lewat tombol angka atau keyboard. Digit benar terbuka di
semua posisinya, digit salah mengurangi kesempatan (batas 5 kali salah). Menang bila semua digit terbuka.

## Tingkatan soal
Tidak ada level bertahap; pemain bebas memilih tingkat apa saja: **mudah**, **sedang**, **sulit**.
Tingkat ditentukan Admin saat menambah/mengubah soal. Jika dipilih "Otomatis", tingkat diambil dari
jumlah digit (sampai 3 digit mudah, 4 sedang, 5 ke atas sulit). Rumus skor sama untuk semua tingkat.

## Skor
Kalah atau menyerah = 0. Menang = 100 dikurangi 10 untuk setiap percobaan yang melebihi
percobaan minimum (banyak digit berbeda pada jawaban). Semakin sedikit percobaan, semakin tinggi skor.

## Pembagian berkas (sesuai kegiatan pada timeline)
| Kegiatan | Berkas |
| --- | --- |
| 3. Struktur data dan data awal | `data_store.py` |
| 4. Login dan hak akses peran | `auth.py` |
| 5. Kelola soal Admin | `soal.py` |
| 6. Logika permainan hangman angka | `game.py` |
| 7. Sistem skor dan hasil ronde | `skor.py` |
| 8. Riwayat dan leaderboard | `riwayat.py`, `leaderboard.py` |
| 9. Navigasi dan tampilan GUI | `gui.py` (layar), `main.py` (titik masuk) |
| Pengujian | `test_numhunter.py` |

Modul 3-8 tidak memakai `input()`/`print()` maupun tkinter; semua tampilan hanya ada di `gui.py`.

## Aturan akun dan petunjuk soal
- Username pemain: hanya huruf dan angka, wajib memiliki minimal 8 huruf; jumlah angka bebas dan tidak ada batas maksimal angka.
- Password: 3-5 karakter dan wajib memuat huruf, angka, serta simbol (tanpa spasi).
- Petunjuk soal: minimal 15 huruf, maksimal 150 karakter; hanya huruf, spasi, dan tanda tanya (?) yang diperbolehkan.


## Database PostgreSQL

NumHunter menggunakan PostgreSQL sebagai penyimpanan utama. File JSON tidak digunakan.
Koneksi dan struktur tabel mengikuti file `db.py`.

### Persiapan pertama
1. Pastikan PostgreSQL sudah aktif.
2. Buat database bernama `db` melalui pgAdmin atau perintah SQL `CREATE DATABASE db;`.
3. Buka `db.py`, lalu sesuaikan `KONFIGURASI` (host, port, dbname, user, password) dengan PostgreSQL di komputer.
4. Pasang library koneksi:
   `pip install psycopg2-binary`
5. Jalankan `python db.py setup` satu kali. Perintah ini hanya membuat tabel dan data awal jika tabel `users` belum ada; tidak menghapus data yang sudah tersimpan.
6. Jalankan aplikasi dengan `python main.py`.

### Catatan
- Pastikan nama database dan akun PostgreSQL sesuai dengan `KONFIGURASI` pada `db.py`.
- Jangan menjalankan perintah DROP TABLE secara manual jika ingin mempertahankan data.
- Tidak perlu membuat atau mengisi file JSON.


### Perbaikan migrasi PostgreSQL
Saat aplikasi dijalankan, `db.py` akan melepas sementara view `v_riwayat_lengkap`,
mengubah tipe kolom `users.username`, memasang kembali aturan username, lalu
membuat ulang view tersebut. Data lama tidak dihapus. Constraint dipasang
dengan `NOT VALID` agar data akun lama yang tidak sesuai aturan baru tetap
dapat dibaca, sedangkan data baru tetap diperiksa oleh PostgreSQL.
