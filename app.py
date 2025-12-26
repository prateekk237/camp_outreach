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
# DATABASE
# --------------------------------------------------
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Doctors table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    # Camp entries base table
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
            spectacles INTEGER,
            created_at TEXT
        )
    """)

    # ---- SCHEMA MIGRATION (SAFE) ----
    cur.execute("PRAGMA table_info(camp_entries)")
    existing_cols = {row[1] for row in cur.fetchall()}

    if "glucose_strips" not in existing_cols:
        cur.execute("ALTER TABLE camp_entries ADD COLUMN glucose_strips INTEGER DEFAULT 0")

    if "photo_name" not in existing_cols:
        cur.execute("ALTER TABLE camp_entries ADD COLUMN photo_name TEXT")

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

def save_entry(data_dict):
    conn = get_connection()
    cur = conn.cursor()

    # Get real columns from DB
    cur.execute("PRAGMA table_info(camp_entries)")
    db_columns = [row[1] for row in cur.fetchall() if row[1] != "id"]

    # Align values to DB schema
    values = [data_dict.get(col) for col in db_columns]

    placeholders = ",".join(["?"] * len(values))
    columns = ",".join(db_columns)

    sql = f"INSERT INTO camp_entries ({columns}) VALUES ({placeholders})"
    cur.execute(sql, values)

    conn.commit()
    conn.close()

def load_all_entries():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM camp_entries", conn)
    conn.close()
    return df

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

doctor_list = get_doctors()
doctor = st.selectbox("Doctor Name", ["Select"] + doctor_list)

with st.expander("➕ Add New Doctor"):
    new_doctor = st.text_input("Doctor Full Name")
    if st.button("Add Doctor"):
        if new_doctor.strip():
            add_doctor(new_doctor.strip())
            st.success(f"Doctor '{new_doctor}' added successfully.")
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
glucose_strips = c1.number_input("Glucose Strips", min_value=0)

st.divider()
spectacles = st.number_input("Spectacles Given", min_value=0)

st.subheader("Camp Photo (Optional)")
photo = st.file_uploader(
    "Upload Camp Photo (Geo-tagged if available)",
    type=["jpg", "jpeg", "png"]
)
photo_name = photo.name if photo else None

# --------------------------------------------------
# PREVIEW
# --------------------------------------------------
st.divider()
st.subheader("🔍 Preview Submission")

preview_df = pd.DataFrame([{
    "Place": place,
    "Camp Date": camp_date,
    "Doctor": doctor,
    "OPD Total": opd_t,
    "Surgery Total": surg_t,
    "Hospital Total": hosp_t,
    "Glucose Strips": glucose_strips,
    "Spectacles": spectacles,
    "Photo": photo_name
}])

st.dataframe(preview_df, use_container_width=True)

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
        st.stop()

    if hosp_t > surg_t:
        st.error("Brought to Hospital total cannot exceed Selected for Surgery total.")
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

    st.success("Outreach camp data saved successfully.")

# --------------------------------------------------
# VIEW + EXPORT
# --------------------------------------------------
st.divider()
st.subheader("📋 Saved Records")

df = load_all_entries()
df = df.drop(columns=["id"], errors="ignore")

if df.empty:
    st.info("No records available yet.")
else:
    with st.expander("View Saved Data"):
        st.dataframe(df, use_container_width=True, hide_index=True)

    safe_place = place.replace(" ", "_") if place else "camp"
    filename = f"{camp_date}_{safe_place}.csv"

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download CSV",
        csv,
        filename,
        "text/csv"
    )
