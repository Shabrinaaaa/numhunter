import sys

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
    RealDictCursor = None

KONFIGURASI = {
    "host": "localhost",
    "port": "5432",
    "dbname": "algo_numhunter",
    "user": "postgres",
    "password": "shbrinankayam80",
}


def koneksi():
    if psycopg2 is None:
        raise RuntimeError(
            "Library psycopg2 belum terpasang. Jalankan: pip install psycopg2-binary"
        )
    return psycopg2.connect(cursor_factory=RealDictCursor, **KONFIGURASI)


SQL_TABEL = """
CREATE TABLE users (
    user_id   VARCHAR(10) PRIMARY KEY,
    username  TEXT        NOT NULL,
    password  TEXT        NOT NULL,
    role      VARCHAR(10) NOT NULL,
    CONSTRAINT ck_users_role     CHECK (role IN ('admin', 'pemain')),
    CONSTRAINT ck_users_username CHECK (
        (role = 'admin' AND username = 'admin')
        OR
        (username ~ '^[A-Za-z0-9]+$'
         AND LENGTH(REGEXP_REPLACE(username, '[^A-Za-z]', '', 'g')) >= 8)
    )
);
CREATE UNIQUE INDEX uq_users_username_lower ON users (LOWER(username));

CREATE TABLE soal (
    soal_id       VARCHAR(10)  PRIMARY KEY,
    petunjuk      VARCHAR(150) NOT NULL,
    jawaban       VARCHAR(10)  NOT NULL,
    jumlah_digit  INTEGER GENERATED ALWAYS AS (LENGTH(jawaban)) STORED,
    tingkat       VARCHAR(10)  NOT NULL,
    dibuat_oleh   VARCHAR(10)  REFERENCES users (user_id)
                      ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT ck_soal_petunjuk CHECK (LENGTH(TRIM(petunjuk)) > 0),
    CONSTRAINT ck_soal_jawaban  CHECK (jawaban ~ '^[0-9]{2,10}$'),
    CONSTRAINT ck_soal_tingkat  CHECK (tingkat IN ('mudah', 'sedang', 'sulit'))
);
CREATE UNIQUE INDEX uq_soal_petunjuk_lower ON soal (LOWER(TRIM(petunjuk)));

CREATE TABLE riwayat (
    riwayat_id        VARCHAR(10) PRIMARY KEY,
    user_id           VARCHAR(10) NOT NULL REFERENCES users (user_id)
                          ON UPDATE CASCADE ON DELETE CASCADE,
    soal_id           VARCHAR(10) REFERENCES soal (soal_id)
                          ON UPDATE CASCADE ON DELETE SET NULL,
    skor              INTEGER     NOT NULL DEFAULT 0,
    status            VARCHAR(10) NOT NULL,
    jumlah_percobaan  INTEGER     NOT NULL DEFAULT 0,
    waktu_main        TIMESTAMP   NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_riwayat_skor      CHECK (skor BETWEEN 0 AND 100),
    CONSTRAINT ck_riwayat_status    CHECK (status IN ('menang', 'kalah')),
    CONSTRAINT ck_riwayat_percobaan CHECK (jumlah_percobaan >= 0),
    CONSTRAINT ck_riwayat_kalah_nol CHECK (status = 'menang' OR skor = 0)
);
CREATE INDEX idx_riwayat_user  ON riwayat (user_id);
CREATE INDEX idx_riwayat_soal  ON riwayat (soal_id);
CREATE INDEX idx_riwayat_waktu ON riwayat (waktu_main);

CREATE VIEW v_riwayat_lengkap AS
SELECT r.riwayat_id, r.user_id, u.username, r.soal_id, s.petunjuk, s.tingkat,
       r.status, r.jumlah_percobaan, r.skor, r.waktu_main
FROM riwayat r
JOIN users u     ON u.user_id = r.user_id
LEFT JOIN soal s ON s.soal_id = r.soal_id;
"""

# ---------------------------------------------------------------------
# Data awal untuk PostgreSQL
# ---------------------------------------------------------------------
DATA_USERS = [
    ("U001", "admin", "0ac596174a4c7392cd08442fba1523c4$c5cbc2a4ad50a6a8291c22022c0eb7f23e0ec41aaccfc2dbc0b1b1bb21fa3862", "admin"),
    ("U002", "Shabrina", "233dd84d94442b0c05503180082c4329$4dbbb1ab17324aa491c6dd505ccd5909f6f3bcca90ce3ebd3a5f65333b255bf3", "pemain"),
    ("U003", "PemainUtama123", "16a8d48df440a5c0f66d607098aead7a$3f128c8c2180574137baf702f4a3868c5c9da54f30d0c154d621242f8e652e47", "pemain"),
]

DATA_SOAL = [
    ("S001", "Berapa nomor telepon darurat Polisi di Indonesia?", "110", "mudah", "U001"),
    ("S002", "Berapa hasil dari 12 dikali 12?", "144", "mudah", "U001"),
    ("S003", "Berapa jumlah jam dalam satu minggu?", "168", "mudah", "U001"),
    ("S004", "Berapa jumlah hari dalam satu tahun biasa (bukan kabisat)?", "365", "mudah", "U001"),
    ("S005", "Tahun berapa Indonesia merdeka?", "1945", "sedang", "U001"),
    ("S006", "Tahun berapa Sumpah Pemuda diikrarkan?", "1928", "sedang", "U001"),
    ("S007", "Berapa menit dalam satu hari?", "1440", "sedang", "U001"),
    ("S008", "Berapa detik dalam satu jam?", "3600", "sedang", "U001"),
    ("S009", "Berapa detik dalam satu hari?", "86400", "sulit", "U001"),
    ("S010", "Berapa hasil dari 2 pangkat 16?", "65536", "sulit", "U001"),
    ("S011", "Berapa hasil dari 999 dikali 999?", "998001", "sulit", "U001"),
    ("S012", "tanggal lahir bina", "18", "mudah", "U001"),
    ("S014", "123456665656", "12", "mudah", "U001"),
]

DATA_RIWAYAT = [
    ("R001", "U002", "S014", 0, "kalah", 0, "2026-11-10 12:01:35"),
    ("R002", "U002", "S001", 90, "menang", 3, "2026-11-10 12:03:39"),
    ("R003", "U002", "S011", 100, "menang", 4, "2026-11-10 12:04:16"),
    ("R004", "U002", "S003", 60, "menang", 7, "2026-11-10 12:06:19"),
    ("R005", "U003", "S001", 100, "menang", 2, "2026-11-10 12:29:43"),
    ("R006", "U003", "S001", 100, "menang", 2, "2026-11-10 12:30:03"),
    ("R007", "U003", "S012", 0, "kalah", 1, "2026-11-10 12:33:44"),
    ("R008", "U003", "S012", 0, "kalah", 2, "2026-11-10 12:36:31"),
]


def siapkan_database(conn=None):
    """Siapkan PostgreSQL tanpa menghapus tabel atau data yang sudah ada."""
    if conn is not None:
        conn.close()
    pastikan_database()


def pastikan_database():
    """Buat tabel dan isi data awal hanya jika database belum memiliki tabel users.

    Fungsi ini tidak menghapus database yang sudah ada.
    """
    conn = koneksi()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('public.users') AS ada")
            if cur.fetchone()["ada"] is None:
                cur.execute(SQL_TABEL)
                cur.executemany(
                    "INSERT INTO users (user_id, username, password, role) VALUES (%s, %s, %s, %s)",
                    DATA_USERS)
                cur.executemany(
                    "INSERT INTO soal (soal_id, petunjuk, jawaban, tingkat, dibuat_oleh) "
                    "VALUES (%s, %s, %s, %s, %s)", DATA_SOAL)
                cur.executemany(
                    "INSERT INTO riwayat (riwayat_id, user_id, soal_id, skor, status, "
                    "jumlah_percobaan, waktu_main) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    DATA_RIWAYAT)

            # Migrasi aman untuk database versi lama.
            # View harus dilepas sementara karena menggunakan kolom users.username.
            cur.execute("DROP VIEW IF EXISTS v_riwayat_lengkap")
            cur.execute("ALTER TABLE users ALTER COLUMN username TYPE TEXT")

            # Aturan username pemain: minimal 8 huruf, angka boleh bebas,
            # dan hanya huruf serta angka yang diperbolehkan.
            cur.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS ck_users_username")
            cur.execute(
                """
                ALTER TABLE users ADD CONSTRAINT ck_users_username
                CHECK (
                    (role = 'admin' AND username = 'admin')
                    OR
                    (
                        role = 'pemain'
                        AND username ~ '^[A-Za-z0-9]+$'
                        AND LENGTH(
                            REGEXP_REPLACE(username, '[^A-Za-z]', '', 'g')
                        ) >= 8
                    )
                ) NOT VALID
                """
            )

            # Buat kembali view setelah perubahan kolom selesai.
            cur.execute(
                """
                CREATE VIEW v_riwayat_lengkap AS
                SELECT r.riwayat_id, r.user_id, u.username, r.soal_id,
                       s.petunjuk, s.tingkat, r.status, r.jumlah_percobaan,
                       r.skor, r.waktu_main
                FROM riwayat r
                JOIN users u ON u.user_id = r.user_id
                LEFT JOIN soal s ON s.soal_id = r.soal_id
                """
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


_TABEL_ID = {
    "U": ("users", "user_id"),
    "S": ("soal", "soal_id"),
    "R": ("riwayat", "riwayat_id"),
}


def id_baru(cur, prefix):
    """ID berikutnya, mis. S015. Prefix: 'U' (users), 'S' (soal), 'R' (riwayat)."""
    tabel, kolom = _TABEL_ID[prefix]
    cur.execute(
        f"SELECT COALESCE(MAX(SUBSTRING({kolom} FROM 2)::INT), 0) + 1 AS n FROM {tabel}")
    return f"{prefix}{cur.fetchone()['n']:03d}"


def cari_user(cur, username):
    cur.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(%s)", (username.strip(),))
    return cur.fetchone()


def cari_user_id(cur, user_id):
    cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    return cur.fetchone()


def tambah_pemain(cur, username, password_hash):
    """password_hash dari auth.hash_password()."""
    user_id = id_baru(cur, "U")
    cur.execute(
        "INSERT INTO users (user_id, username, password, role) VALUES (%s, %s, %s, 'pemain')",
        (user_id, username.strip(), password_hash))
    return user_id



def daftar_soal(cur, tingkat=None):
    if tingkat is None:
        cur.execute("SELECT * FROM soal ORDER BY soal_id")
    else:
        cur.execute("SELECT * FROM soal WHERE tingkat = %s ORDER BY soal_id", (tingkat,))
    return cur.fetchall()


def cari_soal(cur, soal_id):
    cur.execute("SELECT * FROM soal WHERE LOWER(soal_id) = LOWER(%s)", (soal_id.strip(),))
    return cur.fetchone()


def tambah_soal(cur, admin_id, petunjuk, jawaban, tingkat):
    soal_id = id_baru(cur, "S")
    cur.execute(
        "INSERT INTO soal (soal_id, petunjuk, jawaban, tingkat, dibuat_oleh) "
        "VALUES (%s, %s, %s, %s, %s)",
        (soal_id, petunjuk.strip(), jawaban.strip(), tingkat, admin_id))
    return soal_id


def ubah_soal(cur, soal_id, petunjuk, jawaban, tingkat):
    cur.execute(
        "UPDATE soal SET petunjuk = %s, jawaban = %s, tingkat = %s WHERE soal_id = %s",
        (petunjuk.strip(), jawaban.strip(), tingkat, soal_id))
    return cur.rowcount > 0


def hapus_soal(cur, soal_id):
    """Riwayat lama tetap ada (soal_id di riwayat menjadi NULL)."""
    cur.execute("DELETE FROM soal WHERE soal_id = %s", (soal_id,))
    return cur.rowcount > 0


# ---------------------------------------------------------------------
# Query: riwayat (riwayat.py)
# ---------------------------------------------------------------------
def catat_riwayat(cur, user_id, soal_id, skor, status, jumlah_percobaan):
    riwayat_id = id_baru(cur, "R")
    cur.execute(
        "INSERT INTO riwayat (riwayat_id, user_id, soal_id, skor, status, jumlah_percobaan) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (riwayat_id, user_id, soal_id, skor, status, jumlah_percobaan))
    return riwayat_id


def riwayat_pemain(cur, user_id, status=None):
    """Terbaru lebih dulu. status: None / 'menang' / 'kalah'."""
    cur.execute(
        "SELECT * FROM v_riwayat_lengkap "
        "WHERE user_id = %s AND (%s::text IS NULL OR status = %s) "
        "ORDER BY waktu_main DESC, riwayat_id DESC",
        (user_id, status, status))
    return cur.fetchall()


def soal_belum_dimainkan(cur, user_id):
    cur.execute(
        "SELECT * FROM soal WHERE soal_id NOT IN "
        "(SELECT soal_id FROM riwayat WHERE user_id = %s AND soal_id IS NOT NULL) "
        "ORDER BY soal_id", (user_id,))
    return cur.fetchall()


_PERIODE = {   # nama periode -> (satuan date_trunc, panjang periode)
    "harian": ("day", "1 day"),
    "mingguan": ("week", "1 week"),    # minggu mulai hari Senin
    "bulanan": ("month", "1 month"),
    "tahunan": ("year", "1 year"),
}


def leaderboard(cur, periode, acuan=None):
    """Peringkat pemain pada periode yang memuat tanggal acuan (default hari ini).
    Skor sama = peringkat sama (1, 1, 3)."""
    satuan, panjang = _PERIODE[periode]
    cur.execute(
        """
        SELECT RANK() OVER (ORDER BY SUM(r.skor) DESC) AS peringkat,
               u.user_id, u.username,
               SUM(r.skor) AS total_skor,
               COUNT(*)    AS jumlah_main
        FROM riwayat r
        JOIN users u ON u.user_id = r.user_id
        WHERE r.waktu_main >= date_trunc(%(satuan)s, COALESCE(%(acuan)s::timestamp, NOW()::timestamp))
          AND r.waktu_main <  date_trunc(%(satuan)s, COALESCE(%(acuan)s::timestamp, NOW()::timestamp))
                              + %(panjang)s::interval
        GROUP BY u.user_id, u.username
        ORDER BY total_skor DESC, LOWER(u.username)
        """,
        {"satuan": satuan, "panjang": panjang, "acuan": acuan})
    return cur.fetchall()


def statistik_pemain(cur):
    cur.execute(
        """
        SELECT u.username,
               COUNT(r.riwayat_id)                         AS total_main,
               COUNT(*) FILTER (WHERE r.status = 'menang') AS menang,
               COUNT(*) FILTER (WHERE r.status = 'kalah')  AS kalah,
               COALESCE(SUM(r.skor), 0)                    AS total_skor,
               ROUND(AVG(r.skor), 2)                       AS rata_rata_skor
        FROM users u
        LEFT JOIN riwayat r ON r.user_id = u.user_id
        WHERE u.role = 'pemain'
        GROUP BY u.user_id, u.username
        ORDER BY total_skor DESC
        """)
    return cur.fetchall()


def statistik_soal(cur):
    cur.execute(
        """
        SELECT s.soal_id, s.petunjuk, s.tingkat,
               COUNT(r.riwayat_id)                         AS dimainkan,
               COUNT(*) FILTER (WHERE r.status = 'menang') AS menang,
               ROUND(AVG(r.skor), 2)                       AS rata_rata_skor
        FROM soal s
        LEFT JOIN riwayat r ON r.soal_id = s.soal_id
        GROUP BY s.soal_id, s.petunjuk, s.tingkat
        ORDER BY s.soal_id
        """)
    return cur.fetchall()


# ---------------------------------------------------------------------
# Demo: jalankan semua query dan cetak hasilnya
# ---------------------------------------------------------------------
def _cetak(judul, baris):
    print(f"\n=== {judul} ===")
    if not baris:
        print("(kosong)")
    for b in (baris if isinstance(baris, list) else [baris]):
        print(dict(b) if b else None)


def demo(conn):
    with conn.cursor() as cur:
        _cetak("Cari user 'shabrina'", cari_user(cur, "shabrina"))
        _cetak("Soal tingkat sedang", daftar_soal(cur, "sedang"))
        _cetak("Riwayat Shabrina (U002)", riwayat_pemain(cur, "U002"))
        _cetak("Riwayat Shabrina, hanya menang", riwayat_pemain(cur, "U002", "menang"))
        _cetak("Soal belum dimainkan U002", soal_belum_dimainkan(cur, "U002"))
        _cetak("Leaderboard bulanan (acuan 2026-11-10)", leaderboard(cur, "bulanan", "2026-11-10"))
        _cetak("Leaderboard harian (acuan 2026-11-10)", leaderboard(cur, "harian", "2026-11-10"))
        _cetak("Statistik pemain", statistik_pemain(cur))
        _cetak("Statistik soal", statistik_soal(cur))


def main():
    perintah = sys.argv[1] if len(sys.argv) > 1 else "demo"
    if perintah == "setup":
        pastikan_database()
        print("Database siap digunakan. Data lama tidak dihapus.")
    elif perintah == "demo":
        conn = koneksi()
        try:
            demo(conn)
        finally:
            conn.close()
    else:
        print("Perintah: python db.py setup | demo")


if __name__ == "__main__":
    main()
