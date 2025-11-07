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

# ✅ AUTO RESET DAILY FIXED
def auto_reset_daily():
    today = date.today().isoformat()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT value FROM metadata WHERE key='last_reset'")
    row = c.fetchone()

    if not row or row[0] != today:
        # Hapus klaim hari sebelumnya
        c.execute("DELETE FROM claims")

        # Reset quota kembali 168
        c.execute("UPDATE employees SET quota = 168")

        # Update metadata
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

# =========================
# STYLE + FADE-IN ANIMATION + MODAL CSS
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

/* Apply fade to main content, header and cards */
.main > div {{
    animation: fadeIn 0.8s ease-in-out;
}}
.ut-header {{
    animation: fadeIn 1s ease-in-out;
}}
.card {{
    animation: fadeIn 1.1s ease-in-out;
}}

/* Header */
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

/* Card */
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

/* Button */
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

.stTabs [data-baseweb="tab-list"] {{
    display: flex;
    justify-content: center;
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

/* Toast (small) */
.toast {{
    position: fixed;
    right: 20px;
    top: 20px;
    z-index: 99998;
}}

/* FULLSCREEN SUCCESS MODAL */
.success-modal-overlay {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0,0,0,0.55);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 99999;
}}

.success-modal-box {{
    background: white;
    border-radius: 14px;
    padding: 32px;
    width: 90%;
    max-width: 480px;
    text-align: center;
    animation: fadeIn .3s ease;
    box-shadow: 0 12px 32px rgba(0,0,0,0.15);
}}

.success-modal-box h2 {{
    margin: 0 0 10px 0;
    font-size: 26px;
    font-weight: 700;
    color: white !important;
}}

.success-modal-box p {{
    font-size: 18px;
    margin-bottom: 20px;
    font-weight: 600;
}}

.success-modal-btn {{
    background: #16A34A;
    color: white;
    border: none;
    padding: 12px 14px;
    border-radius: 10px;
    width: 100%;
    font-size: 16px;
    cursor: pointer;
    font-weight: 700;
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
    # Simple toast — duration param kept for possible future JS-based auto-hide
    toast_html = f"""
    <div class="toast" style="background-color:{color};color:white;padding:12px 18px;border-radius:10px;box-shadow:0 6px 18px rgba(0,0,0,0.12);font-weight:700;">
        {message}
    </div>
    """
    st.markdown(toast_html, unsafe_allow_html=True)


# Modal function (full-screen)
def show_success_modal(message, timestamp):
    modal_html = f"""
    <div class="success-modal-overlay">
        <div class="success-modal-box">
            <h2>Berhasil!</h2>
            <p>{message}</p>
            <p style='font-size:14px;opacity:0.8;margin-top:4px;'>{timestamp}</p>
        </div>
    </div>
    """
    st.markdown(modal_html, unsafe_allow_html=True)


# logo HTML (if available)
logo_html = f"<img src=\"data:image/png;base64,{base64_logo}\">" if base64_logo else ""

# Wrap main content with a fade container for extra safety (optional)
st.markdown('<div class="main">', unsafe_allow_html=True)

st.markdown(f"""
<div class="ut-header">
    {logo_html}
    <div style='text-align:center'>
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

    remaining = get_remaining_meals()
    st.markdown(f"""
        <div class="card" style="background: linear-gradient(135deg, #1D4ED8, #3B82F6);color:white;box-shadow:0 8px 18px rgba(29,78,216,0.4);">
            <h3 style="margin:0;font-weight:700;">Sisa Kupon Hari Ini</h3>
            <div style="font-size:34px;margin-top:1px;">{remaining} / 168</div>
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
                        # tampilkan success biasa + toast + modal full-screen supaya sangat terlihat
                        show_toast("Klaim berhasil!", "#4BB543")
                        now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                        show_success_modal(f"Selamat makan, {name}!", now)

# =========================
# TAB 2 — ADMIN
# =========================
with tab2:
    st.header("🔒 Admin Panel")
    admin_pass = st.text_input("Masukkan Password Admin:", type="password")

    if admin_pass == "admin123":
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
            try:
                data = pd.read_csv(uploaded)
                conn = sqlite3.connect(DB_NAME)
                data.to_sql("employees", conn, if_exists="append", index=False)
                conn.close()
                show_toast("Data karyawan berhasil di-upload!", "#4BB543")
            except Exception as e:
                st.error(f"Gagal upload: {e}")

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
</div>
<div style="text-align:center;padding:14px 0;color:#9CA3AF;font-size:13px;">
    © {date.today().year} United Tractors — Aplikasi klaim makan siang
</div>
""", unsafe_allow_html=True)


st.markdown("""
<style>

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
@keyframes scaleUp {
    0% { transform: scale(.85); opacity:.4; }
    100% { transform: scale(1); opacity:1; }
}

.success-modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0,0,0,0.55);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 99999;
    animation: fadeIn .3s ease-in-out;
}

.success-modal-box {
    background: #16A34A;
    border-radius: 18px;
    width: 92%;
    max-width: 650px;
    padding: 50px 44px;
    color: white;
    text-align: center;
    position: relative;
    animation: scaleUp .28s ease-in-out;
}

.success-modal-box h2 {
    font-size: 36px;
    font-weight: 800;
    margin: 0 0 10px;
}

.success-modal-box p {
    font-size: 20px;
    margin: 6px 0 30px;
    font-weight: 500;
    line-height: 1.4;
}

.success-modal-close {
    position: absolute;
    top: 14px;
    right: 20px;
    font-size: 32px;
    cursor: pointer;
    font-weight: 700;
    opacity: .75;
}
.success-modal-close:hover {
    opacity: 1;
}

.success-modal-btn {
    background: white;
    color: #16A34A;
    font-weight: 800;
    border: none;
    width: 100%;
    max-width: 240px;
    padding: 16px;
    border-radius: 12px;
    font-size: 18px;
    cursor: pointer;
    transition: .18s;
}
.success-modal-btn:hover {
    transform: translateY(-3px);
}

</style>
""", unsafe_allow_html=True)


# =============== AUTO CHECK PERGANTIAN HARI REALTIME ===============
import threading
import time

def background_daily_reset():
    while True:
        auto_reset_daily()
        time.sleep(60)

reset_thread = threading.Thread(target=background_daily_reset, daemon=True)
reset_thread.start()

