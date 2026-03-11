import streamlit as st
import pandas as pd
from pymongo import MongoClient
import time
from datetime import datetime, timedelta

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

# --- 1. THE SIDEBAR FILTER ---
st.sidebar.header("⚙️ Dashboard Controls")
time_filter = st.sidebar.selectbox(
    "Select Time Range",
    ("Last 1 Hour", "Last 24 Hours", "Last 7 Days", "All Time")
)

# Fetch the data (Only downloading what we need!)
def get_data(filter_choice):
    query = {}
    # Force the cloud server to use Pakistan Standard Time (UTC + 5)
    now = datetime.utcnow() + timedelta(hours=5)
    
    if filter_choice == "Last 1 Hour":
        query = {"timestamp": {"$gte": now - timedelta(hours=1)}}
    elif filter_choice == "Last 24 Hours":
        query = {"timestamp": {"$gte": now - timedelta(hours=24)}}
    elif filter_choice == "Last 7 Days":
        query = {"timestamp": {"$gte": now - timedelta(days=7)}}
        
    cursor = collection.find(query, {"_id": 0}) 
    df = pd.DataFrame(list(cursor))
    return df

df = get_data(time_filter)

# Check if we have data
if df.empty:
    st.warning(f"No data found for the {time_filter}. Make sure your Python bridge is running!")
else:
    df.set_index('timestamp', inplace=True)
    df.sort_index(inplace=True) # Ensure data is in chronological order
    
    # --- 2. CALCULATING TRENDS & METRICS ---
    latest_temp = df['temperature'].iloc[-1]
    latest_hum = df['humidity'].iloc[-1]
    
    # Compare to ~1 minute ago to get the Trend Arrow (assuming readings every ~5 seconds)
    if len(df) > 12:
        past_temp = df['temperature'].iloc[-12]
        past_hum = df['humidity'].iloc[-12]
    else:
        past_temp = df['temperature'].iloc[0]
        past_hum = df['humidity'].iloc[0]
        
    temp_trend = round(latest_temp - past_temp, 2)
    hum_trend = round(latest_hum - past_hum, 2)
    
    # Find the peak temperature for the selected time period
    max_temp = df['temperature'].max()

    # --- 3. SYSTEM HEALTH CHECK ---
    last_update = df.index[-1]
    time_since_last = (datetime.utcnow() + timedelta(hours=5)) - last_update
    
    if time_since_last < timedelta(minutes=2):
        st.markdown("### 🟢 **System Online** *(Receiving live edge data)*")
    else:
        mins_ago = int(time_since_last.total_seconds() / 60)
        st.markdown(f"### 🔴 **System Offline** *(Last seen {mins_ago} minutes ago)*")

    # --- DRAWING THE UI ---
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    # The new metrics with built-in Streamlit delta arrows
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

# Auto-Refresh Loop
time.sleep(5)  
st.rerun()