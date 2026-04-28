import streamlit as st
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)).replace(os.sep+'pages',''))
from db import q

st.set_page_config(page_title="Analisis · GymBase", page_icon="📈", layout="wide")
st.title("📈 Analisis & Insight")
st.caption("8 Query SQL Wajib + Visualisasi Data")
st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# 8 QUERY SQL WAJIB
# ══════════════════════════════════════════════════════════════════════════════
queries = {
    "Query 1 — Anggota Premium Aktif": {
        "desc": "SELECT + JOIN + WHERE + ORDER BY · Menampilkan anggota dengan membership Premium yang masih aktif.",
        "sql": """
            SELECT a.nama, m.tipe, m.tgl_selesai, m.biaya_bulanan
            FROM   anggota a
            JOIN   membership m ON a.anggota_id = m.anggota_id
            WHERE  m.tipe = 'Premium' AND m.status = 'Aktif'
            ORDER  BY m.tgl_selesai ASC
            LIMIT  15
        """
    },
    "Query 2 — Rata-rata Kalori & Durasi per Tipe Kelas": {
        "desc": "JOIN + GROUP BY + AVG + COUNT · Membandingkan efektivitas tiap tipe kelas dalam membakar kalori.",
        "sql": """
            SELECT k.tipe_latihan,
                   COUNT(s.sesi_id)                AS total_sesi,
                   ROUND(AVG(s.kalori_terbakar),1) AS avg_kalori,
                   ROUND(AVG(s.durasi_menit),1)    AS avg_durasi_menit
            FROM   sesi_latihan s
            JOIN   kelas k ON s.kelas_id = k.kelas_id
            GROUP  BY k.tipe_latihan
            ORDER  BY avg_kalori DESC
        """
    },
    "Query 3 — Total Pendapatan per Tipe Membership": {
        "desc": "JOIN + GROUP BY + SUM + COUNT · Analisis pendapatan gym berdasarkan segmen membership.",
        "sql": """
            SELECT m.tipe,
                   COUNT(p.pembayaran_id)  AS jumlah_transaksi,
                   SUM(p.jumlah)           AS total_pendapatan,
                   ROUND(AVG(p.jumlah),0)  AS rata_rata_bayar
            FROM   pembayaran p
            JOIN   membership m ON p.membership_id = m.membership_id
            WHERE  p.status_bayar = 'Lunas'
            GROUP  BY m.tipe
            ORDER  BY total_pendapatan DESC
        """
    },
    "Query 4 — Performa Trainer (MAX, MIN, AVG Kalori)": {
        "desc": "3-table JOIN + GROUP BY + MAX + MIN + AVG · Evaluasi kinerja trainer berdasarkan sesi yang dipandu.",
        "sql": """
            SELECT t.nama AS trainer,
                   t.spesialisasi,
                   COUNT(s.sesi_id)                AS total_sesi,
                   MAX(s.kalori_terbakar)           AS kalori_max,
                   MIN(s.kalori_terbakar)           AS kalori_min,
                   ROUND(AVG(s.kalori_terbakar),1)  AS avg_kalori
            FROM   trainer t
            JOIN   kelas k        ON t.trainer_id = k.trainer_id
            JOIN   sesi_latihan s ON k.kelas_id   = s.kelas_id
            GROUP  BY t.trainer_id
            ORDER  BY total_sesi DESC
            LIMIT  10
        """
    },
    "Query 5 — Anggota Paling Aktif (Sesi > Rata-rata)": {
        "desc": "GROUP BY + HAVING + Subquery · Mengidentifikasi anggota dengan frekuensi latihan di atas rata-rata.",
        "sql": """
            SELECT a.nama, COUNT(s.sesi_id) AS total_sesi
            FROM   anggota a
            JOIN   sesi_latihan s ON a.anggota_id = s.anggota_id
            GROUP  BY a.anggota_id
            HAVING total_sesi > (
                SELECT AVG(cnt) FROM (
                    SELECT COUNT(*) AS cnt
                    FROM   sesi_latihan
                    GROUP  BY anggota_id
                )
            )
            ORDER  BY total_sesi DESC
            LIMIT  10
        """
    },
    "Query 6 — Tren Pendaftaran Anggota Baru per Bulan": {
        "desc": "GROUP BY + strftime + COUNT · Melihat tren pertumbuhan anggota dari waktu ke waktu.",
        "sql": """
            SELECT strftime('%Y-%m', tgl_daftar) AS bulan,
                   COUNT(*)                       AS anggota_baru
            FROM   anggota
            GROUP  BY bulan
            ORDER  BY bulan DESC
            LIMIT  12
        """
    },
    "Query 7 — Segmentasi Anggota Berdasarkan Frekuensi Latihan": {
        "desc": "LEFT JOIN + CASE WHEN + Subquery · Mengelompokkan anggota ke segmen Sangat Aktif / Aktif / Jarang / Tidak Pernah.",
        "sql": """
            SELECT segmen,
                   COUNT(*)              AS jumlah_anggota,
                   ROUND(AVG(total),1)   AS rata_rata_sesi
            FROM (
                SELECT a.anggota_id,
                       COUNT(s.sesi_id) AS total,
                       CASE
                           WHEN COUNT(s.sesi_id) >= 20 THEN 'Sangat Aktif'
                           WHEN COUNT(s.sesi_id) >= 10 THEN 'Aktif'
                           WHEN COUNT(s.sesi_id) >= 1  THEN 'Jarang'
                           ELSE                             'Tidak Pernah'
                       END AS segmen
                FROM   anggota a
                LEFT   JOIN sesi_latihan s ON a.anggota_id = s.anggota_id
                GROUP  BY a.anggota_id
            )
            GROUP  BY segmen
            ORDER  BY jumlah_anggota DESC
        """
    },
    "Query 8 — Anggota Belum Pernah Ikut Sesi Latihan": {
        "desc": "LEFT JOIN + WHERE IS NULL · Mendeteksi anggota tidak aktif — berguna untuk strategi retensi.",
        "sql": """
            SELECT a.anggota_id, a.nama, a.tgl_daftar,
                   m.tipe, m.status
            FROM   anggota a
            JOIN   membership m    ON a.anggota_id = m.anggota_id
            LEFT   JOIN sesi_latihan s ON a.anggota_id = s.anggota_id
            WHERE  s.sesi_id IS NULL
            ORDER  BY a.tgl_daftar DESC
            LIMIT  10
        """
    },
}

# ── Render semua query ─────────────────────────────────────────────────────────
for title, info in queries.items():
    with st.expander(f"🔍 {title}", expanded=False):
        st.info(info["desc"])
        with st.container():
            st.code(info["sql"].strip(), language="sql")
        df_result = q(info["sql"])
        st.dataframe(df_result, use_container_width=True, hide_index=True)
        st.caption(f"↳ {len(df_result)} baris hasil")

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# INSIGHT CHARTS
# ══════════════════════════════════════════════════════════════════════════════
st.subheader("💡 Insight Utama")

col_l, col_r = st.columns(2)

with col_l:
    df_seg = q("""
        SELECT segmen, COUNT(*) AS jumlah
        FROM (
            SELECT CASE
                WHEN COUNT(s.sesi_id) >= 20 THEN 'Sangat Aktif'
                WHEN COUNT(s.sesi_id) >= 10 THEN 'Aktif'
                WHEN COUNT(s.sesi_id) >= 1  THEN 'Jarang'
                ELSE 'Tidak Pernah' END AS segmen
            FROM anggota a
            LEFT JOIN sesi_latihan s ON a.anggota_id = s.anggota_id
            GROUP BY a.anggota_id
        ) GROUP BY segmen
    """)
    color_map = {
        'Sangat Aktif':'#1b4332','Aktif':'#2d6a4f',
        'Jarang':'#95d5b2','Tidak Pernah':'#d8f3dc'
    }
    fig = px.pie(df_seg, names='segmen', values='jumlah',
                 title="Segmentasi Aktivitas Anggota",
                 color='segmen', color_discrete_map=color_map,
                 hole=0.4)
    fig.update_layout(margin=dict(t=50,b=10), height=300)
    st.plotly_chart(fig, use_container_width=True)

with col_r:
    df_rev = q("""
        SELECT m.tipe,
               ROUND(SUM(p.jumlah)/1000000.0, 2) AS pendapatan_juta
        FROM   pembayaran p
        JOIN   membership m ON p.membership_id = m.membership_id
        WHERE  p.status_bayar = 'Lunas'
        GROUP  BY m.tipe
        ORDER  BY pendapatan_juta DESC
    """)
    fig2 = px.bar(df_rev, x='tipe', y='pendapatan_juta',
                  title="Pendapatan per Tipe Membership (Juta Rp)",
                  color='tipe',
                  color_discrete_sequence=px.colors.sequential.Greens_r,
                  labels={'tipe':'Tipe Membership','pendapatan_juta':'Rp (Juta)'})
    fig2.update_layout(margin=dict(t=50,b=10), height=300, showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

df_kalori = q("""
    SELECT k.tipe_latihan,
           ROUND(AVG(s.kalori_terbakar),0) AS avg_kalori,
           ROUND(AVG(s.avg_bpm),0)         AS avg_bpm
    FROM   sesi_latihan s
    JOIN   kelas k ON s.kelas_id = k.kelas_id
    GROUP  BY k.tipe_latihan
    ORDER  BY avg_kalori DESC
""")
fig3 = px.bar(df_kalori, x='tipe_latihan', y='avg_kalori',
              color='avg_bpm',
              title="Rata-rata Kalori per Tipe Kelas (warna = avg BPM)",
              labels={'tipe_latihan':'Tipe Kelas','avg_kalori':'Avg Kalori','avg_bpm':'Avg BPM'},
              color_continuous_scale='Reds')
fig3.update_layout(margin=dict(t=50,b=10), height=280)
st.plotly_chart(fig3, use_container_width=True)

# ── Insight teks ──────────────────────────────────────────────────────────────
st.subheader("📝 Kesimpulan Insight")
df_i1 = q("SELECT tipe, COUNT(*) AS n FROM membership WHERE status='Aktif' GROUP BY tipe ORDER BY n DESC LIMIT 1")
df_i2 = q("SELECT tipe_latihan, ROUND(AVG(kalori_terbakar),0) AS k FROM sesi_latihan s JOIN kelas c ON s.kelas_id=c.kelas_id GROUP BY tipe_latihan ORDER BY k DESC LIMIT 1")
df_i3 = q("SELECT COUNT(*) AS n FROM anggota a LEFT JOIN sesi_latihan s ON a.anggota_id=s.anggota_id WHERE s.sesi_id IS NULL")

if not df_i1.empty:
    st.info(f"💳 **Tipe membership terpopuler** (aktif): **{df_i1.iloc[0]['tipe']}** "
            f"dengan {int(df_i1.iloc[0]['n'])} anggota.")
if not df_i2.empty:
    st.success(f"🔥 **Kelas paling efektif membakar kalori**: **{df_i2.iloc[0]['tipe_latihan']}** "
               f"rata-rata {int(df_i2.iloc[0]['k'])} kalori/sesi.")
if not df_i3.empty:
    st.warning(f"⚠️  **{int(df_i3.iloc[0]['n'])} anggota** belum pernah mengikuti sesi latihan — "
               f"potensi target program retensi dan reaktivasi.")
