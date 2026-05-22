"""auth.py — Login, logout, session, manajemen user"""
import streamlit as st
from database import verify_password, get_user_by_username, create_user, update_user_password, get_user_by_id

def init_session_state():
    for k,v in {"user_id":None,"username":None,"nama_lengkap":None,"role":None,"logged_in":False}.items():
        if k not in st.session_state: st.session_state[k]=v

def login_user(username, password):
    user = get_user_by_username(username)
    if user and verify_password(password, user["password"]):
        st.session_state.user_id      = user["id"]
        st.session_state.username     = user["username"]
        st.session_state.nama_lengkap = user["nama_lengkap"]
        st.session_state.role         = user["role"]
        st.session_state.logged_in    = True
        return True
    return False

def logout_user():
    for k in ["user_id","username","nama_lengkap","role","logged_in",
              "ujian_in_progress","ujian_soal_list","ujian_jawaban","ujian_materi_id"]:
        st.session_state[k] = None if k not in ["logged_in","ujian_soal_list","ujian_jawaban"] else \
                              (False if k=="logged_in" else ([] if k=="ujian_soal_list" else {}))

def isLoggedIn(): return st.session_state.get("logged_in",False)
def isGuru():     return st.session_state.get("role")=="guru"
def isSiswa():    return st.session_state.get("role")=="siswa"

def get_current_user():
    if isLoggedIn():
        return {k:st.session_state.get(k) for k in ["user_id","username","nama_lengkap","role"]}
    return None

def require_login():
    if not isLoggedIn(): show_login_page(); st.stop()

def show_login_page():
    """Tampilan login page dengan logo TAB SMK N 6 Batam."""
    from utils import apply_custom_style, TAB_LOGO_SVG
    col_l, col_c, col_r = st.columns([1, 1.3, 1])
    with col_c:
        # Logo + judul
        st.markdown(f"""
        <div style="text-align:center;padding:2rem 0 1.5rem;
                    background:linear-gradient(135deg,#0D1B2A,#1C2E40);
                    border-radius:18px;border:1px solid rgba(255,140,0,.25);
                    margin-bottom:1.2rem;box-shadow:0 8px 32px rgba(0,0,0,.3);">
            <div style="border-bottom:1px solid rgba(255,140,0,.2);
                        padding-bottom:1rem;margin-bottom:1rem;">
                {tab_logo(80)}
            </div>
            <div style="font-size:1.7rem;font-weight:800;color:#FF8C00;
                        letter-spacing:3px;font-family:'Inter',sans-serif;">
                LMS ALAT BERAT
            </div>
            <div style="font-size:.75rem;color:#6B8FAA;letter-spacing:2px;margin-top:4px;">
                LEARNING MANAGEMENT SYSTEM
            </div>
            <div style="font-size:.82rem;color:#9CB3C9;font-weight:600;margin-top:6px;">
                SMK NEGERI 6 BATAM
            </div>
            <div style="font-size:.68rem;color:rgba(255,140,0,.5);
                        letter-spacing:3px;margin-top:2px;">
                TEKNIK ALAT BERAT
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Form login
        with st.form("login_form", clear_on_submit=False):
            st.markdown("**🔐 Masuk ke Sistem**")
            username = st.text_input("👤 Username", placeholder="Username Anda")
            password = st.text_input("🔒 Password", type="password", placeholder="Password")
            submitted = st.form_submit_button("🚀 Login", use_container_width=True, type="primary")
            if submitted:
                if not username or not password:
                    st.warning("⚠️ Isi username dan password!")
                elif login_user(username.strip(), password):
                    st.success(f"✅ Selamat datang, {st.session_state.nama_lengkap}!")
                    st.rerun()
                else:
                    st.error("❌ Username atau password salah!")

        st.markdown("""
        <div style="background:rgba(255,140,0,.06);border-radius:10px;padding:.9rem 1rem;
                    margin-top:1rem;border:1px solid rgba(255,140,0,.15);font-size:.82rem;">
            <b style="color:#FF8C00;">⬡ Cara Login:</b><br>
            <span style="color:#64748B;">
            👨‍🏫 Guru &nbsp;→&nbsp; username: <code>yohanes</code>, <code>andrew</code>, ...<br>
            👷 Siswa &nbsp;→&nbsp; username: NIS (<code>244464</code>, <code>244465</code>, ...)<br>
            🔒 Password: <code>guru123</code> / <code>siswa123</code>
            </span>
        </div>
        """, unsafe_allow_html=True)


def render_logout_button():
    if st.sidebar.button("🚪  Logout", use_container_width=True):
        logout_user(); st.rerun()

def render_user_info():
    if not isLoggedIn(): return
    user_db   = get_user_by_id(st.session_state.user_id) or {}
    is_guru   = st.session_state.role == "guru"
    role_icon = "👨‍🏫" if is_guru else "👷"
    role_txt  = "Guru" if is_guru else "Siswa"
    nama      = st.session_state.nama_lengkap or ""
    nis       = user_db.get("nis","") if not is_guru else ""
    kelas     = user_db.get("kelas","") if not is_guru else ""

    st.sidebar.markdown("**Logged in as**")
    st.sidebar.markdown(f"**{nama}**")
    if nis:   st.sidebar.caption(f"NIS: {nis}")
    if kelas: st.sidebar.caption(f"📌 {kelas}")
    st.sidebar.caption(f"{role_icon} {role_txt}")

def render_user_management():
    if not isGuru():
        st.error("⛔ Hanya guru yang dapat mengakses fitur ini."); return
    from utils import page_header, show_success, show_error
    page_header("Manajemen Pengguna","Kelola akun guru & siswa","👥")

    tab1,tab2,tab3 = st.tabs(["📋 Daftar Pengguna","➕ Tambah Pengguna","🔑 Reset Password"])

    with tab1:
        import pandas as pd
        from database import get_all_users
        users = get_all_users()
        if not users:
            st.info("Belum ada data.")
        else:
            guru_list  = [u for u in users if u["role"]=="guru"]
            siswa_list = [u for u in users if u["role"]=="siswa"]
            st.markdown(f"### 👨‍🏫 Guru ({len(guru_list)} orang)")
            df_g = pd.DataFrame(guru_list)[["username","nama_lengkap","created_at"]]
            df_g.columns = ["Username","Nama Lengkap","Tgl Daftar"]
            df_g["Tgl Daftar"] = df_g["Tgl Daftar"].apply(lambda x:str(x)[:10])
            st.dataframe(df_g,use_container_width=True,hide_index=True)
            st.markdown(f"### 👷 Siswa ({len(siswa_list)} orang)")
            df_s = pd.DataFrame(siswa_list)[["nis","nama_lengkap","username","kelas"]]
            df_s.columns = ["NIS","Nama Lengkap","Username","Kelas"]
            st.dataframe(df_s,use_container_width=True,hide_index=True)
            st.download_button("📥 Export Daftar Siswa",
                df_s.to_csv(index=False).encode("utf-8-sig"),
                "daftar_siswa.csv","text/csv")

    with tab2:
        with st.form("form_tambah",clear_on_submit=True):
            c1,c2 = st.columns(2)
            with c1:
                nama     = st.text_input("Nama Lengkap *")
                username = st.text_input("Username *")
                role     = st.selectbox("Role *",["siswa","guru"])
            with c2:
                nis      = st.text_input("NIS",placeholder="24.4.xxx")
                kelas    = st.text_input("Kelas",placeholder="XI TAB")
                password = st.text_input("Password *",type="password",value="siswa123")
                konfirm  = st.text_input("Konfirmasi *",type="password",value="siswa123")
            save = st.form_submit_button("💾 Simpan",type="primary",use_container_width=True)
            if save:
                errs=[]
                if not nama:     errs.append("Nama wajib diisi")
                if not username: errs.append("Username wajib diisi")
                if not password or len(password)<6: errs.append("Password min 6 karakter")
                if password!=konfirm: errs.append("Password tidak cocok")
                if errs:
                    for e in errs: st.error(f"❌ {e}")
                elif get_user_by_username(username):
                    st.error("❌ Username sudah ada!")
                else:
                    create_user(username.strip(),password,nama.strip(),role,kelas.strip(),nis.strip())
                    show_success(f"Pengguna **{nama}** ditambahkan! Login: `{username}` / `{password}`")
                    st.rerun()

    with tab3:
        from database import get_all_users
        users = get_all_users()
        umap  = {f"[{u['role'].upper()}] {u['nama_lengkap']} ({u['username']})": u["id"] for u in users}
        with st.form("form_reset",clear_on_submit=True):
            sel   = st.selectbox("Pilih Pengguna *",list(umap.keys()))
            new_pw= st.text_input("Password Baru *",type="password",placeholder="Min. 6 karakter")
            kon2  = st.text_input("Konfirmasi *",type="password")
            if st.form_submit_button("🔄 Reset Password",type="primary",use_container_width=True):
                if not new_pw or len(new_pw)<6:
                    st.error("❌ Password minimal 6 karakter!")
                elif new_pw!=kon2:
                    st.error("❌ Password tidak cocok!")
                else:
                    update_user_password(umap[sel],new_pw)
                    show_success(f"Password berhasil direset! Password baru: `{new_pw}`")
