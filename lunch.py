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
# PAGE CONFIG & STYLING
# =========================
st.set_page_config(page_title="UT Yard Sukapura Lunch Claim System", layout="wide")

st.markdown("""
    <style>
    body {
        background-color: #fafafa;
    }
    .ut-header {
        display: flex;
        align-items: center;
        background-color: #000000;
        padding: 1rem 2rem;
        border-radius: 12px;
        margin-bottom: 25px;
    }
    .ut-header img {
        height: 60px;
        margin-right: 15px;
    }
    .ut-header h1 {
        color: #FFD200;
        font-size: 28px;
        margin: 0;
    }
    .stButton button {
        background-color: #FFD200;
        color: black;
        border-radius: 8px;
        font-weight: bold;
    }
    .stButton button:hover {
        background-color: #FFE84D;
        transform: scale(1.02);
    }

    /* === HILANGKAN GARIS KUNING DI INPUT FIELD + STYLING BARU === */
    .stTextInput > div > div > input {
        border: 1px solid #ccc !important;
        box-shadow: none !important;
        border-radius: 10px !important;
        padding: 8px 10px !important;
        background-color: #fff !important;
        transition: all 0.2s ease-in-out;
    }
    .stTextInput > div > div > input:focus {
        border: 1px solid #FFD200 !important;
        outline: none !important;
        box-shadow: 0px 0px 5px rgba(255,210,0,0.4) !important;
    }

    a { color: #0078FF; text-decoration: none; }
    a:hover { text-decoration: underline; }
    </style>
""", unsafe_allow_html=True)

# =========================
# TOAST NOTIFICATION
# =========================
def show_toast(message, color="#4BB543", duration=3):
    toast_html = f"""
    <div id="toast" style="
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: {color};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.2);
        z-index: 9999;
        font-weight: bold;
        animation: fadeIn 0.5s, fadeOut 0.5s {duration}s forwards;
    ">
        {message}
    </div>
    <style>
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes fadeOut {{
        from {{ opacity: 1; transform: translateY(0); }}
        to {{ opacity: 0; transform: translateY(20px); }}
    }}
    </style>
    """
    st.markdown(toast_html, unsafe_allow_html=True)

# =========================
# HEADER
# =========================
st.markdown("""
<div class="ut-header">
    <img src="https://upload.wikimedia.org/wikipedia/en/0/03/United_Tractors_logo.png">
    <h1>UT Yard Sukapura Lunch Claim System</h1>
</div>
""", unsafe_allow_html=True)

st.caption("Sistem klaim makan siang karyawan — United Tractors")

tab1, tab2, tab3 = st.tabs(["Karyawan", "Admin", "Kontak Bantuan"])

# =========================
# TAB 1: KARYAWAN
# =========================
with tab1:
    st.header("Form Klaim Makan Siang")

    # === DASHBOARD MINI CARD (BERDAMPINGAN) ===
    remaining = get_remaining_meals()
    percentage = (remaining / 168) * 100

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div style="
            background-color:#ffffff;
            border-radius:15px;
            box-shadow:0px 4px 12px rgba(0,0,0,0.1);
            padding:20px;
            text-align:center;
            border-top:6px solid #FFD200;
            height:200px;
        ">
            <h2 style="color:#000; margin-bottom:10px;">Sisa Jatah Makan Hari Ini</h2>
            <h1 style="font-size:48px; color:#FFD200; margin:0;">{remaining} / 168</h1>
            <div style="width:100%; background-color:#eee; border-radius:10px; margin-top:15px;">
                <div style="width:{percentage}%; background-color:#FFD200; height:12px; border-radius:10px;"></div>
            </div>
            <p style="color:#555; margin-top:10px;">{percentage:.1f}% tersisa</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div id="indivCard" style="
            background-color:#f8f8f8;
            border-radius:15px;
            box-shadow:0px 4px 12px rgba(0,0,0,0.05);
            padding:20px;
            text-align:center;
            border-top:6px solid #000000;
            height:200px;
        ">
            <h3 style="color:#000; margin-bottom:10px;">Sisa Kuota Individu</h3>
            <h1 style="font-size:48px; color:#999; margin:0;">–</h1>
            <p style="color:#aaa; margin-top:10px;">Isi NRP dan Nama untuk melihat</p>
        </div>
        """, unsafe_allow_html=True)

    # === INPUT FORM ===
    nrp = st.text_input("Masukkan NRP Anda:")
    name = st.text_input("Masukkan Nama Lengkap:")

    if st.button("Cek / Klaim Makan Siang"):
        if not nrp or not name:
            st.warning("⚠️ Mohon isi NRP dan Nama terlebih dahulu.")
            show_toast("Lengkapi NRP dan Nama!", "#E67E22")
        else:
            with st.spinner("Sedang memproses klaim makan siang kamu..."):
                time.sleep(1)
                employee = get_employee(nrp)
                if not employee:
                    add_employee(nrp, name)
                    st.success(f"Karyawan baru '{name}' terdaftar dengan NRP {nrp}.")
                    show_toast("Karyawan baru terdaftar!", "#3498DB")
                    employee = get_employee(nrp)

                if employee[2] <= 0:
                    st.error("❌ Kuota makan siang Anda telah habis.")
                    show_toast("Kuota makan siang sudah habis!", "#E74C3C")
                else:
                    if get_claim_today(nrp):
                        st.info(f"Halo {name}, kamu sudah klaim makan siang hari ini.")
                        show_toast("Kamu sudah klaim makan siang hari ini!", "#F39C12")
                    else:
                        add_claim(nrp)
                        st.success(f"✅ Klaim makan siang berhasil! Selamat makan, {name}")
                        show_toast("Klaim makan siang berhasil!", "#4BB543")

                # === CARD SISA KUOTA INDIVIDU ===
                individual_quota = employee[2] - (0 if not get_claim_today(nrp) else 1)
                individual_percentage = (individual_quota / 168) * 100

                st.markdown(f"""
                <div style="
                    background-color:#ffffff;
                    border-radius:15px;
                    box-shadow:0px 4px 12px rgba(0,0,0,0.1);
                    padding:20px;
                    text-align:center;
                    border-top:6px solid #000000;
                    margin-top:20px;
                ">
                    <h3 style="color:#000; margin-bottom:10px;">Sisa Kuota Individu</h3>
                    <h1 style="font-size:48px; color:#000; margin:0;">{individual_quota}</h1>
                    <div style="width:100%; background-color:#eee; border-radius:10px; margin-top:15px;">
                        <div style="width:{individual_percentage}%; background-color:#000; height:12px; border-radius:10px;"></div>
                    </div>
                    <p style="color:#666; margin-top:10px;">{individual_percentage:.1f}% dari total kuota</p>
                </div>
                """, unsafe_allow_html=True)

# =========================
# TAB 2 & TAB 3 tetap sama
# =========================
with tab2:
    st.header("Admin Panel")
    admin_pass = st.text_input("Masukkan Password Admin:", type="password")

    if admin_pass == "admin123":
        st.success("Admin mode aktif!")

        # ======== DASHBOARD RINGKAS ========
        st.subheader("Dashboard Ringkas")

        conn = sqlite3.connect(DB_NAME)
        total_emp = pd.read_sql_query("SELECT COUNT(*) as total FROM employees", conn).iloc[0]['total']
        today_claims = pd.read_sql_query(f"SELECT COUNT(*) as total FROM claims WHERE claim_date = '{date.today().isoformat()}'", conn).iloc[0]['total']
        not_claimed = total_emp - today_claims
        conn.close()

        st.markdown(f"""
        <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-top: 10px;">
            <div style="flex:1; min-width: 250px; background-color:#000000; color:#FFD200; padding:20px; border-radius:15px; box-shadow:0px 2px 6px rgba(0,0,0,0.2); text-align:center;">
                <h3>Total Karyawan</h3><h1>{total_emp}</h1>
            </div>
            <div style="flex:1; min-width: 250px; background-color:#FFD200; color:#000; padding:20px; border-radius:15px; box-shadow:0px 2px 6px rgba(0,0,0,0.2); text-align:center;">
                <h3>Sudah Klaim Hari Ini</h3><h1>{today_claims}</h1>
            </div>
            <div style="flex:1; min-width: 250px; background-color:#F2F2F2; color:#000; padding:20px; border-radius:15px; box-shadow:0px 2px 6px rgba(0,0,0,0.2); text-align:center;">
                <h3>Belum Klaim</h3><h1>{not_claimed}</h1>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

        df = get_all_claims()
        if not df.empty:
            st.subheader("Statistik Klaim")
            with st.spinner("Memuat grafik klaim..."):
                fig1 = px.histogram(df, x="claim_date", title="Distribusi Klaim per Hari", color_discrete_sequence=["#FFD200"])
                st.plotly_chart(fig1, use_container_width=True)

                today_claims_df = df[df['claim_date'] == date.today().isoformat()]
                conn = sqlite3.connect(DB_NAME)
                total_emp = pd.read_sql_query("SELECT COUNT(*) as total FROM employees", conn).iloc[0]['total']
                conn.close()
                claimed = len(today_claims_df)
                not_claimed = total_emp - claimed
                donut_df = pd.DataFrame({
                    'Status': ['Sudah Klaim', 'Belum Klaim'],
                    'Jumlah': [claimed, not_claimed]
                })
                fig2 = px.pie(donut_df, values='Jumlah', names='Status', hole=0.5,
                              color='Status', color_discrete_map={'Sudah Klaim': '#FFD200', 'Belum Klaim': '#B0B0B0'},
                              title="Proporsi Karyawan Klaim Hari Ini")
                st.plotly_chart(fig2, use_container_width=True)
            st.success("✅ Grafik berhasil dimuat.")
        else:
            st.info("Belum ada data klaim untuk ditampilkan.")

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
                st.info("✅ Klaim sebelum hari ini telah dihapus.")
                show_toast("Reset klaim harian berhasil!", "#3498DB")
        with colB:
            if st.button("Hapus Semua Data Klaim"):
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("DELETE FROM claims")
                conn.commit()
                conn.close()
                st.warning("⚠️ Semua data klaim dihapus!")
                show_toast("Semua data klaim dihapus!", "#E74C3C")

    elif admin_pass:
        st.error("❌ Password salah.")
        show_toast("Password admin salah!", "#E74C3C")
    else:
        st.info("Masukkan password admin untuk melanjutkan.")

with tab3:
    st.header("Kontak Bantuan")
    st.markdown("""
    <h2 style='color:#FFD200;font-weight:bold;'>Kontak & Bantuan</h2>
    <p>Jika mengalami kendala, silakan hubungi:</p>
    <div style="background-color:#F9F9F9;border-radius:10px;padding:15px;margin-top:15px;">
        <h4>Helmalya RP</h4>
        <p>📧 <a href="mailto:HelmalyaRP@unitedtractors.com">HelmalyaRP@unitedtractors.com</a><br>
        📱 0858 5982 3983</p>
        <a href="https://wa.me/6285859823983" target="_blank">
            <button style="background:#25D366;color:white;border:none;border-radius:6px;padding:6px 10px;cursor:pointer;">💬 Chat via WhatsApp</button>
        </a>
    </div>
    <p style="color:#666;">Jam kerja: 08.00 - 17.00 WIB</p>
    """, unsafe_allow_html=True)
