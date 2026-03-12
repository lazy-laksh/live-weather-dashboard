import streamlit as st
import pandas as pd
from pymongo import MongoClient
import time

# Configure the web page layout
st.set_page_config(page_title="Room Environment Dashboard", layout="wide")
st.title("🌡️ Live Room Environment Dashboard")

# Connect to the Cloud Database
@st.cache_resource 
def init_connection():
    return MongoClient("mongodb+srv://lazypanda:Lazy%402005@cluster0.yzixbpi.mongodb.net/?appName=Cluster0")

client = init_connection()
db = client['RoomEnvironment']
collection = db['SensorData']

# --- THE SIDEBAR FILTER ---
st.sidebar.header("⚙️ Dashboard Controls")
time_filter = st.sidebar.selectbox(
    "Select Time Range",
    ("Last 1 Hour", "Last 24 Hours", "Last 7 Days", "All Time")
)

# Fetch the data 
def get_data(filter_choice):
    cursor = collection.find({}, {"_id": 0}) 
    df = pd.DataFrame(list(cursor))
    
    if df.empty:
        return df

   # 1. Convert to pandas datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 2. THE REAL TIMEZONE FIX:
    # The Arduino bridge already saves in PKT. We just "stamp" it as Karachi time without adding hours!
    if df['timestamp'].dt.tz is None:
        df['timestamp'] = df['timestamp'].dt.tz_localize('Asia/Karachi')
    else:
        df['timestamp'] = df['timestamp'].dt.tz_convert('Asia/Karachi')
    
    df.set_index('timestamp', inplace=True)
    df.sort_index(inplace=True)
    
    # 3. The Anchor Filter
    latest_time = df.index[-1]
    
    if filter_choice == "Last 1 Hour":
        df = df[df.index >= (latest_time - pd.Timedelta(hours=1))]
    elif filter_choice == "Last 24 Hours":
        df = df[df.index >= (latest_time - pd.Timedelta(hours=24))]
    elif filter_choice == "Last 7 Days":
        df = df[df.index >= (latest_time - pd.Timedelta(days=7))]
        
    return df

df = get_data(time_filter)

# Check if we have data
if df.empty:
    st.warning(f"No data found for the {time_filter}. Make sure your Python bridge is running!")
else:
    # --- CALCULATING TRENDS & METRICS ---
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

    # --- SYSTEM HEALTH CHECK ---
    last_update = df.index[-1]
    
    # Get the exact current time in Pakistan
    current_pkt_time = pd.Timestamp.now('Asia/Karachi')
    
    time_since_last = current_pkt_time - last_update
    
    if time_since_last < pd.Timedelta(minutes=2):
        st.markdown("### 🟢 **System Online** *(Receiving live edge data)*")
    else:
        mins_ago = int(time_since_last.total_seconds() / 60)
        mins_ago = max(0, mins_ago) # Prevent negative numbers
        st.markdown(f"### 🔴 **System Offline** *(Last seen {mins_ago} minutes ago)*")

    # --- DRAWING THE UI ---
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
    
    # Format the timestamp to hide the +05:00 timezone tag for a cleaner look
    sorted_df.index = sorted_df.index.strftime('%Y-%m-%d %H:%M:%S')
    
    st.dataframe(sorted_df, width='stretch')

# Auto-Refresh Loop
time.sleep(5)  
st.rerun()