import streamlit as st
import pandas as pd
from pymongo import MongoClient
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="Room Environment Dashboard", layout="wide")
st.title("🌡️ Live Room Environment Dashboard")

@st.cache_resource 
def init_connection():
    return MongoClient("mongodb+srv://lazypanda:Lazy%402005@cluster0.yzixbpi.mongodb.net/?appName=Cluster0")

client = init_connection()
db = client['RoomEnvironment']
collection = db['SensorData']

st.sidebar.header("⚙️ Dashboard Controls")
time_filter = st.sidebar.selectbox(
    "Select Time Range",
    ("Last 1 Hour", "Last 24 Hours", "Last 7 Days", "All Time")
)

def get_data(filter_choice):
    # 1. Pull all data first to let Pandas handle the complex time math safely
    cursor = collection.find({}, {"_id": 0}) 
    df = pd.DataFrame(list(cursor))
    
    if df.empty:
        return df

    # 2. Convert to proper datetime format
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 3. The AM/PM Chart Fix: Force the naive datetimes forward by 12 hours 
    df['timestamp'] = df['timestamp'] + pd.Timedelta(hours=12)
    
    df.set_index('timestamp', inplace=True)
    df.sort_index(inplace=True)
    
    # 4. The Anchor Filter: Base the time off the LATEST data point, not the server clock!
    latest_time = df.index[-1]
    
    if filter_choice == "Last 1 Hour":
        df = df[df.index >= (latest_time - pd.Timedelta(hours=1))]
    elif filter_choice == "Last 24 Hours":
        df = df[df.index >= (latest_time - pd.Timedelta(hours=24))]
    elif filter_choice == "Last 7 Days":
        df = df[df.index >= (latest_time - pd.Timedelta(days=7))]
        
    return df

df = get_data(time_filter)

if df.empty:
    st.warning(f"No data found for the {time_filter}. Make sure your Python bridge is running!")
else:
    # Calculate Trends
    latest_temp = df['temperature'].iloc[-1]
    latest_hum = df['humidity'].iloc[-1]
    
    if len(df) > 12:
        past_temp = df['temperature'].iloc[-12]
        past_hum = df['humidity'].iloc[-12]
    else:
        past_temp = df['temperature'].iloc[0]
        past_hum = df['humidity'].iloc[0]
        
    temp_trend = round(latest_temp - past_temp, 2)
    hum_trend = round(latest_hum - past_hum, 2)
    max_temp = df['temperature'].max()

    # System Health Check (Synced to PKT)
    last_update = df.index[-1]
    current_pkt_time = datetime.utcnow() + timedelta(hours=5)
    
    # Since we artificially shifted the data +12 hours for the chart, we adjust the health check clock too
    adjusted_current_time = current_pkt_time + timedelta(hours=12) 
    
    time_since_last = adjusted_current_time - last_update
    
    if time_since_last < timedelta(minutes=2):
        st.markdown("### 🟢 **System Online** *(Receiving live edge data)*")
    else:
        mins_ago = int(time_since_last.total_seconds() / 60)
        # Prevent negative numbers if clocks are slightly out of sync
        mins_ago = max(0, mins_ago) 
        st.markdown(f"### 🔴 **System Offline** *(Last seen {mins_ago} minutes ago)*")

    # Draw the UI
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    col1.metric("Current Temperature", f"{latest_temp} °C", f"{temp_trend} °C (last min)")
    col2.metric("Current Humidity", f"{latest_hum} %", f"{hum_trend} % (last min)")
    col3.metric("Peak Temp (Selected Period)", f"{max_temp} °C", "Max")
    
    st.divider() 
    
    st.subheader(f"Temperature History ({time_filter})")
    st.line_chart(df['temperature'], color="#ff2b2b")
    
    st.subheader(f"Humidity History ({time_filter})")
    st.line_chart(df['humidity'], color="#00a4ff")

    st.divider()
    
    st.subheader("Raw Data Log")
    sorted_df = df.sort_index(ascending=False)
    st.dataframe(sorted_df, width='stretch')

time.sleep(5)  
st.rerun()