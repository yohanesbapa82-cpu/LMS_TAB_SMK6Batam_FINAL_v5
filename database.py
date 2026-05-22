"""
Database layer untuk LMS Alat Berat - SMK Negeri 6 Batam
"""
import sqlite3, hashlib
from contextlib import contextmanager

DB_NAME = "lms_alat_berat.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@contextmanager
def get_db():
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()
def verify_password(p, h): return hash_password(p) == h

def get_user_by_username(username):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        row = c.fetchone()
        return dict(row) if row else None

def init_database():
    with get_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nama_lengkap TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('guru','siswa')),
            kelas TEXT DEFAULT '',
            nis TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS materi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            judul TEXT NOT NULL,
            tujuan_pembelajaran TEXT,
            isi_materi TEXT,
            link_video TEXT,
            kategori TEXT NOT NULL,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_path  TEXT DEFAULT '',
            file_type  TEXT DEFAULT '',
            FOREIGN KEY (created_by) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS soal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            materi_id INTEGER NOT NULL,
            pertanyaan TEXT NOT NULL,
            opsi_a TEXT NOT NULL, opsi_b TEXT NOT NULL,
            opsi_c TEXT NOT NULL, opsi_d TEXT NOT NULL,
            jawaban_benar TEXT NOT NULL CHECK(jawaban_benar IN ('A','B','C','D')),
            created_by INTEGER,
            FOREIGN KEY (materi_id) REFERENCES materi(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS nilai_teori (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            siswa_id INTEGER NOT NULL, materi_id INTEGER NOT NULL,
            skor REAL NOT NULL,
            tanggal TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (siswa_id) REFERENCES users(id),
            FOREIGN KEY (materi_id) REFERENCES materi(id)
        );
        CREATE TABLE IF NOT EXISTS nilai_praktik (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            siswa_id INTEGER NOT NULL,
            modul_praktik TEXT NOT NULL,
            safety REAL NOT NULL, prosedur REAL NOT NULL, hasil REAL NOT NULL,
            nilai_praktik REAL NOT NULL,
            foto_praktik TEXT, catatan TEXT DEFAULT '',
            tanggal TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            assessed_by INTEGER,
            FOREIGN KEY (siswa_id) REFERENCES users(id),
            FOREIGN KEY (assessed_by) REFERENCES users(id)
        );
        -- Jadwal ujian dibuat guru
        CREATE TABLE IF NOT EXISTS ujian_jadwal (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            judul           TEXT    NOT NULL,
            materi_id       INTEGER,
            durasi_menit    INTEGER DEFAULT 60,
            max_soal        INTEGER DEFAULT 10,
            acak_soal       INTEGER DEFAULT 1,
            tanggal_mulai   TIMESTAMP,
            tanggal_selesai TIMESTAMP,
            status          TEXT    DEFAULT 'draft'
                            CHECK(status IN ('draft','aktif','selesai')),
            syarat_materi   INTEGER DEFAULT 1,
            created_by      INTEGER,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (materi_id)   REFERENCES materi(id),
            FOREIGN KEY (created_by)  REFERENCES users(id)
        );

        -- Tracking siswa sudah baca/selesai materi
        CREATE TABLE IF NOT EXISTS materi_progress (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            siswa_id        INTEGER NOT NULL,
            materi_id       INTEGER NOT NULL,
            selesai         INTEGER DEFAULT 0,
            tanggal_selesai TIMESTAMP,
            UNIQUE(siswa_id, materi_id),
            FOREIGN KEY (siswa_id)  REFERENCES users(id),
            FOREIGN KEY (materi_id) REFERENCES materi(id)
        );

        -- Sesi ujian per siswa per jadwal
        CREATE TABLE IF NOT EXISTS ujian_sesi (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            jadwal_id       INTEGER NOT NULL,
            siswa_id        INTEGER NOT NULL,
            mulai_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            selesai_at      TIMESTAMP,
            total_soal      INTEGER DEFAULT 0,
            benar           INTEGER DEFAULT 0,
            skor            REAL    DEFAULT 0,
            status          TEXT    DEFAULT 'berlangsung'
                            CHECK(status IN ('berlangsung','selesai')),
            FOREIGN KEY (jadwal_id) REFERENCES ujian_jadwal(id),
            FOREIGN KEY (siswa_id)  REFERENCES users(id)
        );

        -- Jawaban per soal per sesi
        CREATE TABLE IF NOT EXISTS ujian_jawaban (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            sesi_id         INTEGER NOT NULL,
            soal_id         INTEGER NOT NULL,
            jawaban_siswa   TEXT,
            is_correct      INTEGER DEFAULT 0,
            FOREIGN KEY (sesi_id) REFERENCES ujian_sesi(id) ON DELETE CASCADE,
            FOREIGN KEY (soal_id) REFERENCES soal(id)
        );

        CREATE INDEX IF NOT EXISTS idx_uu   ON users(username);
        CREATE INDEX IF NOT EXISTS idx_sm   ON soal(materi_id);
        CREATE INDEX IF NOT EXISTS idx_nts  ON nilai_teori(siswa_id);
        CREATE INDEX IF NOT EXISTS idx_nps  ON nilai_praktik(siswa_id);
        CREATE INDEX IF NOT EXISTS idx_mp   ON materi_progress(siswa_id,materi_id);
        CREATE INDEX IF NOT EXISTS idx_us   ON ujian_sesi(jadwal_id,siswa_id);
        """)
    # Migrasi tabel baru (idempotent)
    with get_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS ujian_jadwal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            materi_id INTEGER NOT NULL,
            judul_ujian TEXT NOT NULL,
            guru_id INTEGER NOT NULL,
            tanggal_mulai TIMESTAMP NOT NULL,
            tanggal_selesai TIMESTAMP NOT NULL,
            durasi_menit INTEGER DEFAULT 60,
            acak_soal INTEGER DEFAULT 1,
            jumlah_soal INTEGER DEFAULT 10,
            status TEXT DEFAULT 'aktif' CHECK(status IN ('aktif','nonaktif','selesai')),
            keterangan TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (materi_id) REFERENCES materi(id),
            FOREIGN KEY (guru_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS materi_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            siswa_id INTEGER NOT NULL,
            materi_id INTEGER NOT NULL,
            selesai INTEGER DEFAULT 0,
            tanggal_selesai TIMESTAMP,
            UNIQUE(siswa_id, materi_id),
            FOREIGN KEY (siswa_id) REFERENCES users(id),
            FOREIGN KEY (materi_id) REFERENCES materi(id)
        );
        CREATE TABLE IF NOT EXISTS ujian_sesi_baru (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jadwal_id INTEGER NOT NULL,
            siswa_id INTEGER NOT NULL,
            mulai_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            selesai_at TIMESTAMP,
            durasi_detik INTEGER DEFAULT 0,
            total_soal INTEGER DEFAULT 0,
            benar INTEGER DEFAULT 0,
            skor REAL DEFAULT 0,
            sudah_submit INTEGER DEFAULT 0,
            UNIQUE(jadwal_id, siswa_id),
            FOREIGN KEY (jadwal_id) REFERENCES ujian_jadwal(id),
            FOREIGN KEY (siswa_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS ujian_jawaban_baru (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sesi_id INTEGER NOT NULL,
            soal_id INTEGER NOT NULL,
            pertanyaan TEXT,
            opsi_a TEXT, opsi_b TEXT, opsi_c TEXT, opsi_d TEXT,
            jawaban_benar TEXT,
            jawaban_siswa TEXT DEFAULT '',
            is_correct INTEGER DEFAULT 0,
            FOREIGN KEY (sesi_id) REFERENCES ujian_sesi_baru(id)
        );
        CREATE INDEX IF NOT EXISTS idx_uj_materi ON ujian_jadwal(materi_id);
        CREATE INDEX IF NOT EXISTS idx_mp_siswa ON materi_progress(siswa_id);
        CREATE INDEX IF NOT EXISTS idx_usb_jadwal ON ujian_sesi_baru(jadwal_id);
        CREATE INDEX IF NOT EXISTS idx_ujb_sesi ON ujian_jawaban_baru(sesi_id);
        """)
    _seed_data()
    seed_jobsheet()

def _seed_data():
    with get_db() as conn:
        c = conn.cursor()
        # Safe migrations — tambah kolom baru jika belum ada
        for migration in [
            "ALTER TABLE users ADD COLUMN nis TEXT DEFAULT ''",
            "ALTER TABLE materi ADD COLUMN file_path TEXT DEFAULT ''",
            "ALTER TABLE materi ADD COLUMN file_type TEXT DEFAULT ''",
        ]:
            try:
                c.execute(migration)
                conn.commit()
            except Exception:
                pass  # Kolom sudah ada

        if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
            return

        pw_guru  = hash_password("guru123")
        pw_siswa = hash_password("siswa123")

        # ── GURU (5 orang) ────────────────────────────────────────────────
        # username: nama depan lowercase, password: guru123
        guru = [
            ("yohanes", pw_guru, "Yohanes Bapa Mukin, S.T.",       "guru", "", ""),
            ("nurkomar", pw_guru, "Nur Komar Akbar, S.Pd.",         "guru", "", ""),
            ("andrew",   pw_guru, "Andrew Marciano Medellu, S.Pd.", "guru", "", ""),
            ("rizky",    pw_guru, "Rizky Kurniawan, S.Pd.",         "guru", "", ""),
            ("arifan",   pw_guru, "Arifan Asnaga Yusuf, S.Pd.",    "guru", "", ""),
        ]

        # ── SISWA KELAS XI TAB ────────────────────────────────────────────
        # username: NIS tanpa titik, password: siswa123
        siswa_data = [
            ("244464", "Adelberth Mario Marcelino",             "244464"),
            ("244465", "Ahmad Maolana",                         "244465"),
            ("244466", "Ahmad Putra Karim",                     "244466"),
            ("244467", "Alfonsus Luguory Kleden",               "244467"),
            ("244468", "Alghifari Akbar Auwinez Aulia Ansori",  "244468"),
            ("244469", "Alief Vio Revanza",                     "244469"),
            ("244471", "Andi Febryansyah",                      "244471"),
            ("244472", "Andika Putra",                          "244472"),
            ("244473", "Angga Sang Putra Dachi",                "244473"),
            ("244474", "Arkanjela Girlani Rionaldo",            "244474"),
            ("244475", "Bagus Respationo",                      "244475"),
            ("244476", "Bober Dwi Saktiawan",                   "244476"),
            ("244477", "Dandi",                                  "244477"),
            ("244478", "Dimas Almadany",                        "244478"),
            ("244479", "Dimas Meika Fiandra",                   "244479"),
            ("244480", "Ezar Nugraha",                          "244480"),
            ("244481", "Fadjar Khairu Kurniawan",               "244481"),
            ("244482", "Gabriel Dayren Timminurel",             "244482"),
            ("244483", "Gilang Ramadhan Putra",                 "244483"),
            ("244484", "Ikram Hadinata",                        "244484"),
            ("244485", "Jikraldo Sitorus",                      "244485"),
            ("244486", "Josephus Casafo Ratu",                  "244486"),
            ("244488", "Julianda Jazmi Zaki",                   "244488"),
            ("244489", "Kamal Syaputra Harahap",                "244489"),
            ("244490", "Kaysan Firas",                          "244490"),
            ("244491", "Leonel Misi Zai",                       "244491"),
            ("244492", "Lukman Hakim",                          "244492"),
            ("244493", "M. Yusup",                              "244493"),
            ("244494", "Mohammad Shofi'ul Fuad",                "244494"),
            ("244496", "Muhammad Rakha Alfarizi",               "244496"),
            ("244497", "Putra Inerazzurri Firgo",               "244497"),
            ("244498", "Radhitya Rohmana Putra",               "244498"),
            ("244499", "Ridho Kurniawan",                       "244499"),
            ("244500", "Ripaldo Pranata",                       "244500"),
            ("244501", "Saydita Charyati",                      "244501"),
            ("244502", "Tiyo",                                   "244502"),
            ("244504", "Zamzami Azri Ilham",                    "244504"),
            ("244505", "Zazky Angga Santigo",                   "244505"),
        ]
        siswa = [
            (username, pw_siswa, nama, "siswa", "XI TAB", nis)
            for username, nama, nis in siswa_data
        ]

        all_users = guru + siswa
        c.executemany(
            "INSERT INTO users(username,password,nama_lengkap,role,kelas,nis) VALUES(?,?,?,?,?,?)",
            all_users
        )
        conn.commit()
        # materi dan soal seed dilakukan di bawah
        _seed_materi(conn)
        _seed_soal(conn)

def _seed_materi(conn):
    c = conn.cursor()
    materi = [
        ("Sistem Hidrolik Alat Berat","Hydraulic",
         "Siswa memahami prinsip kerja sistem hidrolik dan mampu melakukan perawatan.",
         """# Sistem Hidrolik Alat Berat\n\n## Pendahuluan\nSistem hidrolik menggunakan **Hukum Pascal** sebagai dasar: tekanan pada fluida dalam ruang tertutup diteruskan ke segala arah sama besar.\n\n## Komponen Utama\n| Komponen | Fungsi |\n|---|---|\n| Pompa Hidrolik | Energi mekanik → hidrolik |\n| Silinder Hidrolik | Energi hidrolik → gerak linier |\n| Motor Hidrolik | Energi hidrolik → rotasi |\n| Control Valve | Mengatur arah & aliran |\n| Filter | Menyaring kontaminan |\n| Reservoir | Tangki penyimpan oli |\n\n## Perawatan\n1. Cek level oli setiap **10 jam**\n2. Ganti filter setiap **500 jam**\n3. Ganti oli setiap **2.000 jam**\n4. Monitor suhu oli — max **80°C**\n\n## ⚠️ K3\n- Tekanan sistem hingga **350 bar** — BAHAYA!\n- Selalu *release pressure* sebelum buka sistem\n- Gunakan APD lengkap\n""",
         "https://www.youtube.com/watch?v=ErCiSFaGAuE", 1),
        ("Perawatan Mesin Diesel","Engine",
         "Siswa mampu melaksanakan perawatan berkala mesin diesel sesuai jadwal PM.",
         """# Perawatan Mesin Diesel Alat Berat\n\n## Jadwal PM\n\n### Harian / 10 Jam\n- Cek level oli & coolant\n- Cek indikator filter udara\n- Drain water separator\n\n### 250 Jam\n- Ganti oli + filter oli\n- Cek belt tension\n\n### 500 Jam\n- Ganti filter BBM\n- Setel valve clearance\n\n## Troubleshooting\n| Gejala | Penyebab | Tindakan |\n|---|---|---|\n| Asap hitam | Filter udara kotor | Ganti filter |\n| Asap putih | Air di BBM | Cek head gasket |\n| Asap biru | Oli ke ruang bakar | Cek ring piston |\n| Overheat | Coolant kurang | Isi coolant |\n""",
         "", 1),
        ("Operasional Excavator PC200","Unit Spesifik",
         "Siswa mampu mengoperasikan Excavator Komatsu PC200 sesuai SOP dengan aman.",
         """# Operasional Excavator Komatsu PC200\n\n## Spesifikasi\n- Operating Weight: **20.100 kg**\n- Engine: Komatsu SAA6D107E-1, 110 kW\n- Bucket: 0,8 m³\n\n## Pre-Operation\n1. Cek track & undercarriage\n2. Cek bucket teeth\n3. Cek level fluida\n4. Cek lampu & alarm\n\n## Start-Up\n1. Naiki kabin dengan **3-point contact**\n2. Pasang **seatbelt** — WAJIB\n3. Posisi semua lever → **NETRAL**\n4. Key START → idle **3–5 menit**\n\n## ⛔ Larangan\n- Operasi di slope > 35%\n- Swing di atas orang\n- Melebihi rated load\n- Jarak < 3m dari kabel listrik\n""",
         "", 1),
        ("Sistem Kelistrikan Alat Berat","Kelistrikan",
         "Siswa memahami sistem kelistrikan dan mampu melakukan troubleshooting.",
         """# Sistem Kelistrikan Alat Berat\n\n## Komponen Utama\n\n### Baterai\n- Tegangan: **12V atau 24V** (2 baterai seri)\n- Normal: 12,5–12,7V (terisi penuh)\n\n### Alternator\n- Output: **27,5–29V** saat running\n- Fungsi: isi baterai & suplai beban\n\n### Starter Motor\n- Arus: 300–600 A saat cranking\n\n## Troubleshooting\n| Masalah | Cek |\n|---|---|\n| Tidak mau start | Baterai, starter, solenoid |\n| Lampu redup | Alternator, belt |\n| Baterai cepat habis | Parasitic drain |\n\n## ⚠️ Keselamatan\n- Lepas kabel **negatif** dulu\n- Waspadai gas H₂ saat charge\n- Gunakan fuse sesuai rating\n""",
         "", 1),
        ("Pengoperasian Forklift","Unit Spesifik",
         "Siswa mampu mengoperasikan forklift dengan aman dan efisien sesuai SOP.",
         """# Pengoperasian Forklift\n\n## Pre-Operation Checklist\n- [ ] Cek level oli & hidrolik\n- [ ] Cek kondisi fork (tidak retak/bengkok)\n- [ ] Cek rem service & parking\n- [ ] Cek klakson & lampu\n- [ ] Cek seatbelt\n\n## Prosedur Angkat Beban\n1. Dekati dengan kecepatan rendah\n2. Fork lurus dengan pallet\n3. Masukkan fork **2/3 panjang**\n4. Angkat **20–30 cm** dari lantai\n5. Tilt mast **ke belakang** sebelum jalan\n\n## ⛔ Larangan\n- JANGAN melebihi kapasitas\n- DILARANG membawa penumpang di fork\n- Load center standard: **500 mm** dari tumit fork\n\n## APD Wajib\nHelm | Sepatu Safety | Vest | Seatbelt\n""",
         "", 1),
    ]
    c.executemany(
        "INSERT INTO materi(judul,kategori,tujuan_pembelajaran,isi_materi,link_video,created_by) VALUES(?,?,?,?,?,?)",
        materi
    )
    conn.commit()

def _seed_soal(conn):
    c = conn.cursor()
    # Ambil id materi yang baru dibuat
    rows = c.execute("SELECT id FROM materi ORDER BY id").fetchall()
    if len(rows) < 5:
        return
    m = [r[0] for r in rows]  # [m1_id, m2_id, ...]

    soal = [
        # Hidrolik
        (m[0],"Hukum fisika dasar sistem hidrolik adalah...","Hukum Newton","Hukum Pascal","Hukum Archimedes","Hukum Ohm","B"),
        (m[0],"Pompa hidrolik berfungsi mengubah...","Energi listrik menjadi mekanik","Energi mekanik menjadi hidrolik","Energi panas menjadi mekanik","Energi hidrolik menjadi mekanik","B"),
        (m[0],"Tekanan kerja sistem hidrolik alat berat umumnya maksimal...","100 bar","200 bar","350 bar","500 bar","C"),
        (m[0],"Interval penggantian oli hidrolik alat berat adalah...","500 jam","1.000 jam","2.000 jam","5.000 jam","C"),
        (m[0],"Suhu maksimum oli hidrolik dalam operasi normal...","60°C","80°C","100°C","120°C","B"),
        (m[0],"Komponen yang mengubah energi hidrolik menjadi gerak linier...","Motor Hidrolik","Pompa Hidrolik","Silinder Hidrolik","Control Valve","C"),
        (m[0],"Sebelum membuka sistem hidrolik, langkah PERTAMA adalah...","Buka fitting langsung","Matikan mesin dan release pressure","Panaskan mesin dulu","Tutup semua valve","B"),
        (m[0],"Filter hidrolik harus diganti setiap berapa jam?","100 jam","250 jam","500 jam","1.000 jam","C"),
        # Engine
        (m[1],"Perawatan harian mesin diesel dilakukan setiap...","5 jam","10 jam","50 jam","100 jam","B"),
        (m[1],"Asap hitam tebal menandakan kemungkinan...","Coolant bocor","Filter udara kotor / injektor bermasalah","Aki lemah","Oli bocor ke knalpot","B"),
        (m[1],"Interval penggantian oli mesin diesel standar adalah...","100 jam","250 jam","500 jam","1.000 jam","B"),
        (m[1],"Langkah PERTAMA ganti oli mesin yang benar adalah...","Buka drain plug","Isi oli baru","Panaskan mesin ±5 menit","Matikan mesin langsung","C"),
        (m[1],"Asap biru dari knalpot biasanya disebabkan...","BBM berlebih","Air masuk ruang bakar","Oli masuk ruang bakar","Filter udara kotor","C"),
        (m[1],"Water separator berfungsi untuk...","Mendinginkan bahan bakar","Memisahkan air dari bahan bakar","Menyaring debu dari udara","Mengatur tekanan bahan bakar","B"),
        (m[1],"Mesin perlu idle 3–5 menit setelah start agar...","Kabin menjadi hangat","Bahan bakar memanas","Oli bersirkulasi ke semua komponen","Baterai terisi penuh","C"),
        # Excavator
        (m[2],"Operating weight Komatsu PC200 adalah...","10.100 kg","15.000 kg","20.100 kg","25.000 kg","C"),
        (m[2],"Kemiringan operasi maksimum excavator...","15%","25%","35%","50%","C"),
        (m[2],"Naiki kabin excavator menggunakan prinsip...","1-point contact","2-point contact","3-point contact","4-point contact","C"),
        (m[2],"Setelah start, excavator harus idle selama...","30 detik","1 menit","3–5 menit","10 menit","C"),
        (m[2],"APD wajib operator excavator adalah...","Masker saja","Kacamata saja","Helm, rompi, sepatu safety","Sarung tangan saja","C"),
        (m[2],"Jarak minimum aman dari kabel listrik saat operasi excavator...","1 meter","3 meter","5 meter","10 meter","B"),
        (m[2],"Bucket capacity Komatsu PC200 adalah...","0,5 m³","0,8 m³","1,2 m³","1,5 m³","B"),
        # Kelistrikan
        (m[3],"Tegangan baterai 12V terisi penuh adalah...","11V","12,5–12,7V","13,5V","14V","B"),
        (m[3],"Tegangan output alternator normal saat engine running...","12–14V","24–26V","27,5–29V","30–32V","C"),
        (m[3],"Saat ganti baterai, kabel yang dilepas PERTAMA...","Kabel positif","Kabel negatif","Keduanya sekaligus","Terserah urutan","B"),
        (m[3],"Gas berbahaya yang dihasilkan saat charge baterai adalah...","CO₂","O₂","H₂ (Hidrogen)","N₂","C"),
        (m[3],"Specific gravity baterai terisi penuh adalah...","1,10–1,15","1,20–1,22","1,26–1,28","1,30–1,35","C"),
        # Forklift
        (m[4],"Fork dimasukkan sampai kedalaman berapa panjang fork?","1/3 panjang","1/2 panjang","2/3 panjang","Penuh sampai mast","C"),
        (m[4],"Load center standar forklift adalah...","300 mm dari tumit fork","500 mm dari tumit fork","700 mm dari tumit fork","1.000 mm dari tumit fork","B"),
        (m[4],"Posisi mast saat membawa beban bergerak adalah...","Tilt maju","Tilt ke belakang","Tegak lurus","Miring ke kiri","B"),
        (m[4],"Tindakan yang DILARANG keras pada operasi forklift...","Cek kondisi ban","Membawa penumpang di fork","Menggunakan seatbelt","Cek kondisi chain","B"),
        (m[4],"Tinggi angkat beban saat bergerak di jalan adalah...","5 cm dari lantai","20–30 cm dari lantai","50 cm dari lantai","1 meter dari lantai","B"),
    ]
    c.executemany(
        "INSERT INTO soal(materi_id,pertanyaan,opsi_a,opsi_b,opsi_c,opsi_d,jawaban_benar,created_by) VALUES(?,?,?,?,?,?,?,1)",
        soal
    )
    conn.commit()

# ─── USER CRUD ────────────────────────────────────────────────────────────────
def create_user(username, password, nama_lengkap, role, kelas="", nis=""):
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO users(username,password,nama_lengkap,role,kelas,nis) VALUES(?,?,?,?,?,?)",
            (username, hash_password(password), nama_lengkap, role, kelas, nis)
        )
        return c.lastrowid

def update_user_password(uid, new_password):
    """Reset password user oleh guru."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET password=? WHERE id=?", (hash_password(new_password), uid))
        return c.rowcount > 0

def get_user_by_id(uid):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id=?", (uid,))
        r = c.fetchone()
        return dict(r) if r else None

def get_all_siswa():
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute(
            "SELECT * FROM users WHERE role='siswa' ORDER BY kelas,nama_lengkap").fetchall()]

def get_all_guru():
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute(
            "SELECT * FROM users WHERE role='guru' ORDER BY nama_lengkap").fetchall()]

def get_all_users():
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute(
            "SELECT id,username,nama_lengkap,role,kelas,nis,created_at FROM users ORDER BY role DESC,kelas,nama_lengkap").fetchall()]

def delete_user(uid):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM users WHERE id=?", (uid,))
        return c.rowcount > 0

# ─── MATERI CRUD ──────────────────────────────────────────────────────────────
def create_materi(judul, tujuan_pembelajaran, isi_materi, link_video, kategori, created_by, file_path="", file_type=""):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO materi(judul,tujuan_pembelajaran,isi_materi,link_video,kategori,created_by,file_path,file_type) VALUES(?,?,?,?,?,?,?,?)",
                  (judul, tujuan_pembelajaran, isi_materi, link_video, kategori, created_by, file_path, file_type))
        return c.lastrowid

def get_all_materi():
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute("""
            SELECT m.*, u.nama_lengkap as guru_name FROM materi m
            LEFT JOIN users u ON m.created_by=u.id ORDER BY m.created_at DESC""").fetchall()]

def get_materi_by_id(mid):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM materi WHERE id=?", (mid,))
        r = c.fetchone()
        return dict(r) if r else None

def get_materi_by_kategori(kategori):
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute(
            "SELECT * FROM materi WHERE kategori=? ORDER BY judul", (kategori,)).fetchall()]

def get_kategori_by_kategori(k): return get_materi_by_kategori(k)

def update_materi(mid, judul, tujuan_pembelajaran, isi_materi, link_video, kategori, file_path=None, file_type=None):
    with get_db() as conn:
        c = conn.cursor()
        if file_path is not None:
            c.execute("UPDATE materi SET judul=?,tujuan_pembelajaran=?,isi_materi=?,link_video=?,kategori=?,file_path=?,file_type=? WHERE id=?",
                      (judul, tujuan_pembelajaran, isi_materi, link_video, kategori, file_path, file_type, mid))
        else:
            c.execute("UPDATE materi SET judul=?,tujuan_pembelajaran=?,isi_materi=?,link_video=?,kategori=? WHERE id=?",
                      (judul, tujuan_pembelajaran, isi_materi, link_video, kategori, mid))
        return c.rowcount > 0

def delete_materi(mid):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM materi WHERE id=?", (mid,))
        return c.rowcount > 0

# ─── SOAL CRUD ────────────────────────────────────────────────────────────────
def create_soal(materi_id, pertanyaan, opsi_a, opsi_b, opsi_c, opsi_d, jawaban_benar, created_by):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO soal(materi_id,pertanyaan,opsi_a,opsi_b,opsi_c,opsi_d,jawaban_benar,created_by) VALUES(?,?,?,?,?,?,?,?)",
                  (materi_id, pertanyaan, opsi_a, opsi_b, opsi_c, opsi_d, jawaban_benar, created_by))
        return c.lastrowid

def get_all_soal():
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute("""
            SELECT s.*, m.judul as materi_judul FROM soal s
            LEFT JOIN materi m ON s.materi_id=m.id ORDER BY s.materi_id,s.id""").fetchall()]

def get_soal_by_materi(materi_id):
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute(
            "SELECT * FROM soal WHERE materi_id=?", (materi_id,)).fetchall()]

def get_soal_count_by_materi(materi_id=None):
    with get_db() as conn:
        c = conn.cursor()
        if materi_id is None:
            return c.execute("SELECT COUNT(*) FROM soal").fetchone()[0]
        return c.execute("SELECT COUNT(*) FROM soal WHERE materi_id=?", (materi_id,)).fetchone()[0]

def update_soal(sid, pertanyaan, opsi_a, opsi_b, opsi_c, opsi_d, jawaban_benar):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE soal SET pertanyaan=?,opsi_a=?,opsi_b=?,opsi_c=?,opsi_d=?,jawaban_benar=? WHERE id=?",
                  (pertanyaan, opsi_a, opsi_b, opsi_c, opsi_d, jawaban_benar, sid))
        return c.rowcount > 0

def delete_soal(sid):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM soal WHERE id=?", (sid,))
        return c.rowcount > 0

# ─── NILAI TEORI ──────────────────────────────────────────────────────────────
def save_nilai_teori(siswa_id, materi_id, skor):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO nilai_teori(siswa_id,materi_id,skor) VALUES(?,?,?)",
                  (siswa_id, materi_id, skor))
        return c.lastrowid

def get_nilai_teori_by_siswa(siswa_id):
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute("""
            SELECT nt.*, m.judul as materi_judul FROM nilai_teori nt
            LEFT JOIN materi m ON nt.materi_id=m.id
            WHERE nt.siswa_id=? ORDER BY nt.tanggal DESC""", (siswa_id,)).fetchall()]

def get_rata_nilai_teori(siswa_id):
    """Ambil rata-rata dari ujian_sesi (sistem baru) dan nilai_teori (legacy)."""
    with get_db() as conn:
        # Sistem ujian terjadwal baru
        r1 = conn.cursor().execute(
            "SELECT AVG(skor) FROM ujian_sesi WHERE siswa_id=? AND status='selesai'",
            (siswa_id,)).fetchone()[0] or 0.0
        # Legacy nilai_teori
        r2 = conn.cursor().execute(
            "SELECT AVG(skor) as rata FROM nilai_teori WHERE siswa_id=?",
            (siswa_id,)).fetchone()["rata"] or 0.0
        if r1 > 0 and r2 > 0:
            return round((r1 + r2) / 2, 2)
        return round(r1 or r2, 2)

def get_all_nilai_teori():
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute("""
            SELECT nt.*, u.nama_lengkap as siswa_name, m.judul as materi_judul
            FROM nilai_teori nt LEFT JOIN users u ON nt.siswa_id=u.id
            LEFT JOIN materi m ON nt.materi_id=m.id ORDER BY nt.tanggal DESC""").fetchall()]

def get_all_nilai_teori_by_materi(materi_id):
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute("""
            SELECT nt.*, u.nama_lengkap as siswa_name FROM nilai_teori nt
            LEFT JOIN users u ON nt.siswa_id=u.id WHERE nt.materi_id=?
            ORDER BY nt.skor DESC""", (materi_id,)).fetchall()]

def delete_nilai_teori(nid):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM nilai_teori WHERE id=?", (nid,))
        return c.rowcount > 0

# ─── NILAI PRAKTIK ────────────────────────────────────────────────────────────
def save_nilai_praktik(siswa_id, modul_praktik, safety, prosedur, hasil, assessed_by, foto_praktik=None, catatan=""):
    np_val = (safety * 0.30) + (prosedur * 0.30) + (hasil * 0.40)
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO nilai_praktik(siswa_id,modul_praktik,safety,prosedur,hasil,nilai_praktik,foto_praktik,catatan,assessed_by) VALUES(?,?,?,?,?,?,?,?,?)",
                  (siswa_id, modul_praktik, safety, prosedur, hasil, np_val, foto_praktik, catatan, assessed_by))
        return c.lastrowid

def get_nilai_praktik_by_siswa(siswa_id):
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute("""
            SELECT np.*, u.nama_lengkap as assessor_name FROM nilai_praktik np
            LEFT JOIN users u ON np.assessed_by=u.id
            WHERE np.siswa_id=? ORDER BY np.tanggal DESC""", (siswa_id,)).fetchall()]

def get_rata_nilai_praktik(siswa_id):
    with get_db() as conn:
        r = conn.cursor().execute("SELECT AVG(nilai_praktik) as rata FROM nilai_praktik WHERE siswa_id=?", (siswa_id,)).fetchone()
        return r["rata"] or 0.0

def get_all_nilai_praktik():
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute("""
            SELECT np.*, u.nama_lengkap as siswa_name, g.nama_lengkap as assessor_name
            FROM nilai_praktik np LEFT JOIN users u ON np.siswa_id=u.id
            LEFT JOIN users g ON np.assessed_by=g.id ORDER BY np.tanggal DESC""").fetchall()]

def delete_nilai_praktik(nid):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM nilai_praktik WHERE id=?", (nid,))
        return c.rowcount > 0

# ─── FINAL GRADE ──────────────────────────────────────────────────────────────
def get_nilai_akhir(siswa_id):
    rt, rp = get_rata_nilai_teori(siswa_id), get_rata_nilai_praktik(siswa_id)
    if rt == 0 and rp == 0: return 0.0
    if rt == 0: return round(rp, 2)
    if rp == 0: return round(rt, 2)
    return round((rt * 0.30) + (rp * 0.70), 2)

# ─── STATS ────────────────────────────────────────────────────────────────────
def get_total_siswa():
    with get_db() as conn: return conn.cursor().execute("SELECT COUNT(*) FROM users WHERE role='siswa'").fetchone()[0]
def get_total_materi():
    with get_db() as conn: return conn.cursor().execute("SELECT COUNT(*) FROM materi").fetchone()[0]
def get_total_soal():
    with get_db() as conn: return conn.cursor().execute("SELECT COUNT(*) FROM soal").fetchone()[0]
def get_total_ujian():
    with get_db() as conn: return conn.cursor().execute("SELECT COUNT(*) FROM nilai_teori").fetchone()[0]
def get_total_praktik():
    with get_db() as conn: return conn.cursor().execute("SELECT COUNT(*) FROM nilai_praktik").fetchone()[0]

def get_siswa_ranking():
    siswa = get_all_siswa()
    rank = []
    for s in siswa:
        na = get_nilai_akhir(s["id"])
        rank.append({"nama": s["nama_lengkap"], "kelas": s.get("kelas",""), "nilai_akhir": na,
                     "teori": get_rata_nilai_teori(s["id"]), "praktik": get_rata_nilai_praktik(s["id"])})
    return sorted(rank, key=lambda x: x["nilai_akhir"], reverse=True)

def get_aktivitas_terbaru(limit=8):
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute("""
            SELECT u.nama_lengkap, 'Ujian' as tipe, m.judul as keterangan,
                   nt.skor as nilai, nt.tanggal
            FROM nilai_teori nt JOIN users u ON nt.siswa_id=u.id
            JOIN materi m ON nt.materi_id=m.id
            UNION ALL
            SELECT u.nama_lengkap, 'Praktik' as tipe, np.modul_praktik,
                   np.nilai_praktik, np.tanggal
            FROM nilai_praktik np JOIN users u ON np.siswa_id=u.id
            ORDER BY tanggal DESC LIMIT ?""", (limit,)).fetchall()]

# ─── JADWAL UJIAN ─────────────────────────────────────────────────────────────

def create_jadwal_ujian(materi_id, judul_ujian, guru_id, tanggal_mulai,
                         tanggal_selesai, durasi_menit, jumlah_soal, acak_soal, keterangan=""):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""INSERT INTO ujian_jadwal
            (materi_id,judul_ujian,guru_id,tanggal_mulai,tanggal_selesai,
             durasi_menit,jumlah_soal,acak_soal,keterangan,status)
            VALUES(?,?,?,?,?,?,?,?,?,'aktif')""",
            (materi_id, judul_ujian, guru_id, tanggal_mulai, tanggal_selesai,
             durasi_menit, jumlah_soal, 1 if acak_soal else 0, keterangan))
        return c.lastrowid

def get_all_jadwal_ujian():
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute("""
            SELECT j.*, m.judul as materi_judul, u.nama_lengkap as guru_nama
            FROM ujian_jadwal j
            LEFT JOIN materi m ON j.materi_id=m.id
            LEFT JOIN users u ON j.guru_id=u.id
            ORDER BY j.tanggal_mulai DESC""").fetchall()]

def get_jadwal_aktif_untuk_siswa():
    """Jadwal yang saat ini sedang aktif (waktu masuk rentang)."""
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute("""
            SELECT j.*, m.judul as materi_judul, u.nama_lengkap as guru_nama
            FROM ujian_jadwal j
            LEFT JOIN materi m ON j.materi_id=m.id
            LEFT JOIN users u ON j.guru_id=u.id
            WHERE j.status='aktif'
              AND datetime('now','localtime') BETWEEN j.tanggal_mulai AND j.tanggal_selesai
            ORDER BY j.tanggal_mulai""").fetchall()]

def get_jadwal_mendatang_untuk_siswa():
    """Jadwal yang belum dimulai."""
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute("""
            SELECT j.*, m.judul as materi_judul, u.nama_lengkap as guru_nama
            FROM ujian_jadwal j
            LEFT JOIN materi m ON j.materi_id=m.id
            LEFT JOIN users u ON j.guru_id=u.id
            WHERE j.status='aktif'
              AND datetime('now','localtime') < j.tanggal_mulai
            ORDER BY j.tanggal_mulai""").fetchall()]

def get_jadwal_by_id(jid):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""SELECT j.*, m.judul as materi_judul
            FROM ujian_jadwal j LEFT JOIN materi m ON j.materi_id=m.id
            WHERE j.id=?""", (jid,))
        r = c.fetchone()
        return dict(r) if r else None

def update_jadwal_status(jid, status):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE ujian_jadwal SET status=? WHERE id=?", (status, jid))
        return c.rowcount > 0

def delete_jadwal_ujian(jid):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM ujian_jadwal WHERE id=?", (jid,))
        return c.rowcount > 0

def get_hasil_ujian_jadwal(jadwal_id):
    """Ambil semua hasil siswa untuk jadwal tertentu."""
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute("""
            SELECT s.*, u.nama_lengkap as siswa_nama, u.nis, u.kelas
            FROM ujian_sesi_baru s
            JOIN users u ON s.siswa_id=u.id
            WHERE s.jadwal_id=?
            ORDER BY s.skor DESC""", (jadwal_id,)).fetchall()]

# ─── SESI UJIAN TERJADWAL ─────────────────────────────────────────────────────

def get_sesi_ujian(jadwal_id, siswa_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM ujian_sesi_baru WHERE jadwal_id=? AND siswa_id=?",
                  (jadwal_id, siswa_id))
        r = c.fetchone()
        return dict(r) if r else None

def create_sesi_ujian(jadwal_id, siswa_id, total_soal):
    with get_db() as conn:
        c = conn.cursor()
        try:
            c.execute("""INSERT INTO ujian_sesi_baru(jadwal_id,siswa_id,total_soal)
                VALUES(?,?,?)""", (jadwal_id, siswa_id, total_soal))
            return c.lastrowid
        except Exception:
            c.execute("SELECT id FROM ujian_sesi_baru WHERE jadwal_id=? AND siswa_id=?",
                      (jadwal_id, siswa_id))
            r = c.fetchone()
            return r[0] if r else None

def save_jawaban_sesi(sesi_id, soal_list, jawaban_dict):
    """Simpan jawaban per soal ke ujian_jawaban_baru."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM ujian_jawaban_baru WHERE sesi_id=?", (sesi_id,))
        for soal in soal_list:
            jwb   = jawaban_dict.get(str(soal["id"]), "")
            benar = 1 if jwb == soal["jawaban_benar"] else 0
            c.execute("""INSERT INTO ujian_jawaban_baru
                (sesi_id,soal_id,pertanyaan,opsi_a,opsi_b,opsi_c,opsi_d,
                 jawaban_benar,jawaban_siswa,is_correct)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (sesi_id, soal["id"], soal["pertanyaan"],
                 soal["opsi_a"], soal["opsi_b"], soal["opsi_c"], soal["opsi_d"],
                 soal["jawaban_benar"], jwb, benar))

def submit_sesi_ujian(sesi_id, benar, total, skor, durasi_detik):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""UPDATE ujian_sesi_baru
            SET selesai_at=datetime('now','localtime'), benar=?, skor=?,
                durasi_detik=?, sudah_submit=1
            WHERE id=?""", (benar, skor, durasi_detik, sesi_id))

def get_jawaban_sesi(sesi_id):
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute(
            "SELECT * FROM ujian_jawaban_baru WHERE sesi_id=? ORDER BY id",
            (sesi_id,)).fetchall()]

def get_riwayat_ujian_siswa(siswa_id):
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute("""
            SELECT s.*, j.judul_ujian, j.durasi_menit, m.judul as materi_judul
            FROM ujian_sesi_baru s
            JOIN ujian_jadwal j ON s.jadwal_id=j.id
            JOIN materi m ON j.materi_id=m.id
            WHERE s.siswa_id=? AND s.sudah_submit=1
            ORDER BY s.selesai_at DESC""", (siswa_id,)).fetchall()]

# ─── MATERI PROGRESS ──────────────────────────────────────────────────────────

def tandai_materi_selesai(siswa_id, materi_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""INSERT INTO materi_progress(siswa_id,materi_id,selesai,tanggal_selesai)
            VALUES(?,?,1,datetime('now','localtime'))
            ON CONFLICT(siswa_id,materi_id) DO UPDATE SET
            selesai=1, tanggal_selesai=datetime('now','localtime')""",
            (siswa_id, materi_id))

def is_materi_selesai(siswa_id, materi_id):
    with get_db() as conn:
        r = conn.cursor().execute(
            "SELECT selesai FROM materi_progress WHERE siswa_id=? AND materi_id=?",
            (siswa_id, materi_id)).fetchone()
        return bool(r and r[0])

def get_progress_siswa(siswa_id):
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute("""
            SELECT mp.*, m.judul FROM materi_progress mp
            JOIN materi m ON mp.materi_id=m.id
            WHERE mp.siswa_id=? AND mp.selesai=1""", (siswa_id,)).fetchall()]

def get_semua_progress():
    """Untuk guru: berapa siswa yang sudah selesai tiap materi."""
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute("""
            SELECT m.judul, COUNT(mp.id) as jml_selesai
            FROM materi m LEFT JOIN materi_progress mp
            ON m.id=mp.materi_id AND mp.selesai=1
            GROUP BY m.id ORDER BY m.id""").fetchall()]

# ─── UJIAN JADWAL (GURU) ──────────────────────────────────────────────────────

def create_ujian_jadwal(judul, materi_id, durasi_menit, max_soal, acak_soal,
                        tanggal_mulai, tanggal_selesai, syarat_materi, created_by):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO ujian_jadwal
            (judul,materi_id,durasi_menit,max_soal,acak_soal,
             tanggal_mulai,tanggal_selesai,syarat_materi,status,created_by)
            VALUES(?,?,?,?,?,?,?,?,'draft',?)
        """, (judul, materi_id, durasi_menit, max_soal, acak_soal,
              tanggal_mulai, tanggal_selesai, syarat_materi, created_by))
        return c.lastrowid

def get_all_ujian_jadwal():
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute("""
            SELECT uj.*, m.judul as materi_judul,
                   u.nama_lengkap as guru_name,
                   (SELECT COUNT(*) FROM ujian_sesi s
                    WHERE s.jadwal_id=uj.id AND s.status='selesai') as jml_peserta
            FROM ujian_jadwal uj
            LEFT JOIN materi m ON uj.materi_id=m.id
            LEFT JOIN users  u ON uj.created_by=u.id
            ORDER BY uj.created_at DESC
        """).fetchall()]

def get_ujian_jadwal_by_id(jid):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM ujian_jadwal WHERE id=?", (jid,))
        r = c.fetchone()
        return dict(r) if r else None

def update_ujian_jadwal(jid, judul, materi_id, durasi_menit, max_soal,
                         acak_soal, tanggal_mulai, tanggal_selesai, syarat_materi):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE ujian_jadwal
            SET judul=?,materi_id=?,durasi_menit=?,max_soal=?,acak_soal=?,
                tanggal_mulai=?,tanggal_selesai=?,syarat_materi=?
            WHERE id=?
        """, (judul, materi_id, durasi_menit, max_soal, acak_soal,
              tanggal_mulai, tanggal_selesai, syarat_materi, jid))
        return c.rowcount > 0

def set_status_ujian(jid, status):
    """status: 'draft' | 'aktif' | 'selesai'"""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("UPDATE ujian_jadwal SET status=? WHERE id=?", (status, jid))
        return c.rowcount > 0

def delete_ujian_jadwal(jid):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM ujian_jadwal WHERE id=?", (jid,))
        return c.rowcount > 0

# ─── UJIAN JADWAL AKTIF (SISWA) ───────────────────────────────────────────────

def get_ujian_aktif_untuk_siswa(siswa_id):
    """Ambil jadwal ujian yang status='aktif' dan belum dikerjakan siswa ini."""
    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute("""
            SELECT uj.*, m.judul as materi_judul,
                   (SELECT COUNT(*) FROM ujian_sesi s
                    WHERE s.jadwal_id=uj.id AND s.siswa_id=? AND s.status='selesai') as sudah_dikerjakan
            FROM ujian_jadwal uj
            LEFT JOIN materi m ON uj.materi_id=m.id
            WHERE uj.status='aktif'
              AND (uj.tanggal_selesai IS NULL OR uj.tanggal_selesai >= ?)
            ORDER BY uj.tanggal_mulai
        """, (siswa_id, now)).fetchall()]

def get_ujian_sudah_selesai_siswa(siswa_id):
    """Riwayat ujian siswa yang sudah selesai."""
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute("""
            SELECT s.*, uj.judul as judul_ujian, uj.durasi_menit,
                   m.judul as materi_judul
            FROM ujian_sesi s
            JOIN ujian_jadwal uj ON s.jadwal_id=uj.id
            LEFT JOIN materi m ON uj.materi_id=m.id
            WHERE s.siswa_id=? AND s.status='selesai'
            ORDER BY s.selesai_at DESC
        """, (siswa_id,)).fetchall()]

# ─── MATERI PROGRESS ──────────────────────────────────────────────────────────

def tandai_materi_selesai(siswa_id, materi_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO materi_progress(siswa_id,materi_id,selesai,tanggal_selesai)
            VALUES(?,?,1,CURRENT_TIMESTAMP)
            ON CONFLICT(siswa_id,materi_id) DO UPDATE
            SET selesai=1, tanggal_selesai=CURRENT_TIMESTAMP
        """, (siswa_id, materi_id))
        return True

def get_materi_selesai(siswa_id):
    """Return set materi_id yang sudah diselesaikan siswa ini."""
    with get_db() as conn:
        rows = conn.cursor().execute(
            "SELECT materi_id FROM materi_progress WHERE siswa_id=? AND selesai=1",
            (siswa_id,)).fetchall()
        return {r[0] for r in rows}

def cek_materi_selesai(siswa_id, materi_id):
    with get_db() as conn:
        r = conn.cursor().execute(
            "SELECT selesai FROM materi_progress WHERE siswa_id=? AND materi_id=? AND selesai=1",
            (siswa_id, materi_id)).fetchone()
        return r is not None

def get_progress_all_siswa(materi_id):
    """Berapa siswa yang sudah selesai materi ini."""
    with get_db() as conn:
        return conn.cursor().execute(
            "SELECT COUNT(*) FROM materi_progress WHERE materi_id=? AND selesai=1",
            (materi_id,)).fetchone()[0]

# ─── UJIAN SESI ───────────────────────────────────────────────────────────────

def buat_ujian_sesi(jadwal_id, siswa_id, total_soal):
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO ujian_sesi(jadwal_id,siswa_id,total_soal) VALUES(?,?,?)",
            (jadwal_id, siswa_id, total_soal))
        return c.lastrowid

def get_sesi_aktif(jadwal_id, siswa_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT * FROM ujian_sesi
            WHERE jadwal_id=? AND siswa_id=? AND status='berlangsung'
            ORDER BY mulai_at DESC LIMIT 1
        """, (jadwal_id, siswa_id))
        r = c.fetchone()
        return dict(r) if r else None

def selesaikan_sesi(sesi_id, benar, total, skor):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE ujian_sesi
            SET status='selesai', selesai_at=CURRENT_TIMESTAMP,
                benar=?, total_soal=?, skor=?
            WHERE id=?
        """, (benar, total, skor, sesi_id))
        return c.rowcount > 0

def simpan_jawaban(sesi_id, soal_id, jawaban_siswa, is_correct):
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO ujian_jawaban(sesi_id,soal_id,jawaban_siswa,is_correct) VALUES(?,?,?,?)",
            (sesi_id, soal_id, jawaban_siswa, is_correct))

def get_jawaban_sesi(sesi_id):
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute("""
            SELECT uj.*, s.pertanyaan, s.opsi_a, s.opsi_b, s.opsi_c, s.opsi_d,
                   s.jawaban_benar
            FROM ujian_jawaban uj JOIN soal s ON uj.soal_id=s.id
            WHERE uj.sesi_id=? ORDER BY uj.id
        """, (sesi_id,)).fetchall()]

def get_hasil_ujian_jadwal(jadwal_id):
    """Semua hasil sesi selesai untuk satu jadwal ujian."""
    with get_db() as conn:
        return [dict(r) for r in conn.cursor().execute("""
            SELECT s.*, u.nama_lengkap as nama_siswa, u.kelas, u.nis
            FROM ujian_sesi s JOIN users u ON s.siswa_id=u.id
            WHERE s.jadwal_id=? AND s.status='selesai'
            ORDER BY s.skor DESC
        """, (jadwal_id,)).fetchall()]

def siswa_sudah_kerjakan(jadwal_id, siswa_id):
    with get_db() as conn:
        r = conn.cursor().execute(
            "SELECT id FROM ujian_sesi WHERE jadwal_id=? AND siswa_id=? AND status='selesai'",
            (jadwal_id, siswa_id)).fetchone()
        return r is not None

# ─── JOBSHEET SEED ────────────────────────────────────────────────────────────

def seed_jobsheet():
    """Tambahkan jobsheet praktikum jika belum ada."""
    with get_db() as conn:
        c = conn.cursor()
        # Cek apakah sudah ada jobsheet
        existing = c.execute(
            "SELECT COUNT(*) FROM materi WHERE judul LIKE '%Jobsheet%' OR judul LIKE '%Job Sheet%'"
        ).fetchone()[0]
        if existing > 0:
            return

        guru_id = c.execute("SELECT id FROM users WHERE role='guru' LIMIT 1").fetchone()
        gid = guru_id[0] if guru_id else 1

        jobsheets = [
            (
                "Jobsheet 01 — Tune-Up Engine Diesel (Service Berkala)",
                "Engine",
                "Siswa mampu melaksanakan tune-up engine diesel sesuai prosedur standar pabrik, mencakup pemeriksaan, penyetelan, dan penggantian komponen berkala.",
                """# JOBSHEET PRAKTIKUM
## Tune-Up Engine Diesel (Service Berkala)
**Program Keahlian :** Teknik Alat Berat
**Mata Pelajaran    :** Pemeliharaan Mesin Alat Berat
**Kelas / Semester  :** XI TAB / Genap
**Waktu             :** 4 × 45 menit (180 menit)
**Kompetensi Dasar  :** Melaksanakan tune-up engine diesel sesuai SOP

---

## A. TUJUAN PRAKTIKUM
1. Siswa dapat melakukan pemeriksaan komponen engine diesel secara sistematis
2. Siswa dapat menyetel celah katup (valve clearance) sesuai spesifikasi
3. Siswa dapat mengganti filter oli, filter BBM, dan filter udara dengan benar
4. Siswa dapat melakukan bleeding sistem bahan bakar
5. Siswa dapat mengisi lembar kerja dan laporan praktikum

---

## B. KESELAMATAN KERJA (K3) — WAJIB DIBACA
> ⚠️ **PELANGGARAN K3 = NILAI GUGUR**

- ✅ Gunakan wearpack, helm safety, kacamata, sarung tangan
- ✅ Pastikan mesin **MATI** dan kunci kontak dilepas sebelum kerja
- ✅ Pasang label **"MESIN DALAM PERBAIKAN — JANGAN DIHIDUPKAN"**
- ✅ Gunakan ganjal roda sebelum bekerja di bawah unit
- ❌ Dilarang merokok di area bengkel
- ❌ Dilarang menghidupkan mesin tanpa seizin instruktur

---

## C. ALAT DAN BAHAN

### Alat:
| No | Nama Alat | Spesifikasi | Jumlah |
|----|-----------|-------------|--------|
| 1 | Kunci sok | Set 8–32 mm | 1 set |
| 2 | Kunci ring/pas | Set 8–32 mm | 1 set |
| 3 | Fuller gauge (Feeler gauge) | 0,05–1,00 mm | 1 buah |
| 4 | Torque wrench | 0–200 N·m | 1 buah |
| 5 | Obeng (+) dan (−) | Medium | Masing-masing 1 |
| 6 | Tang kombinasi | — | 1 buah |
| 7 | Wadah penampung oli | Min. 10 liter | 1 buah |
| 8 | Corong oli | — | 1 buah |
| 9 | Lap majun / kain bersih | — | Secukupnya |
| 10 | Service manual engine | Sesuai unit | 1 buah |

### Bahan:
| No | Nama Bahan | Spesifikasi | Jumlah |
|----|------------|-------------|--------|
| 1 | Oli mesin | SAE 15W-40 API CI-4 | Sesuai kapasitas |
| 2 | Filter oli | Sesuai part number unit | 1 buah |
| 3 | Filter BBM primer | Sesuai part number unit | 1 buah |
| 4 | Filter BBM sekunder | Sesuai part number unit | 1 buah |
| 5 | Gasket/seal drain plug | Sesuai unit | 1 buah |
| 6 | Solar (BBM diesel) | Bersih | Secukupnya |

---

## D. DASAR TEORI SINGKAT

### Tune-Up Engine Diesel
Tune-up adalah serangkaian kegiatan pemeriksaan, penyetelan, dan penggantian komponen engine secara berkala untuk mempertahankan performa mesin sesuai standar pabrik.

### Celah Katup (Valve Clearance)
Celah katup adalah jarak antara rocker arm dengan ujung batang katup (valve stem). Fungsinya mengompensasi pemuaian termal saat mesin panas.

**Akibat celah terlalu kecil:** Katup tidak menutup sempurna → kompresi bocor → tenaga turun
**Akibat celah terlalu besar:** Bunyi ketukan keras → katup terlambat buka → efisiensi turun

**Spesifikasi umum engine diesel alat berat:**
| Katup | Kondisi Dingin | Kondisi Panas |
|-------|---------------|---------------|
| Intake (Masuk) | 0,25–0,30 mm | 0,30–0,35 mm |
| Exhaust (Buang) | 0,51–0,56 mm | 0,51–0,56 mm |

> 📌 Selalu gunakan spesifikasi dari **service manual unit** yang dikerjakan

---

## E. LANGKAH KERJA

### TAHAP 1: Persiapan (15 menit)
```
□ 1. Pakai APD lengkap
□ 2. Siapkan semua alat dan bahan di tool trolley
□ 3. Baca service manual — catat spesifikasi valve clearance
□ 4. Panaskan mesin ± 5 menit hingga suhu operasi
□ 5. Matikan mesin, lepas kunci kontak
□ 6. Pasang label peringatan
□ 7. Tunggu mesin dingin ± 30 menit (untuk penyetelan katup)
```

### TAHAP 2: Penggantian Oli Mesin (30 menit)
```
□ 1. Siapkan wadah penampung di bawah drain plug
□ 2. Buka drain plug dengan kunci yang sesuai
□ 3. Tampung oli bekas hingga habis
□ 4. Ganti gasket drain plug (jika diperlukan)
□ 5. Pasang drain plug — kencangkan dengan torque wrench
       Torque: _____ N·m (lihat service manual)
□ 6. Lepas filter oli lama dengan filter wrench
□ 7. Olesi bibir seal filter baru dengan oli bersih
□ 8. Pasang filter oli baru — kencangkan tangan + ¾ putaran
□ 9. Isi oli mesin baru melalui tutup pengisian
□ 10. Cek level dengan dipstick — harus antara L dan H
□ 11. Catat volume oli yang digunakan: _____ liter
```

### TAHAP 3: Penggantian Filter Bahan Bakar (20 menit)
```
□ 1. Tutup kran BBM (fuel shutoff valve)
□ 2. Siapkan wadah penampung BBM
□ 3. Drain air dari water separator — kendurkan drain valve
□ 4. Lepas filter BBM primer dan sekunder
□ 5. Isi filter baru dengan BBM bersih sebelum dipasang
□ 6. Pasang filter baru — kencangkan sesuai torque
□ 7. Buka kembali kran BBM
□ 8. Lakukan priming/bleeding udara dari sistem BBM
```

### TAHAP 4: Penyetelan Celah Katup (60 menit)
```
□ 1. Lepas tutup rocker arm (valve cover)
□ 2. Cari TMA (Top Dead Center) silinder No. 1 kompresi:
       - Putar crankshaft searah putaran mesin
       - Cari tanda TMA pada flywheel
       - Pastikan kedua katup silinder No.1 dalam posisi bebas
□ 3. Catat urutan penyetelan sesuai firing order:
       Firing order engine: ___________________
□ 4. Untuk setiap katup yang bisa disetel:
       - Kendurkan lock nut rocker arm
       - Masukkan fuller gauge ukuran spesifikasi
       - Setel adjusting screw hingga fuller gauge
         bergerak dengan sedikit hambatan (slight drag)
       - Kencangkan lock nut sambil tahan adjusting screw
       - Cek ulang celah setelah lock nut dikencangkan
□ 5. Putar crankshaft sesuai firing order untuk katup berikutnya
□ 6. Ulangi langkah 4 untuk semua katup
□ 7. Pasang valve cover dengan gasket baru
       Torque: _____ N·m
```

### TAHAP 5: Pemeriksaan Akhir dan Start-Up (20 menit)
```
□ 1. Periksa semua baut dan koneksi sudah terpasang
□ 2. Pastikan tidak ada alat tertinggal di atas mesin
□ 3. Isi oli mesin jika kurang (cek dipstick)
□ 4. Hidupkan mesin — idle 3–5 menit
□ 5. Periksa kebocoran:
       - Oli mesin (drain plug, filter)
       - Bahan bakar (filter, selang)
□ 6. Cek suhu operasi normal
□ 7. Matikan mesin, tunggu 5 menit, cek level oli kembali
□ 8. Bersihkan area kerja
```

---

## F. DATA HASIL PRAKTIKUM

### Data Penyetelan Celah Katup
| Silinder | Katup Intake | Katup Exhaust | Status |
|----------|-------------|---------------|--------|
| 1 | _____ mm | _____ mm | ☐ OK |
| 2 | _____ mm | _____ mm | ☐ OK |
| 3 | _____ mm | _____ mm | ☐ OK |
| 4 | _____ mm | _____ mm | ☐ OK |
| 5 | _____ mm | _____ mm | ☐ OK |
| 6 | _____ mm | _____ mm | ☐ OK |

**Spesifikasi Intake :** _____ mm | **Spesifikasi Exhaust :** _____ mm

### Data Pelumasan
| Item | Spesifikasi | Hasil Pengukuran | Status |
|------|-------------|-----------------|--------|
| Level oli sebelum | — | _____ | ☐ L ☐ H |
| Volume oli terpakai | _____ liter | _____ liter | ☐ OK |
| Level oli setelah | — | _____ | ☐ L ☐ H |
| Kondisi drain plug | — | _____ | ☐ OK |

---

## G. PERTANYAAN EVALUASI
1. Sebutkan akibat jika celah katup terlalu kecil dari spesifikasi!
2. Mengapa penggantian oli dilakukan saat mesin masih hangat?
3. Jelaskan fungsi bleeding pada sistem bahan bakar diesel!
4. Apa yang dimaksud dengan firing order? Sebutkan contohnya!
5. Sebutkan 3 tanda bahaya yang harus dihentikan saat tune-up!

---

## H. KESIMPULAN DAN PENILAIAN

**Kesimpulan Praktikum:**
```
_______________________________________________
_______________________________________________
_______________________________________________
```

**Rubrik Penilaian:**
| Aspek | Bobot | Nilai |
|-------|-------|-------|
| K3 & APD | 25% | |
| Ketepatan Prosedur | 30% | |
| Hasil Pengukuran | 30% | |
| Laporan & Kebersihan | 15% | |
| **TOTAL** | **100%** | |

**Nama Siswa :** _______________________
**NIS :** _______________________
**Tanggal Praktikum :** _______________________
**Tanda Tangan Instruktur :** _______________________
""",
                "", gid
            ),
            (
                "Jobsheet 02 — Penyetelan Celah Katup Engine Diesel",
                "Engine",
                "Siswa mampu mengidentifikasi posisi TMA, membaca firing order, dan menyetel celah katup engine diesel sesuai spesifikasi menggunakan fuller gauge.",
                """# JOBSHEET PRAKTIKUM
## Penyetelan Celah Katup (Valve Clearance Adjustment)
**Program Keahlian :** Teknik Alat Berat
**Mata Pelajaran    :** Pemeliharaan Mesin Alat Berat
**Kelas / Semester  :** XI TAB / Genap
**Waktu             :** 3 × 45 menit (135 menit)
**Kompetensi Dasar  :** Menyetel celah katup engine diesel sesuai spesifikasi pabrik

---

## A. TUJUAN PRAKTIKUM
1. Siswa dapat menemukan posisi TMA (Top Dead Center) silinder No.1
2. Siswa dapat membaca dan menerapkan firing order engine
3. Siswa dapat menggunakan fuller gauge dengan benar
4. Siswa dapat menyetel celah katup intake dan exhaust sesuai spesifikasi
5. Siswa dapat memverifikasi hasil penyetelan

---

## B. KESELAMATAN KERJA (K3)
> ⚠️ **BAHAYA: Memutar crankshaft saat ada orang di dekat flywheel!**

- ✅ Wearpack, helm, kacamata, sarung tangan WAJIB
- ✅ Engine harus MATI TOTAL — lepas kabel negatif baterai
- ✅ Pasang label "JANGAN DIHIDUPKAN" di kunci kontak
- ✅ Lakukan penyetelan saat mesin DINGIN (< 40°C) kecuali ditentukan lain
- ❌ Dilarang memutar crankshaft dengan tangan di area berbahaya
- ❌ Dilarang membiarkan kunci tertinggal di flywheel/crankshaft

---

## C. ALAT DAN BAHAN

| No | Alat / Bahan | Keterangan |
|----|-------------|------------|
| 1 | Fuller gauge (Feeler Gauge) set | 0,05 mm – 1,00 mm |
| 2 | Kunci ring 14, 17 mm | Untuk rocker arm adjuster |
| 3 | Obeng (-) pipih | Untuk adjusting screw |
| 4 | Kunci flywheel / barring tool | Memutar crankshaft |
| 5 | Torque wrench | 10–100 N·m |
| 6 | Service Manual | Sesuai tipe engine |
| 7 | Lap bersih | Membersihkan area kerja |
| 8 | Senter/work light | Penerangan area kerja |

---

## D. DASAR TEORI

### Siklus 4 Langkah Engine Diesel
```
Langkah 1 — HISAP    : Katup intake BUKA, piston turun → udara masuk
Langkah 2 — KOMPRESI : Kedua katup TUTUP, piston naik → udara terkompresi
Langkah 3 — USAHA    : Kedua katup TUTUP, injeksi BBM → ledakan → piston turun
Langkah 4 — BUANG    : Katup exhaust BUKA, piston naik → gas sisa keluar
```

### Menentukan TMA Kompresi (Langkah Kritis!)
```
TMA Kompresi = Silinder pada akhir langkah kompresi
              = Kedua katup (intake & exhaust) dalam posisi BEBAS/MENUTUP
              = Piston berada di titik paling atas

CARA CEK:
1. Putar crankshaft → amati katup silinder yang dicari
2. Jika kedua katup baru saja menutup (bebas) → itu TMA Kompresi
3. Konfirmasi dengan tanda TMA di flywheel
```

### Firing Order (Urutan Pengapian)
Engine diesel alat berat umumnya:
- **4 silinder:** 1-3-4-2
- **6 silinder:** 1-5-3-6-2-4 (Komatsu, Cummins, Caterpillar umumnya)

> 📌 **SELALU cek service manual unit yang dikerjakan!**

### Metode "Dua Putaran" (Two-Shot Method)
Cara efisien menyetel semua katup 6 silinder dalam 2 posisi crankshaft:

**Posisi 1 — Silinder No.1 TMA Kompresi:**
Katup yang dapat disetel: *(lihat tabel service manual)*

**Posisi 2 — Putar crankshaft 360°:**
Katup yang dapat disetel: *(lihat tabel service manual)*

---

## E. PROSEDUR LANGKAH KERJA

### Tahap 1: Persiapan (10 menit)
```
□ 1. Baca service manual → catat spesifikasi:
      Intake clearance  : _______ mm
      Exhaust clearance : _______ mm
      Torque lock nut   : _______ N·m
      Firing order      : _______________________

□ 2. Pastikan engine dingin (< 40°C) atau sesuai spesifikasi
□ 3. Lepas kabel negatif (−) baterai
□ 4. Siapkan semua alat di tempat yang mudah dijangkau
□ 5. Pasang work light agar area rocker arm terlihat jelas
```

### Tahap 2: Membuka Akses Rocker Arm (10 menit)
```
□ 1. Bersihkan area sekitar valve cover dari debu/kotoran
□ 2. Lepas selang pernapasan (breather) jika ada
□ 3. Kendurkan baut valve cover secara menyilang (cross pattern)
□ 4. Angkat valve cover — letakkan terbalik di tempat bersih
□ 5. Periksa kondisi gasket valve cover:
      Kondisi gasket : ______________________________
      Perlu diganti  : ☐ Ya  ☐ Tidak
```

### Tahap 3: Mencari TMA Silinder No. 1 (20 menit)
```
□ 1. Gunakan barring tool di flywheel/crankshaft pulley
□ 2. Putar crankshaft searah putaran mesin (biasanya searah jarum jam dilihat dari depan)
□ 3. Amati katup silinder No. 1:
      - Saat katup exhaust mulai membuka → terus putar
      - Saat katup exhaust menutup & intake mulai membuka → terus putar
      - Saat KEDUA katup bebas/menutup → BERHENTI
      - Ini adalah TMA Kompresi Silinder No. 1
□ 4. Verifikasi dengan tanda TMA di flywheel
      Tanda TMA terlihat : ☐ Ya  ☐ Tidak
□ 5. Catat posisi ini sebagai "POSISI 1"
```

### Tahap 4: Penyetelan Katup Posisi 1 (35 menit)
```
Katup yang disetel pada Posisi 1: (sesuai service manual)
Silinder No: _______ | Katup: Intake ☐  Exhaust ☐

Untuk setiap katup:
□ 1. Pilih fuller gauge ukuran spesifikasi
□ 2. Kendurkan lock nut (jangan dilepas)
□ 3. Masukkan fuller gauge antara rocker arm dan valve stem
□ 4. Putar adjusting screw:
      - Searah jarum jam → celah mengecil
      - Berlawanan jarum jam → celah membesar
□ 5. Setel hingga fuller gauge bergerak dengan SLIGHT DRAG
      (sedikit hambatan, tidak longgar, tidak macet)
□ 6. Tahan adjusting screw dengan obeng
□ 7. Kencangkan lock nut dengan torque wrench
      Torque: _______ N·m
□ 8. Cek ulang celah setelah lock nut kencang
      Hasil cek ulang: _______ mm → ☐ Sesuai  ☐ Ulangi
```

### Tahap 5: Putar Crankshaft ke Posisi 2 (5 menit)
```
□ 1. Putar crankshaft 360° (satu putaran penuh)
□ 2. Verifikasi posisi dengan service manual
□ 3. Lakukan penyetelan katup Posisi 2
      (ulangi prosedur Tahap 4 untuk katup yang tersisa)
```

### Tahap 6: Verifikasi dan Penutupan (15 menit)
```
□ 1. Cek ulang SEMUA katup yang telah disetel
□ 2. Bersihkan area rocker arm dari kotoran
□ 3. Periksa kondisi gasket valve cover
□ 4. Pasang gasket baru jika bocor
□ 5. Pasang valve cover — kencangkan baut secara menyilang
      Torque: _______ N·m
□ 6. Pasang kembali breather hose
□ 7. Sambung kabel baterai
□ 8. Hidupkan engine → dengarkan suara ketukan katup
      Suara normal    : ☐ Ya  ☐ Tidak
      Tindakan lanjut : ______________________________
```

---

## F. LEMBAR DATA HASIL PRAKTIKUM

### Spesifikasi dari Service Manual
| Parameter | Nilai |
|-----------|-------|
| Tipe/Model Engine | |
| Firing Order | |
| Celah Intake (dingin) | mm |
| Celah Exhaust (dingin) | mm |
| Torque Lock Nut | N·m |
| Torque Valve Cover Bolt | N·m |

### Hasil Pengukuran Celah Katup

#### POSISI 1 — Silinder No.1 TMA
| Silinder | Jenis Katup | Celah Sebelum | Celah Setelah | Status |
|----------|-------------|--------------|--------------|--------|
| | Intake | mm | mm | ☐ OK |
| | Exhaust | mm | mm | ☐ OK |
| | Intake | mm | mm | ☐ OK |
| | Exhaust | mm | mm | ☐ OK |
| | Intake | mm | mm | ☐ OK |
| | Exhaust | mm | mm | ☐ OK |

#### POSISI 2 — Crankshaft +360°
| Silinder | Jenis Katup | Celah Sebelum | Celah Setelah | Status |
|----------|-------------|--------------|--------------|--------|
| | Intake | mm | mm | ☐ OK |
| | Exhaust | mm | mm | ☐ OK |
| | Intake | mm | mm | ☐ OK |
| | Exhaust | mm | mm | ☐ OK |
| | Intake | mm | mm | ☐ OK |
| | Exhaust | mm | mm | ☐ OK |

---

## G. ANALISIS DAN EVALUASI

**1. Katup manakah yang celahnya paling jauh dari spesifikasi sebelum disetel? Mengapa?**
```
_______________________________________________
```

**2. Jelaskan cara kerja fuller gauge dan teknik "slight drag" yang benar!**
```
_______________________________________________
```

**3. Apa dampak jika lock nut tidak dikencangkan dengan torque yang benar?**
```
_______________________________________________
```

---

## H. PENILAIAN

| Aspek Penilaian | Bobot | Nilai |
|----------------|-------|-------|
| K3 — APD & Sikap Kerja | 20% | |
| Prosedur mencari TMA | 20% | |
| Ketepatan penyetelan (celah sesuai spesifikasi) | 35% | |
| Laporan & Data | 15% | |
| Kebersihan alat & area | 10% | |
| **TOTAL** | **100%** | |

**Nama Siswa :** _______________________  **NIS :** _______________________
**Tanggal    :** _______________________  **Instruktur :** _______________________
""",
                "", gid
            ),
            (
                "Jobsheet 03 — Service Berkala Forklift Caterpillar DP40",
                "Unit Spesifik",
                "Siswa mampu melaksanakan service berkala (PM) Forklift Caterpillar DP40 secara sistematis sesuai Operation and Maintenance Manual (OMM) Caterpillar.",
                """# JOBSHEET PRAKTIKUM
## Service Berkala Forklift Caterpillar DP40
**Program Keahlian :** Teknik Alat Berat
**Mata Pelajaran    :** Pemeliharaan Unit Alat Berat
**Kelas / Semester  :** XI TAB / Genap
**Waktu             :** 4 × 45 menit (180 menit)
**Kompetensi Dasar  :** Melaksanakan Preventive Maintenance (PM) Forklift CAT DP40

---

## A. SPESIFIKASI UNIT

| Parameter | Spesifikasi |
|-----------|------------|
| **Model** | Caterpillar DP40 |
| **Kapasitas Angkat** | 4.000 kg (4 ton) |
| **Load Center** | 500 mm |
| **Engine** | CAT C3.3B DIT (Diesel), 4 silinder |
| **Displacement Engine** | 3.3 liter |
| **Daya Engine** | 55 kW (74 HP) @ 2.400 rpm |
| **Transmisi** | Otomatis (Torque Converter) |
| **Sistem Hidrolik** | Open center hydraulic system |
| **Kapasitas Oli Mesin** | 9 liter (termasuk filter) |
| **Kapasitas Oli Transmisi** | 7 liter |
| **Kapasitas Oli Hidrolik** | 45 liter |
| **Kapasitas Coolant** | 12 liter |
| **Berat Operasi** | ± 7.100 kg |

---

## B. TUJUAN PRAKTIKUM
1. Siswa dapat melakukan walkaround inspection sesuai OMM CAT
2. Siswa dapat memeriksa dan mengganti oli mesin, filter oli
3. Siswa dapat memeriksa sistem pendingin (coolant, radiator)
4. Siswa dapat memeriksa sistem hidrolik
5. Siswa dapat memeriksa kondisi mast, chain, dan fork
6. Siswa dapat mengisi checklist PM dengan benar

---

## C. KESELAMATAN KERJA (K3) — FORKLIFT
> ⚠️ **FORKLIFT TERBALIK BISA FATAL — SELALU GUNAKAN PARKING BRAKE**

- ✅ **Wearpack, helm, safety shoes, kacamata, sarung tangan WAJIB**
- ✅ Parkir di permukaan **RATA** dan **KERAS** sebelum service
- ✅ Turunkan **FORK KE TANAH** — tilt mast ke belakang — parking brake ON
- ✅ Pasang **wheel chock** (ganjal roda) di depan dan belakang
- ✅ Matikan mesin, lepas kunci kontak, simpan kunci di saku
- ✅ Pasang label: **"UNIT DALAM PERAWATAN — DILARANG DIOPERASIKAN"**
- ❌ Dilarang bekerja di bawah mast/fork tanpa safety stand
- ❌ Dilarang membersihkan unit yang masih panas dengan air langsung

---

## D. JADWAL PM CATERPILLAR DP40

### 🔵 Service Harian — Sebelum Operasi (10 Jam)
| No | Item Pemeriksaan | Metode | Standar |
|----|-----------------|--------|---------|
| 1 | Level oli mesin | Dipstick | Antara L–H |
| 2 | Level coolant | Sight glass reservoir | ¾ penuh |
| 3 | Level oli hidrolik | Sight glass tangki | Antara L–H |
| 4 | Level elektrolit baterai | Visual | Di atas minimum |
| 5 | Tekanan ban (jika pneumatik) | Tire gauge | 7–8 bar |
| 6 | Kondisi fork & pin | Visual | Tidak retak, pin aman |
| 7 | Kondisi mast chain | Visual | Tidak aus, terlumasi |
| 8 | Fungsi rem service | Test jalan | Berhenti normal |
| 9 | Fungsi rem parkir | Test | Unit tidak bergerak |
| 10 | Fungsi klakson | Test | Berbunyi jelas |
| 11 | Fungsi lampu | Test | Semua menyala |
| 12 | Kebocoran fluida | Visual walkaround | Tidak ada bocor |

### 🟢 Service 250 Jam
| No | Item | Tindakan |
|----|------|----------|
| 1 | Oli mesin + filter oli | Ganti |
| 2 | Filter BBM | Ganti |
| 3 | Pelumas chain mast | Lumasi |
| 4 | Pelumas pin mast | Lumasi |
| 5 | Grease nipple steering | Grease |
| 6 | Belt alternator & fan | Periksa & setel |
| 7 | Baterai | Periksa + bersihkan terminal |

### 🟡 Service 500 Jam
| No | Item | Tindakan |
|----|------|----------|
| 1 | Filter udara (inner & outer) | Ganti |
| 2 | Filter oli transmisi | Ganti |
| 3 | Filter oli hidrolik | Ganti |
| 4 | Coolant | Periksa & tambah jika perlu |
| 5 | Selang & fitting hidrolik | Periksa kebocoran |
| 6 | Liftchain wear | Ukur elongasi |

### 🔴 Service 2.000 Jam
| No | Item | Tindakan |
|----|------|----------|
| 1 | Oli transmisi | Ganti |
| 2 | Oli hidrolik + flush | Ganti |
| 3 | Coolant (Anti-freeze) | Ganti total |
| 4 | Injektor bahan bakar | Kalibrasi |
| 5 | Liftchain | Ukur, ganti jika perlu |

---

## E. LANGKAH KERJA PRAKTIKUM

### TAHAP 1: Walkaround Inspection (25 menit)

**1.1 Sisi Kiri Unit**
```
□ Periksa kondisi ban kiri depan: ______________________
□ Periksa kondisi ban kiri belakang: ___________________
□ Periksa kebocoran oli mesin (bawah unit): ____________
□ Periksa kondisi exhaust pipe & muffler: ______________
```

**1.2 Bagian Depan (Mast & Fork)**
```
□ Kondisi fork kiri — ukur ketebalan: ________ mm (min. 90% tebal awal)
□ Kondisi fork kanan — ukur ketebalan: ________ mm
□ Kondisi pin fork: ☐ Aman  ☐ Perlu diganti
□ Kondisi mast chain kiri:
   - Elongasi: ________ mm / 12 link (maks 3% elongasi)
   - Pelumasan: ☐ Cukup  ☐ Perlu dilumasi
□ Kondisi mast chain kanan:
   - Elongasi: ________ mm / 12 link
□ Kondisi roller mast: ☐ Baik  ☐ Ada keausan
□ Kondisi selang hidrolik mast: ☐ Baik  ☐ Ada lecet/bocor
```

**1.3 Bagian Kanan Unit**
```
□ Kondisi tangki BBM — level: _______ % (atau gauge: _____)
□ Kondisi water separator — ada air: ☐ Ya  ☐ Tidak
□ Kondisi selang BBM: ☐ Baik  ☐ Ada bocor/lecet
```

**1.4 Bagian Belakang (Counterweight)**
```
□ Kondisi counterweight — tidak ada retak: ☐ OK  ☐ Ada masalah
□ Kondisi ban kiri belakang: _______________________
□ Kondisi ban kanan belakang: _____________________
```

**1.5 Area Mesin (Buka Hood)**
```
□ Level oli mesin (dipstick):
   Kondisi: _______ (L/H/antara L-H)
   Warna oli: ☐ Hitam pekat  ☐ Coklat normal  ☐ Abu-abu (ada air!)
   
□ Level coolant:
   Level di reservoir: _______________________
   Warna coolant: ______________________________
   
□ Level oli hidrolik:
   Kondisi sight glass: _______________________
   
□ Kondisi belt alternator:
   Defleksi: _______ mm (standar: 8–13 mm dengan beban 10 kgf)
   Kondisi visual: ☐ Baik  ☐ Retak  ☐ Aus
   
□ Kondisi baterai:
   Tegangan: _______ V
   Kondisi terminal: ☐ Bersih  ☐ Korosi (bersihkan!)
   Level elektrolit: ☐ Normal  ☐ Kurang
```

---

### TAHAP 2: Penggantian Oli Mesin & Filter (35 menit)

**Spesifikasi:**
- Oli mesin: **CAT DEO (Diesel Engine Oil) SAE 15W-40**
- Kapasitas total dengan filter: **9 liter**
- Part number filter oli: ___________________________

```
□ 1. Panaskan mesin 5 menit → matikan
□ 2. Tunggu 5 menit agar oli turun
□ 3. Siapkan wadah penampung (min. 10 liter)
□ 4. Buka drain plug (kunci 24 mm) → kuras oli
      Volume oli keluar: _______ liter
      Warna/kondisi oli: ______________________________
□ 5. Ganti gasket drain plug baru (atau pastikan kondisi baik)
□ 6. Pasang drain plug → torque: _______ N·m
□ 7. Lepas filter oli lama
□ 8. Olesi gasket filter baru dengan oli bersih
□ 9. Pasang filter baru → kencangkan tangan + ¾ putaran
□ 10. Isi oli baru melalui oil filler cap
       Volume oli diisi: _______ liter
□ 11. Cek level dipstick → sesuaikan
□ 12. Hidupkan mesin → cek kebocoran → matikan mesin
□ 13. Tunggu 5 menit → cek level akhir dipstick
       Level akhir: ☐ Antara L–H  ☐ Perlu tambah
```

---

### TAHAP 3: Pemeriksaan & Service Mast Chain (25 menit)

**Pengukuran Elongasi Chain:**
```
Alat: Penggaris / chain wear gauge
Cara: Ukur 12 link dalam kondisi chain tegang

Spesifikasi: 1 link nominal _______ mm
             12 link nominal _______ mm
             Elongasi maks 3% = _______ mm

Hasil pengukuran:
Chain kiri  = _______ mm / 12 link → Elongasi = _______ %
Chain kanan = _______ mm / 12 link → Elongasi = _______ %

Status: ☐ OK  ☐ Perlu diganti (> 3% elongasi)
```

**Pelumasan Chain:**
```
□ Gunakan CAT Chain Lube atau oli SAE 30
□ Aplikasikan merata di seluruh panjang chain
□ Naik/turunkan mast 3–4 kali untuk meratakan pelumas
□ Lap sisa pelumas yang menetes
```

---

### TAHAP 4: Pemeriksaan Sistem Pendingin (20 menit)

```
□ 1. Cek level coolant di reservoir (jangan buka tutup radiator panas!)
      Level: ______________________________
      
□ 2. Cek pH coolant (jika tersedia alat test):
      pH: _______ (standar: 8,5–10,5)
      
□ 3. Cek konsentrasi anti-freeze (jika cuaca ekstrem):
      Freezing point: _______ °C
      
□ 4. Bersihkan fin radiator dari debu/kotoran:
      Metode: ☐ Compressed air (arah dalam ke luar)
              ☐ Air bertekanan rendah
      Kondisi fin: ☐ Bersih  ☐ Banyak kotoran  ☐ Ada kerusakan
      
□ 5. Periksa kondisi hose radiator (atas & bawah):
      Kondisi: ☐ Baik  ☐ Retak/mengeras  ☐ Bocor
```

---

### TAHAP 5: Pelumasan Komponen (20 menit)

**Grease Point — Forklift CAT DP40:**

| No | Lokasi Grease Nipple | Jumlah | Grease |
|----|---------------------|--------|--------|
| 1 | Tilt cylinder pin depan (kiri-kanan) | 2 | CAT Ultra 5 Moly |
| 2 | Tilt cylinder pin belakang (kiri-kanan) | 2 | CAT Ultra 5 Moly |
| 3 | Mast support pin (kiri-kanan) | 2 | CAT Ultra 5 Moly |
| 4 | Steering knuckle (kiri-kanan) | 2 | CAT Ultra 5 Moly |
| 5 | Tie rod end | 2 | CAT Ultra 5 Moly |
| 6 | Pedal linkage | 2 | CAT Ultra 5 Moly |

```
Untuk setiap grease nipple:
□ Bersihkan nipple dari kotoran
□ Pasang grease gun
□ Pompa grease hingga keluar dari sisi sambungan (tidak berlebihan)
□ Lap sisa grease yang keluar
□ Catat jumlah pompa: _______ kali/nipple (rata-rata)
```

---

### TAHAP 6: Test Drive & Fungsi (20 menit)

```
□ 1. Hidupkan engine → idle 3–5 menit
□ 2. Cek panel instrument:
      - Lampu peringatan: ☐ Semua mati (normal) ☐ Ada yang menyala
      - Suhu coolant: _______ °C (normal < 100°C)
      - Oil pressure: ☐ Normal ☐ Rendah
      
□ 3. Test fungsi hidrolik:
      - Naik/turun fork (3 kali): ☐ Halus  ☐ Kasar/ada suara
      - Tilt maju-mundur (3 kali): ☐ Halus  ☐ Ada problem
      - Side shift (jika ada): ☐ Halus  ☐ Ada problem
      
□ 4. Test rem di area aman:
      Jalan ± 5 km/h → rem mendadak
      Berhenti dalam: _______ meter
      Status: ☐ Normal  ☐ Jarak terlalu jauh
      
□ 5. Test klakson & lampu
      Klakson: ☐ OK | Lampu depan: ☐ OK | Lampu sein: ☐ OK
      
□ 6. Periksa kebocoran setelah engine running:
      ☐ Tidak ada kebocoran
      ☐ Ada kebocoran di: ______________________________
```

---

## F. REKAP LEMBAR KERJA PM

### Ringkasan Temuan
| No | Item | Kondisi Sebelum | Tindakan | Status |
|----|------|----------------|----------|--------|
| 1 | Oli Mesin | | Diganti | ☐ Done |
| 2 | Filter Oli | | Diganti | ☐ Done |
| 3 | Chain Kiri | | | ☐ Done |
| 4 | Chain Kanan | | | ☐ Done |
| 5 | Coolant | | | ☐ Done |
| 6 | Belt | | | ☐ Done |
| 7 | Grease | | Dilumasi | ☐ Done |
| 8 | Fork | | | ☐ Done |

### Parts / Material yang Digunakan
| No | Nama Part | Part Number | Qty |
|----|-----------|-------------|-----|
| 1 | Filter oli | | 1 |
| 2 | Oli mesin | | liter |
| 3 | Grease | | gram |

---

## G. PERTANYAAN EVALUASI
1. Apa perbedaan antara service 250 jam dan 500 jam pada Forklift CAT DP40?
2. Jelaskan cara mengukur elongasi mast chain dan batas maksimumnya!
3. Mengapa fork tidak boleh dipakai jika ketebalannya kurang dari 90% tebal awal?
4. Sebutkan 5 titik grease nipple pada forklift dan jenis grease yang digunakan!
5. Apa yang harus dilakukan jika ditemukan kebocoran oli hidrolik saat walkaround?

---

## H. PENILAIAN PRAKTIKUM

| Aspek Penilaian | Bobot | Nilai Instruktur |
|----------------|-------|-----------------|
| K3 & APD — Selama Praktikum | 25% | |
| Walkaround Inspection — Kelengkapan | 20% | |
| Prosedur Ganti Oli — Ketepatan | 20% | |
| Pengukuran Chain & Data | 15% | |
| Pelumasan & Service Komponen | 10% | |
| Laporan, Kebersihan Alat & Area | 10% | |
| **TOTAL** | **100%** | |

**Nama Siswa  :** _______________________  **NIS :** _______________________
**Tanggal     :** _______________________
**Nama Instruktur :** _______________________
**Tanda Tangan :** _______________________
""",
                "", gid
            ),
        ]

        for j in jobsheets:
            judul, kategori, tujuan, isi, video, gid_ = j
            c.execute(
                "INSERT INTO materi(judul,kategori,tujuan_pembelajaran,isi_materi,link_video,created_by) VALUES(?,?,?,?,?,?)",
                (judul, kategori, tujuan, isi, video, gid_)
            )
        conn.commit()
        print(f"✅ {len(jobsheets)} jobsheet berhasil ditambahkan")
