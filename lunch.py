import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import plotly.express as px
import time

# =========================
# DATABASE SETUP
# =========================
DB_NAME = "lunch.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
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
            claim_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# =========================
# HELPER FUNCTIONS
# =========================
def get_employee(nrp):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM employees WHERE nrp=?", (nrp,))
    row = c.fetchone()
    conn.close()
    return row

def add_employee(nrp, name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO employees (nrp, name) VALUES (?, ?)", (nrp, name))
    conn.commit()
    conn.close()

def get_claim_today(nrp):
    today = date.today().isoformat()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM claims WHERE nrp=? AND claim_date=?", (nrp, today))
    row = c.fetchone()
    conn.close()
    return row

def add_claim(nrp):
    today = date.today().isoformat()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO claims (nrp, claim_date) VALUES (?, ?)", (nrp, today))
    c.execute("UPDATE employees SET quota = quota - 1 WHERE nrp=?", (nrp,))
    conn.commit()
    conn.close()

def get_all_claims():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM claims", conn)
    conn.close()
    return df

def reset_daily_claims():
    today = date.today().isoformat()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM claims WHERE claim_date < ?", (today,))
    conn.commit()
    conn.close()

def get_remaining_meals():
    today = date.today().isoformat()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM claims WHERE claim_date=?", (today,))
    used = c.fetchone()[0]
    conn.close()
    remaining = 168 - used
    return remaining

# =========================
# PAGE CONFIG & STYLE
# =========================
st.set_page_config(page_title="UTone Lunch Claim System", layout="centered")

st.markdown("""
    <style>
    body { background-color: #fafafa; }
    .ut-header {
        display: flex; align-items: center; justify-content: center;
        background-color: #000; padding: 1rem 2rem; border-radius: 12px;
        margin-bottom: 25px; flex-wrap: wrap;
    }
    .ut-header img { height: 60px; margin-right: 15px; }
    .ut-header h1 { color: #FFD200; font-size: 28px; margin: 0; }

    .stButton button {
        background-color: #FFD200; color: black;
        border-radius: 8px; font-weight: bold;
        width: 100%; padding: 12px; font-size: 16px;
    }
    .stButton button:hover {
        background-color: #FFE84D; transform: scale(1.02);
    }

    .card {
        background-color: #FFD200;
        color: #000;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0px 3px 6px rgba(0,0,0,0.15);
        text-align: center;
        font-weight: bold;
        margin-bottom: 20px;
    }

    a { color: #0078FF; text-decoration: none; }
    a:hover { text-decoration: underline; }

    @media (max-width: 768px) {
        .ut-header { flex-direction: column; text-align: center; }
        .ut-header img { height: 45px !important; margin-bottom: 10px; }
        .ut-header h1 { font-size: 22px !important; }
        div.block-container { padding-left: 1rem !important; padding-right: 1rem !important; }
    }
    </style>
""", unsafe_allow_html=True)

# =========================
# TOAST
# =========================
def show_toast(message, color="#4BB543", duration=3):
    toast_html = f"""
    <div id="toast" style="
        position: fixed; bottom: 20px; right: 20px;
        background-color: {color}; color: white;
        padding: 12px 20px; border-radius: 8px;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.2);
        z-index: 9999; font-weight: bold;
        animation: fadeIn 0.5s, fadeOut 0.5s {duration}s forwards;">
        {message}
    </div>
    <style>
    @keyframes fadeIn {{ from {{opacity:0;}} to {{opacity:1;}} }}
    @keyframes fadeOut {{ from {{opacity:1;}} to {{opacity:0;}} }}
    </style>
    """
    st.markdown(toast_html, unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown("""
<div class="ut-header">
    <h1>UTone Lunch Claim System</h1>
</div>
""", unsafe_allow_html=True)

st.caption("Sistem klaim makan siang karyawan — United Tractors")

tab1, tab2, tab3 = st.tabs(["Karyawan", "Admin", "Bantuan"])

# =========================
# TAB 1: KARYAWAN
# =========================
with tab1:
    st.header("Form Klaim Makan Siang")

    remaining = get_remaining_meals()
    st.markdown(f"""
        <div class="card">
            <h3>Sisa Jatah Makan Hari Ini</h3>
            <h1>{remaining} / 168</h1>
        </div>
    """, unsafe_allow_html=True)

    nrp = st.text_input("Masukkan NRP Anda:")
    name = st.text_input("Masukkan Nama Lengkap:")

    if nrp and name:
        employee = get_employee(nrp)
        if not employee:
            add_employee(nrp, name)

        claimed_today = get_claim_today(nrp)
        if claimed_today:
            st.info("Kamu sudah klaim makan siang hari ini. Tunggu reset harian.")
            disable_button = True
        else:
            disable_button = False
    else:
        disable_button = False

    if st.button("Cek / Klaim Makan Siang", disabled=disable_button):
        if not nrp or not name:
            st.warning("⚠️ Mohon isi NRP dan Nama terlebih dahulu.")
            show_toast("Lengkapi NRP dan Nama!", "#E67E22")
        else:
            with st.spinner("Sedang memproses klaim..."):
                time.sleep(1)
                employee = get_employee(nrp)
                if employee[2] <= 0:
                    st.error("❌ Kuota makan siang Anda telah habis.")
                    show_toast("Kuota makan siang sudah habis!", "#E74C3C")
                else:
                    if get_claim_today(nrp):
                        st.info("Kamu sudah klaim makan siang hari ini.")
                        show_toast("Kamu sudah klaim hari ini!", "#F39C12")
                    else:
                        add_claim(nrp)
                        st.success(f"✅ Klaim makan siang berhasil! Selamat makan, {name}")
                        show_toast("Klaim berhasil!", "#4BB543")

# =========================
# TAB 2: ADMIN
# =========================
with tab2:
    st.header("Admin Panel")
    admin_pass = st.text_input("Masukkan Password Admin:", type="password")

    if admin_pass == "admin123":
        st.success("Admin mode aktif!")

        conn = sqlite3.connect(DB_NAME)
        total_emp = pd.read_sql_query("SELECT COUNT(*) as total FROM employees", conn).iloc[0]['total']
        today_claims = pd.read_sql_query(f"SELECT COUNT(*) as total FROM claims WHERE claim_date = '{date.today().isoformat()}'", conn).iloc[0]['total']
        not_claimed = total_emp - today_claims
        conn.close()

        st.markdown(f"""
        <div style="display:flex;gap:20px;flex-wrap:wrap;margin-top:10px;">
            <div class="card" style="background-color:#000;color:#FFD200;flex:1;min-width:250px;">
                <h3>Total Karyawan</h3><h1>{total_emp}</h1>
            </div>
            <div class="card" style="background-color:#FFD200;color:#000;flex:1;min-width:250px;">
                <h3>Sudah Klaim Hari Ini</h3><h1>{today_claims}</h1>
            </div>
            <div class="card" style="background-color:#F2F2F2;color:#000;flex:1;min-width:250px;">
                <h3>Belum Klaim</h3><h1>{not_claimed}</h1>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        df = get_all_claims()
        if not df.empty:
            today = date.today().isoformat()
            today_df = df[df['claim_date'] == today]
            if not today_df.empty:
                st.subheader("Daftar Karyawan yang Sudah Klaim Hari Ini")
                conn = sqlite3.connect(DB_NAME)
                names = pd.read_sql_query("""
                    SELECT claims.nrp, employees.name, claims.claim_date
                    FROM claims
                    JOIN employees ON claims.nrp = employees.nrp
                    WHERE claims.claim_date = ?
                    ORDER BY claims.id DESC
                """, conn, params=(today,))
                conn.close()
                st.dataframe(names, use_container_width=True)
            else:
                st.info("Belum ada karyawan yang klaim hari ini.")

        st.divider()
        st.subheader("Kelola Data")
        uploaded = st.file_uploader("Upload Data Karyawan (CSV: nrp, name, quota)", type="csv")
        if uploaded:
            data = pd.read_csv(uploaded)
            conn = sqlite3.connect(DB_NAME)
            data.to_sql("employees", conn, if_exists="append", index=False)
            conn.close()
            st.success("✅ Data karyawan berhasil di-upload.")
            show_toast("Data karyawan berhasil di-upload!", "#4BB543")

        colA, colB = st.columns(2)
        with colA:
            if st.button("Reset Klaim Harian"):
                reset_daily_claims()
                st.info("✅ Klaim sebelum hari ini dihapus.")
                show_toast("Reset harian berhasil!", "#3498DB")
        with colB:
            if st.button("Hapus Semua Data Klaim"):
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("DELETE FROM claims")
                conn.commit()
                conn.close()
                st.warning("⚠️ Semua data klaim dihapus!")
                show_toast("Semua klaim dihapus!", "#E74C3C")

    elif admin_pass:
        st.error("❌ Password salah.")
    else:
        st.info("Masukkan password admin untuk melanjutkan.")

# =========================
# TAB 3: KONTAK
# =========================
with tab3:
    st.header("Bantuan")
    st.markdown("""
    <p>Jika mengalami kendala, hubungi:</p>
    <div style="background-color:#F9F9F9;border-radius:10px;padding:15px;margin-bottom:15px;box-shadow:0px 2px 6px rgba(0,0,0,0.1);">
        <h4>Helmalya RP</h4>
        📧 <a href="mailto:HelmalyaRP@unitedtractors.com">HelmalyaRP@unitedtractors.com</a><br>
        📱 0858 5982 3983<br>
        <a href="https://wa.me/6285859823983" target="_blank">
            <button style="background-color:#25D366;color:white;border:none;border-radius:6px;padding:6px 10px;margin-top:5px;cursor:pointer;">
                💬 Chat via WhatsApp
            </button>
        </a>
    </div>
    <p style="color:#666;">Jam kerja: 08.00 - 17.00 WIB</p>
    """, unsafe_allow_html=True)
