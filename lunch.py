import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import plotly.express as px
import time
import base64
import threading

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

# =========================
# AUTO RESET KUOTA HARIAN — TANPA HAPUS DATA
# =========================
def auto_reset_daily():
    today = datetime.now(ZoneInfo("Asia/Jakarta")).date().isoformat()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT value FROM metadata WHERE key='last_reset'")
    row = c.fetchone()

    if not row or row[0] != today:
        c.execute("UPDATE employees SET quota = 168")
        c.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('last_reset', ?)", (today,))
        conn.commit()
    conn.close()

auto_reset_daily()

# =========================
# AUTO DELETE HISTORY > 7 HARI
# =========================
def cleanup_old_claims():
    limit = (date.today() - timedelta(days=7)).isoformat()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM claims WHERE claim_date < ?", (limit,))
    conn.commit()
    conn.close()

cleanup_old_claims()

# =========================
# HELPERS
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
    now_time = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%H:%M:%S")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO claims (nrp, claim_date, claim_time) VALUES (?, ?, ?)",
              (nrp, today, now_time))
    c.execute("UPDATE employees SET quota = quota - 1 WHERE nrp=?", (nrp,))
    conn.commit()
    conn.close()

def get_all_claims():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM claims", conn)
    conn.close()
    return df
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

# =========================
# FULL STYLE + ANIMATIONS
# =========================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');
html, body, [class*="css"]  {{ font-family: 'Montserrat', sans-serif; }}
body {{ background-color: {BG}; color: {TEXT}; }}

* {{
    box-sizing: border-box;
}}

/* Fade-in keyframes (global) */
@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

.main > div {{
    animation: fadeIn 0.8s ease-in-out;
}}
.ut-header {{
    animation: fadeIn 1s ease-in-out;
}}
.card {{
    animation: fadeIn 1.1s ease-in-out;
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

.toast {{
    position: fixed;
    right: 20px;
    top: 20px;
    background-color:#4BB543;
    color:white;
    padding:12px 18px;
    border-radius:10px;
    box-shadow:0 6px 18px rgba(0,0,0,0.12);
    font-weight:700;
    z-index:99998;
}}

/* FULLSCREEN SUCCESS MODAL */
.success-modal-overlay{{
    position:fixed;
    top:0;
    left:0;
    width:100vw;
    height:100vh;
    background:rgba(0,0,0,0.55);
    display:flex;
    justify-content:center;
    align-items:center;
    z-index:99999;
}}
.success-modal-box {{
    background:#16A34A;
    border-radius:18px;
    width:92%;
    max-width:650px;
    padding:50px 44px;
    color:white;
    text-align:center;
}}
.success-modal-box h2 {{
    font-size:36px;
    font-weight:800;
    margin:0 0 10px;
}}
.success-modal-box p {{
    font-size:20px;
    margin:6px 0 30px;
    font-weight:500;
    line-height:1.4;
}}

@media (max-width:768px){{
    .ut-header{{flex-direction:column;padding:14px;text-align:center;}}
    .ut-header img{{height:54px;}}
    .ut-header h1{{font-size:20px;}}
}}
</style>
""", unsafe_allow_html=True)

def show_modal(message, timestamp):
    st.markdown(f"""
    <div class="success-modal-overlay">
        <div class="success-modal-box">
            <h2>Berhasil!</h2>
            <p>{message}</p>
            <p style='font-size:14px;opacity:0.85;margin-top:4px;'>{timestamp}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="main">', unsafe_allow_html=True)

logo_html = f"<img src='data:image/png;base64,{base64_logo}'>" if base64_logo else ""

st.markdown(f"""
<div class="ut-header">
    {logo_html}
    <div>
        <h1>UT Yard Sukapura — Lunch Claim System</h1>
    </div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Karyawan", "Admin", "Bantuan"])
# =========================
# TAB 1 — KARYAWAN
# =========================
with tab1:
    st.markdown("<h1 style='text-align:center; letter-spacing:0.3px; font-weight:700;'>──── Klaim Makan Siang ────</h1>", unsafe_allow_html=True)

    today = date.today().isoformat()
    conn = sqlite3.connect(DB_NAME)

    total_used = pd.read_sql_query(
        "SELECT COUNT(*) AS total FROM claims WHERE claim_date = ?",
        conn, params=(today,)
    ).iloc[0]['total']
    conn.close()

    remaining = 168 - total_used

    st.markdown(f"""
        <div class="card" style="background: linear-gradient(135deg, #1D4ED8, #3B82F6);color:white;box-shadow:0 8px 18px rgba(29,78,216,0.35);">
            <h3 style="margin:0;font-weight:700;">Sisa Kupon Hari Ini</h3>
            <div style="font-size:34px;margin-top:1px;">{remaining} / 168</div>
        </div>
    """, unsafe_allow_html=True)

    nrp = st.text_input("Masukkan NRP Anda:")
    name = st.text_input("Masukkan Nama Lengkap:")

    if nrp and name:
        emp = get_employee(nrp)
        if not emp:
            add_employee(nrp, name)
        claimed_today = get_claim_today(nrp)
        disable_button = bool(claimed_today)
    else:
        disable_button = False

    if st.button("Cek / Klaim Makan Siang", disabled=disable_button):
        if not nrp or not name:
            st.warning("⚠️ Mohon isi NRP dan Nama terlebih dahulu.")
        else:
            with st.spinner("Sedang memproses..."):
                time.sleep(1)

                emp_data = get_employee(nrp)
                if emp_data and emp_data[2] <= 0:
                    st.error("❌ Kuota makan siang Anda telah habis.")
                else:
                    if get_claim_today(nrp):
                        st.info("Kamu sudah klaim makan siang hari ini.")
                    else:
                        add_claim(nrp)
                        now = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%d-%m-%Y %H:%M:%S")
                        show_modal(f"Selamat makan, {name}!", now)
# =========================
# TAB 2 — ADMIN
# =========================
with tab2:
    st.header("🔒 Admin Panel")
    admin_pass = st.text_input("Masukkan Password Admin:", type="password")

    if admin_pass == "admin123":
        quota = 168
        today = date.today().isoformat()

        conn = sqlite3.connect(DB_NAME)
        today_used = pd.read_sql_query(
            "SELECT COUNT(*) AS total FROM claims WHERE claim_date = ?",
            conn, params=(today,)
        ).iloc[0]['total']
        conn.close()

        not_claimed = quota - today_used

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

        # Chart
        fig = px.pie(
            names=["Sudah Klaim", "Belum Klaim"],
            values=[today_used, not_claimed],
            hole=0.45
        )
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # =========================
        # HISTORY 7 HARI TERAKHIR
        # =========================
        st.subheader("📅 History Klaim 7 Hari Terakhir")

        conn = sqlite3.connect(DB_NAME)
        last7 = (date.today() - timedelta(days=7)).isoformat()
        history = pd.read_sql_query("""
            SELECT claims.nrp, employees.name, claims.claim_date, claims.claim_time
            FROM claims
            JOIN employees ON claims.nrp = employees.nrp
            WHERE claims.claim_date >= ?
            ORDER BY claims.claim_date DESC, claims.id DESC
        """, conn, params=(last7,))
        conn.close()

        if not history.empty:
            st.dataframe(history, use_container_width=True)

            dates = sorted(history["claim_date"].unique(), reverse=True)
            selected = st.selectbox("Pilih tanggal download CSV:", dates)

            dl = history[history["claim_date"] == selected]
            csv = dl.to_csv(index=False).encode('utf-8')
            st.download_button(
                "⬇️ Download CSV",
                csv,
                file_name=f"history_{selected}.csv",
                mime="text/csv"
            )
        else:
            st.info("Belum ada data pada 7 hari terakhir.")

        st.divider()
        st.subheader("📁 Kelola Karyawan")

        up = st.file_uploader("Upload CSV: nrp, name, quota", type="csv")
        if up:
            try:
                dat = pd.read_csv(up)
                conn = sqlite3.connect(DB_NAME)
                dat.to_sql("employees", conn, if_exists="append", index=False)
                conn.close()
                st.success("Upload berhasil!")
            except Exception as e:
                st.error(f"Gagal upload: {e}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Reset Kuota Manual"):
                auto_reset_daily()
                st.success("Kuota sudah direset!")
        with c2:
            if st.button("Hapus Semua Klaim"):
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("DELETE FROM claims")
                conn.commit()
                conn.close()
                st.warning("Semua data klaim dihapus!")

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
            <div style="display:inline-block;background-color:#25D366;color:white;border-radius:8px;padding:8px 12px;font-weight:700;text-decoration:none;">💬 WhatsApp</div>
        </a>
    </div>
    """, unsafe_allow_html=True)

# =========================
# FOOTER
# =========================
st.markdown(f"""
</div>
<div style="text-align:center;padding:14px 0;color:#9CA3AF;font-size:13px;">
    © {date.today().year} United Tractors — Sistem Klaim Makan Siang
</div>
""", unsafe_allow_html=True)

# =========================
# BACKGROUND DAILY RESET
# =========================
def bg_reset():
    while True:
        auto_reset_daily()
        cleanup_old_claims()
        time.sleep(60)

thread = threading.Thread(target=bg_reset, daemon=True)
thread.start()
