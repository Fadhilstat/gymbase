import streamlit as st
import plotly.express as px
import sys, os
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)).replace(os.sep+'pages',''))
from db import q, run

st.set_page_config(page_title="Sesi Latihan · GymBase", page_icon="📅", layout="wide")
st.title("📅 Sesi Latihan")
st.divider()

# ── Sidebar filters ────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔽 Filter")
    kelas_list = q("SELECT kelas_id, nama_kelas FROM kelas ORDER BY nama_kelas")
    kelas_opts = ["Semua"] + kelas_list['nama_kelas'].tolist()
    kelas_sel  = st.selectbox("Kelas", kelas_opts)
    tgl_from   = st.date_input("Dari tanggal", value=date(2022,1,1))
    tgl_to     = st.date_input("Sampai tanggal", value=date.today())

# ── Build query ───────────────────────────────────────────────────────────────
sql = """
    SELECT s.sesi_id, a.nama AS anggota, k.nama_kelas,
           k.tipe_latihan, t.nama AS trainer,
           s.tanggal, s.durasi_menit,
           s.kalori_terbakar, s.avg_bpm
    FROM   sesi_latihan s
    JOIN   anggota a ON s.anggota_id = a.anggota_id
    JOIN   kelas   k ON s.kelas_id   = k.kelas_id
    JOIN   trainer t ON k.trainer_id = t.trainer_id
    WHERE  s.tanggal BETWEEN ? AND ?
"""
params = [str(tgl_from), str(tgl_to)]

if kelas_sel != "Semua":
    sql += " AND k.nama_kelas = ?"
    params.append(kelas_sel)
sql += " ORDER BY s.tanggal DESC"

df = q(sql, tuple(params))

# ── Metrics ───────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Sesi",          len(df))
c2.metric("Rata-rata Durasi",    f"{df['durasi_menit'].mean():.0f} mnt"    if not df.empty else "-")
c3.metric("Avg Kalori Terbakar", f"{df['kalori_terbakar'].mean():.0f} kal" if not df.empty else "-")
c4.metric("Avg BPM",             f"{df['avg_bpm'].mean():.0f}"             if not df.empty else "-")

# ── Chart ─────────────────────────────────────────────────────────────────────
if not df.empty:
    df_chart = df.groupby('tipe_latihan').agg(
        avg_kalori=('kalori_terbakar','mean'),
        total_sesi=('sesi_id','count')
    ).reset_index()
    fig = px.bar(df_chart, x='tipe_latihan', y='avg_kalori',
                 title="Rata-rata Kalori per Tipe Kelas",
                 color='tipe_latihan',
                 labels={'tipe_latihan':'Tipe','avg_kalori':'Avg Kalori'},
                 color_discrete_sequence=px.colors.qualitative.Safe)
    fig.update_layout(margin=dict(t=40,b=10), height=260, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ── Table ─────────────────────────────────────────────────────────────────────
st.subheader("📋 Log Sesi Latihan")
st.dataframe(df, use_container_width=True, hide_index=True)
st.divider()

# ── Tambah Sesi ───────────────────────────────────────────────────────────────
with st.expander("➕ Tambah Sesi Latihan Baru"):
    df_anggota = q("SELECT anggota_id, nama FROM anggota ORDER BY nama")
    df_kelas   = q("SELECT kelas_id, nama_kelas, tipe_latihan FROM kelas ORDER BY nama_kelas")

    with st.form("form_sesi"):
        c1, c2 = st.columns(2)
        anggota_nama = c1.selectbox("Anggota *", df_anggota['nama'].tolist())
        kelas_nama   = c2.selectbox("Kelas *",   df_kelas['nama_kelas'].tolist())
        tanggal      = c1.date_input("Tanggal *", value=date.today())
        durasi       = c2.number_input("Durasi (menit) *", 10, 300, 60)
        kalori       = c1.number_input("Kalori Terbakar *", 50, 2000, 300)
        avg_bpm      = c2.number_input("Avg BPM *", 50, 220, 130)
        submitted    = st.form_submit_button("Simpan Sesi", type="primary")

    if submitted:
        aid = int(df_anggota.loc[df_anggota['nama']==anggota_nama,'anggota_id'].values[0])
        kid = int(df_kelas.loc[df_kelas['nama_kelas']==kelas_nama,'kelas_id'].values[0])
        new_id = int(q("SELECT COALESCE(MAX(sesi_id),0)+1 AS nid FROM sesi_latihan").iloc[0]['nid'])
        run("""
            INSERT INTO sesi_latihan
                (sesi_id, anggota_id, kelas_id, tanggal,
                 durasi_menit, kalori_terbakar, avg_bpm)
            VALUES (?,?,?,?,?,?,?)
        """, (new_id, aid, kid, str(tanggal), int(durasi), int(kalori), int(avg_bpm)))
        st.success(f"✅ Sesi latihan berhasil ditambahkan (ID: {new_id})")
        st.rerun()
