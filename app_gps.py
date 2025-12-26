import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
import os
from io import BytesIO
import zipfile

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Outreach Camp Data Entry",
    layout="centered"
)

DB_PATH = "outreach.db"
IMAGE_DIR = "uploaded_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

# --------------------------------------------------
# DATABASE INITIALIZATION
# --------------------------------------------------
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
            latitude REAL,
            longitude REAL,
            accuracy REAL,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()

# --------------------------------------------------
# DOCTOR HELPERS
# --------------------------------------------------
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

def is_doctor_used(name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM camp_entries WHERE doctor = ?",
        (name,)
    )
    count = cur.fetchone()[0]
    conn.close()
    return count > 0

def delete_doctor(name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM doctors WHERE name = ?", (name,))
    conn.commit()
    conn.close()

# --------------------------------------------------
# DATA HELPERS
# --------------------------------------------------
def save_entry(data: dict):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(camp_entries)")
    columns = [c[1] for c in cur.fetchall() if c[1] != "id"]

    values = [data.get(col) for col in columns]
    placeholders = ",".join(["?"] * len(values))

    cur.execute(
        f"INSERT INTO camp_entries ({','.join(columns)}) VALUES ({placeholders})",
        values
    )

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
# SESSION STATE (MESSAGES + PREVIEW)
# --------------------------------------------------
if "doctor_msg" not in st.session_state:
    st.session_state.doctor_msg = None

if "last_submission" not in st.session_state:
    st.session_state.last_submission = None

# --------------------------------------------------
# UI
# --------------------------------------------------
st.title("🩺 Outreach Camp Data Entry")

# ---------------- CAMP DETAILS ----------------
st.subheader("Camp Details")
place = st.text_input("Place of Camp")
camp_date = st.date_input("Date of Camp", value=date.today())
administrator = st.text_input("Administrator Name")

doctor = st.selectbox("Doctor Name", ["Select"] + get_doctors())

# ---------------- DOCTOR ADD ----------------
with st.expander("➕ Add New Doctor"):
    new_doctor = st.text_input("Doctor Full Name")
    if st.button("Add Doctor"):
        if not new_doctor.strip():
            st.session_state.doctor_msg = ("warning", "Doctor name cannot be empty.")
        else:
            add_doctor(new_doctor.strip())
            st.session_state.doctor_msg = (
                "success",
                f"Doctor '{new_doctor}' added successfully."
            )
            st.rerun()

# ---------------- DOCTOR DELETE ----------------
with st.expander("🗑️ Delete Doctor"):
    doc_to_delete = st.selectbox(
        "Select Doctor",
        ["Select"] + get_doctors(),
        key="delete_doctor_select"
    )

    if st.button("Delete Doctor"):
        if doc_to_delete == "Select":
            st.session_state.doctor_msg = ("warning", "Please select a doctor.")
        elif is_doctor_used(doc_to_delete):
            st.session_state.doctor_msg = (
                "error",
                "Doctor cannot be deleted because it is already used in records."
            )
        else:
            delete_doctor(doc_to_delete)
            st.session_state.doctor_msg = (
                "success",
                f"Doctor '{doc_to_delete}' deleted successfully."
            )
            st.rerun()

# ---------------- DOCTOR MESSAGE DISPLAY ----------------
if st.session_state.doctor_msg:
    level, msg = st.session_state.doctor_msg
    if level == "success":
        st.success(msg)
    elif level == "warning":
        st.warning(msg)
    elif level == "error":
        st.error(msg)

# ---------------- OTHER DETAILS ----------------
optom = st.text_input("Optom Name")
optom_intern = st.text_input("Optom Intern Name")

# ---------------- OPD ----------------
st.divider()
st.subheader("OPD Count")
c1, c2, c3 = st.columns(3)
opd_m = c1.number_input("Male", 0)
opd_f = c2.number_input("Female", 0)
opd_t = opd_m + opd_f
c3.metric("Total", opd_t)

# ---------------- SURGERY ----------------
st.subheader("Selected for Surgery")
c1, c2, c3 = st.columns(3)
surg_m = c1.number_input("Male ", 0)
surg_f = c2.number_input("Female ", 0)
surg_t = surg_m + surg_f
c3.metric("Total ", surg_t)

# ---------------- HOSPITAL ----------------
st.subheader("Brought to Hospital")
c1, c2, c3 = st.columns(3)
hosp_m = c1.number_input("Male  ", 0)
hosp_f = c2.number_input("Female  ", 0)
hosp_t = hosp_m + hosp_f
c3.metric("Total  ", hosp_t)

# ---------------- MEDICINE ----------------
st.divider()
st.subheader("Medicine Distribution")
c1, c2 = st.columns(2)
ciplox = c1.number_input("Ciplox", 0)
ciplox_d = c2.number_input("Ciplox D", 0)
cmc = c1.number_input("CMC", 0)
fedtive = c2.number_input("Fedtive", 0)
glucose_strips = c1.number_input("Glucose Strips", 0)

# ---------------- SPECTACLES ----------------
st.divider()
spectacles = st.number_input("Spectacles Given", 0)

# ---------------- GPS (AUTO FROM MOBILE) ----------------
st.subheader("📍 Camp Location (Auto from Mobile GPS)")
st.markdown(
    """
    <script>
    navigator.geolocation.getCurrentPosition(
        (pos) => {
            const url = new URL(window.location);
            url.searchParams.set("lat", pos.coords.latitude);
            url.searchParams.set("lon", pos.coords.longitude);
            url.searchParams.set("acc", pos.coords.accuracy);
            window.history.replaceState({}, "", url);
        }
    );
    </script>
    """,
    unsafe_allow_html=True
)

params = st.experimental_get_query_params()
latitude = float(params.get("lat", [0])[0]) if "lat" in params else None
longitude = float(params.get("lon", [0])[0]) if "lon" in params else None
accuracy = float(params.get("acc", [0])[0]) if "acc" in params else None

if latitude and longitude:
    st.success(f"Location captured: {latitude:.6f}, {longitude:.6f}")

# ---------------- PHOTO ----------------
st.subheader("Camp Photo")
photo = st.file_uploader("Upload Camp Photo", ["jpg", "jpeg", "png"])

photo_name = None
if photo:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    photo_name = f"{ts}_{photo.name.replace(' ', '_')}"
    with open(os.path.join(IMAGE_DIR, photo_name), "wb") as f:
        f.write(photo.getbuffer())

# ---------------- SUBMIT ----------------
if st.button("✅ Submit"):
    if not all([place, administrator, optom, optom_intern, doctor != "Select"]):
        st.error("All fields are mandatory.")
        st.stop()

    if hosp_t > surg_t:
        st.error("Hospital total cannot exceed surgery total.")
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
        "latitude": latitude,
        "longitude": longitude,
        "accuracy": accuracy,
        "created_at": datetime.now().isoformat()
    })

    st.session_state.last_submission = {
        "Place": place,
        "Camp Date": camp_date,
        "Doctor": doctor,
        "Latitude": latitude,
        "Longitude": longitude,
        "Photo": photo_name
    }

    st.success("Outreach camp data saved successfully.")

# ---------------- PREVIEW AFTER SUBMIT ----------------
if st.session_state.last_submission:
    st.divider()
    st.subheader("✅ Last Submitted Record (Preview)")
    st.dataframe(
        pd.DataFrame([st.session_state.last_submission]),
        use_container_width=True
    )

# ---------------- ZIP EXPORT ----------------
st.divider()
st.subheader("📦 Export Data (CSV + Images)")

df = load_all_entries().drop(columns=["id"], errors="ignore")

if not df.empty:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr("outreach_data.csv", df.to_csv(index=False))
        for img in df["photo_name"].dropna().unique():
            path = os.path.join(IMAGE_DIR, img)
            if os.path.exists(path):
                zipf.write(path, arcname=f"images/{img}")

    buffer.seek(0)
    zip_name = f"{camp_date}_{place.replace(' ', '_')}.zip"

    st.download_button(
        "Download ZIP (CSV + Images)",
        buffer,
        zip_name,
        "application/zip"
    )
else:
    st.info("No records available yet.")
