import streamlit as st
import boto3
import pandas as pd
import plotly.express as px

# Configure page layout
st.set_page_config(page_title="EV Station Dashboard", layout="wide")

# Custom CSS styling injection
st.markdown("""
    <style>
    .main-title {
        font-family: 'Helvetica Neue', Arial, sans-serif;
        color: #1E293B;
        font-weight: 700;
        margin-bottom: 5px;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: #0F172A;
    }
    .metric-label {
        font-size: 14px;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 5px;
    }
    .html-alert-banner {
        background-color: #FEE2E2;
        border-left: 6px solid #EF4444;
        padding: 16px;
        border-radius: 6px;
        color: #991B1B;
        font-family: sans-serif;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Main Title via HTML
st.markdown('<h1 class="main-title">⚡ EV Charging Station Intelligence Platform</h1>', unsafe_allow_html=True)
# Sidebar Controls for Real-Time Monitoring
with st.sidebar:
    st.markdown("### 📊 Dashboard Controls")
    if st.button("🔄 Refresh Live Data"):
        st.cache_data.clear()
        st.rerun()
st.markdown('<p style="color: #64748B; font-size: 16px;">Live Edge ML Telemetry & Cloud Analytics Layer</p>', unsafe_allow_html=True)

@st.cache_data(ttl=5)
def fetch_ev_data():
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('EV_Station_Logs')
        response = table.scan()
        items = response.get('Items', [])
        if not items: return pd.DataFrame()

        df = pd.DataFrame(items)
        df['cable_temperature_celsius'] = df['cable_temperature_celsius'].astype(float)
        df['electrical_current_amperes'] = df['electrical_current_amperes'].astype(float)
        df['hydrogen_gas_ppm'] = df['hydrogen_gas_ppm'].astype(float)
        df['cooling_fan_speed_rpm'] = df['cooling_fan_speed_rpm'].astype(int)
        df = df.sort_values(by='timestamp')
        return df
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return pd.DataFrame()

df = fetch_ev_data()

if df.empty:
    st.warning("No telemetry records found in DynamoDB.")
else:
    # 1. HTML ANOMALY ALERT ENGINE
    critical_alerts = df[(df['cable_temperature_celsius'] > 70.0) | (df['cooling_fan_speed_rpm'] < 500)]

    if not critical_alerts.empty:
        for index, row in critical_alerts.iterrows():
            st.markdown(f"""
                <div class="html-alert-banner">
                    <strong>🚨 CRITICAL HARDWARE ANOMALY DETECTED BY EDGE ML ENGINE</strong><br>
                    Station: {row['station_id']} | Timestamp: {row['timestamp']} |
                    Temp: {row['cable_temperature_celsius']}°C | Fan: {row['cooling_fan_speed_rpm']} RPM
                </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown('<div style="background-color: #DCFCE7; border-left: 6px solid #22C55E; padding: 12px; color: #14532D; border-radius: 6px; margin-bottom:20px;"><strong>✅ Systems Operational:</strong> All nodes reporting safe levels.</div>', unsafe_allow_html=True)

    # 2. METRIC CARDS GENERATED WITH HTML/CSS CHIPS
    latest_log = df.iloc[-1]
    col1, col2, col3, col4 = st.columns(4)

    metrics = [
        ("Temperature", f"{latest_log['cable_temperature_celsius']} °C", col1),
        ("Current Load", f"{latest_log['electrical_current_amperes']} A", col2),
        ("Hydrogen Gas", f"{latest_log['hydrogen_gas_ppm']} PPM", col3),
        ("Fan Speed", f"{latest_log['cooling_fan_speed_rpm']} RPM", col4)
    ]

    for label, val, column in metrics:
        with column:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{val}</div>
                    <div class="metric-label">{label}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<br><hr>", unsafe_allow_html=True)

    # 3. GRAPHING LAYER
    st.markdown("### Telemetry Historical Time-Series")
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        fig_temp = px.line(df, x='timestamp', y='cable_temperature_celsius', title="Thermal Performance Profile", markers=True)
        st.plotly_chart(fig_temp, use_container_width=True)
    with chart_col2:
        fig_curr = px.line(df, x='timestamp', y='electrical_current_amperes', title="Electrical Load Signature", markers=True)
        st.plotly_chart(fig_curr, use_container_width=True)
