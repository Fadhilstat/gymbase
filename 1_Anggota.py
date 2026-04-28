import streamlit as st
import sys, os
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)).replace(os.sep+'pages',''))
from db import q, run

st.set_page_config(page_title="Anggota · GymBase", page_icon="👤", layout="wide")
st.title("👤 Manajemen Anggota")
st.divider()

# ── Sidebar filters ────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔽 Filter")
    gender_opt = ["Semua", "L", "P"]
    gender_sel = st.selectbox("Gender", gender_opt)

    daerah_list = q("SELECT DISTINCT asal_daerah FROM anggota ORDER BY asal_daerah")
    daerah_opt  = ["Semua"] + daerah_list['asal_daerah'].tolist()
    daerah_sel  = st.selectbox("Asal Daerah", daerah_opt)

# ── Search ─────────────────────────────────────────────────────────────────────
search = st.text_input("🔍 Cari nama anggota", placeholder="Ketik nama...")

# ── Build query ───────────────────────────────────────────────────────────────
sql = """
    SELECT a.anggota_id, a.nama, a.usia, a.gender,
           a.email, a.no_telp, a.asal_daerah, a.tgl_daftar,
           m.tipe AS membership, m.status
    FROM   anggota a
    LEFT   JOIN membership m ON a.anggota_id = m.anggota_id
    WHERE  1=1
"""
params = []
if search:
    sql += " AND a.nama LIKE ?"
    params.append(f"%{search}%")
if gender_sel != "Semua":
    sql += " AND a.gender = ?"
    params.append(gender_sel)
if daerah_sel != "Semua":
    sql += " AND a.asal_daerah = ?"
    params.append(daerah_sel)
sql += " ORDER BY a.tgl_daftar DESC"

df = q(sql, tuple(params))

# ── Metrics ───────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
c1.metric("Total Ditampilkan", len(df))
c2.metric("Gender L", int((df['gender'] == 'L').sum()))
c3.metric("Gender P", int((df['gender'] == 'P').sum()))

# ── Table ─────────────────────────────────────────────────────────────────────
st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()

# ── Tambah Anggota ────────────────────────────────────────────────────────────
with st.expander("➕ Tambah Anggota Baru"):
    with st.form("form_anggota"):
        c1, c2 = st.columns(2)
        nama       = c1.text_input("Nama *")
        usia       = c2.number_input("Usia *", 10, 100, 25)
        gender     = c1.selectbox("Gender *", ["L", "P"])
        asal       = c2.selectbox("Asal Daerah *", [
            'Jakarta','Depok','Bogor','Tangerang','Bekasi',
            'Bandung','Surabaya','Yogyakarta','Semarang','Medan'])
        email      = c1.text_input("Email")
        no_telp    = c2.text_input("No. Telepon")
        tgl_daftar = st.date_input("Tanggal Daftar *", value=date.today())
        submitted  = st.form_submit_button("Simpan Anggota", type="primary")

    if submitted:
        if not nama.strip():
            st.error("Nama tidak boleh kosong.")
        else:
            new_id = int(q("SELECT COALESCE(MAX(anggota_id),0)+1 AS nid FROM anggota").iloc[0]['nid'])
            run("""
                INSERT INTO anggota
                    (anggota_id, nama, usia, gender, email, no_telp,
                     asal_daerah, tgl_daftar)
                VALUES (?,?,?,?,?,?,?,?)
            """, (new_id, nama.strip(), int(usia), gender,
                  email.strip(), no_telp.strip(),
                  asal, str(tgl_daftar)))
            st.success(f"✅ Anggota **{nama}** berhasil ditambahkan (ID: {new_id})")
            st.rerun()
