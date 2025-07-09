import streamlit as st
from datetime import datetime, timedelta
import time
import json
import os

# File for saving productive time
DATA_FILE = "productive_time.json"

# Set page layout
st.set_page_config(page_title="⏳ Time Tracker", layout="wide")

# -----------------------
# Load or Init Data
# -----------------------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    else:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()
today_str = datetime.now().strftime("%Y-%m-%d")
if today_str not in data:
    data[today_str] = 0.0

# -----------------------
# CSS Styling
# -----------------------
st.markdown("""
    <style>
    html, body, [class*="css"] {
        background-color: #0F0F0F;
        color: #F5DEB3;
        font-family: 'Courier New', monospace;
    }
    .big-timer {
        font-size: 50px !important;
        font-weight: bold;
        color: #FFD700;
        text-align: center;
    }
    .label {
        font-size: 22px !important;
        color: #FFB347;
        text-align: center;
        padding-top: 10px;
        padding-bottom: 4px;
    }
    .section {
        padding: 20px 0;
    }
    .stButton>button {
        border-radius: 10px;
        padding: 0.75em 1.5em;
        font-size: 16px;
        font-weight: bold;
        color: #121212;
        background-color: #FFD700;
        border: none;
        transition: all 0.3s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #FFC300;
        transform: scale(1.05);
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------
# Time Helpers
# -----------------------
def get_remaining_today():
    now = datetime.now()
    end = now.replace(hour=23, minute=59, second=59)
    seconds = int((end - now).total_seconds())
    return seconds

def get_remaining_month():
    now = datetime.now()
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1)
    else:
        next_month = datetime(now.year, now.month + 1, 1)
    end = next_month.replace(hour=0, minute=0, second=0) - timedelta(seconds=1)
    seconds = int((end - now).total_seconds())
    return seconds

# -----------------------
# Session State
# -----------------------
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "timer_running" not in st.session_state:
    st.session_state.timer_running = False
if "live_elapsed" not in st.session_state:
    st.session_state.live_elapsed = 0.0

# -----------------------
# Header Timers
# -----------------------
col1, col2 = st.columns(2)

with col1:
    st.markdown("<div class='label'>📅 Time Remaining This Month</div>", unsafe_allow_html=True)
    sec = get_remaining_month()
    h, m, s = sec // 3600, (sec % 3600) // 60, sec % 60
    st.markdown(f"<div class='big-timer'>{h}h {m}m {s}s</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='label'>📆 Time Remaining Today</div>", unsafe_allow_html=True)
    sec = get_remaining_today()
    h, m, s = sec // 3600, (sec % 3600) // 60, sec % 60
    st.markdown(f"<div class='big-timer'>{h}h {m}m {s}s</div>", unsafe_allow_html=True)

# -----------------------
# Focus Timer + Controls
# -----------------------
st.markdown("<div class='label'>🎯 Focus Session Timer</div>", unsafe_allow_html=True)

# If running, update live_elapsed
if st.session_state.timer_running:
    now = time.time()
    st.session_state.live_elapsed += now - (st.session_state.start_time or now)
    st.session_state.start_time = now

# Combine live + saved for display
total_sec = int(data[today_str] + st.session_state.live_elapsed)
hr, mn, sc = total_sec // 3600, (total_sec % 3600) // 60, total_sec % 60
st.markdown(f"<div class='big-timer'>{hr}h {mn}m {sc}s</div>", unsafe_allow_html=True)

# Buttons
colA, colB, colC = st.columns([2, 2, 2])
with colB:
    colX, colY = st.columns(2)

    if colX.button("▶️ Start"):
        st.session_state.start_time = time.time()
        st.session_state.timer_running = True

    if colY.button("⏹ Stop"):
        st.session_state.timer_running = False
        if st.session_state.live_elapsed > 0:
            data[today_str] += st.session_state.live_elapsed
            save_data(data)
            st.session_state.live_elapsed = 0.0
        st.session_state.start_time = None

# Refresh every second
time.sleep(1)
st.rerun()
