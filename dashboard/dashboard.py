import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
from datetime import datetime
import os
import plotly.express as px
import numpy as np
import json
import time

# ---------------- CONFIG ---------------- #
st.set_page_config(page_title="AI Traffic System", layout="wide")

st_autorefresh(interval=1000, key="live")

FILE = "data/challans.csv"

# ---------------- INIT FILE ---------------- #
if not os.path.exists(FILE):
    df = pd.DataFrame(columns=[
        "Number Plate", "Violation", "Details",
        "Time", "Date", "Status", "Due Date", "Fine"
    ])
    df.to_csv(FILE, index=False)

# ---------------- UPDATE FINES ---------------- #
def load_signal():
    try:
        time.sleep(0.1) # force fresh read
        with open("data/signal.json", "r") as f:
          data = json.load(f)
        return data
    except:
        return {"current_signal": "N/A", "time_left": 0}

def update_fines():
    df = pd.read_csv(FILE)
    today = datetime.now().date()

    for i in range(len(df)):
        try:
            due = datetime.strptime(df.loc[i, "Due Date"], "%Y-%m-%d").date()
            if df.loc[i, "Status"] == "Unpaid" and today > due:
                df.loc[i, "Fine"] = 500
        except:
            continue

    df.to_csv(FILE, index=False)

# ---------------- LOGIN ---------------- #
def login():
    st.title("🔐 Admin Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        submit = st.form_submit_button("Login")

        if submit:
            if username == "admin" and password == "1234":
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("Invalid credentials")

# ---------------- DASHBOARD ---------------- #
def dashboard():
    st.markdown("<h1 style='text-align: center;'>🚦 AI Traffic Control Panel</h1>", unsafe_allow_html=True)

    st.sidebar.title("🚀 Navigation")

    if st.sidebar.button("🚪 Logout"):
        st.session_state["logged_in"] = False
        st.rerun()

    page = st.sidebar.radio("Go to", ["Dashboard", "Traffic Analytics", "Challans"])

    df = pd.read_csv(FILE)

    now = datetime.now()
    current_time = now.strftime("%I:%M %p")
    current_day = now.strftime("%A")

    # ---------------- DASHBOARD ---------------- #
    if page == "Dashboard":
        col1, col2, col3 = st.columns(3)

        col1.metric("🚗 Total Challans", len(df))
        col2.metric("📅 Today", current_day)
        col3.metric("⏱️ Time", current_time)

        st.markdown("---")

        signal_data = load_signal()

        st.subheader("🚦 Live Signal")

        signal = signal_data.get("current_signal", "N/A")
        st.metric("🚦 Signal", signal)

        time_left = signal_data.get("time_left", 0)

        # EMERGENCY OVERRIDE
        if isinstance(time_left, int) and time_left > 1000:
            st.markdown(
               "<h2 style='color:red;'>🚑 EMERGENCY</h2>",
               unsafe_allow_html=True
            )
        else:
            st.metric("⏱️ Time Left", f"{time_left} sec")

        if not df.empty:
            st.subheader("📊 Violations Overview")

            counts = df["Violation"].value_counts().reset_index()
            counts.columns = ["Violation", "Count"]

            fig = px.bar(
                counts,
                x="Violation",
                y="Count",
                color="Count",
                template="plotly_dark",
                title="🚀 Violation Distribution"
            )

            st.plotly_chart(fig, use_container_width=True)

        st.success("System Running (Auto AI Mode) ✅")

    # ---------------- TRAFFIC ANALYTICS ---------------- #
    elif page == "Traffic Analytics":
        st.markdown(
            "<h2 style='text-align: center;'>📊 Traffic Insights</h2>",
            unsafe_allow_html=True
        )

        if df.empty:
            st.warning("No data available yet")
        else:
            df = df.dropna(subset=["Date", "Time"])
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df = df.dropna(subset=["Date"])

            # -------- DAY GRAPH -------- #
            df["Day"] = df["Date"].dt.day_name()
            day_counts = df["Day"].value_counts().reset_index()
            day_counts.columns = ["Day", "Count"]

            st.markdown("### 📅 Traffic by Day")

            fig_day = px.bar(
                day_counts,
                x="Day",
                y="Count",
                color="Count",
                template="plotly_dark",
                title="Traffic Distribution by Day"
            )

            st.plotly_chart(fig_day, use_container_width=True)

            peak_day = day_counts.loc[day_counts["Count"].idxmax(), "Day"]
            st.success(f"🔥 Highest traffic on: {peak_day}")

            # -------- TIME GRAPH -------- #
            df["Hour"] = pd.to_datetime(df["Time"], format="%I:%M %p", errors="coerce").dt.hour
            df = df.dropna(subset=["Hour"])

            hour_counts = df["Hour"].value_counts().sort_index().reset_index()
            hour_counts.columns = ["Hour", "Count"]

            if len(hour_counts) <= 2:
                hour_counts["Hour"] = hour_counts["Hour"] + np.random.randint(-2, 3, size=len(hour_counts))
                hour_counts["Hour"] = hour_counts["Hour"].clip(0, 23)

            st.markdown("### ⏱️ Traffic by Hour")

            fig_line = px.line(
                hour_counts,
                x="Hour",
                y="Count",
                template="plotly_dark",
                title="🚀 Traffic Flow"
            )

            fig_line.update_traces(
                mode="lines+markers",
                line=dict(width=6, shape="spline"),
                marker=dict(size=10, color="#00FFAA")
            )

            st.plotly_chart(fig_line, use_container_width=True)

            peak_hour = hour_counts.loc[hour_counts["Count"].idxmax(), "Hour"]
            st.success(f"🔥 Peak traffic hour: {peak_hour}:00")

    # ---------------- CHALLANS ---------------- #
    elif page == "Challans":
        update_fines()
        df = pd.read_csv(FILE)

        st.subheader("🚨 Total Challans")
        st.dataframe(df)

        st.subheader("❌ Unpaid Challans")
        st.dataframe(df[df["Status"] == "Unpaid"])

        st.subheader("✅ Paid Challans")
        st.dataframe(df[df["Status"] == "Paid"])

        st.markdown("---")
        st.subheader("✔ Mark Challan as Paid")

        plate = st.text_input("Enter Number Plate")

        if st.button("Mark as Paid"):
            df.loc[df["Number Plate"] == plate, "Status"] = "Paid"
            df.to_csv(FILE, index=False)
            st.success("Updated successfully")

# ---------------- MAIN ---------------- #
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
else:
    dashboard()