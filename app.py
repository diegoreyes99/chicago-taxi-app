import streamlit as st
import pickle
import pandas as pd
from river import compose, linear_model, preprocessing
import os

# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="Chicago Taxi Analytics",
    page_icon="🚖",
    layout="wide"
)

st.title("🚖 Chicago Taxi: AI & Analytics")
st.markdown("### Final Cloud Computing Project")
st.markdown("Integrated platform for Fare Prediction (AI) and Business Intelligence (BI).")

# =========================================================
# 2. RESOURCE LOADING (Model + Gold Data from Cloud)
# =========================================================
# Define your bucket path here
BUCKET_NAME = 'final_project_051225'
GOLD_PATH = f"gs://{BUCKET_NAME}/gold"

@st.cache_resource
def load_resources():
    """
    Loads the Machine Learning model from disk and
    downloads the Gold Layer statistics directly from GCS.
    """
    try:
        # A. Load Local Model (.pkl)
        # Ensure the filename matches exactly what you downloaded
        with open('modelo_taxi_fare.pkl', 'rb') as f:
            model = pickle.load(f)

        # B. Load Gold Data from Google Cloud Storage ☁️
        # Pandas uses 'gcsfs' internally to read gs:// paths
        try:
            df_hour = pd.read_csv(f"{GOLD_PATH}/gold_stats_hour.csv")
            df_day = pd.read_csv(f"{GOLD_PATH}/gold_stats_day.csv")
            # Notification for the user
            st.toast("Gold Data successfully loaded from GCS ☁️", icon="✅")
        except Exception as e:
            st.error(f"Error reading from Bucket: {e}")
            # Create empty DataFrames to prevent app crash
            df_hour = pd.DataFrame()
            df_day = pd.DataFrame()

        return model, df_hour, df_day

    except FileNotFoundError:
        return None, None, None

# Load everything
model, df_hour, df_day = load_resources()

# Critical Error Handler
if model is None:
    st.error("⚠️ Critical Error: 'modelo_taxi_river.pkl' not found.")
    st.warning("Please make sure to upload the .pkl file to the app directory.")
    st.stop()

# =========================================================
# 3. APP STRUCTURE (TABS)
# =========================================================
tab1, tab2 = st.tabs(["🔮 Fare Calculator", "📊 Business Dashboard"])

# ---------------------------------------------------------
# TAB 1: PREDICTION (The Calculator)
# ---------------------------------------------------------
with tab1:
    st.subheader("Real-time Fare Estimator")
    st.write("Enter trip details to estimate the taximeter cost.")

    with st.form("trip_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            distance = st.number_input("Distance (km)", min_value=0.1, max_value=200.0, value=5.0, step=0.5)
        with col2:
            duration = st.number_input("Duration (min)", min_value=1, max_value=300, value=15, step=1)
        with col3:
            hour = st.slider("Hour of Day (0-23)", 0, 23, 14)

        day_text = st.selectbox("Day of Week",
            ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])

        submitted = st.form_submit_button("💰 Calculate Fare", use_container_width=True)

    if submitted:
        # A. Map inputs to numbers (Must match training exactly)
        day_map = {
            'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
            'Friday': 4, 'Saturday': 5, 'Sunday': 6
        }

        # B. Create Input Dictionary (X)
        x_input = {
            "km": float(distance),
            "min": float(duration),
            "hour": float(hour),
            "day": float(day_map[day_text])
        }

        try:
            # C. Predict
            prediction = model.predict_one(x_input)

            # D. Display Result
            st.markdown("---")
            st.success(f"### Estimated Fare: ${prediction:.2f} USD")

            # E. Comparative Insight (Using Gold Data)
            if not df_hour.empty:
                # Find the historical average for this specific hour
                avg_fare_at_hour = df_hour[df_hour['Hour'] == hour]['Avg_Fare'].values[0]
                diff = prediction - avg_fare_at_hour

                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Your Estimate", f"${prediction:.2f}")
                with col_b:
                    st.metric("Hist. Avg at this Hour", f"${avg_fare_at_hour:.2f}", delta=f"${diff:.2f}", delta_color="inverse")

        except Exception as e:
            st.error(f"Prediction Error: {e}")

# ---------------------------------------------------------
# TAB 2: DASHBOARD (Gold Layer Visualization)
# ---------------------------------------------------------
with tab2:
    st.subheader("Historical Market Trends (Gold Layer)")

    if df_hour.empty or df_day.empty:
        st.warning("⚠️ Gold data could not be loaded from the Bucket.")
    else:
        # Section 1: KPIs
        st.markdown("#### 📌 Key Performance Indicators")
        kpi1, kpi2, kpi3 = st.columns(3)

        global_avg = df_hour['Avg_Fare'].mean()
        most_expensive_hour = df_hour.sort_values('Avg_Fare', ascending=False).iloc[0]['Hour']
        busiest_day = df_day.sort_values('Total_Trips', ascending=False).iloc[0]['Day']

        kpi1.metric("Global Avg Fare", f"${global_avg:.2f}")
        kpi2.metric("Most Expensive Hour", f"{int(most_expensive_hour)}:00")
        kpi3.metric("Busiest Day", busiest_day)

        st.markdown("---")

        # Section 2: Charts
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("##### 💵 Average Fare by Hour")
            st.line_chart(df_hour.set_index('Hour')['Avg_Fare'], color="#00CC96")
            st.caption("Price fluctuations throughout the day.")

        with c2:
            st.markdown("##### 🚕 Total Trips by Day")
            st.bar_chart(df_day.set_index('Day')['Total_Trips'], color="#636EFA")
            st.caption("Demand volume distribution across the week.")
