"""ujian.py - Sistem Ujian Terjadwal dengan kontrol guru"""
import streamlit as st
import random
import time
import datetime
from database import (
    create_ujian_jadwal, get_all_ujian_jadwal, get_ujian_jadwal_by_id,
    update_ujian_jadwal, set_status_ujian, delete_ujian_jadwal,
    get_ujian_aktif_untuk_siswa, get_ujian_sudah_selesai_siswa,
    get_hasil_ujian_jadwal,
    tandai_materi_selesai, get_materi_selesai, cek_materi_selesai,
    buat_ujian_sesi, selesaikan_sesi, simpan_jawaban, get_jawaban_sesi,
    siswa_sudah_kerjakan, get_soal_by_materi, get_all_materi,
    get_soal_count_by_materi, get_nilai_teori_by_siswa,
    get_rata_nilai_teori, get_all_siswa,
)
from utils import (
    page_header, format_tanggal, format_tanggal_short,
    get_predikat, get_grade_letter, show_success, show_error, show_warning
)

def render_ujian_page():
    if st.session_state.role == "guru":
        _guru_view()
    else:
        _siswa_view()

# ══════════════════════════ GURU ══════════════════════════════════════════════

def _guru_view():
    page_header("Manajemen Ujian",
        "Buat jadwal ujian, atur durasi, aktifkan/tutup & lihat hasil", "📝")
    tabs = st.tabs(["📋 Daftar Jadwal","➕ Buat Jadwal","📊 Hasil Ujian"])
    with tabs[0]: _guru_daftar()
    with tabs[1]: _guru_buat()
    with tabs[2]: _guru_hasil()


def _guru_daftar():
    jadwals = get_all_ujian_jadwal()
    if not jadwals:
        st.info("Belum ada jadwal ujian. Buat melalui tab **➕ Buat Jadwal**.")
        return

    aktif   = sum(1 for j in jadwals if j["status"]=="aktif")
    selesai = sum(1 for j in jadwals if j["status"]=="selesai")
    c1,c2,c3 = st.columns(3)
    with c1: st.metric("Total Jadwal", len(jadwals))
    with c2: st.metric("🟢 Aktif", aktif)
    with c3: st.metric("✅ Selesai", selesai)
    st.divider()

    for j in jadwals:
        sc = {"draft":"#718096","aktif":"#38A169","selesai":"#3182CE"}.get(j["status"],"#718096")
        sb = {"draft":"#F7FAFC","aktif":"#F0FFF4","selesai":"#EBF8FF"}.get(j["status"],"#F7FAFC")
        icon_status = "🟢" if j["status"]=="aktif" else ("✅" if j["status"]=="selesai" else "📝")

        with st.expander(f"{icon_status} **{j['judul']}** | {j.get('materi_judul','?')} | ⏱️{j['durasi_menit']}m | 👥{j['jml_peserta']} peserta"):
            col_i, col_a = st.columns([3,1])
            with col_i:
                st.markdown(f"""
                <div style="background:{sb};border-radius:10px;padding:1rem;border-left:4px solid {sc};">
                <table style="width:100%;font-size:0.86rem;border-collapse:collapse;">
                <tr><td style="color:#718096;padding:3px 8px;">📚 Materi</td><td style="font-weight:600;padding:3px 8px;">{j.get('materi_judul','—')}</td>
                    <td style="color:#718096;padding:3px 8px;">⏱️ Durasi</td><td style="font-weight:600;padding:3px 8px;">{j['durasi_menit']} menit</td></tr>
                <tr><td style="color:#718096;padding:3px 8px;">📝 Jml Soal</td><td style="font-weight:600;padding:3px 8px;">{j['max_soal']} soal</td>
                    <td style="color:#718096;padding:3px 8px;">🔀 Acak</td><td style="font-weight:600;padding:3px 8px;">{'Ya' if j['acak_soal'] else 'Tidak'}</td></tr>
                <tr><td style="color:#718096;padding:3px 8px;">📅 Mulai</td><td style="font-weight:600;padding:3px 8px;">{format_tanggal(j['tanggal_mulai']) if j['tanggal_mulai'] else '—'}</td>
                    <td style="color:#718096;padding:3px 8px;">🏁 Selesai</td><td style="font-weight:600;padding:3px 8px;">{format_tanggal(j['tanggal_selesai']) if j['tanggal_selesai'] else '—'}</td></tr>
                <tr><td style="color:#718096;padding:3px 8px;">📖 Syarat</td>
                    <td colspan="3" style="font-weight:600;padding:3px 8px;">{'✅ Wajib selesaikan materi' if j['syarat_materi'] else '⛔ Tidak ada syarat'}</td></tr>
                <tr><td style="color:#718096;padding:3px 8px;">Status</td>
                    <td colspan="3" style="padding:3px 8px;">
                    <span style="background:{sc};color:white;padding:2px 10px;border-radius:20px;font-weight:600;font-size:0.8rem;">{j['status'].upper()}</span>
                    </td></tr>
                </table></div>
                """, unsafe_allow_html=True)

            with col_a:
                st.markdown("**Aksi:**")
                if j["status"] == "draft":
                    if st.button("🟢 Aktifkan", key=f"ak_{j['id']}", use_container_width=True, type="primary"):
                        set_status_ujian(j["id"], "aktif")
                        show_success("Ujian diaktifkan! Siswa bisa akses.")
                        st.rerun()
                elif j["status"] == "aktif":
                    if st.button("🔴 Tutup", key=f"tu_{j['id']}", use_container_width=True):
                        set_status_ujian(j["id"], "selesai")
                        show_warning("Ujian ditutup.")
                        st.rerun()
                    if st.button("↩️ Draft", key=f"dr_{j['id']}", use_container_width=True):
                        set_status_ujian(j["id"], "draft"); st.rerun()
                elif j["status"] == "selesai":
                    if st.button("🔄 Buka Lagi", key=f"bk_{j['id']}", use_container_width=True):
                        set_status_ujian(j["id"], "aktif")
                        show_success("Ujian dibuka kembali."); st.rerun()

                if st.button("✏️ Edit", key=f"ed_{j['id']}", use_container_width=True):
                    st.session_state.edit_jadwal_id = j["id"]; st.rerun()

                if st.button("🗑️ Hapus", key=f"dj_{j['id']}", use_container_width=True):
                    st.session_state[f"kd_{j['id']}"] = True

                if st.session_state.get(f"kd_{j['id']}"):
                    st.warning("Yakin hapus jadwal ini?")
                    x1,x2 = st.columns(2)
                    with x1:
                        if st.button("✅ Ya", key=f"yd_{j['id']}", type="primary"):
                            delete_ujian_jadwal(j["id"])
                            del st.session_state[f"kd_{j['id']}"]
                            st.rerun()
                    with x2:
                        if st.button("❌ Batal", key=f"nd_{j['id']}"):
                            del st.session_state[f"kd_{j['id']}"]; st.rerun()

            if st.session_state.get("edit_jadwal_id") == j["id"]:
                _form_edit(j["id"])

            if j["jml_peserta"] > 0:
                hasil = get_hasil_ujian_jadwal(j["id"])
                if hasil:
                    avg = sum(h["skor"] for h in hasil)/len(hasil)
                    st.info(f"📊 {len(hasil)} peserta | Rata-rata: **{avg:.1f}** | Tertinggi: **{max(h['skor'] for h in hasil):.1f}**")


def _guru_buat():
    st.subheader("➕ Buat Jadwal Ujian Baru")
    materi_list = get_all_materi()
    if not materi_list:
        st.warning("Tambahkan materi dan soal terlebih dahulu.")
        return

    with st.form("form_buat_jadwal", clear_on_submit=True):
        judul = st.text_input("Judul Ujian *", placeholder="Contoh: Ulangan Harian Sistem Hidrolik XI TAB")
        c1,c2 = st.columns(2)
        with c1:
            mat_opts = {m["judul"]: m["id"] for m in materi_list}
            sel_mat  = st.selectbox("Materi Ujian *", list(mat_opts.keys()))
            mid      = mat_opts[sel_mat]
            jml_db   = get_soal_count_by_materi(mid)
            st.caption(f"📝 Tersedia **{jml_db}** soal")
            durasi   = st.number_input("⏱️ Durasi (menit) *", 5, 180, 60, 5)
            max_soal = st.number_input("📝 Jumlah Soal *", 1, max(jml_db,1), min(10,max(jml_db,1)), 5)
        with c2:
            acak   = st.checkbox("🔀 Acak urutan soal", value=True)
            syarat = st.checkbox("📖 Wajib selesaikan materi dulu", value=True,
                                 help="Siswa harus klik 'Tandai Selesai' di halaman Materi")
            tgl_m  = st.date_input("📅 Tanggal Mulai *",  value=datetime.date.today())
            jam_m  = st.time_input("🕐 Jam Mulai *",      value=datetime.time(8,0))
            tgl_s  = st.date_input("🏁 Tanggal Selesai *",value=datetime.date.today())
            jam_s  = st.time_input("🕐 Jam Selesai *",    value=datetime.time(10,0))

        st.info("💡 Setelah simpan, status = **DRAFT**. Aktifkan manual agar siswa bisa akses.")
        save = st.form_submit_button("💾 Simpan Jadwal", type="primary", use_container_width=True)

        if save:
            dt_m = datetime.datetime.combine(tgl_m, jam_m)
            dt_s = datetime.datetime.combine(tgl_s, jam_s)
            errs = []
            if not judul.strip():      errs.append("Judul wajib diisi")
            if max_soal > jml_db:      errs.append(f"Soal ({max_soal}) melebihi bank soal ({jml_db})")
            if dt_s <= dt_m:           errs.append("Waktu selesai harus setelah waktu mulai")
            if errs:
                for e in errs: show_error(e)
            else:
                jid = create_ujian_jadwal(judul.strip(), mid, int(durasi), int(max_soal),
                                          1 if acak else 0, str(dt_m), str(dt_s),
                                          1 if syarat else 0, st.session_state.user_id)
                show_success(f"Jadwal '{judul}' dibuat! Aktifkan di tab Daftar Jadwal.")
                st.rerun()


def _form_edit(jid):
    j = get_ujian_jadwal_by_id(jid)
    if not j: return
    materi_list = get_all_materi()
    mat_opts    = {m["judul"]: m["id"] for m in materi_list}
    cur_name    = next((k for k,v in mat_opts.items() if v==j["materi_id"]), list(mat_opts.keys())[0])

    st.markdown("---"); st.subheader(f"✏️ Edit: {j['judul']}")
    with st.form(f"edit_j_{jid}"):
        judul  = st.text_input("Judul *", value=j["judul"])
        c1,c2  = st.columns(2)
        with c1:
            sel_m  = st.selectbox("Materi *", list(mat_opts.keys()),
                                  index=list(mat_opts.keys()).index(cur_name))
            durasi   = st.number_input("Durasi (menit)", 5, 180, int(j["durasi_menit"]), 5)
            max_soal = st.number_input("Jml Soal", 1, 100, int(j["max_soal"]), 5)
        with c2:
            acak   = st.checkbox("Acak soal", value=bool(j["acak_soal"]))
            syarat = st.checkbox("Wajib selesai materi", value=bool(j["syarat_materi"]))
            _p = lambda s: datetime.datetime.fromisoformat(str(s)[:16]) if s else datetime.datetime.now()
            dm,ds = _p(j["tanggal_mulai"]), _p(j["tanggal_selesai"])
            tgl_m  = st.date_input("Tgl Mulai",   value=dm.date())
            jam_m  = st.time_input("Jam Mulai",   value=dm.time())
            tgl_s  = st.date_input("Tgl Selesai", value=ds.date())
            jam_s  = st.time_input("Jam Selesai", value=ds.time())
        b1,b2 = st.columns(2)
        with b1: save   = st.form_submit_button("💾 Simpan", type="primary", use_container_width=True)
        with b2: cancel = st.form_submit_button("❌ Batal",  use_container_width=True)
        if save:
            update_ujian_jadwal(jid, judul.strip(), mat_opts[sel_m], int(durasi), int(max_soal),
                                1 if acak else 0,
                                str(datetime.datetime.combine(tgl_m,jam_m)),
                                str(datetime.datetime.combine(tgl_s,jam_s)),
                                1 if syarat else 0)
            show_success("Jadwal diperbarui!")
            st.session_state.edit_jadwal_id = None; st.rerun()
        if cancel:
            st.session_state.edit_jadwal_id = None; st.rerun()


def _guru_hasil():
    import pandas as pd
    jadwals = get_all_ujian_jadwal()
    if not jadwals:
        st.info("Belum ada jadwal ujian."); return

    opts = {f"[{j['status'].upper()}] {j['judul']}": j["id"] for j in jadwals}
    sel  = st.selectbox("Pilih Jadwal", list(opts.keys()))
    jid  = opts[sel]
    j    = get_ujian_jadwal_by_id(jid)
    if not j: return

    st.markdown(f"""
    <div style="background:#EBF8FF;border-radius:10px;padding:0.8rem 1.2rem;margin-bottom:1rem;
                border-left:4px solid #3182CE;font-size:0.87rem;">
        📚 <b>{j['judul']}</b> | ⏱️ {j['durasi_menit']} menit | 📝 {j['max_soal']} soal |
        Status: <b>{j['status'].upper()}</b>
    </div>
    """, unsafe_allow_html=True)

    hasil       = get_hasil_ujian_jadwal(jid)
    all_siswa   = get_all_siswa()
    sudah_ids   = {h["siswa_id"] for h in hasil}
    belum       = [s for s in all_siswa if s["id"] not in sudah_ids]

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("Total Siswa", len(all_siswa))
    with c2: st.metric("✅ Sudah", len(hasil))
    with c3: st.metric("⏳ Belum", len(belum))
    with c4:
        avg = sum(h["skor"] for h in hasil)/len(hasil) if hasil else 0
        st.metric("Rata-rata", f"{avg:.1f}" if hasil else "—")

    st.divider()
    if not hasil:
        st.info("Belum ada siswa yang mengerjakan ujian ini.")
    else:
        df = pd.DataFrame(hasil)
        df["skor"]   = df["skor"].round(1)
        df["Grade"]  = df["skor"].apply(get_grade_letter)
        df["Status"] = df["skor"].apply(lambda v:"✅ Lulus" if v>=75 else "❌ Remedial")
        df["Waktu"]  = df["selesai_at"].apply(lambda x:str(x)[:16] if x else "—")
        disp = df[["nama_siswa","nis","kelas","benar","total_soal","skor","Grade","Status","Waktu"]].rename(
            columns={"nama_siswa":"Nama","nis":"NIS","kelas":"Kelas",
                     "benar":"Benar","total_soal":"Total","skor":"Nilai","Waktu":"Selesai"})
        st.dataframe(disp, use_container_width=True, hide_index=True)

        from utils import bar_chart_nilai
        bar_chart_nilai({h["nama_siswa"].split()[0]:h["skor"] for h in hasil},
                        f"Distribusi Nilai — {j['judul']}")

        if belum:
            st.divider()
            st.markdown(f"### ⏳ Belum Mengerjakan ({len(belum)} siswa)")
            cols = st.columns(3)
            for i,s in enumerate(belum):
                cols[i%3].markdown(f"- {s['nama_lengkap']} *(NIS: {s.get('nis','—')})*")

        st.download_button("📥 Export CSV",
            disp.to_csv(index=False).encode("utf-8-sig"),
            f"hasil_{j['judul'].replace(' ','_')}.csv","text/csv")

        # Detail jawaban
        st.divider(); st.subheader("🔍 Detail Jawaban per Siswa")
        sis_opts = {h["nama_siswa"]: h["id"] for h in hasil}
        sel_s    = st.selectbox("Pilih Siswa", list(sis_opts.keys()))
        detail   = get_jawaban_sesi(sis_opts[sel_s])
        for i,d in enumerate(detail,1):
            oi = "✅" if d["is_correct"] else "❌"
            om = {"A":d["opsi_a"],"B":d["opsi_b"],"C":d["opsi_c"],"D":d["opsi_d"]}
            bc = "#38A169" if d["is_correct"] else "#E53E3E"
            st.markdown(f"""
            <div style="background:{'#F0FFF4' if d['is_correct'] else '#FFF5F5'};border-radius:8px;
                        padding:8px 14px;margin-bottom:6px;border-left:3px solid {bc};">
                <b>{oi} {i}.</b> {d['pertanyaan']}<br>
                <span style="color:#718096;font-size:0.81rem;">
                    Jawaban: <b>{d['jawaban_siswa']}</b> ({om.get(d['jawaban_siswa'],'—')}) |
                    Benar: <b>{d['jawaban_benar']}</b> ({om.get(d['jawaban_benar'],'—')})
                </span>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════ SISWA ═════════════════════════════════════════════

def _siswa_view():
    page_header("Ujian Online",
        "Kerjakan ujian terjadwal — pastikan sudah menyelesaikan materi terlebih dahulu","✏️")
    _init_state()
    if st.session_state.get("ujian_result"):
        _show_result(); return
    if st.session_state.get("ujian_sedang_berjalan"):
        _active_exam(); return
    tab1,tab2 = st.tabs(["🚀 Ujian Tersedia","📋 Riwayat Ujian"])
    with tab1: _daftar_ujian()
    with tab2: _riwayat()


def _init_state():
    for k,v in {"ujian_result":None,"ujian_sedang_berjalan":False,
                "ujian_soal_list":[],"ujian_sesi_id":None,
                "ujian_jadwal_id":None,"ujian_start_ts":None,
                "ujian_durasi_detik":3600}.items():
        if k not in st.session_state: st.session_state[k]=v


def _daftar_ujian():
    sid      = st.session_state.user_id
    jadwals  = get_ujian_aktif_untuk_siswa(sid)
    mat_done = get_materi_selesai(sid)

    if not jadwals:
        st.markdown("""
        <div style="background:#FFFBEB;border-radius:12px;padding:2rem;text-align:center;
                    border:2px dashed #D69E2E;margin-top:1rem;">
            <div style="font-size:3rem;">⏳</div>
            <h3 style="color:#744210;">Belum Ada Ujian Aktif</h3>
            <p style="color:#975A16;">Guru belum mengaktifkan jadwal ujian.<br>
            Gunakan waktu ini untuk menyelesaikan materi pembelajaran.</p>
        </div>""", unsafe_allow_html=True)
        return

    for j in jadwals:
        sudah     = bool(j["sudah_dikerjakan"])
        materi_ok = (not j["syarat_materi"]) or (j["materi_id"] in mat_done)
        expired   = _is_expired(j["tanggal_selesai"])

        if sudah:       border,bg="#38A169","#F0FFF4"
        elif expired:   border,bg="#718096","#F7FAFC"
        elif materi_ok: border,bg="#3182CE","#EBF8FF"
        else:           border,bg="#D69E2E","#FFFBEB"

        st.markdown(f"""
        <div style="background:{bg};border-radius:14px;padding:1.2rem 1.5rem;
                    margin-bottom:1rem;border-left:5px solid {border};
                    box-shadow:0 2px 8px rgba(0,0,0,0.08);">
            <h4 style="color:#1A365D;margin:0 0 4px;">{j['judul']}</h4>
            <span style="color:#718096;font-size:0.82rem;">
                📚 {j.get('materi_judul','?')} &nbsp;|&nbsp;
                ⏱️ {j['durasi_menit']} menit &nbsp;|&nbsp;
                📝 {j['max_soal']} soal &nbsp;|&nbsp;
                📅 s/d {format_tanggal(j['tanggal_selesai'])}
            </span>
        </div>""", unsafe_allow_html=True)

        if sudah:
            st.success("✅ Anda sudah mengerjakan ujian ini. Lihat nilai di tab **Riwayat Ujian**.")
        elif expired:
            st.error("⛔ Waktu ujian sudah berakhir.")
        elif not materi_ok:
            st.warning(f"""
            📖 **Syarat belum terpenuhi!**
            Buka menu **Materi**, baca materi **'{j.get('materi_judul','?')}'** sampai selesai,
            lalu klik tombol **"✅ Tandai Sudah Selesai Dibaca"** yang ada di bawah materi.
            """)
        else:
            sisa = _sisa_waktu(j["tanggal_selesai"])
            if sisa:
                h2,m2 = divmod(sisa//60,60)
                st.info(f"⏰ Sisa waktu akses ujian: **{h2} jam {m2} menit**")

            col_m,_ = st.columns([1,3])
            with col_m:
                if st.button("🚀 Mulai Ujian", key=f"mulai_{j['id']}",
                             type="primary", use_container_width=True):
                    _mulai_ujian(j)


def _is_expired(ts):
    if not ts: return False
    try:
        return datetime.datetime.now() > datetime.datetime.fromisoformat(str(ts)[:19])
    except: return False


def _sisa_waktu(ts):
    if not ts: return None
    try:
        delta = (datetime.datetime.fromisoformat(str(ts)[:19]) - datetime.datetime.now()).total_seconds()
        return max(0, int(delta))
    except: return None


def _mulai_ujian(j):
    soal = get_soal_by_materi(j["materi_id"])
    if not soal: show_error("Tidak ada soal! Hubungi guru."); return
    if j["acak_soal"]: random.shuffle(soal)
    soal = soal[:j["max_soal"]]
    sesi_id = buat_ujian_sesi(j["id"], st.session_state.user_id, len(soal))
    st.session_state.ujian_sedang_berjalan = True
    st.session_state.ujian_soal_list       = soal
    st.session_state.ujian_sesi_id         = sesi_id
    st.session_state.ujian_jadwal_id       = j["id"]
    st.session_state.ujian_start_ts        = time.time()
    st.session_state.ujian_durasi_detik    = j["durasi_menit"]*60
    st.session_state.ujian_result          = None
    st.rerun()


def _active_exam():
    soal_list = st.session_state.ujian_soal_list
    sesi_id   = st.session_state.ujian_sesi_id
    total     = len(soal_list)
    elapsed   = int(time.time()-(st.session_state.ujian_start_ts or time.time()))
    remaining = max(0, st.session_state.ujian_durasi_detik - elapsed)
    mm,ss     = divmod(remaining,60)

    if remaining == 0:
        st.warning("⏰ Waktu habis! Jawaban otomatis dikumpulkan.")
        time.sleep(1); _do_submit(soal_list, sesi_id, {}); return

    jadwal   = get_ujian_jadwal_by_id(st.session_state.ujian_jadwal_id) or {}
    wc       = "#E53E3E" if remaining<300 else "#FF6B35"
    ct,cw,cp = st.columns([3,1,1])
    with ct: st.markdown(f"### ✏️ {jadwal.get('judul','Ujian')}")
    with cw:
        st.markdown(f"""
        <div style="text-align:center;background:white;border-radius:10px;padding:8px;
                    border:2px solid {wc};">
            <div style="font-size:0.7rem;color:{wc};font-weight:600;">⏱️ SISA WAKTU</div>
            <div style="font-size:1.6rem;font-weight:800;color:{wc};">{mm:02d}:{ss:02d}</div>
        </div>""", unsafe_allow_html=True)
    with cp: st.metric("📋 Soal",f"{total}")
    st.divider()

    with st.form("form_ujian_aktif"):
        jawaban_dict = {}
        for i,soal in enumerate(soal_list,1):
            opts = {"A":soal["opsi_a"],"B":soal["opsi_b"],"C":soal["opsi_c"],"D":soal["opsi_d"]}
            st.markdown(f"""
            <div style="background:white;border-radius:10px;padding:1rem 1.2rem;
                        margin-bottom:0.8rem;box-shadow:0 1px 4px rgba(0,0,0,0.08);
                        border-left:4px solid #CBD5E0;">
                <span style="color:#718096;font-size:0.76rem;font-weight:600;">SOAL {i}/{total}</span>
                <p style="color:#1A365D;font-weight:500;margin:6px 0 0;">{soal['pertanyaan']}</p>
            </div>""", unsafe_allow_html=True)
            jwb = st.radio(f"j_{i}",["A","B","C","D"],
                           format_func=lambda x,o=opts:f"{x}.  {o[x]}",
                           key=f"qz_{soal['id']}_{i}",
                           label_visibility="collapsed",horizontal=False)
            jawaban_dict[soal["id"]] = jwb
        st.divider()
        cs,cc = st.columns(2)
        with cs: sub = st.form_submit_button("📤 Submit & Selesai",type="primary",use_container_width=True)
        with cc: can = st.form_submit_button("🚫 Batalkan",use_container_width=True)
        if sub: _do_submit(soal_list, sesi_id, jawaban_dict)
        if can: _do_cancel()


def _do_submit(soal_list, sesi_id, jawaban_dict):
    total = len(soal_list); benar = 0
    for s in soal_list:
        jw  = jawaban_dict.get(s["id"],"")
        ok  = 1 if jw==s["jawaban_benar"] else 0
        benar += ok
        simpan_jawaban(sesi_id, s["id"], jw, ok)
    skor = round((benar/total)*100,1) if total>0 else 0
    selesaikan_sesi(sesi_id, benar, total, skor)
    elapsed = int(time.time()-(st.session_state.ujian_start_ts or time.time()))
    st.session_state.ujian_result = {"skor":skor,"benar":benar,"salah":total-benar,
                                      "total":total,"elapsed":elapsed,"sesi_id":sesi_id}
    st.session_state.ujian_sedang_berjalan = False
    st.session_state.ujian_soal_list = []
    st.rerun()


def _do_cancel():
    sesi_id = st.session_state.ujian_sesi_id
    if sesi_id:
        from database import get_db
        with get_db() as conn:
            conn.execute("DELETE FROM ujian_sesi WHERE id=? AND status='berlangsung'",(sesi_id,))
    for k in ["ujian_sedang_berjalan","ujian_soal_list","ujian_sesi_id","ujian_result"]:
        st.session_state[k] = False if k=="ujian_sedang_berjalan" else ([] if k=="ujian_soal_list" else None)
    st.rerun()


def _show_result():
    r = st.session_state.ujian_result
    skor,lulus,grade = r["skor"], r["skor"]>=75, get_grade_letter(r["skor"])
    bg,fg,br = ("#C6F6D5","#276749","#38A169") if lulus else ("#FED7D7","#822727","#E53E3E")
    mm,ss = divmod(r.get("elapsed",0),60)
    if lulus: st.balloons()

    st.markdown(f"""
    <div style="background:{bg};border:2px solid {br};border-radius:16px;
                padding:2rem;text-align:center;margin-bottom:1.5rem;">
        <div style="font-size:3.5rem;font-weight:800;color:{br};">{skor}</div>
        <div style="font-size:1.3rem;color:{fg};font-weight:700;">
            Grade {grade} — {get_predikat(skor)}
        </div>
        <div style="color:{fg};margin-top:6px;">
            {'🎉 Selamat! Nilai Anda LULUS (KKM 75)' if lulus else '📚 Belum memenuhi KKM 75. Pelajari lagi materi!'}
        </div>
    </div>""", unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("✅ Benar",r["benar"])
    with c2: st.metric("❌ Salah",r["salah"])
    with c3: st.metric("📋 Total",r["total"])
    with c4: st.metric("⏱️ Waktu",f"{mm}m {ss}s")

    if r.get("sesi_id"):
        with st.expander("🔍 Review Jawaban Saya",expanded=False):
            for i,d in enumerate(get_jawaban_sesi(r["sesi_id"]),1):
                oi=("✅" if d["is_correct"] else "❌")
                om={"A":d["opsi_a"],"B":d["opsi_b"],"C":d["opsi_c"],"D":d["opsi_d"]}
                bc="#38A169" if d["is_correct"] else "#E53E3E"
                st.markdown(f"""
                <div style="background:{'#F0FFF4' if d['is_correct'] else '#FFF5F5'};border-radius:8px;
                            padding:8px 14px;margin-bottom:6px;border-left:3px solid {bc};">
                    <b>{oi} {i}.</b> {d['pertanyaan']}<br>
                    <span style="color:#718096;font-size:0.81rem;">
                        Jawaban: <b>{d['jawaban_siswa']}</b> ({om.get(d['jawaban_siswa'],'—')}) |
                        Benar: <b>{d['jawaban_benar']}</b> ({om.get(d['jawaban_benar'],'—')})
                    </span>
                </div>""", unsafe_allow_html=True)

    st.session_state.ujian_result = None


def _riwayat():
    riwayat = get_ujian_sudah_selesai_siswa(st.session_state.user_id)
    if not riwayat:
        st.info("📋 Belum ada riwayat ujian."); return
    for r in riwayat:
        s=r["skor"]; oi="✅" if s>=75 else ("⚠️" if s>=60 else "❌")
        st.markdown(f"""
        <div style="background:white;border-radius:10px;padding:10px 16px;margin-bottom:8px;
                    display:flex;justify-content:space-between;align-items:center;
                    box-shadow:0 1px 4px rgba(0,0,0,0.07);">
            <div>
                <b style="color:#1A365D;">{r.get('judul_ujian','?')}</b><br>
                <span style="color:#718096;font-size:0.8rem;">
                    📚 {r.get('materi_judul','?')} | 📅 {format_tanggal_short(r.get('selesai_at',''))}
                </span>
            </div>
            <div style="text-align:right;">
                <div style="font-size:1.4rem;font-weight:700;color:#FF6B35;">{oi} {s:.1f}</div>
                <div style="font-size:0.74rem;color:#A0AEC0;">{r.get('benar',0)}/{r.get('total_soal',0)} benar</div>
            </div>
        </div>""", unsafe_allow_html=True)
    avg = sum(r["skor"] for r in riwayat)/len(riwayat)
    st.info(f"📊 Rata-rata nilai ujian Anda: **{avg:.1f}** — {get_predikat(avg)}")
