import streamlit as st
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import q, db_exists

st.set_page_config(
    page_title="GymBase",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 2rem; }
.section-title { font-size: 1.05rem; font-weight: 600;
                 margin: 1.2rem 0 0.4rem; color: #1b4332; }
</style>
""", unsafe_allow_html=True)

# ── Guard ─────────────────────────────────────────────────────────────────────
if not db_exists():
    st.error("⚠️  Database belum ditemukan. Jalankan `gymbase_colab_final.py` "
             "di Google Colab terlebih dahulu, lalu taruh `gym_database.sqlite` "
             "di folder yang sama dengan `app.py`.")
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🏋️ GymBase — Dashboard")
st.caption("Mini Project Database untuk Sains Data · SCST602013")
st.divider()

# ── KPI Metrics ───────────────────────────────────────────────────────────────
kpi = q("""
    SELECT
        (SELECT COUNT(*) FROM anggota)                                    AS total_anggota,
        (SELECT COUNT(*) FROM membership WHERE status = 'Aktif')          AS aktif,
        (SELECT COALESCE(SUM(jumlah),0) FROM pembayaran
         WHERE  status_bayar = 'Lunas')                                   AS pendapatan,
        (SELECT COUNT(*) FROM sesi_latihan)                               AS total_sesi
""").iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("👤 Total Anggota",       f"{int(kpi.total_anggota):,}")
c2.metric("✅ Membership Aktif",    f"{int(kpi.aktif):,}")
c3.metric("💰 Total Pendapatan",    f"Rp {int(kpi.pendapatan):,}")
c4.metric("🏃 Total Sesi Latihan", f"{int(kpi.total_sesi):,}")

st.divider()

# ── Row 1: charts ─────────────────────────────────────────────────────────────
col_l, col_r = st.columns([3, 2])

with col_l:
    st.markdown('<p class="section-title">📅 Pendaftaran Anggota Baru per Bulan</p>',
                unsafe_allow_html=True)
    df_trend = q("""
        SELECT strftime('%Y-%m', tgl_daftar) AS bulan,
               COUNT(*) AS anggota_baru
        FROM   anggota
        GROUP  BY bulan
        ORDER  BY bulan
    """)
    if not df_trend.empty:
        fig = px.bar(df_trend, x='bulan', y='anggota_baru',
                     labels={'bulan': 'Bulan', 'anggota_baru': 'Anggota Baru'},
                     color_discrete_sequence=['#2d6a4f'])
        fig.update_layout(margin=dict(t=10, b=10), height=280)
        st.plotly_chart(fig, use_container_width=True)

with col_r:
    st.markdown('<p class="section-title">💳 Distribusi Tipe Membership</p>',
                unsafe_allow_html=True)
    df_mem = q("""
        SELECT tipe, COUNT(*) AS jumlah
        FROM   membership
        GROUP  BY tipe
    """)
    if not df_mem.empty:
        fig2 = px.pie(df_mem, names='tipe', values='jumlah',
                      color_discrete_sequence=px.colors.sequential.Greens_r,
                      hole=0.4)
        fig2.update_layout(margin=dict(t=10, b=10), height=280,
                           legend=dict(orientation='h', y=-0.15))
        st.plotly_chart(fig2, use_container_width=True)

# ── Row 2: recent members ─────────────────────────────────────────────────────
st.markdown('<p class="section-title">🆕 10 Anggota Terbaru</p>',
            unsafe_allow_html=True)
df_recent = q("""
    SELECT a.anggota_id, a.nama, a.usia, a.gender,
           a.asal_daerah, a.tgl_daftar,
           m.tipe AS membership, m.status
    FROM   anggota a
    JOIN   membership m ON a.anggota_id = m.anggota_id
    ORDER  BY a.tgl_daftar DESC
    LIMIT  10
""")
st.dataframe(df_recent, use_container_width=True, hide_index=True)

# ── Row 3: top trainer ────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)
with col_a:
    st.markdown('<p class="section-title">🏆 Top 5 Trainer (Total Sesi)</p>',
                unsafe_allow_html=True)
    df_trainer = q("""
        SELECT t.nama AS trainer, t.spesialisasi,
               COUNT(s.sesi_id) AS total_sesi
        FROM   trainer t
        JOIN   kelas k        ON t.trainer_id = k.trainer_id
        JOIN   sesi_latihan s ON k.kelas_id   = s.kelas_id
        GROUP  BY t.trainer_id
        ORDER  BY total_sesi DESC
        LIMIT  5
    """)
    st.dataframe(df_trainer, use_container_width=True, hide_index=True)

with col_b:
    st.markdown('<p class="section-title">🔥 Top 5 Kelas (Avg Kalori)</p>',
                unsafe_allow_html=True)
    df_kelas = q("""
        SELECT k.nama_kelas, k.tipe_latihan,
               ROUND(AVG(s.kalori_terbakar), 0) AS avg_kalori,
               COUNT(s.sesi_id) AS total_sesi
        FROM   kelas k
        JOIN   sesi_latihan s ON k.kelas_id = s.kelas_id
        GROUP  BY k.kelas_id
        ORDER  BY avg_kalori DESC
        LIMIT  5
    """)
    st.dataframe(df_kelas, use_container_width=True, hide_index=True)
