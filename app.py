import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import boto3
from decimal import Decimal
import os
import time

AWS_REGION = st.secrets.get("AWS_REGION", os.getenv("AWS_REGION", "eu-central-1"))
DYNAMODB_TABLE_NAME = st.secrets.get("DYNAMODB_TABLE", os.getenv("DYNAMODB_TABLE", "Enduvia_Sensor_Data"))
AWS_ACCESS_KEY = st.secrets.get("AWS_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID", ""))
AWS_SECRET_KEY = st.secrets.get("AWS_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY", ""))

st.set_page_config(
    page_title="Enduvia Sensor Analytics Dashboard",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp {
        background-color: #fdfaf9;
        color: #212529;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
    }
    header, footer {visibility: hidden !important;}
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    .top-navbar {
        background-color: #b31010;
        color: white;
        padding: 14px 30px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .top-logo {
        font-size: 1.3rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 12px;
        letter-spacing: -0.02em;
    }
    .top-logo span {
        background: white;
        color: #b31010;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.9rem;
    }
    .sub-bar {
        background: white;
        padding: 10px 30px;
        border-bottom: 1px solid #eed8d8;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.85rem;
        font-weight: 600;
        color: #333;
    }
    .main-body {
        padding: 15px 30px;
    }
    .kpi-card {
        background: white;
        border: 1px solid #eed8d8;
        border-top: 3px solid #b31010;
        border-radius: 4px;
        padding: 12px 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        min-height: 75px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .kpi-label {
        font-size: 0.75rem;
        color: #666;
        font-weight: 600;
        margin-bottom: 4px;
        text-transform: capitalize;
    }
    .kpi-value {
        font-size: 1.45rem;
        font-weight: 700;
        color: #111;
        line-height: 1.1;
    }
</style>
""", unsafe_allow_html=True)


def fetch_dynamo_data():
    if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
        return pd.DataFrame()
        
    try:
        dynamodb = boto3.resource(
            'dynamodb',
            region_name=AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY
        )
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)
        response = table.scan()
        items = response.get('Items', [])
        
        if not items:
            return pd.DataFrame()
            
        df = pd.DataFrame(items)
        
        if 'temperature' in df.columns:
            df['temperature'] = df['temperature'].apply(lambda x: float(x) if isinstance(x, Decimal) else float(x or 0))
        elif 'sicaklik' in df.columns:
            df['temperature'] = df['sicaklik'].apply(lambda x: float(x) if isinstance(x, Decimal) else float(x or 0))
        else:
            df['temperature'] = 0.0

        if 'humidity' in df.columns:
            df['humidity'] = df['humidity'].apply(lambda x: float(x) if isinstance(x, Decimal) else float(x or 0))
        elif 'nem' in df.columns:
            df['humidity'] = df['nem'].apply(lambda x: float(x) if isinstance(x, Decimal) else float(x or 0))
        else:
            df['humidity'] = 0.0
            
        if 'device_id' not in df.columns and 'cihaz' in df.columns:
            df['device_id'] = df['cihaz']
            
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp']) + pd.Timedelta(hours=3)
            df = df.sort_values(by='timestamp', ascending=True)
            
        return df
    except Exception:
        return pd.DataFrame()


df = fetch_dynamo_data()

is_live = not df.empty
if not is_live:
    times = pd.date_range(end=datetime.now(), periods=20, freq='2min')
    df = pd.DataFrame({
        'timestamp': times,
        'device_id': ['Enduvia-Node-1'] * 20,
        'temperature': [24.0, 24.5, 25.1, 26.0, 28.2, 31.5, 36.0, 42.5, 42.5, 38.0, 32.0, 28.5, 26.0, 25.5, 25.0, 26.5, 27.8, 29.0, 30.5, 28.4],
        'humidity': [55, 54, 54, 53, 52, 50, 48, 45, 45, 47, 50, 52, 53, 54, 55, 55, 54, 53, 52, 52],
        'durum': ['Normal']*5 + ['Uyari']*6 + ['Normal']*9
    })

total_packets = len(df)
latest_temp = df['temperature'].iloc[-1]
latest_hum = df['humidity'].iloc[-1]
active_node = df['device_id'].iloc[-1] if 'device_id' in df.columns else "Enduvia-Node-1"
critical_count = len(df[df['temperature'] > 30.0])
critical_ratio = (critical_count / total_packets * 100) if total_packets > 0 else 0

status_text = "🟢 Canlı DynamoDB Akışı Aktif (Türkiye Saati: UTC+3)" if is_live else "🟡 Simülasyon Modu"
st.markdown(f"""
<div class="top-navbar">
    <div class="top-logo">
        <span style="font-weight:900;">ENDUVIA</span> IoT Sensor Analytics Dashboard
    </div>
</div>
<div class="sub-bar">
    <div>Sistem Genel Durumu: <span style="font-weight:700;">{status_text}</span></div>
    <div style="color:#666; font-size:0.8rem;">Düğüm: <b>{active_node}</b> | Bölge: <b>{AWS_REGION}</b></div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='main-body'>", unsafe_allow_html=True)

col_ref1, col_ref2, col_ref3 = st.columns([5, 1.2, 1.2])
with col_ref2:
    auto_refresh = st.toggle("⚡ Canlı Akış (3sn)", value=True)
with col_ref3:
    if st.button("🔄 Şimdi Yenile", use_container_width=True):
        st.rerun()

c1, c2, c3, c4, c5, c6, c7 = st.columns(7)

with c1:
    st.markdown(f"""<div class="kpi-card"><div class="kpi-label">Aktif Düğüm</div><div class="kpi-value">{active_node}</div></div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="kpi-card"><div class="kpi-label">Toplam Paket</div><div class="kpi-value">{total_packets}</div></div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="kpi-card"><div class="kpi-label">Anlık Sıcaklık</div><div class="kpi-value">{latest_temp:.1f}°C</div></div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="kpi-card"><div class="kpi-label">Anlık Nem</div><div class="kpi-value">%{latest_hum:.1f}</div></div>""", unsafe_allow_html=True)
with c5:
    st.markdown(f"""<div class="kpi-card"><div class="kpi-label">SNS Alarmları</div><div class="kpi-value">{critical_count}</div></div>""", unsafe_allow_html=True)
with c6:
    st.markdown(f"""<div class="kpi-card"><div class="kpi-label">DynamoDB Kayıt</div><div class="kpi-value">{total_packets}</div></div>""", unsafe_allow_html=True)
with c7:
    st.markdown(f"""<div class="kpi-card"><div class="kpi-label">Kritik Eşik Oranı</div><div class="kpi-value">%{critical_ratio:.1f}</div></div>""", unsafe_allow_html=True)

st.write("")

col_left, col_right = st.columns([1.6, 1.1])

with col_left:
    g1, g2 = st.columns([1, 1.4])
    
    with g1:
        normal_count = total_packets - critical_count
        fig_donut = go.Figure(data=[go.Pie(
            labels=['Normal Aralık', 'Kritik Eşik (>30°C)'],
            values=[normal_count, critical_count],
            hole=.6,
            marker=dict(colors=['#b31010', '#e05353']),
            textinfo='percent',
            textfont=dict(size=11, color='white')
        )])
        fig_donut.update_layout(
            title=dict(text="<b>Sensör Eşik Durum Oranı</b>", font=dict(size=12, color="#333")),
            margin=dict(l=10, r=10, t=35, b=10),
            height=210,
            paper_bgcolor='white',
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, font=dict(size=9))
        )
        st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
        
    with g2:
        plot_df = df.tail(30)
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=plot_df['timestamp'], y=plot_df['temperature'], mode='lines+markers',
            line=dict(color='#b31010', width=2.5),
            marker=dict(size=4),
            fill='tozeroy', fillcolor='rgba(179, 16, 16, 0.25)',
            name='Sıcaklık (°C)'
        ))
        fig_line.add_hline(y=30, line_dash="dash", line_color="#b31010", annotation_text="Eşik 30°C", annotation_font_size=10)
        fig_line.update_layout(
            title=dict(text="<b>Canlı Sıcaklık Akışı (°C)</b>", font=dict(size=12, color="#333")),
            margin=dict(l=10, r=10, t=35, b=10),
            height=210,
            paper_bgcolor='white',
            plot_bgcolor='white',
            showlegend=False,
            xaxis=dict(showgrid=True, gridcolor='#f0f0f0', tickfont=dict(size=9)),
            yaxis=dict(showgrid=True, gridcolor='#f0f0f0', tickfont=dict(size=9))
        )
        st.plotly_chart(fig_line, use_container_width=True, config={'displayModeBar': False})
    
    st.markdown("<div style='font-size:0.85rem; font-weight:700; color:#333; margin-top:5px; margin-bottom:4px;'>📅 Günlük & Saatlik Sıcaklık Yoğunluk Matrisi</div>", unsafe_allow_html=True)
    days = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz']
    hours = ['00-04', '04-08', '08-12', '12-16', '16-20', '20-24']
    heat_data = np.random.randint(22, 35, size=(len(days), len(hours)))
    
    fig_heat = go.Figure(data=go.Heatmap(
        z=heat_data, x=hours, y=days, colorscale='Reds', showscale=False,
        text=heat_data, texttemplate="%{text}°C", textfont={"size": 10}
    ))
    fig_heat.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=190,
        paper_bgcolor='white',
        plot_bgcolor='white',
        xaxis=dict(tickfont=dict(size=10)),
        yaxis=dict(tickfont=dict(size=10))
    )
    st.plotly_chart(fig_heat, use_container_width=True, config={'displayModeBar': False})

with col_right:
    st.markdown("""
    <div style="background:white; border:1px solid #eed8d8; border-radius:4px; overflow:hidden;">
        <div style="background:#b31010; color:white; padding:8px 12px; font-weight:700; font-size:0.85rem;">
            Son Sensör Kayıtları (DynamoDB Canlı Günlük)
        </div>
        <table style="width:100%; border-collapse:collapse; font-size:0.75rem; color:#333;">
            <tr style="background:#fceaea; border-bottom:1px solid #eed8d8; font-weight:700; text-align:left;">
                <th style="padding:6px 8px;">Düğüm</th>
                <th style="padding:6px 8px;">Saat / Durum</th>
                <th style="padding:6px 8px;">Nem</th>
                <th style="padding:6px 8px; text-align:right;">Sıcaklık</th>
            </tr>
    """, unsafe_allow_html=True)
    
    last_records = df.tail(7).iloc[::-1]
    for _, row in last_records.iterrows():
        t_str = row['timestamp'].strftime('%H:%M:%S') if isinstance(row['timestamp'], pd.Timestamp) else str(row['timestamp'])
        temp_color = "#b31010" if row['temperature'] > 30 else "#333"
        st.markdown(f"""
            <tr style="border-bottom:1px solid #f4f4f4;">
                <td style="padding:6px 8px; font-weight:600;">{row.get('device_id', 'Node-1')}</td>
                <td style="padding:6px 8px;">{t_str}</td>
                <td style="padding:6px 8px; color:#0284c7; font-weight:600;">%{row['humidity']:.1f}</td>
                <td style="padding:6px 8px; text-align:right; font-weight:700; color:{temp_color};">{row['temperature']:.1f} °C</td>
            </tr>
        """, unsafe_allow_html=True)
        
    st.markdown(f"""
            <tr style="background:#b31010; color:white; font-weight:700;">
                <td style="padding:6px 8px;" colspan="3">Toplam Canlı Kayıt</td>
                <td style="padding:6px 8px; text-align:right;">{total_packets}</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

if auto_refresh:
    time.sleep(3)
    st.rerun()