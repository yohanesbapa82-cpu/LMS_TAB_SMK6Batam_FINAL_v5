"""soal.py — Bank Soal Pilihan Ganda"""
import streamlit as st
from database import (
    create_soal, get_all_soal, get_soal_by_materi,
    get_soal_count_by_materi, update_soal, delete_soal,
    get_all_materi
)
from utils import KATEGORI_OPTIONS, get_kategori_emoji, page_header, show_success, show_error

def render_soal_page():
    page_header("Bank Soal","Kelola soal pilihan ganda untuk ujian siswa","❓")
    tabs = st.tabs(["📋 Daftar Soal","➕ Tambah Soal","📊 Statistik"])
    with tabs[0]: render_daftar_soal()
    with tabs[1]: render_tambah_soal()
    with tabs[2]: _render_statistik_soal()

def render_daftar_soal():
    materi_list = get_all_materi()
    materi_map  = {"Semua Materi": None}
    materi_map.update({m["judul"]: m["id"] for m in materi_list})

    col1, col2 = st.columns([3,1])
    with col1:
        filter_m = st.selectbox("🔍 Filter Materi", list(materi_map.keys()), key="filter_soal")
    with col2:
        st.metric("Total Soal", get_soal_count_by_materi(None))

    mid = materi_map[filter_m]
    soal_list = get_all_soal() if mid is None else get_soal_by_materi(mid)

    if not soal_list:
        st.info("Belum ada soal. Tambahkan melalui tab 'Tambah Soal'.")
        return

    # Group by materi
    by_mat = {}
    for s in soal_list:
        key = s.get("materi_judul","Tanpa Materi") or "Tanpa Materi"
        by_mat.setdefault(key, []).append(s)

    for mat_judul, soal_items in by_mat.items():
        st.markdown(f"""
        <div style="background:#EBF8FF;border-left:4px solid #3182CE;
                    padding:0.6rem 1rem;border-radius:0 8px 8px 0;margin:1rem 0 0.5rem;">
            <b style="color:#2C5282;">📚 {mat_judul}</b>
            <span style="color:#718096;font-size:0.8rem;"> — {len(soal_items)} soal</span>
        </div>
        """, unsafe_allow_html=True)

        for idx, soal in enumerate(soal_items, 1):
            short_q = soal["pertanyaan"][:70] + ("..." if len(soal["pertanyaan"]) > 70 else "")
            with st.expander(f"#{soal['id']} &nbsp; {short_q}", expanded=False):
                st.markdown(f"**📌 Pertanyaan:** {soal['pertanyaan']}")
                c1,c2 = st.columns(2)
                with c1:
                    for opt,lbl in [("opsi_a","A"),("opsi_b","B")]:
                        color = "#276749" if lbl == soal["jawaban_benar"] else "#4A5568"
                        icon  = "✅" if lbl == soal["jawaban_benar"] else "🔵"
                        st.markdown(f"<span style='color:{color};'>{icon} **{lbl}.** {soal[opt]}</span>", unsafe_allow_html=True)
                with c2:
                    for opt,lbl in [("opsi_c","C"),("opsi_d","D")]:
                        color = "#276749" if lbl == soal["jawaban_benar"] else "#4A5568"
                        icon  = "✅" if lbl == soal["jawaban_benar"] else "🔵"
                        st.markdown(f"<span style='color:{color};'>{icon} **{lbl}.** {soal[opt]}</span>", unsafe_allow_html=True)

                st.markdown(f"""
                <div style="background:#C6F6D5;border-radius:6px;padding:6px 12px;display:inline-block;margin-top:8px;">
                    ✅ <b>Jawaban Benar: {soal['jawaban_benar']}</b>
                </div>""", unsafe_allow_html=True)

                bc1,bc2,_ = st.columns([1,1,4])
                with bc1:
                    if st.button("✏️ Edit", key=f"es_{soal['id']}", width="stretch"):
                        st.session_state.edit_soal_id = soal["id"]
                        st.rerun()
                with bc2:
                    if st.button("🗑️ Hapus", key=f"ds_{soal['id']}", width="stretch"):
                        if delete_soal(soal["id"]):
                            show_success("Soal dihapus.")
                            st.rerun()

    # Edit form
    if st.session_state.get("edit_soal_id"):
        _render_edit_soal(st.session_state.edit_soal_id)

def _render_edit_soal(soal_id):
    soal = next((s for s in get_all_soal() if s["id"] == soal_id), None)
    if not soal:
        st.session_state.edit_soal_id = None
        return
    st.markdown("---")
    st.subheader(f"✏️ Edit Soal #{soal_id}")
    materi_list = get_all_materi()
    mat_names   = [m["judul"] for m in materi_list]
    cur_mat     = next((m["judul"] for m in materi_list if m["id"] == soal["materi_id"]), mat_names[0] if mat_names else "")
    with st.form(f"form_edit_soal_{soal_id}"):
        sel_mat    = st.selectbox("Materi", mat_names, index=mat_names.index(cur_mat) if cur_mat in mat_names else 0)
        pertanyaan = st.text_area("Pertanyaan *", value=soal["pertanyaan"], height=100)
        c1,c2 = st.columns(2)
        with c1:
            a = st.text_input("A.", value=soal["opsi_a"])
            b = st.text_input("B.", value=soal["opsi_b"])
        with c2:
            cc = st.text_input("C.", value=soal["opsi_c"])
            d  = st.text_input("D.", value=soal["opsi_d"])
        opts = ["A","B","C","D"]
        jwb  = st.radio("Jawaban Benar *", opts, index=opts.index(soal["jawaban_benar"]), horizontal=True)
        s1,s2 = st.columns(2)
        with s1: save   = st.form_submit_button("💾 Simpan", type="primary", width="stretch")
        with s2: cancel = st.form_submit_button("❌ Batal", width="stretch")
        if save:
            if not pertanyaan.strip():
                show_error("Pertanyaan wajib diisi!")
            else:
                mat_id = next((m["id"] for m in materi_list if m["judul"] == sel_mat), soal["materi_id"])
                update_soal(soal_id, pertanyaan.strip(), a.strip(), b.strip(), cc.strip(), d.strip(), jwb)
                show_success("Soal berhasil diperbarui!")
                st.session_state.edit_soal_id = None
                st.rerun()
        if cancel:
            st.session_state.edit_soal_id = None
            st.rerun()

def render_tambah_soal():
    materi_list = get_all_materi()
    if not materi_list:
        st.warning("⚠️ Tambahkan materi terlebih dahulu sebelum membuat soal.")
        return
    mat_map = {m["judul"]: m["id"] for m in materi_list}

    with st.form("form_tambah_soal", clear_on_submit=True):
        st.subheader("➕ Tambah Soal Baru")
        sel_mat    = st.selectbox("Materi *", list(mat_map.keys()))
        pertanyaan = st.text_area("Pertanyaan *", placeholder="Tuliskan pertanyaan di sini...", height=100)
        st.markdown("**Opsi Jawaban:**")
        c1,c2 = st.columns(2)
        with c1:
            a = st.text_input("A.", placeholder="Opsi A")
            b = st.text_input("B.", placeholder="Opsi B")
        with c2:
            cc = st.text_input("C.", placeholder="Opsi C")
            d  = st.text_input("D.", placeholder="Opsi D")
        jwb  = st.radio("Jawaban Benar *", ["A","B","C","D"], horizontal=True)
        save = st.form_submit_button("💾 Simpan Soal", type="primary", width="stretch")
        if save:
            errs = []
            if not pertanyaan.strip(): errs.append("Pertanyaan wajib diisi")
            if not a.strip(): errs.append("Opsi A wajib diisi")
            if not b.strip(): errs.append("Opsi B wajib diisi")
            if not cc.strip(): errs.append("Opsi C wajib diisi")
            if not d.strip(): errs.append("Opsi D wajib diisi")
            if errs:
                for e in errs: show_error(e)
            else:
                sid = create_soal(mat_map[sel_mat], pertanyaan.strip(), a.strip(),
                                  b.strip(), cc.strip(), d.strip(), jwb, st.session_state.user_id)
                if sid:
                    show_success("Soal berhasil ditambahkan ke bank soal!")
                    st.rerun()

def _render_statistik_soal():
    st.subheader("📊 Statistik Bank Soal per Materi")
    materi_list = get_all_materi()
    if not materi_list:
        st.info("Belum ada materi.")
        return
    total = get_soal_count_by_materi(None)
    st.metric("Total Soal Seluruh Materi", total)
    import pandas as pd
    data = [{"Materi": m["judul"], "Kategori": m["kategori"],
              "Jumlah Soal": get_soal_count_by_materi(m["id"])} for m in materi_list]
    df = pd.DataFrame(data).sort_values("Jumlah Soal", ascending=False)
    st.dataframe(df, width="stretch", hide_index=True)
    from utils import bar_chart_nilai
    bar_chart_nilai({r["Materi"][:20]: r["Jumlah Soal"] for r in data}, "Distribusi Soal per Materi")
