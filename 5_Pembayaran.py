import streamlit as st
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)).replace(os.sep+'pages',''))
from db import q

st.set_page_config(page_title="Pembayaran · GymBase", page_icon="💰", layout="wide")
st.title("💰 Riwayat Pembayaran")
st.divider()

# ── Sidebar filters ────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔽 Filter")
    metode_opts = ["Semua","Transfer Bank","QRIS","Kartu Kredit","Tunai","Dompet Digital"]
    metode_sel  = st.selectbox("Metode Bayar", metode_opts)
    status_opts = ["Semua","Lunas","Pending","Gagal"]
    status_sel  = st.selectbox("Status Bayar", status_opts)
    bulan_sel   = st.text_input("Filter Bulan (YYYY-MM)", placeholder="mis: 2023-06")

# ── Build query ───────────────────────────────────────────────────────────────
sql = """
    SELECT p.pembayaran_id, a.nama AS anggota,
           m.tipe AS membership, p.tgl_bayar,
           p.jumlah, p.metode, p.status_bayar
    FROM   pembayaran p
    JOIN   membership m ON p.membership_id = m.membership_id
    JOIN   anggota    a ON m.anggota_id    = a.anggota_id
    WHERE  1=1
"""
params = []
if metode_sel != "Semua":
    sql += " AND p.metode = ?"
    params.append(metode_sel)
if status_sel != "Semua":
    sql += " AND p.status_bayar = ?"
    params.append(status_sel)
if bulan_sel.strip():
    sql += " AND strftime('%Y-%m', p.tgl_bayar) = ?"
    params.append(bulan_sel.strip())
sql += " ORDER BY p.tgl_bayar DESC"

df = q(sql, tuple(params))

# ── Metrics ───────────────────────────────────────────────────────────────────
lunas   = df[df['status_bayar']=='Lunas']['jumlah'].sum()   if not df.empty else 0
pending = df[df['status_bayar']=='Pending']['jumlah'].sum() if not df.empty else 0
gagal   = df[df['status_bayar']=='Gagal']['jumlah'].sum()   if not df.empty else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Transaksi",   len(df))
c2.metric("💚 Pendapatan (Lunas)",  f"Rp {int(lunas):,}")
c3.metric("🟡 Pending",            f"Rp {int(pending):,}")
c4.metric("🔴 Gagal",              f"Rp {int(gagal):,}")

# ── Charts ────────────────────────────────────────────────────────────────────
if not df.empty:
    col_l, col_r = st.columns(2)
    with col_l:
        df_metode = df.groupby('metode')['jumlah'].sum().reset_index()
        fig = px.pie(df_metode, names='metode', values='jumlah',
                     title="Pendapatan per Metode Bayar",
                     color_discrete_sequence=px.colors.qualitative.Safe,
                     hole=0.35)
        fig.update_layout(margin=dict(t=40,b=10), height=260)
        st.plotly_chart(fig, use_container_width=True)
    with col_r:
        df_tipe = df.groupby(['membership','status_bayar'])['jumlah'].sum().reset_index()
        fig2 = px.bar(df_tipe, x='membership', y='jumlah', color='status_bayar',
                      title="Total Pembayaran per Tipe Membership",
                      barmode='stack',
                      color_discrete_map={'Lunas':'#2d6a4f','Pending':'#f4a261','Gagal':'#e76f51'})
        fig2.update_layout(margin=dict(t=40,b=10), height=260)
        st.plotly_chart(fig2, use_container_width=True)

# ── Table ─────────────────────────────────────────────────────────────────────
st.subheader("📋 Rincian Pembayaran")
st.dataframe(df, use_container_width=True, hide_index=True)
