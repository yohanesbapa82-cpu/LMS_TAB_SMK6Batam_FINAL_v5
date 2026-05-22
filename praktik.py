"""praktik.py — Penilaian Praktik Lapangan SMK TAB"""
import os
import streamlit as st
from database import (
    save_nilai_praktik, get_nilai_praktik_by_siswa, get_all_nilai_praktik,
    get_all_siswa, get_rata_nilai_praktik, delete_nilai_praktik
)
from utils import (
    MODUL_PRAKTIK_OPTIONS, page_header,
    format_tanggal_short, hitung_nilai_praktik,
    get_predikat, get_grade_letter, show_success, show_error
)

UPLOAD_DIR = "uploads"

def render_praktik_page():
    if st.session_state.role == "guru":
        _guru_view()
    else:
        _siswa_view()

# ─── GURU ─────────────────────────────────────────────────────────────────────

def _guru_view():
    page_header("Penilaian Praktik Lapangan",
                "Input & kelola penilaian keterampilan praktik siswa — Safety 30% | Prosedur 30% | Hasil 40%",
                "🔧")
    tabs = st.tabs(["➕ Input Nilai", "📋 Rekap Nilai", "📊 Grafik & Statistik"])
    with tabs[0]: _input_form()
    with tabs[1]: _rekap_nilai()
    with tabs[2]: _grafik()

def _input_form():
    siswa_list = get_all_siswa()
    if not siswa_list:
        st.warning("Belum ada siswa terdaftar.")
        return

    siswa_map = {f"{s['nama_lengkap']} ({s.get('kelas','')})": s["id"] for s in siswa_list}

    with st.form("form_praktik", clear_on_submit=True):
        st.subheader("📝 Input Nilai Praktik Baru")
        c1, c2 = st.columns(2)
        with c1:
            siswa_label = st.selectbox("Siswa *", list(siswa_map.keys()))
            modul       = st.selectbox("Modul Praktik *", MODUL_PRAKTIK_OPTIONS)
            tanggal     = st.date_input("Tanggal Penilaian *")
        with c2:
            st.markdown("#### 📊 Komponen Penilaian (0–100)")
            safety   = st.slider("🦺 Safety — Bobot 30%",   0, 100, 75, 5,
                                  help="APD, kepatuhan K3, kesadaran keselamatan")
            prosedur = st.slider("📋 Prosedur — Bobot 30%", 0, 100, 75, 5,
                                  help="Ketepatan urutan kerja, sesuai SOP")
            hasil    = st.slider("🏆 Hasil Kerja — Bobot 40%", 0, 100, 75, 5,
                                  help="Kualitas dan kerapian hasil akhir pekerjaan")

        # Live preview
        preview = hitung_nilai_praktik(safety, prosedur, hasil)
        p_color = "#276749" if preview >= 80 else ("#7B341E" if preview >= 70 else "#822727")
        p_bg    = "#C6F6D5" if preview >= 80 else ("#FEEBC8" if preview >= 70 else "#FED7D7")
        st.markdown(f"""
        <div style="background:{p_bg};border-radius:10px;padding:1rem 1.5rem;margin:0.5rem 0;">
            <b style="color:{p_color};font-size:1.1rem;">
                🧮 Preview Nilai Praktik:
                <span style="font-size:1.8rem;">{preview:.1f}</span>
                — {get_predikat(preview)} ({get_grade_letter(preview)})
            </b><br>
            <small style="color:{p_color};">
                = Safety({safety}×30%) + Prosedur({prosedur}×30%) + Hasil({hasil}×40%)
                = {safety*0.3:.1f} + {prosedur*0.3:.1f} + {hasil*0.4:.1f}
            </small>
        </div>
        """, unsafe_allow_html=True)

        catatan = st.text_area("📝 Catatan / Observasi", placeholder="Catatan tambahan tentang performa siswa...")
        foto    = st.file_uploader("📷 Foto Bukti Praktik (opsional)", type=["jpg","jpeg","png"])

        save = st.form_submit_button("💾 Simpan Nilai Praktik", type="primary", width="stretch")
        if save:
            foto_path = ""
            if foto:
                os.makedirs(UPLOAD_DIR, exist_ok=True)
                fname = f"praktik_{siswa_map[siswa_label]}_{modul.replace(' ','_')}_{tanggal}_{foto.name}"
                fpath = os.path.join(UPLOAD_DIR, fname)
                with open(fpath, "wb") as f:
                    f.write(foto.getbuffer())
                foto_path = fpath

            nid = save_nilai_praktik(
                siswa_id=siswa_map[siswa_label],
                modul_praktik=modul,
                safety=float(safety), prosedur=float(prosedur), hasil=float(hasil),
                assessed_by=st.session_state.user_id,
                foto_praktik=foto_path or None,
                catatan=catatan or "",
            )
            if nid:
                show_success(f"Nilai praktik **{preview:.1f}** ({get_predikat(preview)}) berhasil disimpan!")
                st.rerun()
            else:
                show_error("Gagal menyimpan nilai. Coba lagi.")

def _rekap_nilai():
    import pandas as pd
    semua = get_all_nilai_praktik()
    siswa_list = get_all_siswa()

    # Filter
    c1, c2 = st.columns(2)
    with c1:
        sis_opts = ["Semua Siswa"] + [s["nama_lengkap"] for s in siswa_list]
        sel_sis  = st.selectbox("Filter Siswa", sis_opts, key="fp_siswa")
    with c2:
        mod_opts = ["Semua Modul"] + MODUL_PRAKTIK_OPTIONS
        sel_mod  = st.selectbox("Filter Modul", mod_opts, key="fp_modul")

    data = semua
    if sel_sis != "Semua Siswa":
        data = [d for d in data if d.get("siswa_name") == sel_sis]
    if sel_mod != "Semua Modul":
        data = [d for d in data if d.get("modul_praktik") == sel_mod]

    if not data:
        st.info("Belum ada data penilaian praktik.")
        return

    # Metrics
    vals = [d["nilai_praktik"] for d in data]
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("Total Penilaian", len(data))
    with c2: st.metric("Rata-rata", f"{sum(vals)/len(vals):.1f}")
    with c3: st.metric("Tertinggi", f"{max(vals):.1f}")
    with c4: st.metric("Terendah",  f"{min(vals):.1f}")

    st.divider()

    # Cards
    for d in data:
        v = d["nilai_praktik"]
        border = "#38A169" if v >= 80 else ("#D69E2E" if v >= 70 else "#E53E3E")
        with st.container():
            st.markdown(f"""
            <div style="background:white;border-radius:10px;padding:1rem 1.2rem;
                        margin-bottom:0.7rem;border-left:4px solid {border};
                        box-shadow:0 1px 6px rgba(0,0,0,0.07);">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                    <div>
                        <b style="color:#1A365D;">{d.get('siswa_name','?')}</b>
                        <span style="color:#718096;font-size:0.8rem;margin-left:8px;">🔧 {d.get('modul_praktik','?')}</span><br>
                        <span style="font-size:0.8rem;color:#A0AEC0;">
                            🦺 Safety: <b>{d['safety']:.0f}</b> &nbsp;|&nbsp;
                            📋 Prosedur: <b>{d['prosedur']:.0f}</b> &nbsp;|&nbsp;
                            🏆 Hasil: <b>{d['hasil']:.0f}</b>
                        </span><br>
                        <span style="font-size:0.75rem;color:#A0AEC0;">
                            👨‍🏫 {d.get('assessor_name','?')} &nbsp;|&nbsp;
                            📅 {format_tanggal_short(d.get('tanggal',''))}
                        </span>
                        {f"<br><i style='font-size:0.75rem;color:#718096;'>📝 {d['catatan']}</i>" if d.get('catatan') else ''}
                    </div>
                    <div style="text-align:center;min-width:80px;">
                        <div style="font-size:1.8rem;font-weight:700;color:{border};">{v:.1f}</div>
                        <div style="font-size:0.75rem;color:{border};">{get_predikat(v)}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Foto & hapus
            col_f, col_d, _ = st.columns([1,1,5])
            with col_f:
                if d.get("foto_praktik") and os.path.exists(d["foto_praktik"]):
                    with st.expander("📷"):
                        try: st.image(d["foto_praktik"], width=300)
                        except: st.error("Foto tidak dapat ditampilkan.")
            with col_d:
                if st.button("🗑️", key=f"del_np_{d['id']}", help="Hapus penilaian ini"):
                    delete_nilai_praktik(d["id"])
                    show_success("Penilaian dihapus.")
                    st.rerun()

    # Export
    df = pd.DataFrame(data)
    if "id" in df.columns: df = df.drop(columns=["id"])
    st.download_button("📥 Export CSV", df.to_csv(index=False).encode("utf-8-sig"),
                       "nilai_praktik.csv", "text/csv")

def _grafik():
    from utils import bar_chart_nilai
    import pandas as pd, matplotlib.pyplot as plt, matplotlib
    matplotlib.use("Agg")

    data = get_all_nilai_praktik()
    if not data:
        st.info("Belum ada data penilaian.")
        return

    # Rata per siswa
    from database import get_all_siswa
    siswa = {s["id"]: s["nama_lengkap"].split()[0] for s in get_all_siswa()}
    per_siswa = {}
    for d in data:
        sid  = d["siswa_id"]
        name = siswa.get(sid, f"ID{sid}")
        per_siswa.setdefault(name, []).append(d["nilai_praktik"])
    avg_siswa = {n: sum(v)/len(v) for n, v in per_siswa.items()}
    bar_chart_nilai(avg_siswa, "Rata-rata Nilai Praktik per Siswa")

    # Grouped bar: komponen
    st.markdown("#### 📊 Rata-rata Komponen per Siswa")
    comp_data = {}
    for d in data:
        sid  = d["siswa_id"]
        name = siswa.get(sid, f"ID{sid}")
        comp_data.setdefault(name, {"safety":[],"prosedur":[],"hasil":[]})
        comp_data[name]["safety"].append(d["safety"])
        comp_data[name]["prosedur"].append(d["prosedur"])
        comp_data[name]["hasil"].append(d["hasil"])

    if comp_data:
        names    = list(comp_data.keys())
        avg_saf  = [sum(comp_data[n]["safety"])/len(comp_data[n]["safety"]) for n in names]
        avg_pro  = [sum(comp_data[n]["prosedur"])/len(comp_data[n]["prosedur"]) for n in names]
        avg_has  = [sum(comp_data[n]["hasil"])/len(comp_data[n]["hasil"]) for n in names]
        x = range(len(names))
        w = 0.28
        fig, ax = plt.subplots(figsize=(max(8,len(names)*1.5), 4))
        ax.bar([i-w for i in x], avg_saf, w, label="🦺 Safety (30%)",   color="#3182CE", alpha=0.85)
        ax.bar(x,                avg_pro, w, label="📋 Prosedur (30%)", color="#38A169", alpha=0.85)
        ax.bar([i+w for i in x], avg_has, w, label="🏆 Hasil (40%)",    color="#FF6B35", alpha=0.85)
        ax.set_xticks(list(x)); ax.set_xticklabels(names, rotation=30, ha="right")
        ax.set_ylim(0,110); ax.legend(fontsize=9)
        ax.axhline(75, color="#E53E3E", linestyle="--", linewidth=1.2, alpha=0.7)
        ax.set_title("Komponen Penilaian Praktik per Siswa", fontweight="bold", color="#1A365D")
        ax.spines[["top","right"]].set_visible(False)
        ax.set_facecolor("#FAFAFA"); fig.patch.set_facecolor("white")
        plt.tight_layout(); st.pyplot(fig); plt.close()

# ─── SISWA ────────────────────────────────────────────────────────────────────

def _siswa_view():
    page_header("Nilai Praktik Saya","Lihat hasil penilaian praktik lapangan","🔧")
    sid  = st.session_state.user_id
    data = get_nilai_praktik_by_siswa(sid)

    if not data:
        st.info("📋 Belum ada penilaian praktik. Hubungi guru untuk dijadwalkan.")
        return

    avg = get_rata_nilai_praktik(sid)
    c1,c2,c3 = st.columns(3)
    with c1: st.metric("Rata-rata Nilai Praktik", f"{avg:.1f}")
    with c2: st.metric("Total Penilaian", len(data))
    with c3: st.metric("Grade", get_grade_letter(avg))

    st.divider()

    for d in data:
        v = d["nilai_praktik"]
        border = "#38A169" if v >= 80 else ("#D69E2E" if v >= 70 else "#E53E3E")
        with st.expander(f"🔧 {d['modul_praktik']} — Nilai: {v:.1f} ({get_predikat(v)})"):
            c1,c2,c3 = st.columns(3)
            with c1: st.metric("🦺 Safety (30%)",    f"{d['safety']:.0f}")
            with c2: st.metric("📋 Prosedur (30%)",  f"{d['prosedur']:.0f}")
            with c3: st.metric("🏆 Hasil (40%)",     f"{d['hasil']:.0f}")
            st.markdown(f"**Nilai Praktik:** {v:.1f} | **Penilai:** {d.get('assessor_name','?')} | **Tanggal:** {format_tanggal_short(d.get('tanggal',''))}")
            if d.get("catatan"):
                st.info(f"📝 Catatan guru: {d['catatan']}")
