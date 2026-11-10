# NumHunter - Game Tebak Angka (Hangman Angka) dengan Sistem Skor

Aplikasi desktop (GUI) Python berbasis tkinter, bawaan Python 3.8+ (tanpa pustaka tambahan).
Di Linux, jika `import tkinter` gagal, pasang dulu paket `python3-tk`.

## Menjalankan
```
python main.py              # jalankan aplikasi (jendela GUI)
python test_numhunter.py    # jalankan pengujian otomatis
```
Akun Admin awal: `admin` / `admin123`. Akun pemain dibuat lewat menu **Daftar akun pemain**.
Data tersimpan di `data/db.json` (dibuat otomatis; hapus file ini untuk kembali ke data awal).

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
