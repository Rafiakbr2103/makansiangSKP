import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import plotly.express as px
import time
import base64
# import threading # Dihapus: Threading tidak ideal di Streamlit Cloud

# =========================
# DATABASE SETUP & CACHING
# =========================
DB_NAME = "lunch.db"

# Menggunakan st.cache_resource untuk koneksi database
@st.cache_resource
def get_db_connection():
    """Mengembalikan objek koneksi database yang di-cache."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    return conn

def init_db(conn):
    """Fungsi inisialisasi DB, dipanggil sekali."""
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            nrp TEXT PRIMARY KEY,
            name TEXT,
            quota INTEGER DEFAULT 168
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nrp TEXT,
            claim_date TEXT,
            claim_time TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.commit()

# Inisialisasi DB hanya sekali
conn = get_db_connection()
init_db(conn)

# =========================
# AUTO RESET KUOTA HARIAN — PERBAIKAN 1 & 2
# =========================
def auto_reset_daily():
    """Reset kuota harian dan update metadata. Dipanggil di awal setiap run."""
    conn = get_db_connection()
    # Menggunakan Asia/Jakarta untuk memastikan reset tepat pukul 00.00 WIB
    today = datetime.now(ZoneInfo("Asia/Jakarta")).date().isoformat()
    c = conn.cursor()
    c.execute("SELECT value FROM metadata WHERE key='last_reset'")
    row = c.fetchone()

    # Perubahan kuota (mutation) harus membersihkan cache data yang relevan
    if not row or row[0] != today:
        c.execute("UPDATE employees SET quota = 168")
        c.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('last_reset', ?)", (today,))
        conn.commit()
        # Perbaikan 1: Membersihkan cache agar kuota ter-update di tampilan
        get_employee.clear()
        get_claim_today.clear()
        get_all_claims.clear()
        # st.cache_data.clear() # Bisa dilakukan untuk memastikan semua data di-refresh
    
auto_reset_daily()

# =========================
# AUTO DELETE HISTORY > 3 HARI — PERBAIKAN 3 (7 hari menjadi 3 hari)
# =========================
def cleanup_old_claims():
    """Hapus klaim yang lebih dari 3 hari."""
    conn = get_db_connection()
    # Mengubah batas hapus dari 7 hari menjadi 3 hari
    limit = (date.today() - timedelta(days=3)).isoformat()
    c = conn.cursor()
    c.execute("DELETE FROM claims WHERE claim_date < ?", (limit,))
    conn.commit()
    # Tidak perlu clear cache karena ini hanya membersihkan data lama
    
cleanup_old_claims()

# =========================
# HELPERS (MENGGUNAKAN CACHING)
# =========================
@st.cache_data(ttl=60) # Cache data karyawan selama 60 detik
def get_employee(nrp):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM employees WHERE nrp=?", (nrp,))
    row = c.fetchone()
    return row

@st.cache_data(ttl=60) # Cache klaim hari ini selama 60 detik
def get_claim_today(nrp):
    today = date.today().isoformat()
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM claims WHERE nrp=? AND claim_date=?", (nrp, today))
    row = c.fetchone()
    return row

@st.cache_data(ttl=5) # Cache data klaim total selama 5 detik
def get_all_claims():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM claims", conn)
    return df

# Fungsi yang memodifikasi DB (tidak boleh di-cache)
def add_employee(nrp, name):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO employees (nrp, name) VALUES (?, ?)", (nrp, name))
    conn.commit()
    # Mutation: Invalidate cache
    get_employee.clear()

def add_claim(nrp):
    conn = get_db_connection()
    today = date.today().isoformat()
    now_time = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%H:%M:%S")
    
    # Perlu memanggil fungsi add_claim yang tidak di-cache
    c = conn.cursor()
    c.execute("INSERT INTO claims (nrp, claim_date, claim_time) VALUES (?, ?, ?)",
              (nrp, today, now_time))
    c.execute("UPDATE employees SET quota = quota - 1 WHERE nrp=?", (nrp,))
    conn.commit()

    # Mutation: Invalidate relevant caches
    get_employee.clear()
    get_claim_today.clear()
    get_all_claims.clear()


# =========================
# PAGE CONFIG & STYLE
# =========================
st.set_page_config(page_title="UT Yard Sukapura - Lunch Claim", layout="centered")

# FUNGSI LOAD GAMBAR BASE64
def load_base64_image(path, mime_type="image/png"):
    try:
        with open(path, "rb") as f:
            data = f.read()
        return f"data:{mime_type};base64,{base64.b64encode(data).decode()}"
    except:
        return None

# Load gambar. Catatan: file "abai.png" dan "pdg.png" harus ada di direktori yang sama
# Jika file tidak ada, Anda akan melihat latar belakang kosong.
base64_logo = load_base64_image("abai.png", "image/png")
base64_food_image = load_base64_image("pdg.png", "image/png")

PRIMARY = "#FFD200"
BG = "#F7F7F9"
CARD = "#FFFFFF"
TEXT = "#0F1724"
ACCENT = "#FFD200"


# =========================
# CSS FULL + HERO BACKGROUND HEADER
# =========================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Montserrat', sans-serif;
}}

/* PERBAIKAN 1: Kontainer utama lebih responsif */
.block-container {{
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    max-width: 800px;
}}

body {{
    background-color: {BG};
    color: {TEXT};
}}

* {{
    box-sizing: border-box;
}}

/* ================= GLOBAL ANIMATIONS ================= */
@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}

.main > div {{
    animation: fadeIn 0.8s ease-in-out;
}}

/* =====================================================
   HERO HEADER: GAMBAR MENJADI BACKGROUND BANNER
===================================================== */

.ut-hero {{
    width: 100%;
    height: 210px;
    border-radius: 18px;
    overflow: hidden;
    position: relative;
    background-image: url('{base64_food_image}');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    box-shadow: 0 6px 20px rgba(16,24,40,0.07);
    margin-bottom: 22px;
}}

.ut-hero-overlay {{
    position: absolute;
    bottom: 0;
    width: 100%;
    padding: 20px 16px;
    background: linear-gradient(to top, rgba(0,0,0,0.55), rgba(0,0,0,0));
    text-align: center;
}}

.ut-hero-overlay h1 {{
    color: white;
    font-size: 26px;
    font-weight: 700;
    margin: 6px 0 0;
    line-height: 1.25;
    text-shadow: 0px 2px 4px rgba(0,0,0,0.55);
}}

.ut-hero-logo {{
    height: 68px;
    margin-bottom: 6px;
    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.55));
    border-radius: 10px;
}}


/* ================== CARD STYLE =================== */
.card {{
    background: {CARD};
    color: {TEXT};
    padding: 18px;
    border-radius: 16px;
    box-shadow: 0 8px 24px rgba(15,23,42,0.06);
    text-align: center;
    font-weight: 700;
    margin-bottom: 16px;
    width: 100%;
}}

/* ================ BUTTON STYLE ================== */
.stButton button {{
    background: linear-gradient(90deg, {PRIMARY}, #FFE766);
    color: black;
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 15px;
    font-weight: 700;
    border: none;
    width: 100%;
    box-shadow: 0 6px 18px rgba(255,210,32,0.22);
}}

.stButton button:hover {{
    transform: translateY(-2px);
}}

/* ================ INPUT (DIPERBAIKI) ================== */
input[type='text'], input[type='password'] {{
    border-radius: 8px;
    padding: 10px;
    width: 100% !important;
    margin-bottom: 12px; /* Tambahkan margin */
}}

/* PERBAIKAN 2: Alignment Label Input */
.stTextInput > label {{
    text-align: left !important;
    padding-bottom: 4px;
    display: block;
    width: 100%;
}}

label {{
    width: 100%;
    text-align: center !important;
    display: block;
}}

.stButton {{
    display: flex;
    justify-content: center;
}}

.stButton > button {{
    width: fit-content !important;
    min-width: 240px;
}}


/* =================================================
   MOBILE RESPONSIVE HERO HEADER (DIPERBAIKI)
================================================= */
@media (max-width: 768px) {{
    .ut-hero {{
        height: 165px;
    }}
    .ut-hero-logo {{
        height: 54px;
        margin-bottom: 4px; /* Sedikit kurangi margin di mobile */
    }}
    .ut-hero-overlay {{
        padding: 16px 10px; /* Kurangi padding horizontal di mobile */
    }}
    .ut-hero-overlay h1 {{
        font-size: 18px; /* Perkecil font */
        margin: 4px 0 0;
    }}
    /* PERBAIKAN 3: Card Kupon Mobile Fix */
    .card > h3 {{
        font-size: 16px;
    }}
    /* Target Div yang menampilkan angka sisa kupon */
    .card > div:last-child {{ 
        font-size: 30px !important;
    }}
}}

/* ================================
   CENTER TABS (KARYAWAN / ADMIN / BANTUAN)
=================================== */
div[data-baseweb="tab-list"] {{
    display: flex !important;
    justify-content: center !important;
}}

.stTabs [role="tablist"] {{
    display: flex !important;
    justify-content: center !important;
}}

.stTabs [role="tab"] {{
    margin: 0 16px !important;
    font-size: 15px !important;
    font-weight: 600 !important;
}}
</style>
""", unsafe_allow_html=True)


# =========================
# HEADER RENDER — HERO BACKGROUND
# =========================
st.markdown(f"""
<div class="ut-hero">
    <div class="ut-hero-overlay">
        <img class="ut-hero-logo" src="{base64_logo}">
        <h1>UT Yard Sukapura — Lunch Claim System</h1>
    </div>
</div>
""", unsafe_allow_html=True)
# =========================
# MULAI MAIN WRAPPER
# =========================
st.markdown('<div class="main">', unsafe_allow_html=True)

# =========================
# TABS
# =========================
tab1, tab2, tab3 = st.tabs(["Karyawan", "Admin", "Bantuan"])


# =========================
# TAB 1 — KARYAWAN
# =========================
with tab1:

    # MODIFIKASI: Mengganti H1 dengan garis dekoratif panjang
    # menjadi H2 dengan garis dekoratif pendek agar tidak berantakan di mobile
    st.markdown(
        "<h2 style='text-align:center; letter-spacing:0.3px; font-weight:700; font-size: 26px; line-height: 1.2;'>— Klaim Makan Siang —</h2>",
        unsafe_allow_html=True
    )

    today = date.today().isoformat()

    # Menggunakan fungsi helper dengan caching
    all_claims_df = get_all_claims()
    total_used = all_claims_df[all_claims_df['claim_date'] == today].shape[0]

    remaining = 168 - total_used

    # Card sisa kupon
    st.markdown(f"""
        <div class="card" style="background: linear-gradient(135deg, #1D4ED8, #3B82F6);
                                 color:white; box-shadow:0 8px 18px rgba(29,78,216,0.35);">
            <h3 style="margin:0;font-weight:700;">Sisa Kupon Hari Ini</h3>
            <div style="font-size:34px;margin-top:1px;">{remaining} / 168</div>
        </div>
    """, unsafe_allow_html=True)


    # Input data karyawan
    nrp = st.text_input("Masukkan NRP Anda:")
    name = st.text_input("Masukkan Nama Lengkap:")

    # Inisialisasi session state untuk pop-up jika belum ada
    if 'claim_success' not in st.session_state:
        st.session_state['claim_success'] = False


    # Perlu memanggil get_employee dan get_claim_today setiap kali nrp/name berubah
    emp = None
    claimed_today = None
    disable_button = False
    
    if nrp and name:
        # Memastikan nama karyawan ditambahkan/diperbarui sebelum pengecekan
        add_employee(nrp, name)
        
        # Panggil fungsi yang di-cache
        emp = get_employee(nrp)
        claimed_today = get_claim_today(nrp)
        # Nonaktifkan jika sudah klaim, kuota habis, atau pop-up sedang aktif
        disable_button = bool(claimed_today) or (emp and emp[2] <= 0) or st.session_state['claim_success']
    else:
        # Nonaktifkan jika data input kosong
        disable_button = True


    # Tombol Cek / Klaim
    if st.button("Cek / Klaim Makan Siang", disabled=disable_button):

        if not nrp or not name:
            st.warning("⚠️ Mohon isi NRP dan Nama terlebih dahulu.")
        else:
            
            # Re-fetch data setelah yakin input valid dan karyawan sudah di-add/update
            emp_data = get_employee(nrp)
            claimed_today = get_claim_today(nrp)

            with st.spinner("Sedang memproses..."):
                time.sleep(0.5) 

                if emp_data and emp_data[2] <= 0:
                    st.error("❌ Kuota makan siang Anda telah habis.")

                elif claimed_today:
                    st.info("Kamu sudah klaim makan siang hari ini.")

                else:
                    # >>> LOGIKA NOTIFIKASI POP-UP YANG BARU <<<
                    # 1. Tambahkan Klaim ke DB
                    add_claim(nrp)
                    
                    # 2. Atur Session State untuk menampilkan Pop-up
                    st.session_state['claim_success'] = True
                    st.session_state['claimed_name'] = name
                    st.session_state['claimed_time'] = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%H:%M:%S")

                    # 3. Re-run aplikasi untuk menampilkan Pop-up (menggunakan st.rerun())
                    st.rerun()
                    # >>> AKHIR LOGIKA NOTIFIKASI POP-UP YANG BARU <<<


# =========================
# TAB 2 — ADMIN
# =========================
with tab2:

    st.header("🔒 Admin Panel")
    admin_pass = st.text_input("Masukkan Password Admin:", type="password")

    if admin_pass == "admin123":

        quota = 168
        today = date.today().isoformat()
        
        # Menggunakan fungsi helper dengan caching
        all_claims_df_admin = get_all_claims()
        today_used = all_claims_df_admin[all_claims_df_admin['claim_date'] == today].shape[0]

        not_claimed = quota - today_used

        # ===== CARD INFO =====
        st.markdown(f"""
        <div style="display:flex;gap:18px;flex-wrap:wrap;margin-top:10px;justify-content:center;">
            <div class="card" style="min-width:200px;">
                <h4 style="margin:0;color:#6B7280;font-weight:600;">Kuota per Hari</h4>
                <div style="font-size:22px;margin-top:6px;">{quota}</div>
            </div>
            <div class="card" style="min-width:200px;">
                <h4 style="margin:0;color:#6B7280;font-weight:600;">Sudah Klaim Hari Ini</h4>
                <div style="font-size:22px;margin-top:6px;color:{ACCENT};">{today_used}</div>
            </div>
            <div class="card" style="min-width:200px;">
                <h4 style="margin:0;color:#6B7280;font-weight:600;">Belum Klaim</h4>
                <div style="font-size:22px;margin-top:6px;">{not_claimed}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # ===== PIE CHART =====
        fig = px.pie(
            names=["Sudah Klaim", "Belum Klaim"],
            values=[today_used, not_claimed],
            hole=0.45
        )
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # =========================
        # HISTORY 3 HARI — PERBAIKAN 2 & 3
        # =========================
        st.subheader("📅 History Klaim 3 Hari Terakhir")

        conn = get_db_connection()
        # Mengubah periode query dari 7 hari menjadi 3 hari
        last3 = (date.today() - timedelta(days=3)).isoformat()

        # Query history langsung, karena get_all_claims hanya mengembalikan semua klaim
        history = pd.read_sql_query("""
            SELECT claims.nrp, employees.name, claims.claim_date, claims.claim_time
            FROM claims
            JOIN employees ON claims.nrp = employees.nrp
            WHERE claims.claim_date >= ?
            ORDER BY claims.claim_date DESC, claims.claim_time DESC
        """, conn, params=(last3,))

        if not history.empty:
            # Perbaikan 2: Logic untuk menampilkan tabel per hari
            
            # Mendapatkan daftar tanggal unik, diurutkan dari terbaru
            dates = history["claim_date"].unique()
            
            for d in dates:
                # Filter data untuk tanggal saat ini
                daily_history = history[history["claim_date"] == d]
                
                # Format tanggal agar mudah dibaca
                try:
                    date_obj = datetime.strptime(d, '%Y-%m-%d').date()
                    # Contoh format: 'Thursday, 20 November 2025'
                    formatted_date = date_obj.strftime("%A, %d %B %Y") 
                except:
                    formatted_date = d # Fallback jika format gagal
                
                # Tampilkan Sub-header untuk tanggal ini
                st.markdown(f"**Tanggal Klaim: {formatted_date}** ({daily_history.shape[0]} klaim)")
                
                # Tampilkan tabel data
                st.dataframe(
                    daily_history[['nrp', 'name', 'claim_time']].rename(columns={'claim_time': 'Waktu Klaim'}), 
                    use_container_width=True,
                    hide_index=True
                )
                st.markdown("---") # Garis pemisah antar tabel harian

            st.divider()
            
            # Pindahkan tombol download CSV ke luar loop harian
            st.subheader("📥 Download Data CSV")

            # Pilih tanggal untuk download CSV
            selected = st.selectbox("Pilih tanggal download CSV:", dates)

            dl = history[history["claim_date"] == selected]
            # Memilih kolom yang relevan untuk download
            csv = dl[['nrp', 'name', 'claim_date', 'claim_time']].to_csv(index=False).encode('utf-8')

            st.download_button(
                "⬇️ Download CSV",
                csv,
                file_name=f"history_{selected}.csv",
                mime="text/csv"
            )

        else:
            st.info("Belum ada data pada 3 hari terakhir.") # Update pesan

        st.divider()

        # =========================
        # KELOLA KARYAWAN
        # =========================
        st.subheader("📁 Kelola Karyawan")

        up = st.file_uploader("Upload CSV: nrp, name, quota", type="csv")
        if up:
            try:
                dat = pd.read_csv(up)
                conn = get_db_connection()
                dat.to_sql("employees", conn, if_exists="append", index=False)
                conn.commit() # Pastikan commit
                # conn.close() # Tidak perlu close
                st.success("Upload berhasil!")
                # Invalidate cache setelah modifikasi
                get_employee.clear()
            except Exception as e:
                st.error(f"Gagal upload: {e}")

        c1, c2 = st.columns(2)

        with c1:
            if st.button("Reset Kuota Manual"):
                auto_reset_daily()
                st.success("Kuota sudah direset! (Refresh halaman untuk melihat perubahan)")

        with c2:
            if st.button("Hapus Semua Klaim"):
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("DELETE FROM claims")
                conn.commit()
                st.warning("Semua data klaim dihapus!")
                # Invalidate cache setelah modifikasi
                get_all_claims.clear()


    elif admin_pass:
        st.error("❌ Password salah.")

    else:
        st.info("Masukkan password admin.")
# =========================
# TAB 3 — BANTUAN
# =========================
with tab3:
    st.markdown("""
    <div class="card" style="padding:16px;text-align:center;">
        <h4 style="margin:0;color:#111827;font-weight:700;">Helmalya RP</h4>
        <p style="margin:6px 0;color:#6B7280;">
            <a href="mailto:HelmalyaRP@unitedtractors.com">HelmalyaRP@unitedtractors.com</a><br>
            0858 5982 3983
        </p>
        <a href="https://wa.me/6285859823983" target="_blank">
            <div style="display:inline-block;background-color:#25D366;color:white;
                        border-radius:8px;padding:8px 12px;font-weight:700;
                        text-decoration:none;">
                💬 WhatsApp
            </div>
        </a>
    </div>
    """, unsafe_allow_html=True)


# =========================
# POP-UP NOTIFICATION (MODAL)
# =========================

# Inisialisasi session state untuk pop-up jika belum ada
if 'claim_success' not in st.session_state:
    st.session_state['claim_success'] = False
    
# Logika Pop-up: Tampilkan jika 'claim_success' di Session State adalah True
if st.session_state.get('claim_success', False):
    
    # Ambil data dari Session State
    claimed_name = st.session_state.get('claimed_name', 'Karyawan')
    claimed_time = st.session_state.get('claimed_time', 'Waktu Klaim')

    # CSS dan HTML untuk Modal Pop-up (Full Screen)
    modal_html = f"""
    <style>
        /* Overlay Full Screen */
        .full-screen-modal-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(4px);
            z-index: 9999; /* Pastikan di atas semua elemen Streamlit */
            display: flex;
            justify-content: center;
            align-items: center;
            animation: fadeInOverlay 0.3s ease-out;
        }}

        /* Konten Modal */
        .modal-content {{
            /* 🟢 MODIFIKASI: Latar Belakang Modal Menjadi Hijau */
            background: linear-gradient(145deg, #28A745, #2ECC71); /* Gradien Hijau Sukses */
            color: white; /* Teks default putih */
            border-radius: 20px;
            padding: 30px 40px;
            max-width: 90%;
            width: 400px;
            text-align: center;
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4);
            animation: popUp 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
            /* Tambahkan margin di bawah agar tombol Streamlit tidak tertutup */
            margin-bottom: 70px; 
        }}

        /* Icon Centang */
        .success-icon {{
            /* 🟢 MODIFIKASI: Icon Menjadi Putih agar Kontras dengan Background Hijau */
            color: white; 
            font-size: 50px;
            margin-bottom: 15px;
            font-weight: 900;
            line-height: 1;
            border: 4px solid white;
            border-radius: 50%;
            width: 70px;
            height: 70px;
            display: inline-flex;
            justify-content: center;
            align-items: center;
        }}

        /* Animasi */
        @keyframes fadeInOverlay {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        @keyframes popUp {{
            from {{ transform: scale(0.7); opacity: 0; }}
            to {{ transform: scale(1); opacity: 1; }}
        }}

        /* Tombol Streamlit untuk nutup (Kita posisikan di atas modal) */
        /* Menggunakan data-testid Streamlit untuk targeting CSS yang lebih stabil */
        .stButton button[data-testid*="modal_streamlit_button"] {{
            position: fixed; /* Menggunakan fixed agar tidak bergerak saat scroll */
            bottom: 30vh; /* Posisikan tombol 30% dari bawah layar */
            left: 50%;
            transform: translateX(-50%); /* Geser ke kiri 50% dari lebar tombol */
            width: 320px !important;
            max-width: 80%;
            z-index: 10000;
            margin: 0;
            
            /* Style tombol Streamlit */
            background: linear-gradient(90deg, #FFD200, #FFE766);
            color: black;
            border: none;
            padding: 12px 20px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(255,210,32,0.3);
            transition: transform 0.1s;
        }}
        .stButton button[data-testid*="modal_streamlit_button"]:hover {{
            transform: translate(-50%, -1px);
        }}
    </style>
    <div class="full-screen-modal-overlay">
        <div class="modal-content">
            <div class="success-icon">✓</div>
            <h2 style="color:white; margin-top:10px; font-weight:700;">Klaim Berhasil!</h2>
            <p style="font-size:16px; font-weight:600; margin-bottom:5px;">Selamat Makan, {claimed_name}!</p>
            <p style="font-size:14px; color:#F0F0F0; margin-top:0;">Waktu Klaim: {claimed_time}</p>
        </div>
    </div>
    """
    
    # Tampilkan HTML Modal
    st.markdown(modal_html, unsafe_allow_html=True)

    # Tambahkan tombol Streamlit. CSS di atas akan memposisikannya di tengah-bawah modal.
    if st.button("Selesai", key="modal_streamlit_button"):
        st.session_state['claim_success'] = False
        st.rerun() 
            

# =========================
# FOOTER
# =========================
st.markdown(f"""
</div>  <div style="text-align:center;padding:14px 0;color:#9CA3AF;font-size:13px;">
    © {date.today().year} United Tractors — Sistem Klaim Makan Siang
</div>
""", unsafe_allow_html=True)


# =========================
# END OF FILE — FINAL CHECK
# =========================

st.markdown("", unsafe_allow_html=True)