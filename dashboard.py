import streamlit as st
import pandas as pd
from pymongo import MongoClient
import time

# Configure the web page layout
st.set_page_config(page_title="My Room Weather", layout="wide")
st.title("🌡️ Live Room Environment Dashboard")

# Connect to the local MongoDB database
@st.cache_resource 
def init_connection():
    return MongoClient("mongodb+srv://lazypanda:Lazy%402005@cluster0.yzixbpi.mongodb.net/?appName=Cluster0")

client = init_connection()
db = client['RoomEnvironment']
collection = db['SensorData']

# Fetch the data from MongoDB
def get_data():
    cursor = collection.find({}, {"_id": 0}) 
    df = pd.DataFrame(list(cursor))
    return df

df = get_data()

# Check if we actually have data yet
if df.empty:
    st.warning("No data found in the database yet. Make sure your Arduino and mongo_bridge.py are running!")
else:
    df.set_index('timestamp', inplace=True)
    
    latest_temp = df['temperature'].iloc[-1]
    latest_hum = df['humidity'].iloc[-1]
    
    col1, col2 = st.columns(2)
    col1.metric("Current Temperature", f"{latest_temp} °C")
    col2.metric("Current Humidity", f"{latest_hum} %")
    
    st.divider() 
    
    st.subheader("Temperature History")
    st.line_chart(df['temperature'], color="#ff2b2b")
    
    st.subheader("Humidity History")
    st.line_chart(df['humidity'], color="#00a4ff")

    st.divider()
    
    # --- NEW: The Raw Data Table ---
    st.subheader("Raw Data Log")
    # Sort the dataframe so the newest timestamps are at the top
    sorted_df = df.sort_index(ascending=False)
    # Display the interactive table
    st.dataframe(sorted_df, width='stretch')

# The Auto-Refresh Magic
time.sleep(5)  
st.rerun()