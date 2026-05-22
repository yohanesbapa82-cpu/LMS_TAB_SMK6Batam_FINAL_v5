"""utils.py — Orange/Navy Industrial Theme V5 — TAB SMK N6 Batam"""
import streamlit as st
from datetime import datetime

KATEGORI_OPTIONS = ["Engine","Hydraulic","Kelistrikan","Unit Spesifik"]
MODUL_PRAKTIK_OPTIONS = [
    "Inspeksi Harian (10 Jam)","Start-Up & Shut-Down Procedure",
    "Perawatan Sistem Hidrolik","Perawatan Mesin Diesel",
    "Pengoperasian Excavator PC200","Pengoperasian Forklift CAT DP40",
    "Pengoperasian Backhoe Loader 428","Troubleshooting Engine",
    "Troubleshooting Hydraulic","Pemeliharaan Sistem Kelistrikan",
    "Pemeriksaan Undercarriage","Penyetelan Celah Katup",
    "Service Berkala Forklift DP40",
]

TAB_LOGO_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="80" height="80">
  <!-- Body excavator -->
  <rect x="40" y="110" width="80" height="30" rx="4" fill="#1C2B4A"/>
  <!-- Cab -->
  <rect x="95" y="85" width="40" height="32" rx="3" fill="#1C2B4A"/>
  <!-- Boom arm -->
  <line x1="130" y1="88" x2="170" y2="55" stroke="#FF6B00" stroke-width="10" stroke-linecap="round"/>
  <!-- Stick arm -->
  <line x1="170" y1="55" x2="185" y2="90" stroke="#FF6B00" stroke-width="8" stroke-linecap="round"/>
  <!-- Bucket -->
  <path d="M180 90 Q192 105 178 115 Q168 118 160 108 Z" fill="#FF6B00"/>
  <!-- Track wheels -->
  <ellipse cx="55" cy="142" rx="14" ry="14" fill="#333"/>
  <ellipse cx="105" cy="142" rx="14" ry="14" fill="#333"/>
  <rect x="40" y="130" width="80" height="12" rx="2" fill="#555"/>
  <!-- Speed lines -->
  <line x1="10" y1="118" x2="38" y2="118" stroke="#FF6B00" stroke-width="4" stroke-linecap="round"/>
  <line x1="16" y1="128" x2="38" y2="128" stroke="#FF6B00" stroke-width="3" stroke-linecap="round"/>
  <line x1="22" y1="137" x2="38" y2="137" stroke="#FF6B00" stroke-width="2.5" stroke-linecap="round"/>
</svg>
"""

def apply_custom_style():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html,body,[class*="css"]{font-family:'Inter',sans-serif;}

    /* ── Sidebar ── */
    [data-testid="stSidebar"]{
        background:linear-gradient(180deg,#0B1524 0%,#0F1E34 60%,#0B1524 100%);
        border-right:1px solid rgba(255,107,0,0.15);
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label{color:#C8D8E8 !important;}
    [data-testid="stSidebar"] strong{color:#FF6B00 !important;}
    [data-testid="stSidebar"] hr{border-color:rgba(255,107,0,0.2) !important;}
    [data-testid="stSidebar"] .stRadio>div{gap:1px !important;}
    [data-testid="stSidebar"] .stRadio label{
        background:transparent !important;
        border-radius:8px !important;
        padding:9px 14px !important;
        transition:all .18s !important;
        border:1px solid transparent !important;
        display:block !important;width:100% !important;
        font-size:0.875rem !important;font-weight:500 !important;
        color:#A0B4C8 !important;
    }
    [data-testid="stSidebar"] .stRadio label:hover{
        background:rgba(255,107,0,0.12) !important;
        border-color:rgba(255,107,0,0.35) !important;
        color:#FF6B00 !important;
    }
    [data-testid="stSidebar"] .stButton>button{
        background:transparent !important;
        border:1px solid rgba(229,92,46,0.4) !important;
        color:#FF8C50 !important;box-shadow:none !important;
        font-size:0.83rem !important;
    }
    [data-testid="stSidebar"] .stButton>button:hover{
        background:rgba(229,92,46,0.12) !important;
        border-color:#FF6B00 !important;color:#FF6B00 !important;
    }

    /* ── Main background ── */
    .stApp{background:#F2F4F7;}
    .main .block-container{padding:1.5rem 2rem 3rem;max-width:1280px;}

    /* ── Global btn ── */
    .main .stButton>button,
    section[data-testid="stMain"] .stButton>button{
        background:linear-gradient(135deg,#FF6B00,#E05500) !important;
        color:#fff !important;border:none !important;border-radius:9px !important;
        font-weight:600 !important;padding:0.5rem 1.2rem !important;
        transition:all .2s !important;
        box-shadow:0 3px 10px rgba(255,107,0,0.28) !important;
    }
    .main .stButton>button:hover,
    section[data-testid="stMain"] .stButton>button:hover{
        background:linear-gradient(135deg,#FF8C00,#FF6B00) !important;
        box-shadow:0 6px 18px rgba(255,107,0,0.38) !important;
        transform:translateY(-1px) !important;
    }
    .main .stButton>button[kind="secondary"],
    section[data-testid="stMain"] .stButton>button[kind="secondary"]{
        background:white !important;color:#FF6B00 !important;
        border:2px solid #FF6B00 !important;box-shadow:none !important;
    }

    /* ── Metric cards ── */
    [data-testid="metric-container"]{
        background:white;border-radius:14px;
        padding:1.1rem 1.3rem;
        box-shadow:0 2px 10px rgba(0,0,0,0.07);
        border-left:4px solid #FF6B00;
        transition:all .22s;
    }
    [data-testid="metric-container"]:hover{
        transform:translateY(-3px);
        box-shadow:0 8px 24px rgba(255,107,0,0.18);
    }
    [data-testid="stMetricValue"]{font-size:2.1rem !important;font-weight:700 !important;color:#FF6B00 !important;}
    [data-testid="stMetricLabel"]{color:#4A5568 !important;font-weight:500 !important;font-size:0.78rem !important;text-transform:uppercase;letter-spacing:0.4px;}

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"]{
        background:white;border-radius:12px;padding:5px;gap:4px;
        box-shadow:0 1px 6px rgba(0,0,0,0.07);
    }
    .stTabs [data-baseweb="tab"]{
        border-radius:9px;padding:8px 20px;
        color:#4A5568;font-weight:500;font-size:0.86rem;transition:all .2s;
    }
    .stTabs [aria-selected="true"]{
        background:linear-gradient(135deg,#FF6B00,#E05500) !important;
        color:white !important;font-weight:700 !important;
        box-shadow:0 3px 10px rgba(255,107,0,0.3) !important;
    }

    /* ── Inputs ── */
    .stTextInput input,.stTextArea textarea,.stNumberInput input{
        border-radius:9px !important;border-color:#D1D9E0 !important;
        background:#FAFBFC !important;transition:all .2s !important;
    }
    .stTextInput input:focus,.stTextArea textarea:focus{
        border-color:#FF6B00 !important;
        box-shadow:0 0 0 3px rgba(255,107,0,0.13) !important;
    }
    .stSelectbox>div>div{border-radius:9px !important;border-color:#D1D9E0 !important;background:#FAFBFC !important;}

    /* ── Expander ── */
    .streamlit-expanderHeader{
        background:white !important;border-radius:10px !important;
        font-weight:600 !important;color:#1C2B4A !important;
        border:1px solid #E8ECF0 !important;transition:all .2s !important;
    }
    .streamlit-expanderHeader:hover{border-color:rgba(255,107,0,0.4) !important;}
    .streamlit-expanderContent{background:white !important;border:1px solid #E8ECF0 !important;border-top:none !important;border-radius:0 0 10px 10px !important;}

    /* ── Progress ── */
    .stProgress>div>div>div>div{background:linear-gradient(90deg,#FF6B00,#FFAA00) !important;border-radius:99px !important;}
    .stProgress>div>div{background:#E8ECF0 !important;border-radius:99px !important;}

    /* ── Alerts ── */
    div[data-testid="stAlert"]{border-radius:10px !important;}

    /* ── Dataframe ── */
    .stDataFrame{border-radius:12px !important;overflow:hidden !important;box-shadow:0 2px 8px rgba(0,0,0,0.06) !important;}

    /* ── Page header ── */
    .page-header{
        background:linear-gradient(135deg,#1C2B4A 0%,#243960 100%);
        color:white;padding:1.4rem 2rem;border-radius:16px;
        margin-bottom:1.5rem;
        box-shadow:0 4px 20px rgba(28,43,74,0.25);
        position:relative;overflow:hidden;
    }
    .page-header::before{
        content:'';position:absolute;top:0;left:0;
        width:4px;height:100%;background:#FF6B00;border-radius:4px 0 0 4px;
    }
    .page-header h1{color:white !important;margin:0 !important;font-size:1.6rem !important;font-weight:700 !important;}
    .page-header p{color:#B8C8E0 !important;margin:3px 0 0 !important;font-size:0.87rem !important;}

    hr{border-color:#E8ECF0 !important;}

    /* ── Download button ── */
    .stDownloadButton>button{
        background:white !important;color:#1C6CB5 !important;
        border:2px solid #1C6CB5 !important;box-shadow:none !important;
    }
    .stDownloadButton>button:hover{background:#EBF4FF !important;}

    /* ── Upload ── */
    [data-testid="stFileUploader"]{
        border:2px dashed rgba(255,107,0,0.3) !important;
        border-radius:12px !important;background:#FFF9F5 !important;
    }
    [data-testid="stFileUploader"]:hover{border-color:#FF6B00 !important;}

    /* ── Slider ── */
    .stSlider [role="slider"]{background:#FF6B00 !important;border:2px solid white !important;box-shadow:0 0 6px rgba(255,107,0,0.4) !important;}
    </style>
    """, unsafe_allow_html=True)

def page_header(title, subtitle="", icon="⚙️"):
    st.markdown(f"""
    <div class="page-header">
        <h1>{icon} {title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def score_badge(nilai):
    if not nilai or nilai==0:
        return '<span style="background:#FEE2E2;color:#991B1B;padding:3px 11px;border-radius:20px;font-size:0.8rem;font-weight:600;">0.0</span>'
    if nilai>=80: c,bg="#065F46","#D1FAE5"
    elif nilai>=70: c,bg="#92400E","#FEF3C7"
    else: c,bg="#991B1B","#FEE2E2"
    return f'<span style="background:{bg};color:{c};padding:3px 11px;border-radius:20px;font-size:0.8rem;font-weight:600;">{nilai:.1f}</span>'

def get_kategori_emoji(k):
    return {"Engine":"⚙️","Hydraulic":"🔩","Kelistrikan":"⚡","Unit Spesifik":"🚜"}.get(k,"🔧")

def get_kategori_color(k):
    return {"Engine":"#FF6B00","Hydraulic":"#1C6CB5","Kelistrikan":"#D97706","Unit Spesifik":"#059669"}.get(k,"#1C2B4A")

def format_tanggal_short(ts):
    if not ts: return "—"
    try:
        dt=datetime.fromisoformat(str(ts).replace("Z","+00:00").split(".")[0])
        return dt.strftime("%d/%m/%Y")
    except: return str(ts)[:10]

def format_tanggal(ts):
    if not ts: return "—"
    try:
        dt=datetime.fromisoformat(str(ts).replace("Z","+00:00").split(".")[0])
        return dt.strftime("%d %b %Y  %H:%M")
    except: return str(ts)

def hitung_nilai_praktik(s,p,h): return round((s*.3)+(p*.3)+(h*.4),2)
def hitung_nilai_akhir(t,p):
    if t==0 and p==0: return 0.0
    if t==0: return p
    if p==0: return t
    return round((t*.3)+(p*.7),2)

def get_predikat(nilai):
    if not nilai or nilai==0: return "Belum Dinilai"
    if nilai>=90: return "Sangat Baik"
    elif nilai>=80: return "Baik"
    elif nilai>=70: return "Cukup"
    elif nilai>=60: return "Kurang"
    else: return "Sangat Kurang"

def get_grade_letter(nilai):
    if not nilai or nilai==0: return "—"
    if nilai>=90: return "A"
    elif nilai>=80: return "B"
    elif nilai>=70: return "C"
    elif nilai>=60: return "D"
    else: return "E"

def show_success(msg): st.success(f"✅ {msg}")
def show_error(msg):   st.error(f"❌ {msg}")
def show_warning(msg): st.warning(f"⚠️ {msg}")
def show_info(msg):    st.info(f"ℹ️ {msg}")

def render_kpi_strip(items):
    cols=st.columns(len(items))
    for i,(icon,label,value,color) in enumerate(items):
        with cols[i]: st.metric(f"{icon} {label}",value)

def bar_chart_nilai(data_dict, title=""):
    import matplotlib.pyplot as plt,matplotlib
    matplotlib.use("Agg")
    if not data_dict: return
    fig,ax=plt.subplots(figsize=(max(6,len(data_dict)*1.3),4))
    names=list(data_dict.keys()); values=list(data_dict.values())
    colors=["#059669" if v>=80 else("#D97706" if v>=70 else("#FF6B00" if v>=60 else "#DC2626"))
            for v in values]
    bars=ax.bar(names,values,color=colors,edgecolor="white",linewidth=1.5,width=0.6)
    ax.axhline(y=75,color="#DC2626",linestyle="--",linewidth=1.5,alpha=0.8,label="KKM (75)")
    ax.set_ylim(0,108)
    ax.set_title(title,fontsize=12,fontweight="bold",color="#1C2B4A",pad=10)
    ax.set_ylabel("Nilai",color="#4A5568")
    ax.legend(fontsize=9)
    ax.spines[["top","right"]].set_visible(False)
    ax.set_facecolor("#FAFBFC"); fig.patch.set_facecolor("white")
    for bar,val in zip(bars,values):
        if val>0:
            ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+1.5,
                    f"{val:.1f}",ha="center",va="bottom",fontsize=9,fontweight="bold",color="#1C2B4A")
    plt.xticks(rotation=30,ha="right",fontsize=9,color="#4A5568")
    plt.tight_layout(); st.pyplot(fig); plt.close()
