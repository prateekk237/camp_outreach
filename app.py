import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Outreach Camp Data Entry",
    layout="centered"
)

DB_PATH = "outreach.db"

# --------------------------------------------------
# DATABASE FUNCTIONS
# --------------------------------------------------
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS camp_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            place TEXT NOT NULL,
            camp_date TEXT NOT NULL,
            administrator TEXT NOT NULL,
            doctor TEXT NOT NULL,
            optom TEXT NOT NULL,
            optom_intern TEXT NOT NULL,

            opd_m INTEGER,
            opd_f INTEGER,
            opd_t INTEGER,

            surg_m INTEGER,
            surg_f INTEGER,
            surg_t INTEGER,

            hosp_m INTEGER,
            hosp_f INTEGER,
            hosp_t INTEGER,

            ciplox INTEGER,
            ciplox_d INTEGER,
            cmc INTEGER,
            fedtive INTEGER,

            spectacles INTEGER,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()

def get_doctors():
    conn = get_connection()
    df = pd.read_sql("SELECT name FROM doctors ORDER BY name", conn)
    conn.close()
    return df["name"].tolist()

def add_doctor(name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO doctors (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()

def save_entry(values):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO camp_entries (
            place, camp_date, administrator, doctor, optom, optom_intern,
            opd_m, opd_f, opd_t,
            surg_m, surg_f, surg_t,
            hosp_m, hosp_f, hosp_t,
            ciplox, ciplox_d, cmc, fedtive,
            spectacles, created_at
        ) VALUES (
            ?,?,?,?,?,?,
            ?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?
        )
    """, values)
    conn.commit()
    conn.close()

def load_all_entries():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM camp_entries", conn)
    conn.close()
    return df

# --------------------------------------------------
# INITIALIZE DATABASE
# --------------------------------------------------
init_db()

# --------------------------------------------------
# UI
# --------------------------------------------------
st.title("🩺 Outreach Camp Data Entry")

st.subheader("Camp Details")
place = st.text_input("Place of Camp")
camp_date = st.date_input("Date of Camp", value=date.today())
administrator = st.text_input("Administrator Name")

doctor_list = get_doctors()
doctor = st.selectbox("Doctor Name", ["Select"] + doctor_list)

with st.expander("➕ Add New Doctor"):
    new_doctor = st.text_input("Doctor Full Name")
    if st.button("Add Doctor"):
        if new_doctor.strip():
            add_doctor(new_doctor.strip())
            st.success("Doctor added")
            st.rerun()

optom = st.text_input("Optom Name")
optom_intern = st.text_input("Optom Intern Name")

st.divider()
st.subheader("OPD Count")
c1, c2, c3 = st.columns(3)
opd_m = c1.number_input("Male", min_value=0)
opd_f = c2.number_input("Female", min_value=0)
opd_t = opd_m + opd_f
c3.metric("Total", opd_t)

st.subheader("Selected for Surgery")
c1, c2, c3 = st.columns(3)
surg_m = c1.number_input("Male ", min_value=0)
surg_f = c2.number_input("Female ", min_value=0)
surg_t = surg_m + surg_f
c3.metric("Total ", surg_t)

st.subheader("Brought to Hospital")
c1, c2, c3 = st.columns(3)
hosp_m = c1.number_input("Male  ", min_value=0)
hosp_f = c2.number_input("Female  ", min_value=0)
hosp_t = hosp_m + hosp_f
c3.metric("Total  ", hosp_t)

st.divider()
st.subheader("Medicine Distribution")
c1, c2 = st.columns(2)
ciplox = c1.number_input("Ciplox", min_value=0)
ciplox_d = c2.number_input("Ciplox D", min_value=0)
cmc = c1.number_input("CMC", min_value=0)
fedtive = c2.number_input("Fedtive", min_value=0)

st.divider()
spectacles = st.number_input("Spectacles Given", min_value=0)

# --------------------------------------------------
# SUBMIT
# --------------------------------------------------
if st.button("✅ Submit"):
    if not all([
        place.strip(),
        administrator.strip(),
        optom.strip(),
        optom_intern.strip(),
        doctor != "Select"
    ]):
        st.error("All fields are mandatory.")
    else:
        save_entry((
            place,
            str(camp_date),
            administrator,
            doctor,
            optom,
            optom_intern,
            opd_m, opd_f, opd_t,
            surg_m, surg_f, surg_t,
            hosp_m, hosp_f, hosp_t,
            ciplox, ciplox_d, cmc, fedtive,
            spectacles,
            datetime.now().isoformat()
        ))
        st.success("Data saved successfully.")

# --------------------------------------------------
# EXPORT
# --------------------------------------------------
st.divider()
st.subheader("📤 Export Data")

df = load_all_entries()
if not df.empty:
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download CSV",
        csv,
        "outreach_camp_data.csv",
        "text/csv"
    )
else:
    st.info("No records available yet.")
