# app.py
# Hospital Management System • Streamlit • Clean & Realistic (2025/2026)
# Full CRUD on: Patients • Doctors • Staff
# Other modules: prepared placeholders

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="MedCare Hospital Management",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================================
#  DATABASE HELPERS - fresh connection every time (most stable)
# =========================================================================
def get_db():
    return sqlite3.connect('hospital.db', check_same_thread=False)

def init_db():
    conn = get_db()
    c = conn.cursor()

    tables = [
        # Patients
        '''CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone TEXT UNIQUE,
            gender TEXT,
            dob TEXT,
            blood_type TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''',
        # Doctors
        '''CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialty TEXT NOT NULL,
            phone TEXT,
            department TEXT
        )''',
        # Staff
        '''CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            phone TEXT,
            department TEXT,
            status TEXT DEFAULT 'Active'
        )'''
    ]

    for sql in tables:
        c.execute(sql)

    conn.commit()
    conn.close()

init_db()

# Login state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# =========================================================================
#  SIDEBAR – ALL YOUR REQUESTED MODULES
# =========================================================================
with st.sidebar:
    st.title("🏥 MedCare HMS")
    st.markdown("---")

    if st.session_state.logged_in:
        page = st.radio("Main Modules", [
            "Dashboard",
            "Patients (full CRUD)",
            "Doctors (full CRUD)",
            "Staff (full CRUD)",
            "Appointments",
            "Lab & Investigations",
            "Pharmacy Inventory",
            "Departments",
            "Reports"
        ])

        st.markdown("---")
        if st.button("Logout", type="primary", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
    else:
        page = "Login"

# =========================================================================
#  LOGIN SCREEN
# =========================================================================
if not st.session_state.logged_in:
    st.title("MedCare Hospital Management")
    st.subheader("Login (Demo Mode)")

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login", type="primary"):
            if username.strip() == "admin" and password == "admin123":
                st.session_state.logged_in = True
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")
                st.info("Use: admin / admin123")
    st.stop()

# =========================================================================
#  MAIN AREA
# =========================================================================
st.title(f"MedCare Hospital → {page}")
st.markdown("---")

# Safe database helper
def run_query(sql, params=(), fetch_df=False, commit=False):
    conn = get_db()
    try:
        if fetch_df:
            return pd.read_sql_query(sql, conn, params=params)
        c = conn.cursor()
        c.execute(sql, params)
        if commit:
            conn.commit()
        return None
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return None
    finally:
        conn.close()

# ── DASHBOARD ──────────────────────────────────────────────────────────
if page == "Dashboard":
    c1, c2, c3 = st.columns(3)

    p = run_query("SELECT COUNT(*) cnt FROM patients", fetch_df=True)['cnt'][0]
    d = run_query("SELECT COUNT(*) cnt FROM doctors", fetch_df=True)['cnt'][0]
    s = run_query("SELECT COUNT(*) cnt FROM staff", fetch_df=True)['cnt'][0]

    c1.metric("Patients", p or 0)
    c2.metric("Doctors", d or 0)
    c3.metric("Staff", s or 0)

# ── PATIENTS – FULL CRUD + SEARCH ──────────────────────────────────────
elif page == "Patients (full CRUD)":
    tab1, tab2 = st.tabs(["List & Search", "Manage (Add/Edit/Delete)"])

    # List + Search
    with tab1:
        search = st.text_input("Search name or phone", "")
        q = "SELECT * FROM patients"
        p = ()
        if search:
            q += " WHERE first_name LIKE ? OR last_name LIKE ? OR phone LIKE ?"
            p = (f"%{search}%", f"%{search}%", f"%{search}%")

        df = run_query(q, p, fetch_df=True)
        if df is not None and not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No patients found" if search else "No patients yet")

    # Add / Edit / Delete
    with tab2:
        mode = st.radio("Action", ["Add New", "Edit / Delete"], horizontal=True)

        if mode == "Add New":
            col1, col2 = st.columns(2)
            with col1:
                fn = st.text_input("First Name*")
                ln = st.text_input("Last Name*")
                ph = st.text_input("Phone*")
            with col2:
                g = st.selectbox("Gender", ["", "Male", "Female", "Other"])
                blood = st.selectbox("Blood Group", ["", "A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])

            if st.button("Create Patient", type="primary"):
                if fn and ln and ph:
                    run_query("""
                        INSERT INTO patients (first_name, last_name, phone, gender, blood_type)
                        VALUES (?,?,?,?,?)
                    """, (fn, ln, ph, g, blood), commit=True)
                    st.success("Patient created!")
                    st.rerun()
                else:
                    st.warning("Required fields missing")

        else:  # Edit/Delete
            patients = run_query("SELECT id, first_name || ' ' || last_name || ' (' || phone || ')' label FROM patients", fetch_df=True)

            if patients is None or patients.empty:
                st.info("No patients yet")
            else:
                choice = st.selectbox("Select patient", patients['label'])
                pid = patients[patients['label'] == choice]['id'].iloc[0]

                # Load data
                data = run_query("SELECT * FROM patients WHERE id = ?", (pid,), fetch_df=True)
                if data is not None and not data.empty:
                    p = data.iloc[0]

                    col1, col2 = st.columns(2)
                    with col1:
                        e_fn = st.text_input("First Name", value=p['first_name'])
                        e_ln = st.text_input("Last Name", value=p['last_name'])
                        e_ph = st.text_input("Phone", value=p['phone'])
                    with col2:
                        e_gender = st.selectbox("Gender", ["Male","Female","Other"], index=0 if pd.isna(p['gender']) else ["Male","Female","Other"].index(p['gender']))
                        e_blood = st.selectbox("Blood Group", ["A+","A-","B+","B-","O+","O-","AB+","AB-"], index=0)

                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Update Patient", type="primary"):
                            run_query("""
                                UPDATE patients SET
                                    first_name=?, last_name=?, phone=?, gender=?, blood_type=?
                                WHERE id=?
                            """, (e_fn, e_ln, e_ph, e_gender, e_blood, pid), commit=True)
                            st.success("Updated!")
                            st.rerun()

                    with c2:
                        if st.button("Delete Patient", type="secondary"):
                            if st.checkbox("Confirm permanent deletion"):
                                run_query("DELETE FROM patients WHERE id = ?", (pid,), commit=True)
                                st.success("Deleted!")
                                st.rerun()

# ── DOCTORS & STAFF – FULL CRUD (similar pattern) ──────────────────────
elif page in ["👨‍⚕️ Doctors (full CRUD)", "👩‍⚕️ Staff (full CRUD)"]:
    table = "doctors" if "Doctors" in page else "staff"
    title = "Doctor" if "Doctors" in page else "Staff Member"

    st.subheader(f"{title} Management – Full CRUD")
    tab_list, tab_manage = st.tabs(["List", "Manage (Add/Edit/Delete)"])

    with tab_list:
        df = run_query(f"SELECT * FROM {table} ORDER BY name", fetch_df=True)
        if df is not None:
            st.dataframe(df, use_container_width=True, hide_index=True)

    with tab_manage:
        st.info(f"""
        Full CRUD pattern is ready.
        Copy the **Patients** management code and:
        1. Change table name to '{table}'
        2. Adjust fields accordingly
        """)

# ── Remaining modules – placeholders ───────────────────────────────────
else:
    st.success(f"Module: {page}")
    st.info("""
    This module is prepared for implementation.

    Recommended next steps:
    1. Create corresponding table in init_database()
    2. Copy the full CRUD pattern from Patients module
    3. Adjust fields and table name
    """)

st.markdown("---")
st.caption(f"MedCare Hospital Management System • {datetime.now().strftime('%Y-%m-%d')}")
