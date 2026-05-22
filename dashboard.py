"""dashboard.py — Dashboard bento-grid interaktif V5"""
import streamlit as st
import pandas as pd
from database import (
    get_total_siswa, get_total_materi, get_total_soal,
    get_total_ujian, get_total_praktik,
    get_all_siswa, get_nilai_akhir, get_rata_nilai_teori,
    get_rata_nilai_praktik, get_siswa_ranking,
    get_aktivitas_terbaru, get_all_nilai_teori, get_all_nilai_praktik,
)
from utils import (
    page_header, bar_chart_nilai, get_predikat, get_grade_letter,
    format_tanggal, score_badge, format_tanggal_short
)

# ─── Warna konsisten TAB ──────────────────────────────────────────────────────
C_ORANGE = "#FF6B00"
C_NAVY   = "#1C2B4A"
C_LIGHT  = "#F2F4F7"
C_WHITE  = "#FFFFFF"

def _card(bg, content, min_h=120, radius=14, border="none"):
    st.markdown(f"""
    <div style="background:{bg};border-radius:{radius}px;padding:1.2rem 1.4rem;
                min-height:{min_h}px;border:{border};
                box-shadow:0 2px 10px rgba(0,0,0,0.07);
                transition:box-shadow .2s,transform .2s;margin-bottom:0;">
        {content}
    </div>
    """, unsafe_allow_html=True)

def _kpi_card(icon, value, label, bg=C_WHITE, val_color=C_ORANGE):
    return f"""
    <div style="background:{bg};border-radius:14px;padding:1.2rem 1.4rem;
                box-shadow:0 2px 10px rgba(0,0,0,0.07);
                border-left:4px solid {C_ORANGE};
                transition:all .2s;">
        <div style="font-size:1.6rem;line-height:1;">{icon}</div>
        <div style="font-size:2rem;font-weight:700;color:{val_color};line-height:1.1;margin:4px 0;">
            {value}
        </div>
        <div style="font-size:0.72rem;color:#6B7280;font-weight:600;
                    text-transform:uppercase;letter-spacing:0.5px;">{label}</div>
    </div>
    """

def _nav_tile(icon, title, nav_label, bg, min_h=110):
    return f"""
    <div style="background:{bg};border-radius:14px;padding:1.2rem 1.4rem;
                min-height:{min_h}px;cursor:pointer;
                box-shadow:0 2px 10px rgba(0,0,0,0.1);
                transition:transform .2s,box-shadow .2s;position:relative;">
        <div style="position:absolute;top:12px;right:12px;
                    background:rgba(255,255,255,0.2);
                    border:1.5px solid rgba(255,255,255,0.4);
                    border-radius:50%;width:26px;height:26px;
                    display:flex;align-items:center;justify-content:center;
                    font-size:0.85rem;color:white;">＋</div>
        <div style="font-size:2rem;line-height:1;">{icon}</div>
        <div style="margin-top:10px;font-size:1rem;font-weight:700;
                    color:white;line-height:1.3;">{title}</div>
    </div>
    """

def render_dashboard():
    if st.session_state.role == "guru":
        _guru_dashboard()
    else:
        _siswa_dashboard()

# ═══════════════════════════════════════════════════════════════
# GURU DASHBOARD
# ═══════════════════════════════════════════════════════════════

def _guru_dashboard():
    nama = st.session_state.nama_lengkap or "Guru"
    hari = _salam()

    # ── HEADER ──────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1C2B4A 0%,#243960 100%);
                border-radius:18px;padding:1.6rem 2rem;margin-bottom:1.5rem;
                position:relative;overflow:hidden;
                box-shadow:0 6px 24px rgba(28,43,74,0.2);">
        <div style="position:absolute;right:-20px;top:-20px;
                    width:140px;height:140px;border-radius:50%;
                    background:rgba(255,107,0,0.12);"></div>
        <div style="position:absolute;right:30px;top:30px;
                    width:80px;height:80px;border-radius:50%;
                    background:rgba(255,107,0,0.08);"></div>
        <div style="font-size:0.8rem;color:#8CA0B8;margin-bottom:4px;
                    letter-spacing:0.5px;">{hari} 👋</div>
        <div style="font-size:1.7rem;font-weight:700;color:white;line-height:1.2;">
            {nama}
        </div>
        <div style="font-size:0.87rem;color:#B8C8E0;margin-top:4px;">
            Dashboard Guru — SMK Negeri 6 Batam · Program TAB
        </div>
        <div style="margin-top:14px;display:flex;gap:10px;flex-wrap:wrap;">
            <span style="background:rgba(255,107,0,0.18);color:#FFB070;
                         padding:4px 14px;border-radius:20px;font-size:0.78rem;
                         font-weight:600;border:1px solid rgba(255,107,0,0.3);">
                ⚙️ Teknik Alat Berat
            </span>
            <span style="background:rgba(255,255,255,0.08);color:#8CA0B8;
                         padding:4px 14px;border-radius:20px;font-size:0.78rem;
                         border:1px solid rgba(255,255,255,0.1);">
                📅 {_tanggal_sekarang()}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI ROW ─────────────────────────────────────────────────
    k1,k2,k3,k4,k5 = st.columns(5)
    kpi_data = [
        (k1,"👷",get_total_siswa(),"Total Siswa"),
        (k2,"📚",get_total_materi(),"Materi"),
        (k3,"❓",get_total_soal(),"Bank Soal"),
        (k4,"📝",get_total_ujian(),"Ujian Selesai"),
        (k5,"🔧",get_total_praktik(),"Nilai Praktik"),
    ]
    for col,icon,val,lbl in kpi_data:
        with col:
            st.markdown(_kpi_card(icon,val,lbl), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── BENTO GRID ROW 1 ────────────────────────────────────────
    col_a, col_b, col_c = st.columns([2.2, 2.2, 1.6])

    # Tile 1 — Ranking siswa (tabel)
    with col_a:
        ranking = get_siswa_ranking()
        rows_html = ""
        for i, r in enumerate(ranking[:8], 1):
            na    = r["nilai_akhir"]
            medal = "🥇" if i==1 else ("🥈" if i==2 else ("🥉" if i==3 else f"<b style='color:#9CA3AF'>#{i}</b>"))
            bar_w = int(na) if na else 0
            bar_c = "#059669" if na>=80 else ("#D97706" if na>=70 else ("#FF6B00" if na>=60 else "#DC2626"))
            rows_html += f"""
            <tr style="border-bottom:1px solid #F3F4F6;">
                <td style="padding:7px 8px;font-size:1rem;">{medal}</td>
                <td style="padding:7px 4px;">
                    <div style="font-size:0.83rem;font-weight:600;color:#111827;
                                white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
                                max-width:160px;">{r['nama']}</div>
                    <div style="font-size:0.7rem;color:#9CA3AF;">{r.get('kelas','')}</div>
                </td>
                <td style="padding:7px 8px;">
                    <div style="background:#F3F4F6;border-radius:99px;height:6px;min-width:60px;">
                        <div style="background:{bar_c};height:6px;border-radius:99px;width:{bar_w}%;"></div>
                    </div>
                </td>
                <td style="padding:7px 8px;text-align:right;">
                    <span style="background:{'#D1FAE5' if na>=80 else ('#FEF3C7' if na>=70 else ('#FEE2E2' if na>0 else '#F3F4F6'))};
                                 color:{'#065F46' if na>=80 else ('#92400E' if na>=70 else ('#991B1B' if na>0 else '#9CA3AF'))};
                                 padding:2px 9px;border-radius:20px;font-size:0.78rem;font-weight:700;">
                        {f'{na:.1f}' if na>0 else '—'}
                    </span>
                </td>
            </tr>
            """
        st.markdown(f"""
        <div style="background:white;border-radius:14px;padding:1.2rem 1.4rem;
                    box-shadow:0 2px 10px rgba(0,0,0,0.07);height:100%;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                <div style="font-size:0.87rem;font-weight:700;color:#1C2B4A;">🏆 Ranking Nilai Akhir</div>
                <span style="background:#FFF3E8;color:#FF6B00;padding:2px 10px;border-radius:20px;
                             font-size:0.72rem;font-weight:600;">{len(ranking)} siswa</span>
            </div>
            <table style="width:100%;border-collapse:collapse;">
                <thead><tr style="background:#F9FAFB;">
                    <th style="padding:6px 8px;font-size:0.7rem;color:#6B7280;font-weight:600;text-align:left;">#</th>
                    <th style="padding:6px 4px;font-size:0.7rem;color:#6B7280;font-weight:600;text-align:left;">NAMA</th>
                    <th style="padding:6px 8px;font-size:0.7rem;color:#6B7280;font-weight:600;text-align:left;">PROGRES</th>
                    <th style="padding:6px 8px;font-size:0.7rem;color:#6B7280;font-weight:600;text-align:right;">NILAI</th>
                </tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)

    # Tile 2 — Aktivitas terbaru
    with col_b:
        aktivitas = get_aktivitas_terbaru(8)
        akt_html  = ""
        for a in aktivitas:
            is_ujian = a["tipe"] == "Ujian"
            icon_a   = "📝" if is_ujian else "🔧"
            color_a  = "#1C6CB5" if is_ujian else "#059669"
            bg_a     = "#EFF6FF" if is_ujian else "#ECFDF5"
            nilai_a  = a["nilai"] or 0
            akt_html += f"""
            <div style="display:flex;align-items:center;gap:10px;
                        padding:8px 0;border-bottom:1px solid #F3F4F6;">
                <div style="background:{bg_a};border-radius:8px;padding:6px;
                            font-size:1.1rem;flex-shrink:0;">{icon_a}</div>
                <div style="flex:1;min-width:0;">
                    <div style="font-size:0.82rem;font-weight:600;color:#111827;
                                white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                        {a['nama_lengkap']}</div>
                    <div style="font-size:0.72rem;color:#9CA3AF;
                                white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
                        {a['keterangan'][:38]}</div>
                </div>
                <div style="text-align:right;flex-shrink:0;">
                    <div style="font-size:0.9rem;font-weight:700;color:{color_a};">
                        {nilai_a:.1f}</div>
                    <div style="font-size:0.68rem;color:#9CA3AF;">
                        {format_tanggal_short(a.get('tanggal',''))}</div>
                </div>
            </div>
            """
        if not aktivitas:
            akt_html = '<div style="color:#9CA3AF;text-align:center;padding:2rem 0;font-size:0.85rem;">Belum ada aktivitas</div>'

        st.markdown(f"""
        <div style="background:white;border-radius:14px;padding:1.2rem 1.4rem;
                    box-shadow:0 2px 10px rgba(0,0,0,0.07);height:100%;">
            <div style="font-size:0.87rem;font-weight:700;color:#1C2B4A;margin-bottom:10px;">
                🕐 Aktivitas Terbaru
            </div>
            {akt_html}
        </div>
        """, unsafe_allow_html=True)

    # Tile 3 — Quick stats vertikal
    with col_c:
        siswa_list = get_all_siswa()
        lulus_cnt  = sum(1 for s in siswa_list if get_nilai_akhir(s["id"]) >= 75)
        belum_cnt  = sum(1 for s in siswa_list if get_nilai_akhir(s["id"]) == 0)
        pct_lulus  = int(lulus_cnt/len(siswa_list)*100) if siswa_list else 0

        st.markdown(f"""
        <div style="background:{C_NAVY};border-radius:14px;padding:1.2rem 1.4rem;
                    box-shadow:0 4px 16px rgba(28,43,74,0.18);height:100%;
                    display:flex;flex-direction:column;gap:14px;">
            <div style="font-size:0.8rem;font-weight:700;color:#8CA0B8;
                        letter-spacing:0.5px;text-transform:uppercase;">📊 Ringkasan Kelas</div>

            <div style="background:rgba(255,255,255,0.07);border-radius:10px;padding:0.9rem;">
                <div style="font-size:0.72rem;color:#8CA0B8;margin-bottom:2px;">Lulus KKM (≥75)</div>
                <div style="font-size:1.8rem;font-weight:700;color:#4ADE80;">{lulus_cnt}
                    <span style="font-size:0.9rem;color:#6EE7B7;"> siswa</span></div>
                <div style="background:rgba(255,255,255,0.1);border-radius:99px;height:5px;margin-top:6px;">
                    <div style="background:#4ADE80;height:5px;border-radius:99px;width:{pct_lulus}%;"></div>
                </div>
                <div style="font-size:0.7rem;color:#6EE7B7;margin-top:3px;">{pct_lulus}% dari total</div>
            </div>

            <div style="background:rgba(255,255,255,0.07);border-radius:10px;padding:0.9rem;">
                <div style="font-size:0.72rem;color:#8CA0B8;margin-bottom:2px;">Belum Dinilai</div>
                <div style="font-size:1.8rem;font-weight:700;color:#FBB040;">{belum_cnt}
                    <span style="font-size:0.9rem;color:#FCD68A;"> siswa</span></div>
            </div>

            <div style="background:rgba(255,107,0,0.15);border:1px solid rgba(255,107,0,0.3);
                        border-radius:10px;padding:0.9rem;">
                <div style="font-size:0.72rem;color:#FFB070;margin-bottom:2px;">Total Siswa Aktif</div>
                <div style="font-size:1.8rem;font-weight:700;color:#FF6B00;">{len(siswa_list)}</div>
                <div style="font-size:0.72rem;color:#FFB070;">Kelas XI TAB</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── BENTO GRID ROW 2 ────────────────────────────────────────
    col_d, col_e, col_f, col_g = st.columns(4)

    nav_tiles = [
        (col_d,"📚","Materi & Jobsheet","Tambah & kelola materi",
         "linear-gradient(135deg,#FF6B00,#E05500)"),
        (col_e,"❓","Bank Soal","Kelola soal ujian",
         "linear-gradient(135deg,#1C6CB5,#134FA0)"),
        (col_f,"🔧","Penilaian Praktik","Input nilai lapangan",
         "linear-gradient(135deg,#059669,#046B4E)"),
        (col_g,"📊","Nilai Akhir","Lihat rekap nilai",
         "linear-gradient(135deg,#7C3AED,#5B21B6)"),
    ]
    for col,icon,title,sub,bg in nav_tiles:
        with col:
            st.markdown(f"""
            <div style="background:{bg};border-radius:14px;padding:1.3rem 1.4rem;
                        min-height:110px;box-shadow:0 4px 14px rgba(0,0,0,0.12);
                        position:relative;overflow:hidden;">
                <div style="position:absolute;right:10px;top:10px;
                            background:rgba(255,255,255,0.15);
                            border:1.5px solid rgba(255,255,255,0.3);
                            border-radius:50%;width:26px;height:26px;
                            display:flex;align-items:center;justify-content:center;
                            font-size:0.9rem;color:white;">＋</div>
                <div style="font-size:1.8rem;">{icon}</div>
                <div style="font-size:0.95rem;font-weight:700;color:white;
                            margin-top:8px;line-height:1.2;">{title}</div>
                <div style="font-size:0.73rem;color:rgba(255,255,255,0.7);margin-top:3px;">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── ROW 3: TABEL LENGKAP + GRAFIK ───────────────────────────
    tab1, tab2 = st.tabs(["📋 Tabel Nilai Semua Siswa", "📊 Grafik Performa"])

    with tab1:
        _tabel_nilai_guru()

    with tab2:
        _grafik_guru()


def _tabel_nilai_guru():
    siswa_list = get_all_siswa()
    if not siswa_list:
        st.info("Belum ada data siswa.")
        return

    rows = []
    for s in siswa_list:
        rt = get_rata_nilai_teori(s["id"])
        rp = get_rata_nilai_praktik(s["id"])
        na = get_nilai_akhir(s["id"])
        rows.append({
            "NIS":         s.get("nis","—"),
            "Nama Siswa":  s["nama_lengkap"],
            "Kelas":       s.get("kelas",""),
            "Nilai Teori": round(rt,1),
            "Nilai Praktik": round(rp,1),
            "Nilai Akhir": round(na,1),
            "Grade":       get_grade_letter(na),
            "Predikat":    get_predikat(na),
            "Status":      "✅ Lulus" if na>=75 else ("⚠️ Remedial" if na>0 else "⏳ Belum"),
        })

    df = pd.DataFrame(rows).sort_values("Nilai Akhir", ascending=False)

    # Metrics ringkasan
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("Total Siswa",    len(df))
    with c2: st.metric("Rata Teori",     f"{df['Nilai Teori'].mean():.1f}" if df['Nilai Teori'].max()>0 else "—")
    with c3: st.metric("Rata Praktik",   f"{df['Nilai Praktik'].mean():.1f}" if df['Nilai Praktik'].max()>0 else "—")
    with c4: st.metric("Rata Nilai Akhir",f"{df['Nilai Akhir'].mean():.1f}" if df['Nilai Akhir'].max()>0 else "—")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Filter
    col_f1, col_f2, _ = st.columns([1,1,2])
    with col_f1:
        filter_status = st.selectbox("Filter Status",
            ["Semua","✅ Lulus","⚠️ Remedial","⏳ Belum"], key="fs_dash")
    with col_f2:
        search = st.text_input("🔍 Cari Nama / NIS", placeholder="Ketik nama atau NIS...", key="search_dash")

    df_show = df.copy()
    if filter_status != "Semua":
        df_show = df_show[df_show["Status"]==filter_status]
    if search:
        df_show = df_show[
            df_show["Nama Siswa"].str.contains(search, case=False, na=False) |
            df_show["NIS"].str.contains(search, case=False, na=False)
        ]

    # Custom HTML tabel
    _render_custom_table(df_show)

    # Export
    col_e1, col_e2, _ = st.columns([1,1,3])
    with col_e1:
        st.download_button("📥 Export CSV",
            df.to_csv(index=False).encode("utf-8-sig"),
            "nilai_siswa.csv","text/csv", use_container_width=True)
    with col_e2:
        try:
            import io, openpyxl
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                df.to_excel(w, index=False, sheet_name="Nilai Siswa")
            st.download_button("📊 Export Excel", buf.getvalue(),
                "nilai_siswa.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True)
        except ImportError:
            pass


def _render_custom_table(df):
    """Tabel HTML custom dengan styling TAB."""
    if df.empty:
        st.info("Tidak ada data yang cocok.")
        return

    status_style = {
        "✅ Lulus":    ("background:#D1FAE5;color:#065F46","✅"),
        "⚠️ Remedial": ("background:#FEF3C7;color:#92400E","⚠️"),
        "⏳ Belum":    ("background:#F3F4F6;color:#6B7280","⏳"),
    }

    rows_html = ""
    for _, row in df.iterrows():
        na     = row["Nilai Akhir"]
        st_css, _ = status_style.get(row["Status"], ("background:#F3F4F6;color:#6B7280",""))
        bar_w  = int(na) if na else 0
        bar_c  = "#059669" if na>=80 else ("#D97706" if na>=70 else ("#FF6B00" if na>=60 else "#DC2626"))
        grade  = row["Grade"]
        g_css  = {
            "A":"background:#D1FAE5;color:#065F46",
            "B":"background:#DBEAFE;color:#1E40AF",
            "C":"background:#FEF3C7;color:#92400E",
            "D":"background:#FEE2E2;color:#991B1B",
            "E":"background:#FEE2E2;color:#991B1B",
            "—":"background:#F3F4F6;color:#9CA3AF",
        }.get(grade,"background:#F3F4F6;color:#9CA3AF")

        rows_html += f"""
        <tr style="border-bottom:1px solid #F3F4F6;transition:background .15s;"
            onmouseover="this.style.background='#FFF9F5'"
            onmouseout="this.style.background='white'">
            <td style="padding:10px 12px;font-size:0.8rem;font-weight:600;
                       color:#6B7280;">{row['NIS']}</td>
            <td style="padding:10px 12px;">
                <div style="font-size:0.87rem;font-weight:600;color:#111827;">{row['Nama Siswa']}</div>
                <div style="font-size:0.72rem;color:#9CA3AF;">{row['Kelas']}</div>
            </td>
            <td style="padding:10px 12px;text-align:center;">
                <span style="font-size:0.87rem;font-weight:600;
                             color:{'#DC2626' if row['Nilai Teori']==0 else '#1C2B4A'};">
                    {row['Nilai Teori'] if row['Nilai Teori']>0 else '—'}
                </span>
            </td>
            <td style="padding:10px 12px;text-align:center;">
                <span style="font-size:0.87rem;font-weight:600;
                             color:{'#DC2626' if row['Nilai Praktik']==0 else '#1C2B4A'};">
                    {row['Nilai Praktik'] if row['Nilai Praktik']>0 else '—'}
                </span>
            </td>
            <td style="padding:10px 16px;min-width:130px;">
                <div style="background:#F3F4F6;border-radius:99px;height:7px;margin-bottom:3px;">
                    <div style="background:{bar_c};height:7px;border-radius:99px;width:{bar_w}%;"></div>
                </div>
                <div style="font-size:0.75rem;font-weight:700;color:{bar_c};">
                    {row['Nilai Akhir'] if row['Nilai Akhir']>0 else '—'}
                </div>
            </td>
            <td style="padding:10px 12px;text-align:center;">
                <span style="padding:3px 10px;border-radius:20px;font-size:0.78rem;
                             font-weight:700;{g_css};">{grade}</span>
            </td>
            <td style="padding:10px 12px;text-align:center;">
                <span style="padding:3px 10px;border-radius:20px;font-size:0.75rem;
                             font-weight:600;{st_css};">{row['Status']}</span>
            </td>
        </tr>
        """

    st.markdown(f"""
    <div style="background:white;border-radius:14px;overflow:hidden;
                box-shadow:0 2px 10px rgba(0,0,0,0.07);margin-bottom:12px;">
        <table style="width:100%;border-collapse:collapse;">
            <thead>
                <tr style="background:linear-gradient(135deg,#1C2B4A,#243960);">
                    <th style="padding:11px 12px;font-size:0.72rem;font-weight:700;
                               color:#8CA0B8;text-align:left;letter-spacing:0.5px;">NIS</th>
                    <th style="padding:11px 12px;font-size:0.72rem;font-weight:700;
                               color:#8CA0B8;text-align:left;letter-spacing:0.5px;">NAMA SISWA</th>
                    <th style="padding:11px 12px;font-size:0.72rem;font-weight:700;
                               color:#8CA0B8;text-align:center;letter-spacing:0.5px;">TEORI</th>
                    <th style="padding:11px 12px;font-size:0.72rem;font-weight:700;
                               color:#8CA0B8;text-align:center;letter-spacing:0.5px;">PRAKTIK</th>
                    <th style="padding:11px 16px;font-size:0.72rem;font-weight:700;
                               color:#8CA0B8;text-align:left;letter-spacing:0.5px;">NILAI AKHIR</th>
                    <th style="padding:11px 12px;font-size:0.72rem;font-weight:700;
                               color:#8CA0B8;text-align:center;letter-spacing:0.5px;">GRADE</th>
                    <th style="padding:11px 12px;font-size:0.72rem;font-weight:700;
                               color:#8CA0B8;text-align:center;letter-spacing:0.5px;">STATUS</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
        <div style="padding:8px 12px;background:#F9FAFB;border-top:1px solid #F3F4F6;
                    font-size:0.75rem;color:#9CA3AF;text-align:right;">
            Menampilkan {len(df)} dari {len(get_all_siswa())} siswa
        </div>
    </div>
    """, unsafe_allow_html=True)


def _grafik_guru():
    siswa_list = get_all_siswa()
    if not siswa_list:
        st.info("Belum ada data.")
        return

    data = []
    for s in siswa_list:
        rt = get_rata_nilai_teori(s["id"])
        rp = get_rata_nilai_praktik(s["id"])
        na = get_nilai_akhir(s["id"])
        data.append({"Nama": s["nama_lengkap"], "Kelas": s.get("kelas",""),
                     "Teori": round(rt,1), "Praktik": round(rp,1), "Nilai Akhir": round(na,1)})
    df = pd.DataFrame(data).sort_values("Nilai Akhir", ascending=False)

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        short = df.head(10)
        bar_chart_nilai(
            dict(zip(short["Nama"].apply(lambda x: x.split()[0]), short["Nilai Akhir"])),
            "Top 10 — Nilai Akhir Siswa"
        )
    with col_g2:
        import matplotlib.pyplot as plt, matplotlib
        matplotlib.use("Agg")
        fig, ax = plt.subplots(figsize=(6,4))
        x,w = range(len(df[:10])),0.38
        ax.bar([i-w/2 for i in x], df["Teori"][:10],   w, label="Teori (30%)",   color="#1C6CB5", alpha=0.88)
        ax.bar([i+w/2 for i in x], df["Praktik"][:10], w, label="Praktik (70%)", color="#FF6B00", alpha=0.88)
        ax.axhline(75, color="#DC2626", linestyle="--", linewidth=1.4, alpha=0.8)
        ax.set_xticks(list(x))
        ax.set_xticklabels([n.split()[0] for n in df["Nama"][:10]], rotation=30, ha="right", fontsize=9)
        ax.set_ylim(0,108); ax.legend(fontsize=9)
        ax.spines[["top","right"]].set_visible(False)
        ax.set_facecolor("#FAFBFC"); fig.patch.set_facecolor("white")
        ax.set_title("Teori vs Praktik", fontweight="bold", color="#1C2B4A", fontsize=12)
        plt.tight_layout(); st.pyplot(fig); plt.close()

    # Distribusi grade
    st.markdown("#### 🎯 Distribusi Grade Kelas")
    grade_cnt = {}
    for s in siswa_list:
        g = get_grade_letter(get_nilai_akhir(s["id"]))
        grade_cnt[g] = grade_cnt.get(g,0) + 1

    gcols = st.columns(6)
    g_info = [
        ("A","#065F46","#D1FAE5","Sangat Baik"),
        ("B","#1E40AF","#DBEAFE","Baik"),
        ("C","#92400E","#FEF3C7","Cukup"),
        ("D","#991B1B","#FEE2E2","Kurang"),
        ("E","#991B1B","#FEE2E2","Sangat Kurang"),
        ("—","#6B7280","#F3F4F6","Belum Dinilai"),
    ]
    for col,(g,tc,bg,lbl) in zip(gcols,g_info):
        cnt = grade_cnt.get(g,0)
        with col:
            st.markdown(f"""
            <div style="background:{bg};border-radius:12px;padding:0.9rem;text-align:center;">
                <div style="font-size:1.4rem;font-weight:700;color:{tc};">{g}</div>
                <div style="font-size:1.6rem;font-weight:700;color:{tc};">{cnt}</div>
                <div style="font-size:0.68rem;color:{tc};opacity:0.8;">{lbl}</div>
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# SISWA DASHBOARD
# ═══════════════════════════════════════════════════════════════

def _siswa_dashboard():
    sid  = st.session_state.user_id
    nama = st.session_state.nama_lengkap or "Siswa"
    rt   = get_rata_nilai_teori(sid)
    rp   = get_rata_nilai_praktik(sid)
    na   = get_nilai_akhir(sid)

    lulus = na >= 75

    # ── HERO ────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1C2B4A 0%,#243960 100%);
                border-radius:18px;padding:1.6rem 2rem;margin-bottom:1.5rem;
                position:relative;overflow:hidden;
                box-shadow:0 6px 24px rgba(28,43,74,0.2);">
        <div style="position:absolute;right:-20px;top:-20px;width:140px;height:140px;
                    border-radius:50%;background:rgba(255,107,0,0.1);"></div>
        <div style="font-size:0.8rem;color:#8CA0B8;margin-bottom:4px;">{_salam()} 👋</div>
        <div style="font-size:1.6rem;font-weight:700;color:white;line-height:1.2;">{nama}</div>
        <div style="font-size:0.85rem;color:#B8C8E0;margin-top:3px;">
            Kelas XI TAB · SMK Negeri 6 Batam
        </div>
        <div style="margin-top:14px;display:flex;gap:10px;flex-wrap:wrap;align-items:center;">
            <div style="background:{'rgba(74,222,128,0.2)' if lulus else 'rgba(251,176,64,0.2)'};
                        border:1px solid {'rgba(74,222,128,0.4)' if lulus else 'rgba(251,176,64,0.4)'};
                        border-radius:20px;padding:5px 16px;">
                <span style="font-size:0.85rem;font-weight:700;
                             color:{'#4ADE80' if lulus else '#FBB040'};">
                    {'✅ LULUS — KKM Terpenuhi' if lulus else ('⏳ Sedang Berlangsung' if na>0 else '📚 Mulai Belajar!')}
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI SISWA ───────────────────────────────────────────────
    c1,c2,c3,c4 = st.columns(4)
    for col, icon, val, lbl, extra_color in [
        (c1,"📝",f"{rt:.1f}" if rt>0 else "—","Nilai Teori","#1C6CB5"),
        (c2,"🔧",f"{rp:.1f}" if rp>0 else "—","Nilai Praktik","#059669"),
        (c3,"🎯",f"{na:.1f}" if na>0 else "—","Nilai Akhir","#FF6B00"),
        (c4,"🏅",get_grade_letter(na),"Grade","#7C3AED"),
    ]:
        with col:
            st.markdown(f"""
            <div style="background:white;border-radius:14px;padding:1.1rem 1.3rem;
                        box-shadow:0 2px 10px rgba(0,0,0,0.07);
                        border-left:4px solid {extra_color};">
                <div style="font-size:1.5rem;">{icon}</div>
                <div style="font-size:2rem;font-weight:700;color:{extra_color};line-height:1.1;margin:3px 0;">
                    {val}</div>
                <div style="font-size:0.72rem;color:#6B7280;font-weight:600;
                            text-transform:uppercase;letter-spacing:0.4px;">{lbl}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── ROW 2 ───────────────────────────────────────────────────
    col_a, col_b = st.columns([1.6, 2.4])

    with col_a:
        st.markdown(f"""
        <div style="background:{C_NAVY};border-radius:14px;padding:1.3rem 1.4rem;
                    box-shadow:0 4px 16px rgba(28,43,74,0.18);">
            <div style="font-size:0.78rem;font-weight:700;color:#8CA0B8;
                        text-transform:uppercase;letter-spacing:0.5px;margin-bottom:14px;">
                🧮 Kalkulasi Nilai
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;
                        padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.07);">
                <span style="color:#8CA0B8;font-size:0.83rem;">📝 Teori × 30%</span>
                <span style="color:#60A5FA;font-weight:700;font-size:0.9rem;">{rt*0.3:.1f}</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;
                        padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.07);">
                <span style="color:#8CA0B8;font-size:0.83rem;">🔧 Praktik × 70%</span>
                <span style="color:#4ADE80;font-weight:700;font-size:0.9rem;">{rp*0.7:.1f}</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;
                        padding:10px 0 0;">
                <span style="color:white;font-weight:700;font-size:0.9rem;">NILAI AKHIR</span>
                <span style="color:#FF6B00;font-weight:800;font-size:1.4rem;">{na:.1f}</span>
            </div>
            <div style="background:{'rgba(74,222,128,0.15)' if lulus else 'rgba(251,176,64,0.15)'};
                        border:1px solid {'rgba(74,222,128,0.3)' if lulus else 'rgba(251,176,64,0.3)'};
                        border-radius:8px;padding:7px;text-align:center;margin-top:12px;">
                <span style="font-weight:700;font-size:0.85rem;
                             color:{'#4ADE80' if lulus else '#FBB040'};">
                    {'✅ LULUS' if lulus else ('⚠️ Kejar KKM 75' if na>0 else '⏳ Belum Ada Data')}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_b:
        # Progress tiap komponen
        st.markdown("""
        <div style="background:white;border-radius:14px;padding:1.3rem 1.4rem;
                    box-shadow:0 2px 10px rgba(0,0,0,0.07);">
            <div style="font-size:0.85rem;font-weight:700;color:#1C2B4A;margin-bottom:14px;">
                📈 Progres Nilai
            </div>
        </div>
        """, unsafe_allow_html=True)

        for lbl, val, color, bobot in [
            ("📝 Nilai Teori",   rt, "#1C6CB5","30%"),
            ("🔧 Nilai Praktik", rp, "#FF6B00","70%"),
            ("🎯 Nilai Akhir",   na, "#7C3AED","—"),
        ]:
            pct = min(val/100,1.0) if val>0 else 0
            st.markdown(f"""
            <div style="background:white;border-radius:10px;padding:0.8rem 1rem;
                        margin-bottom:6px;box-shadow:0 1px 4px rgba(0,0,0,0.06);">
                <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                    <span style="font-size:0.83rem;font-weight:600;color:#374151;">{lbl}</span>
                    <span style="font-size:0.75rem;color:#9CA3AF;">Bobot {bobot} &nbsp;
                        <b style="color:{color};">{val:.1f}</b>/100</span>
                </div>
                <div style="background:#F3F4F6;border-radius:99px;height:8px;">
                    <div style="background:{color};height:8px;border-radius:99px;
                                width:{int(pct*100)}%;transition:width .5s;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── RIWAYAT ─────────────────────────────────────────────────
    tab1, tab2 = st.tabs(["📝 Riwayat Ujian","🔧 Riwayat Praktik"])

    with tab1:
        from database import get_ujian_sudah_selesai_siswa
        riwayat = get_ujian_sudah_selesai_siswa(sid)
        if not riwayat:
            st.info("📝 Belum ada riwayat ujian. Kerjakan ujian di menu **Ujian Online**.")
        else:
            rw_html = ""
            for r in riwayat:
                s = r["skor"]
                bc = "#059669" if s>=80 else ("#D97706" if s>=70 else ("#FF6B00" if s>=60 else "#DC2626"))
                rw_html += f"""
                <tr style="border-bottom:1px solid #F3F4F6;">
                    <td style="padding:9px 12px;font-size:0.87rem;color:#111827;font-weight:500;">
                        {r.get('judul_ujian','?')[:45]}</td>
                    <td style="padding:9px 12px;font-size:0.82rem;color:#6B7280;">
                        {r.get('benar',0)}/{r.get('total_soal',0)} benar</td>
                    <td style="padding:9px 12px;text-align:center;">
                        <span style="background:{'#D1FAE5' if s>=80 else ('#FEF3C7' if s>=70 else '#FEE2E2')};
                                     color:{bc};padding:3px 11px;border-radius:20px;
                                     font-size:0.82rem;font-weight:700;">{s:.1f}</span></td>
                    <td style="padding:9px 12px;font-size:0.75rem;color:#9CA3AF;text-align:right;">
                        {format_tanggal_short(r.get('selesai_at',''))}</td>
                </tr>
                """
            st.markdown(f"""
            <div style="background:white;border-radius:12px;overflow:hidden;
                        box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                <table style="width:100%;border-collapse:collapse;">
                    <thead><tr style="background:#1C2B4A;">
                        <th style="padding:10px 12px;color:#8CA0B8;font-size:0.72rem;text-align:left;">UJIAN</th>
                        <th style="padding:10px 12px;color:#8CA0B8;font-size:0.72rem;text-align:left;">JAWABAN</th>
                        <th style="padding:10px 12px;color:#8CA0B8;font-size:0.72rem;text-align:center;">NILAI</th>
                        <th style="padding:10px 12px;color:#8CA0B8;font-size:0.72rem;text-align:right;">TGL</th>
                    </tr></thead>
                    <tbody>{rw_html}</tbody>
                </table>
            </div>
            """, unsafe_allow_html=True)

    with tab2:
        from database import get_nilai_praktik_by_siswa
        nprak = get_nilai_praktik_by_siswa(sid)
        if not nprak:
            st.info("🔧 Belum ada nilai praktik. Hubungi guru.")
        else:
            pr_html = ""
            for n in nprak:
                v  = n["nilai_praktik"]
                bc = "#059669" if v>=80 else ("#D97706" if v>=70 else ("#FF6B00" if v>=60 else "#DC2626"))
                pr_html += f"""
                <tr style="border-bottom:1px solid #F3F4F6;">
                    <td style="padding:9px 12px;font-size:0.87rem;color:#111827;font-weight:500;">
                        {n['modul_praktik'][:40]}</td>
                    <td style="padding:9px 12px;font-size:0.78rem;color:#6B7280;">
                        🦺{n['safety']:.0f} / 📋{n['prosedur']:.0f} / 🏆{n['hasil']:.0f}</td>
                    <td style="padding:9px 12px;text-align:center;">
                        <span style="background:{'#D1FAE5' if v>=80 else ('#FEF3C7' if v>=70 else '#FEE2E2')};
                                     color:{bc};padding:3px 11px;border-radius:20px;
                                     font-size:0.82rem;font-weight:700;">{v:.1f}</span></td>
                    <td style="padding:9px 12px;font-size:0.75rem;color:#9CA3AF;text-align:right;">
                        {format_tanggal_short(n.get('tanggal',''))}</td>
                </tr>
                """
            st.markdown(f"""
            <div style="background:white;border-radius:12px;overflow:hidden;
                        box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                <table style="width:100%;border-collapse:collapse;">
                    <thead><tr style="background:#1C2B4A;">
                        <th style="padding:10px 12px;color:#8CA0B8;font-size:0.72rem;text-align:left;">MODUL</th>
                        <th style="padding:10px 12px;color:#8CA0B8;font-size:0.72rem;text-align:left;">KOMPONEN</th>
                        <th style="padding:10px 12px;color:#8CA0B8;font-size:0.72rem;text-align:center;">NILAI</th>
                        <th style="padding:10px 12px;color:#8CA0B8;font-size:0.72rem;text-align:right;">TGL</th>
                    </tr></thead>
                    <tbody>{pr_html}</tbody>
                </table>
            </div>
            """, unsafe_allow_html=True)


# ─── STATISTIK PAGE ───────────────────────────────────────────────────────────

def render_statistik_page():
    page_header("Statistik Kelas","Analisis performa keseluruhan siswa XI TAB","📈")
    siswa_list = get_all_siswa()
    if not siswa_list:
        st.info("Belum ada data."); return

    data=[]
    for s in siswa_list:
        rt,rp,na = get_rata_nilai_teori(s["id"]),get_rata_nilai_praktik(s["id"]),get_nilai_akhir(s["id"])
        data.append({"Nama":s["nama_lengkap"],"Kelas":s.get("kelas",""),
                     "Teori":round(rt,1),"Praktik":round(rp,1),"Nilai Akhir":round(na,1),
                     "Grade":get_grade_letter(na),"Status":"Lulus" if na>=75 else ("Remedial" if na>0 else "Belum")})
    df=pd.DataFrame(data).sort_values("Nilai Akhir",ascending=False)

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("Total Siswa",len(df))
    with c2: st.metric("Rata-rata Akhir",f"{df['Nilai Akhir'].mean():.1f}")
    with c3: st.metric("Lulus (≥75)",len(df[df["Nilai Akhir"]>=75]))
    with c4: st.metric("Nilai Tertinggi",f"{df['Nilai Akhir'].max():.1f}")

    st.divider()
    tab1,tab2,tab3 = st.tabs(["📊 Grafik","📋 Tabel","📥 Export"])
    with tab1:
        bar_chart_nilai(dict(zip(df["Nama"].apply(lambda x:x.split()[0]),df["Nilai Akhir"])),
                        "Distribusi Nilai Akhir Siswa XI TAB")
    with tab2:
        _render_custom_table(df.rename(columns={"Teori":"Nilai Teori","Praktik":"Nilai Praktik"}))
    with tab3:
        c1,c2=st.columns(2)
        with c1:
            st.download_button("📥 CSV",df.to_csv(index=False).encode("utf-8-sig"),
                               "statistik.csv","text/csv",use_container_width=True)
        with c2:
            try:
                import io,openpyxl; buf=io.BytesIO()
                with pd.ExcelWriter(buf,engine="openpyxl") as w:
                    df.to_excel(w,index=False,sheet_name="Statistik")
                st.download_button("📊 Excel",buf.getvalue(),"statistik.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True)
            except: pass


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def _salam():
    from datetime import datetime
    h = datetime.now().hour
    if h<11: return "Selamat Pagi"
    elif h<15: return "Selamat Siang"
    elif h<18: return "Selamat Sore"
    else: return "Selamat Malam"

def _tanggal_sekarang():
    from datetime import datetime
    hari = ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"]
    bln  = ["","Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agu","Sep","Okt","Nov","Des"]
    now  = datetime.now()
    return f"{hari[now.weekday()]}, {now.day} {bln[now.month]} {now.year}"
