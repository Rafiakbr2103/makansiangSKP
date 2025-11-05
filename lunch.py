import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime
import plotly.express as px
import time
import base64

# =========================
# DATABASE SETUP (TIDAK DIUBAH)
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
    conn.close()

init_db()

# ✅ AUTO RESET DAILY
def auto_reset_daily():
    today = date.today().isoformat()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT value FROM metadata WHERE key='last_reset'")
    row = c.fetchone()

    if not row or row[0] != today:
        c.execute("DELETE FROM claims")
        c.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES ('last_reset', ?)",
            (today,)
        )
        conn.commit()

    conn.close()

auto_reset_daily()

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

# ✅ Save claim + timestamp
def add_claim(nrp):
    today = date.today().isoformat()
    now_time = datetime.now().strftime("%H:%M:%S")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO claims (nrp, claim_date, claim_time) VALUES (?, ?, ?)",
        (nrp, today, now_time)
    )
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
st.set_page_config(page_title="UT Yard Sukapura - Lunch Claim", layout="centered")

def load_logo(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

base64_logo = load_logo("abai.png")

PRIMARY = "#FFD200"
BG = "#F7F7F9"
CARD = "#FFFFFF"
TEXT = "#0F1724"
ACCENT = "#FFD200"


# ✅ UI/RESPONSIVE IMPROVED
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');
html, body, [class*="css"]  {{ font-family: 'Montserrat', sans-serif; }}
body {{ background-color: {BG}; color: {TEXT}; }}

* {{
    box-sizing: border-box;
}}

.ut-header {{
    display:flex;
    align-items:center;
    justify-content:center;
    padding: 18px 22px;
    border-radius: 12px;
    background: linear-gradient(90deg, rgba(255,210,50,0.06), rgba(255,210,50,0.03));
    box-shadow: 0 6px 20px rgba(16,24,40,0.06);
    gap:16px;
    width: 100%;
    text-align: center;
}}

.ut-header img {{
    height:64px;
    border-radius:8px;
    flex-shrink: 0;
}}

.ut-header h1 {{
    font-size:26px;
    color: {TEXT};
    margin:0;
    letter-spacing:0.2px;
    line-height: 1.2;
}}

.ut-sub {{
    color: #6B7280;
    margin-top:4px;
    font-size:14px;
    text-align:center
}}

.card {{
    background: {CARD};
    color: {TEXT};
    padding: 18px;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(15,23,42,0.06);
    text-align: center;
    font-weight: 700;
    margin-bottom: 16px;
    width: 100%;
}}

.stButton button {{
    background: linear-gradient(90deg, {PRIMARY}, #FFEA66);
    color: #000;
    border-radius:10px;
    padding: 12px 16px;
    font-size:15px;
    font-weight:700;
    border: none;
    width: 100%;
    box-shadow: 0 6px 18px rgba(255,210,32,0.14);
}}

.stButton button:hover {{
    transform: translateY(-2px);
}}

input[type='text'], input[type='password'] {{
    border-radius:8px;
    padding:10px;
    width: 100% !important;
}}

/* === CENTER TAB MENU === */
.stTabs [data-baseweb="tab-list"] {{
    display: flex;
    justify-content: center;
}}

/* === CENTER LABEL INPUT === */
label {{
    width: 100%;
    text-align: center !important;
    display: block;
}}

/* === CENTER BUTTON === */
.stButton {{
    display: flex;
    justify-content: center;
}}
.stButton > button {{
    width: fit-content !important;
    min-width: 240px;
}}

@media (max-width: 768px) {{
    .ut-header {{
        flex-direction: column;
        padding: 14px;
        text-align: center;
    }}

    .ut-header img {{
        height: 54px;
    }}

    .ut-header h1 {{
        font-size: 20px;
    }}

    .ut-sub {{
        font-size: 12px;
    }}

    h1 {{
        font-size: 20px !important;
    }}

    .card h3 {{
        font-size: 18px;
    }}

    .card div {{
        font-size: 28px;
    }}

    .toast {{
        right: 10px;
        left: 10px;
        text-align: center;
    }}

    .block-container {{
        padding-left: 10px !important;
        padding-right: 10px !important;
    }}
}}

@media (max-width: 480px) {{
    .ut-header h1 {{
        font-size: 18px;
    }}
    .card div {{
        font-size: 24px;
    }}
}}
</style>
""", unsafe_allow_html=True)


def show_toast(message, color="#4BB543", duration=3):
    toast_html = f"""
    <div class="toast" style="background-color:{color};color:white;padding:12px 18px;border-radius:10px;box-shadow:0 6px 18px rgba(0,0,0,0.12);font-weight:700;">
        {message}
    </div>
    """
    st.markdown(toast_html, unsafe_allow_html=True)


logo_html = f"<img src=\"data:image/png;base64,{base64_logo}\">" if base64_logo else ""

st.markdown(f"""
<div class="ut-header">
    {logo_html}
    <div style='text-align:left'>
        <h1>UT Yard Sukapura — Lunch Claim System</h1>
</div>
""", unsafe_allow_html=True)


tab1, tab2, tab3 = st.tabs(["Karyawan", "Admin", "Bantuan"])

# =========================
# TAB 1 — KARYAWAN
# =========================
with tab1:
    st.markdown("<h1 style='text-align:center; letter-spacing:0.3px; font-weight:700;'>──── Klaim Makan Siang ────</h1>", unsafe_allow_html=True)

    remaining = get_remaining_meals()
    st.markdown(f"""
        <div class="card" style="background: linear-gradient(135deg, #1D4ED8, #3B82F6);color:white;box-shadow:0 8px 18px rgba(29,78,216,0.4);">
            <h3 style="margin:0;font-weight:700;">Sisa Jatah Makan Hari Ini</h3>
            <div style="font-size:34px;margin-top:8px;">{remaining} / 168</div>
        </div>
    """, unsafe_allow_html=True)

    nrp = st.text_input("Masukkan NRP Anda:")
    name = st.text_input("Masukkan Nama Lengkap:")

    if nrp and name:
        employee = get_employee(nrp)
        if not employee:
            add_employee(nrp, name)

        claimed_today = get_claim_today(nrp)
        disable_button = bool(claimed_today)
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
                if employee and employee[2] <= 0:
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
# TAB 2 — ADMIN
# =========================
with tab2:
    st.header("🔒 Admin Panel")
    admin_pass = st.text_input("Masukkan Password Admin:", type="password")

    if admin_pass == "admin123":
        st.success("Admin mode aktif!")

        quota = 168

        conn = sqlite3.connect(DB_NAME)
        today_claims = pd.read_sql_query(
            f"SELECT COUNT(*) as total FROM claims WHERE claim_date = '{date.today().isoformat()}'",
            conn
        ).iloc[0]['total']
        not_claimed = quota - today_claims
        conn.close()

        st.markdown(f"""
        <div style="display:flex;gap:18px;flex-wrap:wrap;margin-top:10px;justify-content:center">
            <div class="card card-small" style="flex:1;min-width:200px;max-width:300px;">
                <h4 style="margin:0;color:#6B7280;font-weight:600;">Kuota Per Hari</h4>
                <div style="font-size:22px;margin-top:6px;color:{TEXT};">{quota}</div>
            </div>
            <div class="card card-small" style="flex:1;min-width:200px;max-width:300px;">
                <h4 style="margin:0;color:#6B7280;font-weight:600;">Sudah Klaim Hari Ini</h4>
                <div style="font-size:22px;margin-top:6px;color:{ACCENT};">{today_claims}</div>
            </div>
            <div class="card card-small" style="flex:1;min-width:200px;max-width:300px;">
                <h4 style="margin:0;color:#6B7280;font-weight:600;">Belum Klaim</h4>
                <div style="font-size:22px;margin-top:6px;color:{TEXT};">{not_claimed}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        fig = px.pie(names=["Sudah Klaim", "Belum Klaim"], values=[today_claims, not_claimed], hole=0.45)
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        df = get_all_claims()
        if not df.empty:
            today = date.today().isoformat()
            conn = sqlite3.connect(DB_NAME)

            names = pd.read_sql_query("""
                SELECT claims.nrp, employees.name, claims.claim_date, claims.claim_time
                FROM claims
                JOIN employees ON claims.nrp = employees.nrp
                WHERE claims.claim_date = ?
                ORDER BY claims.id DESC
            """, conn, params=(today,))
            conn.close()

            if not names.empty:
                st.subheader("Daftar Karyawan yang Sudah Klaim Hari Ini")
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
# TAB 3 — BANTUAN
# =========================
with tab3:
    st.markdown("""
    <div style="background-color:#FFFFFF;border-radius:10px;padding:16px;margin-bottom:12px;box-shadow:0 6px 18px rgba(15,23,42,0.04);text-align:center">
        <h4 style="margin:0;color:#111827;">Helmalya RP</h4>
        <p style="margin:6px 0;color:#6B7280;"> 
        <a href="mailto:HelmalyaRP@unitedtractors.com">HelmalyaRP@unitedtractors.com</a><br>
         0858 5982 3983
        </p>
        <a href="https://wa.me/6285859823983" target="_blank">
            <div style="display:inline-block;background-color:#25D366;color:white;border-radius:8px;padding:8px 12px;font-weight:700;text-decoration:none;">💬 Chat via WhatsApp</div>
        </a>
    </div>
    <p style="color:#6B7280;text-align:center;">Jam kerja: 08.00 - 16.30 WIB</p>
    """, unsafe_allow_html=True)


# =========================
# Footer
# =========================
st.markdown(f"""
<div style="text-align:center;padding:14px 0;color:#9CA3AF;font-size:13px;">
    © {date.today().year} United Tractors — Aplikasi klaim makan siang
</div>
""", unsafe_allow_html=True)
