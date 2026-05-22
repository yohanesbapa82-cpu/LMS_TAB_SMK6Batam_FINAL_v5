"""
main.py — LMS TAB SMK N6 Batam V5
Fully optimized for Streamlit Community Cloud
"""
import streamlit as st

# 1. KONFIGURASI HALAMAN (Wajib di baris paling atas Streamlit)
st.set_page_config(
    page_title="LMS TAB — SMK N 6 Batam",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. BYPASS IMPORT (Anti-IndentationError di Server Linux)
import utils
database = __import__('database')
auth = __import__('auth')
dashboard = __import__('dashboard')
materi = __import__('materi')
soal = __import__('soal')
ujian = __import__('ujian')
praktik = __import__('praktik')
nilai = __import__('nilai')

# 3. INITIALIZE DATABASE & SESSION
database.init_database()
auth.init_session_state()

# 4. LOGIC TAMPILAN (LOGIN ATAU DASHBOARD)
if not auth.isLoggedIn():
    # Jalankan styling bawaan tema industri
    utils.apply_custom_style()
    
    col_l, col_c, col_r = st.columns([1, 1.3, 1])
    with col_c:
        # Kotak Header Login (Ditutup dengan rapi dan aman)
        html_login = f"""
        <div style="text-align:center;padding:2rem 0 1.5rem;background:linear-gradient(135deg,#0D1B2A,#1C2E40);border-radius:18px;border:1px solid rgba(255,140,0,.25);margin-bottom:1.2rem;box-shadow:0 8px 32px rgba(0,0,0,.3);">
            <div style="border-bottom:1px solid rgba(255,140,0,.2);padding-bottom:1rem;margin-bottom:1rem;">{utils.TAB_LOGO_SVG}</div>
            <h2 style="color:#FF8C00;margin:0;font-weight:700;font-size:1.5rem;">LMS TEKNIK ALAT BERAT</h2>
            <p style="color:#A0B4C8;margin:5px 0 0;font-size:0.9rem;">SMK Negeri 6 Batam</p>
        </div>
        """
        st.markdown(html_login, unsafe_allow_html=True)
        
        # Panggil fungsi bawaan auth untuk merender form input & tombol login
        auth.show_login_page()

else:
    # JIKA USER SUDAH LOGIN, TAMPILKAN NAVIGASI UTAMA
    utils.apply_custom_style()
    
    # Render Informasi User di Sidebar Atas
    auth.render_user_info()
    
    # Menu Navigasi sesuai Role
    is_guru = auth.isGuru()
    
    if is_guru:
        menu_options = ["🏠 Dashboard", "📚 Kelola Materi", "📝 Bank Soal", "⚙️ Ujian Teori", "🚜 Penilaian Praktik", "📊 Rekap Nilai", "👥 Kelola Pengguna"]
    else:
        menu_options = ["🏠 Dashboard", "📚 Materi Belajar", "⚙️ Ujian Teori", "📊 Nilai Saya"]
        
    choice = st.sidebar.radio("NAVIGASI LMS", menu_options)
    
    st.sidebar.markdown("---")
    auth.render_logout_button()
    
    # Routing Halaman Menu
    if "Dashboard" in choice:
        dashboard.render_dashboard()
    elif "Materi" in choice:
        materi.render_materi()
    elif "Bank Soal" in choice:
        soal.render_bank_soal()
    elif "Ujian Teori" in choice:
        ujian.render_ujian()
    elif "Penilaian Praktik" in choice:
        praktik.render_penilaian_praktik()
    elif "Rekap Nilai" in choice or "Nilai Saya" in choice:
        nilai.render_rekap_nilai()
    elif "Kelola Pengguna" in choice:
        auth.render_user_management()
