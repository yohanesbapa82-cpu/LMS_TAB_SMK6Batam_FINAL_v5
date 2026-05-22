"""materi.py — Manajemen materi pembelajaran dengan dukungan upload file PPT/PDF"""
import os
import streamlit as st
from database import (
    create_materi, get_all_materi, get_materi_by_id,
    get_materi_by_kategori, update_materi, delete_materi,
    tandai_materi_selesai, get_materi_selesai
)
from utils import (
    KATEGORI_OPTIONS, get_kategori_emoji, get_kategori_color,
    page_header, show_success, show_error
)

UPLOAD_DIR = "uploads/materi"

def _ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def _save_file(uploaded_file, prefix=""):
    """Simpan file upload, return (path, file_type)."""
    _ensure_upload_dir()
    ext       = os.path.splitext(uploaded_file.name)[1].lower()
    safe_name = uploaded_file.name.replace(" ", "_")
    filename  = f"{prefix}_{safe_name}" if prefix else safe_name
    filepath  = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return filepath, ext.lstrip(".")

def _file_type_icon(file_type):
    icons = {"pdf":"📄","ppt":"📊","pptx":"📊","doc":"📝","docx":"📝","xls":"📈","xlsx":"📈"}
    return icons.get((file_type or "").lower(), "📎")

def _file_size_str(path):
    try:
        size = os.path.getsize(path)
        if size < 1024:         return f"{size} B"
        elif size < 1024**2:    return f"{size/1024:.1f} KB"
        else:                   return f"{size/1024**2:.1f} MB"
    except:
        return "—"


# ═══════════════════════════ GURU ═════════════════════════════════════════════

def render_materi_page():
    page_header("Materi Pembelajaran",
                "Kelola materi teks, video, PDF, dan file presentasi untuk siswa","📚")
    tabs = st.tabs(["📋 Daftar Materi","➕ Tambah Materi","📁 Jobsheet Praktikum"])
    with tabs[0]: _guru_daftar()
    with tabs[1]: _guru_tambah()
    with tabs[2]: _guru_jobsheet()


def _guru_daftar():
    col1,_ = st.columns([3,1])
    with col1:
        fk = st.selectbox("🔍 Filter Kategori", ["Semua"] + KATEGORI_OPTIONS, key="fk_guru")
    materi_list = get_all_materi() if fk=="Semua" else get_materi_by_kategori(fk)

    if not materi_list:
        st.info("Belum ada materi. Tambahkan melalui tab **➕ Tambah Materi**.")
        return

    # Group by kategori
    by_kat = {}
    for m in materi_list:
        by_kat.setdefault(m["kategori"], []).append(m)

    for kat, items in by_kat.items():
        emoji = get_kategori_emoji(kat)
        color = get_kategori_color(kat)
        st.markdown(f"""
        <div style="background:{color}18;border-left:4px solid {color};
                    padding:0.6rem 1rem;border-radius:0 8px 8px 0;margin:1rem 0 0.5rem;">
            <b style="color:{color};font-size:1rem;">{emoji} {kat}</b>
            <span style="color:#718096;font-size:0.8rem;"> — {len(items)} materi</span>
        </div>
        """, unsafe_allow_html=True)

        for m in items:
            has_file  = bool(m.get("file_path")) and os.path.exists(m.get("file_path",""))
            file_icon = _file_type_icon(m.get("file_type","")) if has_file else ""
            is_jobsheet = "Jobsheet" in m["judul"] or "Job Sheet" in m["judul"]
            js_badge    = " 🗒️ *Jobsheet*" if is_jobsheet else ""

            with st.expander(f"{'📄' if has_file else '📝'} **{m['judul']}**{js_badge}", expanded=False):
                col_i, col_b = st.columns([4,1])
                with col_i:
                    st.caption(f"👨‍🏫 {m.get('guru_name','?')} | 📅 {str(m.get('created_at',''))[:10]}")
                    if m.get("tujuan_pembelajaran"):
                        st.info(f"🎯 {m['tujuan_pembelajaran'][:200]}")
                    if m.get("link_video"):
                        st.markdown(f"🎬 **Video:** [{m['link_video'][:50]}...]({m['link_video']})")
                    if has_file:
                        fsize = _file_size_str(m["file_path"])
                        st.markdown(f"""
                        <div style="background:#EBF8FF;border-radius:8px;padding:8px 12px;
                                    border-left:3px solid #3182CE;margin:6px 0;">
                            {file_icon} <b>File Terlampir:</b>
                            {os.path.basename(m['file_path'])} ({m.get('file_type','').upper()}, {fsize})
                        </div>
                        """, unsafe_allow_html=True)
                        with open(m["file_path"],"rb") as f:
                            st.download_button(
                                f"⬇️ Download {m.get('file_type','').upper()}",
                                data=f.read(),
                                file_name=os.path.basename(m["file_path"]),
                                key=f"dl_guru_{m['id']}"
                            )
                    if m.get("isi_materi"):
                        with st.expander("👁️ Preview Isi Materi"):
                            st.markdown(m["isi_materi"][:2000])

                with col_b:
                    if st.button("✏️ Edit",  key=f"eg_{m['id']}", use_container_width=True):
                        st.session_state.edit_materi_id = m["id"]; st.rerun()
                    if st.button("🗑️ Hapus", key=f"dg_{m['id']}", use_container_width=True):
                        # Hapus file fisik juga
                        if has_file:
                            try: os.remove(m["file_path"])
                            except: pass
                        delete_materi(m["id"])
                        show_success("Materi dihapus."); st.rerun()

            # Form edit inline
            if st.session_state.get("edit_materi_id") == m["id"]:
                _form_edit(m["id"])


def _form_edit(mid):
    m = get_materi_by_id(mid)
    if not m: return
    st.markdown("---")
    st.subheader(f"✏️ Edit: {m['judul']}")
    has_file = bool(m.get("file_path")) and os.path.exists(m.get("file_path",""))

    with st.form(f"form_edit_{mid}"):
        c1,c2 = st.columns(2)
        with c1:
            judul  = st.text_input("Judul *", value=m["judul"])
        with c2:
            kat_i  = KATEGORI_OPTIONS.index(m["kategori"]) if m["kategori"] in KATEGORI_OPTIONS else 0
            kat    = st.selectbox("Kategori *", KATEGORI_OPTIONS, index=kat_i)
        tujuan = st.text_area("Tujuan Pembelajaran", value=m.get("tujuan_pembelajaran",""), height=80)
        isi    = st.text_area("Isi Materi (Markdown)", value=m.get("isi_materi",""), height=300)
        video  = st.text_input("Link Video YouTube", value=m.get("link_video",""))

        st.markdown("**📎 Upload File Baru** *(opsional — akan mengganti file lama)*")
        if has_file:
            st.caption(f"File saat ini: `{os.path.basename(m['file_path'])}`")
        new_file = st.file_uploader("Pilih file PPT/PPTX/PDF", type=["pdf","ppt","pptx"],
                                     key=f"uf_edit_{mid}")

        b1,b2 = st.columns(2)
        with b1: save   = st.form_submit_button("💾 Simpan", type="primary", use_container_width=True)
        with b2: cancel = st.form_submit_button("❌ Batal", use_container_width=True)

        if save:
            if not judul.strip():
                show_error("Judul tidak boleh kosong!"); return
            fp, ft = m.get("file_path",""), m.get("file_type","")
            if new_file:
                if has_file:
                    try: os.remove(m["file_path"])
                    except: pass
                fp, ft = _save_file(new_file, prefix=f"mat_{mid}")
            update_materi(mid, judul.strip(), tujuan.strip(), isi.strip(),
                          video.strip(), kat, fp, ft)
            show_success(f"Materi '{judul}' diperbarui!")
            st.session_state.edit_materi_id = None; st.rerun()
        if cancel:
            st.session_state.edit_materi_id = None; st.rerun()


def _guru_tambah():
    st.subheader("➕ Tambah Materi Baru")
    st.markdown("Materi dapat berupa teks markdown, link video YouTube, **dan/atau** file PPT/PDF.")

    with st.form("form_tambah_materi", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            judul  = st.text_input("Judul Materi *", placeholder="Contoh: Sistem Pendingin Mesin Diesel")
        with c2:
            kat    = st.selectbox("Kategori *", KATEGORI_OPTIONS)
        tujuan = st.text_area("Tujuan Pembelajaran *",
                              placeholder="Setelah mempelajari ini, siswa mampu...", height=80)

        st.markdown("---")
        st.markdown("#### 📝 Isi Materi")
        tab_t, tab_f = st.tabs(["✍️ Teks Markdown","📎 Upload File (PDF/PPT)"])
        with tab_t:
            isi = st.text_area("Isi Materi", placeholder="# Judul\n\n## Sub Judul\n\nIsi materi...",
                               height=300, label_visibility="collapsed")
        with tab_f:
            up_file = st.file_uploader(
                "Upload file PDF, PPT, atau PPTX",
                type=["pdf","ppt","pptx"],
                help="File akan dapat didownload oleh siswa di halaman materi"
            )
            if up_file:
                st.success(f"✅ File dipilih: **{up_file.name}** ({up_file.size/1024:.1f} KB)")
                st.caption("File akan disimpan setelah klik Simpan.")

        st.markdown("---")
        video = st.text_input("🎬 Link Video YouTube (opsional)",
                              placeholder="https://www.youtube.com/watch?v=...")
        st.caption("💡 Bisa kombinasikan: teks + file + video sekaligus")
        save = st.form_submit_button("💾 Simpan Materi", type="primary", use_container_width=True)

        if save:
            if not judul.strip() or not tujuan.strip():
                show_error("Judul dan Tujuan Pembelajaran wajib diisi!"); return
            if not isi.strip() and not up_file:
                show_error("Isi setidaknya salah satu: Teks Materi atau Upload File!"); return

            fp, ft = "", ""
            if up_file:
                fp, ft = _save_file(up_file, prefix=f"mat_new")

            mid = create_materi(judul.strip(), tujuan.strip(), isi.strip(),
                                video.strip() or None, kat, st.session_state.user_id,
                                fp, ft)
            if mid:
                msg = f"Materi **'{judul}'** berhasil ditambahkan!"
                if fp: msg += f" File `{os.path.basename(fp)}` tersimpan."
                show_success(msg); st.rerun()


def _guru_jobsheet():
    """Tab khusus menampilkan semua jobsheet yang tersedia."""
    page_header("Jobsheet Praktikum",
                "Daftar jobsheet praktikum yang tersedia untuk siswa kelas XI TAB","🗒️")

    materi_list = get_all_materi()
    jobsheets   = [m for m in materi_list
                   if "Jobsheet" in m["judul"] or "Job Sheet" in m["judul"]]

    if not jobsheets:
        st.info("Belum ada jobsheet. Akan ditambahkan otomatis setelah restart aplikasi.")
        return

    st.success(f"📋 Tersedia **{len(jobsheets)}** Jobsheet Praktikum")
    st.divider()

    for j in jobsheets:
        color = get_kategori_color(j["kategori"])
        with st.expander(f"🗒️ **{j['judul']}** — _{j['kategori']}_"):
            st.markdown(f"""
            <div style="background:{color}12;border-left:4px solid {color};
                        border-radius:0 8px 8px 0;padding:0.8rem 1rem;margin-bottom:1rem;">
                <b style="color:{color};">🎯 Kompetensi:</b><br>
                {j.get('tujuan_pembelajaran','—')}
            </div>
            """, unsafe_allow_html=True)

            with st.expander("📄 Tampilkan Isi Jobsheet", expanded=False):
                st.markdown(j.get("isi_materi",""))

            # Tombol generate PDF jobsheet
            col1, col2, _ = st.columns([1,1,2])
            with col1:
                if st.button("🖨️ Print Jobsheet", key=f"print_js_{j['id']}",
                             use_container_width=True, type="primary"):
                    st.session_state[f"show_print_{j['id']}"] = True
            with col2:
                # Download sebagai teks
                content_dl = j.get("isi_materi","")
                st.download_button(
                    "⬇️ Download (.md)",
                    data=content_dl.encode("utf-8"),
                    file_name=f"{j['judul'].replace(' ','_')}.md",
                    key=f"dl_js_{j['id']}", use_container_width=True
                )

            if st.session_state.get(f"show_print_{j['id']}"):
                st.markdown("""
                <div style="background:#FFFBEB;border-radius:10px;padding:1rem;
                            border:1px solid #D69E2E;margin-top:0.5rem;">
                    💡 <b>Cara print jobsheet:</b><br>
                    1. Klik <b>Tampilkan Isi Jobsheet</b> di atas<br>
                    2. Pilih semua teks (Ctrl+A) → Copy<br>
                    3. Paste ke Microsoft Word / Google Docs<br>
                    4. Print dari sana untuk hasil terbaik
                </div>
                """, unsafe_allow_html=True)


# ═══════════════════════════ SISWA ════════════════════════════════════════════

def render_materi_siswa():
    page_header("Materi Pembelajaran",
                "Baca materi hingga selesai — klik Tandai Selesai untuk membuka ujian","📚")

    sid         = st.session_state.user_id
    selesai_ids = get_materi_selesai(sid)
    all_materi  = get_all_materi()
    total_m     = len(all_materi)
    done_cnt    = len(selesai_ids)
    pct         = int(done_cnt/total_m*100) if total_m else 0

    # Progress bar
    c1,c2 = st.columns([2,1])
    with c1:
        st.markdown(f"""
        <div style="background:white;border-radius:10px;padding:0.8rem 1.2rem;
                    box-shadow:0 1px 4px rgba(0,0,0,0.07);border-left:4px solid #FF6B35;">
            <b style="color:#1A365D;">📈 Progress Materi Saya</b> &nbsp;—&nbsp;
            <span style="color:#FF6B35;font-weight:700;">{done_cnt}/{total_m} materi selesai ({pct}%)</span>
        </div>
        """, unsafe_allow_html=True)
        st.progress(pct/100)
    with c2:
        fk = st.selectbox("📂 Kategori", ["Semua"]+KATEGORI_OPTIONS, key="fk_siswa")

    materi_list = all_materi if fk=="Semua" else get_materi_by_kategori(fk)
    if not materi_list:
        st.info("Belum ada materi."); return

    st.divider()

    # Pisah jobsheet & materi biasa
    jobsheets  = [m for m in materi_list if "Jobsheet" in m["judul"] or "Job Sheet" in m["judul"]]
    reg_materi = [m for m in materi_list if m not in jobsheets]

    # ── Materi Reguler
    if reg_materi:
        st.markdown("### 📚 Materi Pembelajaran")
        for m in reg_materi:
            _siswa_materi_card(m, selesai_ids, sid)

    # ── Jobsheet
    if jobsheets:
        st.divider()
        st.markdown("### 🗒️ Jobsheet Praktikum")
        st.caption("Jobsheet digunakan sebagai panduan saat kegiatan praktikum di bengkel/lapangan.")
        for m in jobsheets:
            _siswa_jobsheet_card(m, selesai_ids, sid)


def _siswa_materi_card(m, selesai_ids, sid):
    emoji   = get_kategori_emoji(m["kategori"])
    color   = get_kategori_color(m["kategori"])
    sudah   = m["id"] in selesai_ids
    has_file= bool(m.get("file_path")) and os.path.exists(m.get("file_path",""))
    badges  = ("✅ Selesai" if sudah else "⏳ Belum") + (" · 📎 Ada File" if has_file else "")

    with st.expander(f"{emoji} **{m['judul']}** &nbsp; {'✅' if sudah else '⏳'}", expanded=False):
        # Badge
        bc  = "#276749" if sudah else "#744210"
        bbg = "#C6F6D5" if sudah else "#FEEBC8"
        st.markdown(f"""
        <span style="background:{bbg};color:{bc};padding:3px 12px;
                     border-radius:20px;font-weight:600;font-size:0.82rem;">{badges}</span>
        """, unsafe_allow_html=True)

        # Tujuan
        st.markdown(f"""
        <div style="background:{color}10;border-radius:8px;padding:10px 14px;
                    margin:10px 0;border-left:3px solid {color};">
            <b style="color:{color};">🎯 Tujuan:</b> {m.get('tujuan_pembelajaran','—')}
        </div>
        """, unsafe_allow_html=True)

        # Video
        if m.get("link_video"):
            st.markdown(f"🎬 **Video Pembelajaran:** [Klik untuk menonton]({m['link_video']})")

        # File download
        if has_file:
            fsize = _file_size_str(m["file_path"])
            ficon = _file_type_icon(m.get("file_type",""))
            st.markdown(f"""
            <div style="background:#EBF8FF;border-radius:8px;padding:8px 14px;
                        border-left:3px solid #3182CE;margin:8px 0;">
                {ficon} <b>File Materi:</b> {os.path.basename(m['file_path'])}
                <span style="color:#718096;font-size:0.8rem;">({m.get('file_type','').upper()}, {fsize})</span>
            </div>
            """, unsafe_allow_html=True)
            col_dl,_ = st.columns([1,3])
            with col_dl:
                with open(m["file_path"],"rb") as f:
                    st.download_button(
                        f"⬇️ Download {m.get('file_type','File').upper()}",
                        data=f.read(),
                        file_name=os.path.basename(m["file_path"]),
                        key=f"dl_sis_{m['id']}", use_container_width=True, type="primary"
                    )

        # Isi teks
        if m.get("isi_materi"):
            st.divider()
            st.markdown(m["isi_materi"])
        elif not has_file:
            st.info("Isi materi belum tersedia.")

        # Tandai Selesai
        st.divider()
        if sudah:
            st.success("✅ Materi ini sudah kamu selesaikan. Akses ujian terkait sudah terbuka!")
        else:
            st.markdown("""
            <div style="background:#FFFBEB;border-radius:8px;padding:0.7rem 1rem;
                        border-left:3px solid #D69E2E;font-size:0.87rem;">
                📌 Setelah selesai membaca/melihat materi di atas, klik tombol berikut
                untuk membuka akses ujian materi ini.
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"✅ Tandai Sudah Selesai Dibaca — '{m['judul']}'",
                         key=f"done_{m['id']}", type="primary"):
                tandai_materi_selesai(sid, m["id"])
                show_success("Materi ditandai selesai! Akses ujian terbuka.")
                st.rerun()


def _siswa_jobsheet_card(m, selesai_ids, sid):
    color = get_kategori_color(m["kategori"])
    sudah = m["id"] in selesai_ids

    with st.expander(f"🗒️ **{m['judul']}** &nbsp; {'✅' if sudah else '📋'}"):
        st.markdown(f"""
        <div style="background:{color}10;border-left:4px solid {color};border-radius:0 8px 8px 0;
                    padding:0.7rem 1rem;margin-bottom:0.8rem;">
            <b style="color:{color};">📋 Kompetensi:</b> {m.get('tujuan_pembelajaran','—')}
        </div>
        """, unsafe_allow_html=True)

        # File download jika ada
        has_file = bool(m.get("file_path")) and os.path.exists(m.get("file_path",""))
        if has_file:
            ficon = _file_type_icon(m.get("file_type",""))
            col_dl,_ = st.columns([1,3])
            with col_dl:
                with open(m["file_path"],"rb") as f:
                    st.download_button(
                        f"{ficon} Download Jobsheet",
                        data=f.read(),
                        file_name=os.path.basename(m["file_path"]),
                        key=f"dl_js_sis_{m['id']}", use_container_width=True, type="primary"
                    )

        # Isi jobsheet
        if m.get("isi_materi"):
            with st.expander("📄 Buka Isi Jobsheet", expanded=False):
                st.markdown(m["isi_materi"])
                # Download sebagai markdown
                col_d,_ = st.columns([1,3])
                with col_d:
                    st.download_button(
                        "⬇️ Download (.md)",
                        data=m["isi_materi"].encode("utf-8"),
                        file_name=f"{m['judul'].replace(' ','_')}.md",
                        key=f"dl_jstxt_{m['id']}", use_container_width=True
                    )

        # Tandai selesai untuk jobsheet juga
        st.divider()
        if sudah:
            st.success("✅ Jobsheet ini sudah kamu tandai selesai.")
        else:
            if st.button(f"✅ Tandai Jobsheet Selesai Dibaca",
                         key=f"js_done_{m['id']}", type="secondary"):
                tandai_materi_selesai(sid, m["id"])
                show_success("Jobsheet ditandai selesai!")
                st.rerun()
