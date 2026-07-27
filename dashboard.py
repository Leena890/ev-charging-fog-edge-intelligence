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
        font-family: 'Inter', Arial, sans-serif;
        color: #F8FAFC;
        font-weight: 700;
        margin-bottom: 2px;
    }
    .metric-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-value {
        font-size: 26px;
        font-weight: bold;
        color: #38BDF8;
    }
    .metric-label {
        font-size: 13px;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }
    .html-alert-banner {
        background-color: #450A0A;
        border-left: 6px solid #EF4444;
        padding: 14px;
        border-radius: 8px;
        color: #FCA5A5;
        font-family: sans-serif;
        margin-bottom: 20px;
    }
    .html-healthy-banner {
        background-color: #052E16;
        border-left: 6px solid #22C55E;
        padding: 14px;
        border-radius: 8px;
        color: #86EFAC;
        font-family: sans-serif;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Main Title Header
st.markdown('<h1 class="main-title">⚡ EV Station Intelligence Platform</h1>', unsafe_allow_html=True)
st.markdown('<p style="color: #94A3B8; font-size: 15px; margin-bottom: 25px;">Real-Time Edge ML Telemetry & Cloud Analytics Layer</p>', unsafe_allow_html=True)

@st.cache_data(ttl=3)
def fetch_ev_data():
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table('EV_Station_Logs')
        response = table.scan()
        items = response.get('Items', [])
        if not items:
            return pd.DataFrame()

        df = pd.DataFrame(items)
        df['cable_temperature_celsius'] = df['cable_temperature_celsius'].astype(float)
        df['electrical_current_amperes'] = df['electrical_current_amperes'].astype(float)
        df['hydrogen_gas_ppm'] = df['hydrogen_gas_ppm'].astype(float)
        df['cooling_fan_speed_rpm'] = df['cooling_fan_speed_rpm'].astype(int)
        df = df.sort_values(by='timestamp')
        return df
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame()

raw_df = fetch_ev_data()

if raw_df.empty:
    st.warning("No telemetry records found in DynamoDB.")
else:
    # SIDEBAR CONTROLS
    with st.sidebar:
        st.subheader("⚙️ Controls")

        if st.button("🔄 Refresh Data Now", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")
        st.subheader("📍 Filter Station")
        available_stations = sorted(raw_df['station_id'].unique().tolist())
        selected_station = st.selectbox("Select Target Station", ["All Stations"] + available_stations)

        st.markdown("---")
        st.subheader("📈 System Summary")
        total_records = len(raw_df)
        total_anomalies = len(raw_df[(raw_df['cable_temperature_celsius'] > 70.0) | (raw_df['cooling_fan_speed_rpm'] < 500)])
        healthy_records = total_records - total_anomalies

        st.metric(label="Total Telemetry Logs", value=total_records)
        st.metric(label="Healthy States", value=healthy_records)
        st.metric(label="Anomalies Recorded", value=total_anomalies)

    # Filter data based on selection
    if selected_station != "All Stations":
        df = raw_df[raw_df['station_id'] == selected_station].copy()
    else:
        df = raw_df.copy()

    # RECENT ANOMALY CHECK (Only checks the last 5 logs for active critical alerts)
    recent_logs = df.tail(5)
    recent_alerts = recent_logs[(recent_logs['cable_temperature_celsius'] > 70.0) | (recent_logs['cooling_fan_speed_rpm'] < 500)]

    if not recent_alerts.empty:
        latest_alert = recent_alerts.iloc[-1]
        st.markdown(f"""
            <div class="html-alert-banner">
                <strong>🚨 ACTIVE HARDWARE ANOMALY DETECTED</strong><br>
                Station: <b>{latest_alert['station_id']}</b> | Timestamp: <b>{latest_alert['timestamp']}</b> |
                Temp: <b>{latest_alert['cable_temperature_celsius']}°C</b> | Fan: <b>{latest_alert['cooling_fan_speed_rpm']} RPM</b>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="html-healthy-banner">
                <strong>✅ System Operational:</strong> All active sensor nodes reporting normal telemetry values.
            </div>
        """, unsafe_allow_html=True)

    # LIVE METRIC CARDS
    latest_log = df.iloc[-1]
    col1, col2, col3, col4 = st.columns(4)

    metrics = [
        ("Cable Temp", f"{latest_log['cable_temperature_celsius']} °C", col1),
        ("Electrical Current", f"{latest_log['electrical_current_amperes']} A", col2),
        ("Hydrogen Gas", f"{latest_log['hydrogen_gas_ppm']} PPM", col3),
        ("Cooling Fan Speed", f"{latest_log['cooling_fan_speed_rpm']} RPM", col4)
    ]

    for label, val, column in metrics:
        with column:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{val}</div>
                    <div class="metric-label">{label}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # TIME-SERIES CHARTS
    st.subheader("📊 Telemetry Time-Series Analysis")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        fig_temp = px.line(df, x='timestamp', y='cable_temperature_celsius', title="Thermal Profile (°C)", markers=True, template="plotly_dark")
        fig_temp.update_traces(line_color='#F87171')
        st.plotly_chart(fig_temp, use_container_width=True)

    with chart_col2:
        fig_curr = px.line(df, x='timestamp', y='electrical_current_amperes', title="Current Load Signature (A)", markers=True, template="plotly_dark")
        fig_curr.update_traces(line_color='#38BDF8')
        st.plotly_chart(fig_curr, use_container_width=True)

    chart_col3, chart_col4 = st.columns(2)
    with chart_col3:
        fig_gas = px.line(df, x='timestamp', y='hydrogen_gas_ppm', title="Hydrogen Gas Concentration (PPM)", markers=True, template="plotly_dark")
        fig_gas.update_traces(line_color='#FBBF24')
        st.plotly_chart(fig_gas, use_container_width=True)

    with chart_col4:
        fig_fan = px.line(df, x='timestamp', y='cooling_fan_speed_rpm', title="Fan Actuator Dynamics (RPM)", markers=True, template="plotly_dark")
        fig_fan.update_traces(line_color='#34D399')
        st.plotly_chart(fig_fan, use_container_width=True)
