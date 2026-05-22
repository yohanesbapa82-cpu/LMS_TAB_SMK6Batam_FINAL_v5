"""nilai.py — Nilai Akhir: Teori 30% + Praktik 70%"""
import streamlit as st
import pandas as pd
from database import (
    get_all_siswa, get_nilai_akhir,
    get_rata_nilai_teori, get_rata_nilai_praktik,
    get_nilai_teori_by_siswa, get_nilai_praktik_by_siswa,
)
from utils import (
    page_header, bar_chart_nilai, get_predikat, get_grade_letter,
    format_tanggal_short, score_badge
)

def render_nilai_page():
    if st.session_state.role == "guru":
        _guru_view()
    else:
        _siswa_view()

# ─── GURU ─────────────────────────────────────────────────────────────────────

def _guru_view():
    page_header("Nilai Akhir Siswa",
                "Rekap nilai gabungan Teori (30%) + Praktik (70%) — KKM: 75",
                "📊")
    tabs = st.tabs(["📊 Rekap Nilai", "📈 Perbandingan", "🏆 Ranking", "📥 Export"])
    with tabs[0]: _rekap_nilai()
    with tabs[1]: _perbandingan()
    with tabs[2]: _ranking()
    with tabs[3]: _export()

def _get_df_nilai():
    siswa = get_all_siswa()
    rows  = []
    for s in siswa:
        rt = get_rata_nilai_teori(s["id"])
        rp = get_rata_nilai_praktik(s["id"])
        na = get_nilai_akhir(s["id"])
        rows.append({
            "id": s["id"],
            "Nama": s["nama_lengkap"],
            "Kelas": s.get("kelas",""),
            "Nilai Teori": round(rt,1),
            "Nilai Praktik": round(rp,1),
            "Nilai Akhir": round(na,1),
            "Grade": get_grade_letter(na),
            "Predikat": get_predikat(na),
            "Status": "✅ Lulus" if na >= 75 else ("⚠️ Remedial" if na > 0 else "⏳ Belum"),
        })
    return pd.DataFrame(rows).sort_values("Nilai Akhir", ascending=False)

def _rekap_nilai():
    df = _get_df_nilai()
    if df.empty:
        st.info("Belum ada data siswa.")
        return

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.metric("Total Siswa", len(df))
    with c2: st.metric("Rata-rata Teori",   f"{df['Nilai Teori'].mean():.1f}")
    with c3: st.metric("Rata-rata Praktik", f"{df['Nilai Praktik'].mean():.1f}")
    with c4: st.metric("Rata-rata Akhir",   f"{df['Nilai Akhir'].mean():.1f}")
    with c5: st.metric("Lulus (≥75)",       len(df[df["Nilai Akhir"]>=75]))

    st.divider()

    # Filter kelas
    kelas_list = sorted(df["Kelas"].unique().tolist())
    if kelas_list:
        sel_kelas = st.selectbox("Filter Kelas", ["Semua Kelas"] + kelas_list)
        if sel_kelas != "Semua Kelas":
            df = df[df["Kelas"]==sel_kelas]

    st.dataframe(df.drop(columns=["id"]).reset_index(drop=True),
                 width="stretch", hide_index=True)

def _perbandingan():
    df = _get_df_nilai()
    if df.empty:
        st.info("Belum ada data.")
        return
    import matplotlib.pyplot as plt, matplotlib
    matplotlib.use("Agg")

    labels = df["Nama"].apply(lambda x: x.split()[0])

    fig, axes = plt.subplots(1,2, figsize=(14,5))

    # Chart 1: Nilai akhir
    colors = ["#2ecc71" if v>=75 else ("#f39c12" if v>=60 else "#e74c3c") for v in df["Nilai Akhir"]]
    bars   = axes[0].bar(labels, df["Nilai Akhir"], color=colors, edgecolor="white", linewidth=1.5)
    axes[0].axhline(75, color="#E53E3E", linestyle="--", linewidth=1.5, label="KKM 75")
    axes[0].set_ylim(0,110); axes[0].legend(fontsize=9)
    axes[0].set_title("Nilai Akhir per Siswa", fontweight="bold", color="#1A365D")
    axes[0].set_ylabel("Nilai"); axes[0].spines[["top","right"]].set_visible(False)
    for bar,v in zip(bars,df["Nilai Akhir"]):
        if v>0: axes[0].text(bar.get_x()+bar.get_width()/2, v+1, f"{v:.1f}",
                              ha="center", va="bottom", fontsize=8, fontweight="bold")
    plt.setp(axes[0].get_xticklabels(), rotation=30, ha="right", fontsize=9)

    # Chart 2: Grouped Teori vs Praktik
    x,w = range(len(df)), 0.35
    axes[1].bar([i-w/2 for i in x], df["Nilai Teori"],   w, label="Teori (30%)",   color="#3182CE", alpha=0.85)
    axes[1].bar([i+w/2 for i in x], df["Nilai Praktik"], w, label="Praktik (70%)", color="#38A169", alpha=0.85)
    axes[1].axhline(75, color="#E53E3E", linestyle="--", linewidth=1.2, alpha=0.7)
    axes[1].set_xticks(list(x)); axes[1].set_xticklabels(labels, rotation=30, ha="right", fontsize=9)
    axes[1].set_ylim(0,110); axes[1].legend(fontsize=9)
    axes[1].set_title("Perbandingan Teori vs Praktik", fontweight="bold", color="#1A365D")
    axes[1].spines[["top","right"]].set_visible(False)

    for ax in axes:
        ax.set_facecolor("#FAFAFA"); fig.patch.set_facecolor("white")
    plt.tight_layout(); st.pyplot(fig); plt.close()

def _ranking():
    df = _get_df_nilai()
    if df.empty:
        st.info("Belum ada data.")
        return
    st.markdown("### 🏆 Leaderboard Nilai Akhir")
    for i, (_, row) in enumerate(df.iterrows(), 1):
        medal = "🥇" if i==1 else ("🥈" if i==2 else ("🥉" if i==3 else f"**#{i}**"))
        na    = row["Nilai Akhir"]
        bg    = "#FFFBEB" if i<=3 else "white"
        st.markdown(f"""
        <div style="background:{bg};border-radius:10px;padding:0.7rem 1.2rem;
                    margin-bottom:0.5rem;box-shadow:0 1px 4px rgba(0,0,0,0.07);
                    display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:1.2rem;">{medal}</span>
            <span style="flex:1;margin:0 1rem;">
                <b style="color:#1A365D;">{row['Nama']}</b>
                <span style="color:#718096;font-size:0.8rem;"> — {row['Kelas']}</span>
            </span>
            <span>
                <b style="color:#718096;font-size:0.8rem;">Teori: {row['Nilai Teori']} | Praktik: {row['Nilai Praktik']}</b>
            </span>
            <span style="margin-left:1rem;">
                {score_badge(na)}
            </span>
            <span style="margin-left:0.5rem;font-weight:700;color:#1A365D;min-width:24px;text-align:center;">
                {row['Grade']}
            </span>
        </div>
        """, unsafe_allow_html=True)

def _export():
    df = _get_df_nilai().drop(columns=["id"])
    st.subheader("📥 Export Data Nilai")

    c1,c2 = st.columns(2)
    with c1:
        st.download_button("📄 Download CSV",
            df.to_csv(index=False).encode("utf-8-sig"),
            "nilai_akhir.csv","text/csv", width="stretch")
    with c2:
        try:
            import openpyxl, io
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                df.to_excel(w, index=False, sheet_name="Nilai Akhir")
            st.download_button("📊 Download Excel", buf.getvalue(),
                "nilai_akhir.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch")
        except ImportError:
            st.info("Install openpyxl untuk export Excel.")

    st.divider()
    st.subheader("👁️ Preview Data")
    st.dataframe(df, width="stretch", hide_index=True)

# ─── SISWA ────────────────────────────────────────────────────────────────────

def _siswa_view():
    page_header(f"Nilai Akhir — {st.session_state.nama_lengkap}",
                "Ringkasan nilai teori dan praktik Anda","📊")
    sid = st.session_state.user_id
    rt  = get_rata_nilai_teori(sid)
    rp  = get_rata_nilai_praktik(sid)
    na  = get_nilai_akhir(sid)

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("📝 Nilai Teori",   f"{rt:.1f}", f"bobot 30%")
    with c2: st.metric("🔧 Nilai Praktik", f"{rp:.1f}", f"bobot 70%")
    with c3: st.metric("🎯 Nilai Akhir",   f"{na:.1f}", get_predikat(na))
    with c4: st.metric("🏅 Grade",         get_grade_letter(na))

    st.divider()

    # Tabel komponen
    st.markdown(f"""
    <div style="background:white;border-radius:12px;padding:1.5rem;
                box-shadow:0 2px 8px rgba(0,0,0,0.08);max-width:500px;">
        <h4 style="color:#1A365D;margin-top:0;">🧮 Perhitungan Nilai Akhir</h4>
        <table style="width:100%;border-collapse:collapse;font-size:0.9rem;">
            <tr style="background:#F7FAFC;">
                <th style="padding:8px;text-align:left;color:#4A5568;">Komponen</th>
                <th style="padding:8px;text-align:center;color:#4A5568;">Nilai</th>
                <th style="padding:8px;text-align:center;color:#4A5568;">Bobot</th>
                <th style="padding:8px;text-align:right;color:#4A5568;">Kontribusi</th>
            </tr>
            <tr style="border-top:1px solid #E2E8F0;">
                <td style="padding:8px;">📝 Teori</td>
                <td style="padding:8px;text-align:center;font-weight:600;color:#3182CE;">{rt:.1f}</td>
                <td style="padding:8px;text-align:center;">30%</td>
                <td style="padding:8px;text-align:right;font-weight:600;">{rt*0.3:.1f}</td>
            </tr>
            <tr style="border-top:1px solid #E2E8F0;">
                <td style="padding:8px;">🔧 Praktik</td>
                <td style="padding:8px;text-align:center;font-weight:600;color:#38A169;">{rp:.1f}</td>
                <td style="padding:8px;text-align:center;">70%</td>
                <td style="padding:8px;text-align:right;font-weight:600;">{rp*0.7:.1f}</td>
            </tr>
            <tr style="border-top:2px solid #E2E8F0;background:#FFF5F0;">
                <td style="padding:10px;font-weight:700;color:#1A365D;">NILAI AKHIR</td>
                <td colspan="2"></td>
                <td style="padding:10px;text-align:right;font-size:1.4rem;font-weight:800;color:#FF6B35;">{na:.1f}</td>
            </tr>
        </table>
        <div style="margin-top:1rem;padding:0.6rem;text-align:center;
                    background:{'#C6F6D5' if na>=75 else '#FED7D7'};border-radius:8px;">
            <b style="color:{'#276749' if na>=75 else '#822727'};">
                {'✅ LULUS — Nilai memenuhi KKM (75)' if na>=75 else '❌ BELUM LULUS — KKM: 75'}
            </b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Detail
    tab1, tab2 = st.tabs(["📝 Riwayat Ujian Teori","🔧 Riwayat Praktik"])
    with tab1:
        from database import get_ujian_sudah_selesai_siswa
        riwayat_jadwal = get_ujian_sudah_selesai_siswa(sid)
        if not riwayat_jadwal:
            st.info("Belum ada riwayat ujian. Kerjakan ujian terjadwal di menu **Ujian**.")
        else:
            for n in riwayat_jadwal:
                s    = n["skor"]
                icon = "✅" if s>=75 else ("⚠️" if s>=60 else "❌")
                st.markdown(
                    f'''<div style="background:white;border-radius:8px;padding:10px 14px;
                    margin-bottom:6px;display:flex;justify-content:space-between;
                    box-shadow:0 1px 4px rgba(0,0,0,0.06);">
                    <span>📚 {n.get("judul_ujian","?")[:50]}</span>
                    <span>{icon} <b style="color:#FF6B35;">{s:.1f}</b>
                    &nbsp;<small style="color:#A0AEC0;">{format_tanggal_short(n.get("selesai_at",""))}</small>
                    </span></div>''', unsafe_allow_html=True)

    with tab2:
        np_list = get_nilai_praktik_by_siswa(sid)
        if not np_list:
            st.info("Belum ada nilai praktik. Hubungi guru.")
        else:
            for n in np_list:
                v = n["nilai_praktik"]
                icon = "✅" if v>=75 else ("⚠️" if v>=60 else "❌")
                st.markdown(f"""
                <div style="background:white;border-radius:8px;padding:10px 14px;margin-bottom:6px;
                            display:flex;justify-content:space-between;
                            box-shadow:0 1px 4px rgba(0,0,0,0.06);">
                    <span>🔧 {n['modul_praktik'][:50]}</span>
                    <span>{icon} <b style="color:#FF6B35;">{v:.1f}</b>
                          &nbsp;<small style="color:#A0AEC0;">{format_tanggal_short(n.get('tanggal',''))}</small>
                    </span>
                </div>
                """, unsafe_allow_html=True)
