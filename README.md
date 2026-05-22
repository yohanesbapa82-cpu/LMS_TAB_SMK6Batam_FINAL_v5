# LMS Teknik Alat Berat — SMK Negeri 6 Batam
**Version 5.0 | Offline-Ready | Python + Streamlit + SQLite**

## Cara Menjalankan
```bash
pip install -r requirements.txt
streamlit run main.py
```
Buka browser: http://localhost:8501

## Akun Login
| Role   | Username  | Password   |
|--------|-----------|------------|
| Guru   | yohanes   | guru123    |
| Guru   | nurkomar  | guru123    |
| Guru   | andrew    | guru123    |
| Guru   | rizky     | guru123    |
| Guru   | arifan    | guru123    |
| Siswa  | 244464    | siswa123   |
| Siswa  | 244465    | siswa123   |
| Siswa  | (NIS)     | siswa123   |

## Fitur Lengkap
- Dashboard bento-grid interaktif (guru & siswa)
- Logo TAB SMK N6 Batam di sidebar
- Manajemen Materi + Upload PDF/PPT
- 3 Jobsheet Praktikum otomatis (Tune-Up, Valve Clearance, Forklift DP40)
- Bank Soal (32 soal, 5 materi)
- Ujian Terjadwal (guru aktifkan, siswa kerjakan)
- Timer ujian otomatis
- Syarat selesai materi sebelum ujian
- Penilaian Praktik (Safety 30% + Prosedur 30% + Hasil 40%)
- Nilai Akhir (Teori 30% + Praktik 70%)
- Tabel nilai interaktif (filter, search, color-coded)
- Ranking siswa dengan progress bar
- Export CSV & Excel
- Reset password oleh guru
- 38 siswa + 5 guru XI TAB

## Struktur File
- main.py        — Entry point & routing
- database.py    — SQLite CRUD & seed data
- auth.py        — Login, logout, manajemen user
- utils.py       — CSS tema TAB + helpers
- dashboard.py   — Dashboard bento-grid
- materi.py      — Manajemen materi + upload file
- soal.py        — Bank soal
- ujian.py       — Sistem ujian terjadwal
- praktik.py     — Penilaian praktik lapangan
- nilai.py       — Nilai akhir & rekap
- requirements.txt

## Teknologi
Python 3.10+ | Streamlit 1.28+ | SQLite | Pandas | Matplotlib | Openpyxl
