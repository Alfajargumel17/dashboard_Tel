import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import numpy as np

# Konfigurasi halaman
st.set_page_config(
    page_title="Dashboard ODP Telkom Witel Lampung",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS untuk styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .status-hijau {
        background: linear-gradient(135deg, #4CAF50, #45a049);
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
    }
    .status-kuning {
        background: linear-gradient(135deg, #FFC107, #FF8F00);
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
    }
    .status-merah {
        background: linear-gradient(135deg, #F44336, #D32F2F);
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #2C3E50, #34495E);
    }
</style>
""", unsafe_allow_html=True)

# Header utama
st.markdown("""
<div class="main-header">
    <h1>📡 DASHBOARD MONITORING ODP</h1>
    <h2>TELKOM WITEL LAMPUNG</h2>
    <p>Real-time Monitoring & Analytics Dashboard</p>
</div>
""", unsafe_allow_html=True)

# Data ODP
uploaded_file = st.sidebar.file_uploader("📁 Upload data CSV atau Excel", type=["csv", "xlsx"])

@st.cache_data
def load_data(file):
    if file.name.endswith('.csv'):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    df['datetime'] = pd.to_datetime(df[['tahun', 'bulan', 'tanggal']].rename(columns={
        'tahun': 'year', 
        'bulan': 'month', 
        'tanggal': 'day'
    }))
    return df

if uploaded_file is not None:
    df = load_data(uploaded_file)
    # lanjutkan seperti biasa
else:
    st.warning("Silakan upload file data terlebih dahulu.")
    st.stop()

# Sidebar untuk filter
st.sidebar.header("🔧 FILTER & KONTROL")
st.sidebar.markdown("---")

# Real-time counter
st.sidebar.metric("📊 Total Data", len(df))

# Filter kecamatan dengan counter
kecamatan_counts = df['kecamatan'].value_counts()
kecamatan_options = ['Semua'] + [f"{k} ({kecamatan_counts[k]})" for k in sorted(kecamatan_counts.index)]
selected_kecamatan_display = st.sidebar.selectbox("🏢 Pilih Kecamatan:", kecamatan_options)

# Extract kecamatan name
if selected_kecamatan_display == 'Semua':
    selected_kecamatan = 'Semua'
else:
    selected_kecamatan = selected_kecamatan_display.split(' (')[0]

# Filter status ODP dengan counter
status_counts = df['jenis_odp'].value_counts()
status_options = ['Semua'] + [f"{s} ({status_counts[s]})" for s in sorted(status_counts.index)]
selected_status_display = st.sidebar.selectbox("🚦 Pilih Status ODP:", status_options)

# Extract status name
if selected_status_display == 'Semua':
    selected_status = 'Semua'
else:
    selected_status = selected_status_display.split(' (')[0]

# Filter tanggal
st.sidebar.markdown("📅 **Rentang Tanggal:**")
date_range = st.sidebar.date_input(
    "Pilih rentang:",
    value=[df['datetime'].min().date(), df['datetime'].max().date()],
    min_value=df['datetime'].min().date(),
    max_value=df['datetime'].max().date()
)

# Quick filter buttons
st.sidebar.markdown("---")
st.sidebar.markdown("⚡ **Quick Filters:**")

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🚨 Hanya Kritis", use_container_width=True):
        selected_status = 'Merah'
        st.rerun()

with col2:
    if st.button("✅ Reset Filter", use_container_width=True):
        selected_kecamatan = 'Semua'
        selected_status = 'Semua'
        st.rerun()

# Update filter values for session state
st.session_state.selected_kecamatan = selected_kecamatan
st.session_state.selected_status = selected_status

# Apply filters dengan validasi
filtered_df = df.copy()

# Filter berdasarkan kecamatan
if selected_kecamatan != 'Semua':
    filtered_df = filtered_df[filtered_df['kecamatan'] == selected_kecamatan]

# Filter berdasarkan status ODP
if selected_status != 'Semua':
    filtered_df = filtered_df[filtered_df['jenis_odp'] == selected_status]

# Filter berdasarkan tanggal
if len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df['datetime'].dt.date >= date_range[0]) & 
        (filtered_df['datetime'].dt.date <= date_range[1])
    ]

# Tampilkan info filter aktif
if len(filtered_df) == 0:
    st.warning("⚠️ Tidak ada data ODP yang sesuai dengan filter yang dipilih. Silakan ubah pengaturan filter.")
    st.stop()
else:
    filter_info = []
    if selected_kecamatan != 'Semua':
        filter_info.append(f"Kecamatan: {selected_kecamatan}")
    if selected_status != 'Semua':
        filter_info.append(f"Status: {selected_status}")
    if len(date_range) == 2:
        filter_info.append(f"Tanggal: {date_range[0]} - {date_range[1]}")
    
    if filter_info:
        st.info(f"🔍 Filter aktif: {' | '.join(filter_info)} | Menampilkan {len(filtered_df)} dari {len(df)} ODP")

# Metrics utama
st.header("📊 RINGKASAN EKSEKUTIF")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_odp = len(filtered_df)
    st.markdown(f"""
    <div class="metric-container">
        <h3>📡 Total ODP</h3>
        <h2>{total_odp}</h2>
    </div>
    """, unsafe_allow_html=True)

with col2:
    hijau_count = len(filtered_df[filtered_df['jenis_odp'] == 'Hijau'])
    hijau_pct = (hijau_count / total_odp * 100) if total_odp > 0 else 0
    st.markdown(f"""
    <div class="status-hijau">
        <h3>✅ Status Baik</h3>
        <h2>{hijau_count} ({hijau_pct:.1f}%)</h2>
    </div>
    """, unsafe_allow_html=True)

with col3:
    kuning_count = len(filtered_df[filtered_df['jenis_odp'] == 'Kuning'])
    kuning_pct = (kuning_count / total_odp * 100) if total_odp > 0 else 0
    st.markdown(f"""
    <div class="status-kuning">
        <h3>⚠️ Perlu Perhatian</h3>
        <h2>{kuning_count} ({kuning_pct:.1f}%)</h2>
    </div>
    """, unsafe_allow_html=True)

with col4:
    merah_count = len(filtered_df[filtered_df['jenis_odp'] == 'Merah'])
    merah_pct = (merah_count / total_odp * 100) if total_odp > 0 else 0
    st.markdown(f"""
    <div class="status-merah">
        <h3>🚨 Kritis</h3>
        <h2>{merah_count} ({merah_pct:.1f}%)</h2>
    </div>
    """, unsafe_allow_html=True)

# Layout dua kolom untuk visualisasi
col_left, col_right = st.columns([2, 1])

with col_left:
    st.header("🗺️ PETA DISTRIBUSI ODP")
    
    # Informasi filter peta
    st.write(f"📍 Menampilkan {len(filtered_df)} titik ODP sesuai filter yang dipilih")
    
    # Membuat peta interaktif dengan data yang sudah difilter
    if len(filtered_df) > 0:
        center_lat = filtered_df['latitude'].mean()
        center_lon = filtered_df['longitude'].mean()
        
        # Tentukan zoom level berdasarkan jumlah dan sebaran data
        if len(filtered_df) == 1:
            zoom_start = 15
        elif selected_kecamatan != 'Semua':
            zoom_start = 13
        else:
            zoom_start = 12
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_start)
        
        # Warna marker berdasarkan status
        color_map = {'Hijau': 'green', 'Kuning': 'orange', 'Merah': 'red'}
        icon_map = {'Hijau': 'ok-sign', 'Kuning': 'warning-sign', 'Merah': 'remove-sign'}
        
        # Tambahkan marker untuk setiap ODP yang sudah difilter
        for idx, row in filtered_df.iterrows():
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(f"""
                <div style="width: 200px;">
                    <h4 style="color: {color_map[row['jenis_odp']]};">🏢 ODP {row['jenis_odp']}</h4>
                    <hr>
                    <b>📍 Lokasi:</b><br>
                    Kecamatan: {row['kecamatan']}<br>
                    Kelurahan: {row['kelurahan']}<br><br>
                    <b>📅 Tanggal Install:</b><br>
                    {row['tanggal']}/{row['bulan']}/{row['tahun']}<br><br>
                    <b>📐 Koordinat:</b><br>
                    Lat: {row['latitude']}<br>
                    Lon: {row['longitude']}
                </div>
                """, max_width=250),
                tooltip=f"ODP {row['jenis_odp']} - {row['kelurahan']}",
                icon=folium.Icon(
                    color=color_map[row['jenis_odp']], 
                    icon=icon_map[row['jenis_odp']],
                    prefix='glyphicon'
                )
            ).add_to(m)
        
        # Tambahkan legenda
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 150px; height: 90px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4>Status ODP:</h4>
        <p><i class="fa fa-circle" style="color:green"></i> Hijau: Normal</p>
        <p><i class="fa fa-circle" style="color:orange"></i> Kuning: Warning</p>
        <p><i class="fa fa-circle" style="color:red"></i> Merah: Critical</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Tampilkan peta
        map_data = st_folium(m, width=700, height=500, returned_objects=["last_object_clicked"])
        
        # Tampilkan info jika ada marker yang diklik
        if map_data["last_object_clicked"]:
            clicked_lat = map_data["last_object_clicked"]["lat"]
            clicked_lng = map_data["last_object_clicked"]["lng"]
            
            # Cari ODP yang diklik
            clicked_odp = filtered_df[
                (abs(filtered_df['latitude'] - clicked_lat) < 0.001) & 
                (abs(filtered_df['longitude'] - clicked_lng) < 0.001)
            ]
            
            if len(clicked_odp) > 0:
                odp_info = clicked_odp.iloc[0]
                st.success(f"📍 ODP dipilih: {odp_info['kelurahan']}, {odp_info['kecamatan']} - Status: {odp_info['jenis_odp']}")
    else:
        st.warning("Tidak ada data ODP untuk ditampilkan di peta dengan filter saat ini.")

with col_right:
    st.header("📈 DISTRIBUSI STATUS")
    
    # Pie chart status ODP
    status_counts = filtered_df['jenis_odp'].value_counts()
    colors = ['#4CAF50', '#FFC107', '#F44336']
    
    fig_pie = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        title="Distribusi Status ODP",
        color_discrete_sequence=colors
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)

# Visualisasi tambahan
st.header("📊 ANALISIS DETAIL")

col1, col2 = st.columns(2)

with col1:
    # Bar chart per kecamatan (stacked)
    if len(filtered_df) > 0:
        kecamatan_counts = filtered_df.groupby(['kecamatan', 'jenis_odp']).size().reset_index(name='count')
        fig_kecamatan = px.bar(
            kecamatan_counts,
            x='kecamatan',
            y='count',
            color='jenis_odp',
            title=f"Distribusi ODP per Kecamatan",
            color_discrete_map={'Hijau': '#4CAF50', 'Kuning': '#FFC107', 'Merah': '#F44336'},
            text='count'
        )
        fig_kecamatan.update_xaxes(tickangle=45, title='Kecamatan')
        fig_kecamatan.update_yaxes(title='Jumlah ODP')
        fig_kecamatan.update_traces(texttemplate='%{text}', textposition='inside')
        fig_kecamatan.update_layout(
            showlegend=True, 
            height=450,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                title="Status ODP"
            )
        )
        st.plotly_chart(fig_kecamatan, use_container_width=True)
    else:
        st.info("Tidak ada data kecamatan untuk ditampilkan")

with col2:
    # Bar chart per kelurahan (stacked)
    if len(filtered_df) > 0:
        kelurahan_counts = filtered_df.groupby(['kelurahan', 'jenis_odp']).size().reset_index(name='count')
        total_kelurahan = len(filtered_df)
        
        fig_kelurahan = px.bar(
            kelurahan_counts,
            x='kelurahan',
            y='count',
            color='jenis_odp',
            title=f"Distribusi ODP per Kelurahan ({total_kelurahan} ODP)",
            color_discrete_map={'Hijau': '#4CAF50', 'Kuning': '#FFC107', 'Merah': '#F44336'},
            text='count'
        )
        fig_kelurahan.update_xaxes(tickangle=45, title='Kelurahan')
        fig_kelurahan.update_yaxes(title='Jumlah ODP')
        fig_kelurahan.update_traces(texttemplate='%{text}', textposition='inside')
        fig_kelurahan.update_layout(
            showlegend=True, 
            height=450,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                title="Status ODP"
            )
        )
        st.plotly_chart(fig_kelurahan, use_container_width=True)
    else:
        st.info("Tidak ada data kelurahan untuk ditampilkan")

# Row kedua untuk visualisasi tambahan
col3, col4 = st.columns(2)

with col3:
    # Timeline trend - data yang difilter
    if len(filtered_df) > 0:
        daily_counts = filtered_df.groupby(['datetime', 'jenis_odp']).size().reset_index(name='count')
        fig_line = px.line(
            daily_counts,
            x='datetime',
            y='count',
            color='jenis_odp',
            title=f"Trend Instalasi ODP Harian",
            color_discrete_map={'Hijau': '#4CAF50', 'Kuning': '#FFC107', 'Merah': '#F44336'},
            markers=True
        )
        fig_line.update_layout(height=400)
        fig_line.update_xaxes(title='Tanggal')
        fig_line.update_yaxes(title='Jumlah ODP')
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Tidak ada data untuk trend analysis")

with col4:
    # Summary statistics dengan visual yang lebih menarik
    if len(filtered_df) > 0:
        st.subheader("📈 Statistik Ringkasan")
        
        # Metrics dalam format card
        total_kecamatan = filtered_df['kecamatan'].nunique()
        total_kelurahan = filtered_df['kelurahan'].nunique()
        
        st.metric("🏢 Total Kecamatan", total_kecamatan)
        st.metric("🏘️ Total Kelurahan", total_kelurahan)
        st.metric("📅 Periode Data", f"{len(filtered_df['datetime'].dt.date.unique())} hari")
        
        # Status distribution dalam bentuk progress bar
        st.markdown("**Distribusi Status:**")
        for status in ['Hijau', 'Kuning', 'Merah']:
            count = len(filtered_df[filtered_df['jenis_odp'] == status])
            percentage = (count / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
            
            if status == 'Hijau':
                st.success(f"✅ {status}: {count} ODP ({percentage:.1f}%)")
            elif status == 'Kuning':
                st.warning(f"⚠️ {status}: {count} ODP ({percentage:.1f}%)")
            else:
                st.error(f"🚨 {status}: {count} ODP ({percentage:.1f}%)")
    else:
        st.info("Tidak ada data untuk statistik ringkasan")

# Tabel detail dengan filter interaktif
st.header("📋 DATA DETAIL ODP")

# Tambahkan search box untuk tabel
search_term = st.text_input("🔍 Cari berdasarkan kelurahan atau kecamatan:", "")

# Filter tabel berdasarkan search
table_df = filtered_df.copy()
if search_term:
    table_df = table_df[
        table_df['kelurahan'].str.contains(search_term, case=False, na=False) |
        table_df['kecamatan'].str.contains(search_term, case=False, na=False)
    ]

# Format tabel untuk tampilan yang lebih baik
display_df = table_df[['kecamatan', 'kelurahan', 'jenis_odp', 'datetime', 'latitude', 'longitude']].copy()
display_df['datetime'] = display_df['datetime'].dt.strftime('%d/%m/%Y')
display_df = display_df.sort_values('datetime')

# Styling berdasarkan status
def highlight_status(row):
    if row['jenis_odp'] == 'Merah':
        return ['background-color: #ffcccb'] * len(row)
    elif row['jenis_odp'] == 'Kuning':
        return ['background-color: #fff2cc'] * len(row)
    elif row['jenis_odp'] == 'Hijau':
        return ['background-color: #d4edda'] * len(row)
    return [''] * len(row)

if len(display_df) > 0:
    styled_df = display_df.style.apply(highlight_status, axis=1)
    st.dataframe(styled_df, use_container_width=True, height=300)
    
    # Export option
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Data CSV",
        data=csv,
        file_name=f"odp_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
else:
    st.info("Tidak ada data yang sesuai dengan filter dan pencarian")

# Insights dan rekomendasi
st.header("💡 INSIGHTS & REKOMENDASI")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🔍 Insights Utama")
    st.write(f"• Total {total_odp} ODP terpantau di wilayah terpilih")
    st.write(f"• {hijau_count} ODP dalam kondisi baik ({hijau_pct:.1f}%)")
    st.write(f"• {merah_count} ODP memerlukan perhatian segera ({merah_pct:.1f}%)")
    
    # Area dengan masalah terbanyak
    problem_areas = filtered_df[filtered_df['jenis_odp'].isin(['Kuning', 'Merah'])]['kecamatan'].value_counts()
    if len(problem_areas) > 0:
        st.write(f"• Area dengan masalah terbanyak: {problem_areas.index[0]} ({problem_areas.iloc[0]} kasus)")

with col2:
    st.subheader("🎯 Rekomendasi Aksi")
    if merah_count > 0:
        st.error(f"🚨 Prioritas Tinggi: {merah_count} ODP status merah memerlukan tindakan segera")
    if kuning_count > 0:
        st.warning(f"⚠️ Prioritas Sedang: {kuning_count} ODP status kuning perlu dipantau")
    if hijau_pct > 80:
        st.success("✅ Performa jaringan dalam kondisi baik secara keseluruhan")
    else:
        st.info("📈 Peningkatan maintenance diperlukan untuk optimalisasi jaringan")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p>Dashboard ODP Telkom Witel Lampung | Update Terakhir: {}</p>
    <p>💡 Powered by Streamlit | 📊 Data Analytics Dashboard</p>
</div>
""".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")), unsafe_allow_html=True)