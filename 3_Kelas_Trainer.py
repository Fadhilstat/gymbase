import streamlit as st
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)).replace(os.sep+'pages',''))
from db import q

st.set_page_config(page_title="Kelas & Trainer · GymBase", page_icon="🏃", layout="wide")
st.title("🏃 Kelas & Trainer")
st.divider()

tab_trainer, tab_kelas = st.tabs(["👨‍🏫 Trainer", "📚 Kelas"])

# ══════════════════════════════════════════════════════════
# TAB TRAINER
# ══════════════════════════════════════════════════════════
with tab_trainer:
    with st.sidebar:
        st.header("🔽 Filter Trainer")
        sp_list = q("SELECT DISTINCT spesialisasi FROM trainer ORDER BY spesialisasi")
        sp_opts = ["Semua"] + sp_list['spesialisasi'].tolist()
        sp_sel  = st.selectbox("Spesialisasi", sp_opts, key="sp_trainer")

    sql_t = """
        SELECT t.trainer_id, t.nama, t.spesialisasi, t.gender,
               t.pengalaman_thn,
               COUNT(k.kelas_id) AS jumlah_kelas
        FROM   trainer t
        LEFT   JOIN kelas k ON t.trainer_id = k.trainer_id
        WHERE  1=1
    """
    params_t = []
    if sp_sel != "Semua":
        sql_t += " AND t.spesialisasi = ?"
        params_t.append(sp_sel)
    sql_t += " GROUP BY t.trainer_id ORDER BY t.pengalaman_thn DESC"

    df_t = q(sql_t, tuple(params_t))

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Trainer",       len(df_t))
    c2.metric("Rata-rata Pengalaman", f"{df_t['pengalaman_thn'].mean():.1f} thn" if not df_t.empty else "-")
    c3.metric("Total Kelas",          int(df_t['jumlah_kelas'].sum()) if not df_t.empty else 0)

    if not df_t.empty:
        fig = px.bar(df_t.head(10), x='nama', y='jumlah_kelas',
                     color='spesialisasi', title="Jumlah Kelas per Trainer",
                     labels={'nama':'Trainer','jumlah_kelas':'Jumlah Kelas'},
                     color_discrete_sequence=px.colors.qualitative.Safe)
        fig.update_layout(margin=dict(t=40,b=10), height=280, xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df_t, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════
# TAB KELAS
# ══════════════════════════════════════════════════════════
with tab_kelas:
    tipe_list = q("SELECT DISTINCT tipe_latihan FROM kelas ORDER BY tipe_latihan")
    tipe_opts = ["Semua"] + tipe_list['tipe_latihan'].tolist()
    tipe_sel  = st.selectbox("Filter Tipe Latihan", tipe_opts, key="tipe_kelas")
    search_k  = st.text_input("🔍 Cari nama kelas", key="search_kelas")

    sql_k = """
        SELECT k.kelas_id, k.nama_kelas, k.tipe_latihan,
               t.nama AS trainer, k.jadwal_hari,
               k.jam_mulai, k.kapasitas,
               COUNT(s.sesi_id) AS total_sesi
        FROM   kelas k
        JOIN   trainer t      ON k.trainer_id = t.trainer_id
        LEFT   JOIN sesi_latihan s ON k.kelas_id = s.kelas_id
        WHERE  1=1
    """
    params_k = []
    if tipe_sel != "Semua":
        sql_k += " AND k.tipe_latihan = ?"
        params_k.append(tipe_sel)
    if search_k:
        sql_k += " AND k.nama_kelas LIKE ?"
        params_k.append(f"%{search_k}%")
    sql_k += " GROUP BY k.kelas_id ORDER BY total_sesi DESC"

    df_k = q(sql_k, tuple(params_k))

    st.metric("Total Kelas Ditampilkan", len(df_k))
    st.dataframe(df_k, use_container_width=True, hide_index=True)
