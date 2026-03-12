# 🌡️ End-to-End IoT Environmental Data Pipeline

An enterprise-grade IoT pipeline that captures local climate data via edge hardware, streams it through a custom Python ingestion bridge, stores it in a NoSQL cloud vault, and visualizes it in real-time via a public web application and Power BI.

## 🏗️ System Architecture
This project is decoupled into four distinct layers:

1. **The Edge (Hardware):** An Arduino Uno R3 paired with a DHT22 sensor captures ambient temperature and humidity. It provides a local I2C OLED readout and streams raw data via USB Serial.
2. **The Ingestion Layer (Middleware):** A continuous Python script (`mongo_bridge.py`) intercepts the serial byte stream, performs ETL (Extract, Transform, Load), formats it into JSON, and securely injects it into the cloud.
3. **The Storage Layer (Database):** MongoDB Atlas serves as the permanent, scalable time-series data vault, entirely independent of the local network.
4. **The Presentation Layer (Frontend):** A live Streamlit Community Cloud web app (`dashboard.py`) and a Power BI dashboard query the MongoDB cluster to render real-time analytics and system health metrics.

## 🛠️ Tech Stack
* **C++ (Arduino):** Hardware polling, I2C display protocol, UART serial transmission.
* **Python 3:** `pyserial`, `pymongo[srv]`, `pandas`, `streamlit`.
* **Database:** MongoDB Atlas (NoSQL Document Store).
* **Analytics:** Power BI (via Python Scripting Connector).

## 🚀 Key Features
* **Live System Heartbeat:** The dashboard calculates the delta between the server clock and the last received timestamp to display a live "System Online / Offline" status.
* **Timezone Immunity:** Implemented native Pandas timezone localization (`tz_localize` / `tz_convert`) to seamlessly translate UTC server time to local Pakistan Standard Time (PKT), ensuring chart accuracy regardless of where the app is hosted.
* **Dynamic Querying:** Prevents out-of-memory crashes by utilizing MongoDB query operators (`$gte`) to fetch only relevant time slices (e.g., "Last 1 Hour") rather than the entire database.

## 🧠 Major Engineering Challenges Solved
1. **RFC 3986 Authentication:** Mitigated `pymongo.errors.InvalidURI` crashes during cloud migration by URL-encoding special characters in the database credentials.
2. **Cloud Container Dependencies:** Resolved `ModuleNotFoundError` upon Streamlit deployment by authoring a strict `requirements.txt` to trigger Linux container dependency builds.
3. **Interpolation Artifacts:** Successfully managed edge-device downtime (sleep states) by allowing Pandas to organically interpolate missing temporal data points across multi-hour gaps.

## 🔌 Hardware Setup
* Arduino Uno R3
* DHT22 Temperature & Humidity Sensor (Pin 2)
* 0.96" I2C OLED Display (SDA -> A4, SCL -> A5)
