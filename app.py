import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
import os
import base64
from pathlib import Path

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="Outreach Camp Data Entry", layout="centered")

DB_PATH = "outreach.db"
IMAGE_DIR = "uploaded_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# --------------------------------------------------
# DATABASE
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
            place TEXT,
            camp_date TEXT,
            administrator TEXT,
            doctor TEXT,
            optom TEXT,
            optom_intern TEXT,
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
            glucose_strips INTEGER,
            spectacles INTEGER,
            photo_name TEXT,
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

def save_entry(data: dict):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(camp_entries)")
    cols = [c[1] for c in cur.fetchall() if c[1] != "id"]

    values = [data.get(c) for c in cols]
    placeholders = ",".join(["?"] * len(values))
    columns = ",".join(cols)

    cur.execute(f"INSERT INTO camp_entries ({columns}) VALUES ({placeholders})", values)
    conn.commit()
    conn.close()

def load_all_entries():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM camp_entries", conn)
    conn.close()
    return df

# --------------------------------------------------
# IMAGE LINK (DATA URL)
# --------------------------------------------------
def image_to_data_url(filename):
    if not filename:
        return ""
    path = Path(IMAGE_DIR) / filename
    if not path.exists():
        return ""

    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    ext = path.suffix.replace(".", "").lower()
    return f"data:image/{ext};base64,{encoded}"

# --------------------------------------------------
# INIT
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

doctor = st.selectbox("Doctor Name", ["Select"] + get_doctors())

with st.expander("➕ Add New Doctor"):
    new_doc = st.text_input("Doctor Full Name")
    if st.button("Add Doctor"):
        if new_doc.strip():
            add_doctor(new_doc.strip())
            st.success(f"Doctor '{new_doc}' added successfully.")
            st.rerun()

optom = st.text_input("Optom Name")
optom_intern = st.text_input("Optom Intern Name")

st.divider()
st.subheader("OPD Count")
c1, c2, c3 = st.columns(3)
opd_m = c1.number_input("Male", 0)
opd_f = c2.number_input("Female", 0)
opd_t = opd_m + opd_f
c3.metric("Total", opd_t)

st.subheader("Selected for Surgery")
c1, c2, c3 = st.columns(3)
surg_m = c1.number_input("Male ", 0)
surg_f = c2.number_input("Female ", 0)
surg_t = surg_m + surg_f
c3.metric("Total ", surg_t)

st.subheader("Brought to Hospital")
c1, c2, c3 = st.columns(3)
hosp_m = c1.number_input("Male  ", 0)
hosp_f = c2.number_input("Female  ", 0)
hosp_t = hosp_m + hosp_f
c3.metric("Total  ", hosp_t)

st.divider()
st.subheader("Medicine Distribution")
c1, c2 = st.columns(2)
ciplox = c1.number_input("Ciplox", 0)
ciplox_d = c2.number_input("Ciplox D", 0)
cmc = c1.number_input("CMC", 0)
fedtive = c2.number_input("Fedtive", 0)
glucose_strips = c1.number_input("Glucose Strips", 0)

st.divider()
spectacles = st.number_input("Spectacles Given", 0)

st.subheader("Camp Photo")
photo = st.file_uploader("Upload Camp Photo", type=["jpg", "jpeg", "png"])

photo_name = None
if photo:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    photo_name = f"{ts}_{photo.name.replace(' ', '_')}"
    with open(os.path.join(IMAGE_DIR, photo_name), "wb") as f:
        f.write(photo.getbuffer())

# --------------------------------------------------
# SUBMIT
# --------------------------------------------------
if st.button("✅ Submit"):
    if not all([place, administrator, optom, optom_intern, doctor != "Select"]):
        st.error("All fields are mandatory.")
        st.stop()

    if hosp_t > surg_t:
        st.error("Brought to Hospital total cannot exceed Selected for Surgery.")
        st.stop()

    save_entry({
        "place": place,
        "camp_date": str(camp_date),
        "administrator": administrator,
        "doctor": doctor,
        "optom": optom,
        "optom_intern": optom_intern,
        "opd_m": opd_m,
        "opd_f": opd_f,
        "opd_t": opd_t,
        "surg_m": surg_m,
        "surg_f": surg_f,
        "surg_t": surg_t,
        "hosp_m": hosp_m,
        "hosp_f": hosp_f,
        "hosp_t": hosp_t,
        "ciplox": ciplox,
        "ciplox_d": ciplox_d,
        "cmc": cmc,
        "fedtive": fedtive,
        "glucose_strips": glucose_strips,
        "spectacles": spectacles,
        "photo_name": photo_name,
        "created_at": datetime.now().isoformat()
    })

    st.success("Data saved successfully.")

# --------------------------------------------------
# VIEW + EXPORT
# --------------------------------------------------
st.divider()
st.subheader("📋 Saved Records")

df = load_all_entries()
if not df.empty:
    df["photo_download_link"] = df["photo_name"].apply(image_to_data_url)

    st.dataframe(df.drop(columns=["id"], errors="ignore"), use_container_width=True)

    safe_place = place.replace(" ", "_") if place else "camp"
    filename = f"{camp_date}_{safe_place}.csv"

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, filename, "text/csv")
else:
    st.info("No records available yet.")
