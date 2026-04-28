import streamlit as st
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)).replace(os.sep+'pages',''))
from db import q

st.set_page_config(page_title="Membership · GymBase", page_icon="💳", layout="wide")
st.title("💳 Data Membership")
st.divider()

# ── Sidebar filters ────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔽 Filter")
    tipe_sel   = st.multiselect("Tipe Membership",
                                ["Basic","Standard","Premium","VIP"],
                                default=["Basic","Standard","Premium","VIP"])
    status_sel = st.radio("Status", ["Semua", "Aktif", "Expired"])

# ── Build query ───────────────────────────────────────────────────────────────
sql = """
    SELECT m.membership_id, a.nama AS anggota, a.gender,
           m.tipe, m.tgl_mulai, m.tgl_selesai,
           m.biaya_bulanan, m.status
    FROM   membership m
    JOIN   anggota a ON m.anggota_id = a.anggota_id
    WHERE  m.tipe IN ({})
""".format(','.join('?' * len(tipe_sel)))

params = list(tipe_sel)
if status_sel != "Semua":
    sql += " AND m.status = ?"
    params.append(status_sel)
sql += " ORDER BY m.tgl_mulai DESC"

df = q(sql, tuple(params)) if tipe_sel else q("SELECT * FROM membership LIMIT 0")

# ── Metrics ───────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Ditampilkan", len(df))
c2.metric("Aktif",   int((df['status']=='Aktif').sum())   if not df.empty else 0)
c3.metric("Expired", int((df['status']=='Expired').sum()) if not df.empty else 0)
total_biaya = int(df['biaya_bulanan'].sum()) if not df.empty else 0
c4.metric("Total Biaya",  f"Rp {total_biaya:,}")

# ── Charts ────────────────────────────────────────────────────────────────────
if not df.empty:
    col_l, col_r = st.columns(2)
    with col_l:
        df_pie = df.groupby('tipe').size().reset_index(name='jumlah')
        fig = px.pie(df_pie, names='tipe', values='jumlah',
                     title="Distribusi Tipe Membership",
                     color_discrete_sequence=px.colors.sequential.Greens_r,
                     hole=0.35)
        fig.update_layout(margin=dict(t=40,b=10), height=260)
        st.plotly_chart(fig, use_container_width=True)
    with col_r:
        df_bar = df.groupby(['tipe','status']).size().reset_index(name='jumlah')
        fig2 = px.bar(df_bar, x='tipe', y='jumlah', color='status',
                      title="Aktif vs Expired per Tipe",
                      barmode='group',
                      color_discrete_map={'Aktif':'#2d6a4f','Expired':'#b5c4b1'})
        fig2.update_layout(margin=dict(t=40,b=10), height=260)
        st.plotly_chart(fig2, use_container_width=True)

# ── Table ─────────────────────────────────────────────────────────────────────
st.subheader("📋 Daftar Membership")
st.dataframe(df, use_container_width=True, hide_index=True)
