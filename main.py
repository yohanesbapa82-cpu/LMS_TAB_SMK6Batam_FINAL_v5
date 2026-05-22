"""main.py — LMS TAB SMK N6 Batam V5"""
import streamlit as st
import sys

# Mengamankan konfigurasi halaman di baris awal tunggal tanpa blok menggantung
st.set_page_config(page_title="LMS TAB — SMK N 6 Batam", page_icon="⚙️", layout="wide", initial_sidebar_state="expanded")

# Trik Bypass: Memasukkan modul langsung ke sistem runtime Python
import utils
database = __import__('database')
auth = __import__('auth')
dashboard = __import__('dashboard')
materi = __import__('materi')
soal = __import__('soal')
ujian = __import__('ujian')
praktik = __import__('praktik')
nilai = __import__('nilai')

# Mendefinisikan alias fungsi agar kode main.py Anda ke bawah tidak perlu diubah
init_database = database.init_database
init_session_state = auth.init_session_state
show_login_page = auth.show_login_page
isLoggedIn = auth.isLoggedIn
isGuru = auth.isGuru
render_user_info = auth.render_user_info
render_logout_button = auth.render_logout_button
render_user_management = auth.render_user_management
apply_custom_style = utils.apply_custom_style
TAB_LOGO_SVG = utils.TAB_LOGO_SVG
{TAB_LOGO_SVG}
        <div style="margin-top:8px;">
            <div style="font-size:1.3rem;font-weight:700;color:#FF6B00;letter-spacing:2px;line-height:1;">TAB</div>
            <div style="font-size:0.68rem;color:#8CA0B8;letter-spacing:1.5px;margin-top:2px;">SMK NEGERI 6 BATAM</div>
            <div style="font-size:0.62rem;color:rgba(255,107,0,0.55);margin-top:1px;letter-spacing:1px;">TEKNIK ALAT BERAT</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    render_user_info()
    st.divider()

    if isGuru():
        st.markdown('<p style="font-size:0.65rem;font-weight:700;letter-spacing:2px;color:rgba(255,107,0,0.55);margin:0 0 4px 2px;">MENU UTAMA</p>', unsafe_allow_html=True)
        page = st.radio("nav_g", [
            "🏠  Dashboard",
            "📚  Materi & Jobsheet",
            "❓  Bank Soal",
            "📝  Kelola Ujian",
            "🔧  Penilaian Praktik",
            "📊  Nilai Akhir",
            "📈  Statistik Kelas",
        ], label_visibility="collapsed")
        st.markdown('<p style="font-size:0.65rem;font-weight:700;letter-spacing:2px;color:rgba(255,107,0,0.55);margin:8px 0 4px 2px;">ADMINISTRASI</p>', unsafe_allow_html=True)
        page_adm = st.radio("nav_adm",[
            "👥  Manajemen User",
            "—",
        ], label_visibility="collapsed", index=1)
        if page_adm != "—": page = page_adm
    else:
        st.markdown('<p style="font-size:0.65rem;font-weight:700;letter-spacing:2px;color:rgba(255,107,0,0.55);margin:0 0 4px 2px;">MENU SISWA</p>', unsafe_allow_html=True)
        page = st.radio("nav_s", [
            "🏠  Dashboard",
            "📚  Materi & Jobsheet",
            "✏️  Ujian Online",
            "🔧  Nilai Praktik",
            "📊  Nilai Akhir Saya",
        ], label_visibility="collapsed")
        page_adm = "—"

    st.divider()
    render_logout_button()
    st.markdown('<p style="text-align:center;color:#2A3B55;font-size:0.67rem;padding-top:6px;">v5.0 · Offline Ready<br>© 2025 SMK N 6 Batam</p>', unsafe_allow_html=True)

# ── ROUTER ────────────────────────────────────────────────────────────────────
p = page.strip()
if isGuru():
    if   "Dashboard"         in p: render_dashboard()
    elif "Materi"            in p: render_materi_page()
    elif "Bank Soal"         in p: render_soal_page()
    elif "Kelola Ujian"      in p: render_ujian_page()
    elif "Penilaian Praktik" in p: render_praktik_page()
    elif "Nilai Akhir"       in p: render_nilai_page()
    elif "Statistik"         in p: render_statistik_page()
    elif "Manajemen User"    in p: render_user_management()
else:
    if   "Dashboard"         in p: render_dashboard()
    elif "Materi"            in p: render_materi_siswa()
    elif "Ujian Online"      in p: render_ujian_page()
    elif "Nilai Praktik"     in p: render_praktik_page()
    elif "Nilai Akhir"       in p: render_nilai_page()
