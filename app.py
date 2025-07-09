import streamlit as st
from datetime import datetime, timedelta
import time
import json
import os
import pandas as pd
from collections import defaultdict
import plotly.express as px
import plotly.graph_objects as go
import pytz

# File for saving productive time
DATA_FILE = "productive_time.json"

# Set page layout
st.set_page_config(page_title="⏳ Enhanced Time Tracker", layout="wide")

# India timezone
INDIA_TZ = pytz.timezone('Asia/Kolkata')


# -----------------------
# Load or Init Data
# -----------------------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    else:
        return {
            "daily_time": {},
            "sessions": [],
            "goals": {"daily": 8 * 3600, "weekly": 40 * 3600},  # in seconds
            "categories": ["Work", "Study", "Personal", "Exercise"],
            "settings": {"theme": "dark", "pomodoro": {"work": 25, "break": 5}}
        }


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_india_now():
    """Get current time in India timezone"""
    return datetime.now(INDIA_TZ)


data = load_data()
today_str = get_india_now().strftime("%Y-%m-%d")
if today_str not in data["daily_time"]:
    data["daily_time"][today_str] = 0.0

# -----------------------
# CSS Styling
# -----------------------
theme = data["settings"]["theme"]
if theme == "dark":
    bg_color = "#0F0F0F"
    text_color = "#F5DEB3"
    accent_color = "#FFD700"
    button_color = "#FFD700"
else:
    bg_color = "#FFFFFF"
    text_color = "#333333"
    accent_color = "#2E86AB"
    button_color = "#2E86AB"

st.markdown(f"""
    <style>
    html, body, [class*="css"] {{
        background-color: {bg_color};
        color: {text_color};
        font-family: 'Courier New', monospace;
    }}
    .big-timer {{
        font-size: 50px !important;
        font-weight: bold;
        color: {accent_color};
        text-align: center;
    }}
    .label {{
        font-size: 22px !important;
        color: {accent_color};
        text-align: center;
        padding-top: 10px;
        padding-bottom: 4px;
    }}
    .section {{
        padding: 20px 0;
    }}
    .stButton>button {{
        border-radius: 10px;
        padding: 0.75em 1.5em;
        font-size: 16px;
        font-weight: bold;
        color: {bg_color};
        background-color: {button_color};
        border: none;
        transition: all 0.3s ease-in-out;
    }}
    .stButton>button:hover {{
        background-color: {accent_color};
        transform: scale(1.05);
    }}
    .streak-box {{
        background-color: {accent_color};
        color: {bg_color};
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        margin: 10px 0;
    }}
    .timezone-info {{
        text-align: center;
        font-size: 14px;
        color: {accent_color};
        margin-bottom: 20px;
    }}
    </style>
""", unsafe_allow_html=True)


# -----------------------
# Helper Functions
# -----------------------
def get_remaining_today():
    """Get remaining time in current day (India timezone)"""
    now = get_india_now()
    end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    seconds = int((end - now).total_seconds())
    return max(0, seconds)


def get_remaining_month():
    """Get remaining time in current month (India timezone)"""
    now = get_india_now()
    if now.month == 12:
        next_month = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        next_month = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)

    # Last second of current month
    end = next_month - timedelta(microseconds=1)
    seconds = int((end - now).total_seconds())
    return max(0, seconds)


def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours}h {minutes}m {secs}s"


def get_streak():
    dates = sorted(data["daily_time"].keys())
    if not dates:
        return 0

    streak = 0
    current_date = get_india_now().date()

    for i in range(len(dates)):
        date_obj = datetime.strptime(dates[-(i + 1)], "%Y-%m-%d").date()
        if data["daily_time"][dates[-(i + 1)]] > 0:
            if date_obj == current_date - timedelta(days=i):
                streak += 1
            else:
                break
        else:
            break
    return streak


def get_weekly_time():
    """Get total time for current week (Monday to Sunday, India timezone)"""
    now = get_india_now()
    week_start = now - timedelta(days=now.weekday())
    week_time = 0

    for i in range(7):
        date_str = (week_start + timedelta(days=i)).strftime("%Y-%m-%d")
        if date_str in data["daily_time"]:
            week_time += data["daily_time"][date_str]

    return week_time


# -----------------------
# Session State
# -----------------------
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "timer_running" not in st.session_state:
    st.session_state.timer_running = False
if "live_elapsed" not in st.session_state:
    st.session_state.live_elapsed = 0.0
if "current_category" not in st.session_state:
    st.session_state.current_category = "Work"
if "session_note" not in st.session_state:
    st.session_state.session_note = ""
if "pomodoro_mode" not in st.session_state:
    st.session_state.pomodoro_mode = False
if "pomodoro_work_time" not in st.session_state:
    st.session_state.pomodoro_work_time = data["settings"]["pomodoro"]["work"] * 60
if "pomodoro_break_time" not in st.session_state:
    st.session_state.pomodoro_break_time = data["settings"]["pomodoro"]["break"] * 60
if "is_break" not in st.session_state:
    st.session_state.is_break = False

# -----------------------
# Sidebar
# -----------------------
with st.sidebar:
    st.title("🎯 Controls")

    # Theme selector
    theme_option = st.selectbox("Theme", ["dark", "light"],
                                index=0 if data["settings"]["theme"] == "dark" else 1)
    if theme_option != data["settings"]["theme"]:
        data["settings"]["theme"] = theme_option
        save_data(data)
        st.rerun()

    # Category selector
    st.session_state.current_category = st.selectbox("Category", data["categories"])

    # Session note
    st.session_state.session_note = st.text_area("Session Note",
                                                 value=st.session_state.session_note,
                                                 height=80)

    # Pomodoro settings
    st.subheader("🍅 Pomodoro")
    st.session_state.pomodoro_mode = st.checkbox("Enable Pomodoro",
                                                 value=st.session_state.pomodoro_mode)

    if st.session_state.pomodoro_mode:
        work_min = st.slider("Work time (min)", 15, 60, data["settings"]["pomodoro"]["work"])
        break_min = st.slider("Break time (min)", 5, 30, data["settings"]["pomodoro"]["break"])

        if work_min != data["settings"]["pomodoro"]["work"] or break_min != data["settings"]["pomodoro"]["break"]:
            data["settings"]["pomodoro"]["work"] = work_min
            data["settings"]["pomodoro"]["break"] = break_min
            st.session_state.pomodoro_work_time = work_min * 60
            st.session_state.pomodoro_break_time = break_min * 60
            save_data(data)

    # Goals
    st.subheader("🎯 Goals")
    daily_goal = st.slider("Daily goal (hours)", 1, 16, data["goals"]["daily"] // 3600)
    weekly_goal = st.slider("Weekly goal (hours)", 5, 80, data["goals"]["weekly"] // 3600)

    if daily_goal != data["goals"]["daily"] // 3600 or weekly_goal != data["goals"]["weekly"] // 3600:
        data["goals"]["daily"] = daily_goal * 3600
        data["goals"]["weekly"] = weekly_goal * 3600
        save_data(data)

# -----------------------
# Main Content
# -----------------------
# Show current India time
india_time = get_india_now()
st.markdown(f"<div class='timezone-info'>🇮🇳 India Time: {india_time.strftime('%Y-%m-%d %I:%M:%S %p IST')}</div>",
            unsafe_allow_html=True)

# Header with streak
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("<div class='label'>📅 Time Remaining This Month</div>", unsafe_allow_html=True)
    sec = get_remaining_month()
    st.markdown(f"<div class='big-timer'>{format_time(sec)}</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='label'>📆 Time Remaining Today</div>", unsafe_allow_html=True)
    sec = get_remaining_today()
    st.markdown(f"<div class='big-timer'>{format_time(sec)}</div>", unsafe_allow_html=True)

with col3:
    streak = get_streak()
    st.markdown(f"<div class='streak-box'>🔥 {streak} Day Streak</div>", unsafe_allow_html=True)

# -----------------------
# Focus Timer + Controls
# -----------------------
st.markdown("<div class='label'>🎯 Focus Session Timer</div>", unsafe_allow_html=True)

# If running, update live_elapsed
if st.session_state.timer_running:
    now = time.time()
    st.session_state.live_elapsed += now - (st.session_state.start_time or now)
    st.session_state.start_time = now

# Pomodoro logic
if st.session_state.pomodoro_mode and st.session_state.timer_running:
    if not st.session_state.is_break:
        remaining = st.session_state.pomodoro_work_time - st.session_state.live_elapsed
        if remaining <= 0:
            st.session_state.is_break = True
            st.session_state.live_elapsed = 0
            st.session_state.start_time = time.time()
            st.success("Work session complete! Take a break!")
    else:
        remaining = st.session_state.pomodoro_break_time - st.session_state.live_elapsed
        if remaining <= 0:
            st.session_state.is_break = False
            st.session_state.live_elapsed = 0
            st.session_state.start_time = time.time()
            st.success("Break over! Ready for next work session!")

# Display timer
if st.session_state.pomodoro_mode:
    if st.session_state.is_break:
        remaining = st.session_state.pomodoro_break_time - st.session_state.live_elapsed
        st.markdown(f"<div class='label'>☕ Break Time</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='big-timer'>{format_time(max(0, remaining))}</div>", unsafe_allow_html=True)
    else:
        remaining = st.session_state.pomodoro_work_time - st.session_state.live_elapsed
        st.markdown(f"<div class='label'>🍅 Work Time</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='big-timer'>{format_time(max(0, remaining))}</div>", unsafe_allow_html=True)
else:
    total_sec = int(data["daily_time"][today_str] + st.session_state.live_elapsed)
    st.markdown(f"<div class='big-timer'>{format_time(total_sec)}</div>", unsafe_allow_html=True)

# Progress bars
col1, col2 = st.columns(2)
with col1:
    daily_progress = (data["daily_time"][today_str] + st.session_state.live_elapsed) / data["goals"]["daily"]
    st.progress(min(daily_progress, 1.0))
    st.caption(f"Daily Goal: {format_time(data['goals']['daily'])}")

with col2:
    weekly_progress = get_weekly_time() / data["goals"]["weekly"]
    st.progress(min(weekly_progress, 1.0))
    st.caption(f"Weekly Goal: {format_time(data['goals']['weekly'])}")

# Buttons
colA, colB, colC = st.columns([2, 2, 2])
with colB:
    colX, colY = st.columns(2)

    if colX.button("▶️ Start"):
        st.session_state.start_time = time.time()
        st.session_state.timer_running = True
        st.session_state.live_elapsed = 0

    if colY.button("⏹ Stop"):
        st.session_state.timer_running = False
        if st.session_state.live_elapsed > 0:
            # Save session with India timezone
            session = {
                "date": today_str,
                "start_time": get_india_now().isoformat(),
                "duration": st.session_state.live_elapsed,
                "category": st.session_state.current_category,
                "note": st.session_state.session_note,
                "pomodoro": st.session_state.pomodoro_mode
            }
            data["sessions"].append(session)

            # Update daily time
            if not st.session_state.is_break:  # Only count work time
                data["daily_time"][today_str] += st.session_state.live_elapsed

            save_data(data)
            st.session_state.live_elapsed = 0.0
            st.session_state.session_note = ""
        st.session_state.start_time = None
        st.session_state.is_break = False

# -----------------------
# Analytics Tab
# -----------------------
tabs = st.tabs(["📊 Analytics", "📈 Reports", "⚙️ Settings"])

with tabs[0]:
    if data["sessions"]:
        # Recent sessions
        st.subheader("Recent Sessions")
        recent_sessions = data["sessions"][-10:]  # Last 10 sessions
        for session in reversed(recent_sessions):
            # Parse and format time in India timezone
            try:
                session_time = datetime.fromisoformat(session['start_time'].replace('Z', '+00:00'))
                if session_time.tzinfo is None:
                    session_time = INDIA_TZ.localize(session_time)
                else:
                    session_time = session_time.astimezone(INDIA_TZ)
                formatted_time = session_time.strftime('%I:%M %p IST')
            except:
                formatted_time = "Unknown time"

            with st.expander(
                    f"{session['category']} - {format_time(session['duration'])} ({session['date']} at {formatted_time})"):
                st.write(f"**Duration:** {format_time(session['duration'])}")
                st.write(f"**Category:** {session['category']}")
                st.write(f"**Note:** {session['note'] or 'No note'}")
                st.write(f"**Pomodoro:** {'Yes' if session['pomodoro'] else 'No'}")

        # Category breakdown
        st.subheader("Time by Category")
        category_time = defaultdict(float)
        for session in data["sessions"]:
            category_time[session["category"]] += session["duration"]

        if category_time:
            fig = px.pie(
                values=list(category_time.values()),
                names=list(category_time.keys()),
                title="Time Distribution by Category"
            )
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No sessions recorded yet. Start tracking to see analytics!")

with tabs[1]:
    if data["daily_time"]:
        # Daily time chart
        st.subheader("Daily Time Report")
        dates = sorted(data["daily_time"].keys())[-30:]  # Last 30 days
        times = [data["daily_time"][date] / 3600 for date in dates]  # Convert to hours

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=times, mode='lines+markers', name='Daily Time'))
        fig.add_hline(y=data["goals"]["daily"] / 3600, line_dash="dash", line_color="red", annotation_text="Daily Goal")
        fig.update_layout(title="Daily Time Tracking (India Timezone)", xaxis_title="Date", yaxis_title="Hours")
        st.plotly_chart(fig, use_container_width=True)

        # Export data
        if st.button("📥 Export Data"):
            df = pd.DataFrame(data["sessions"])
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"time_tracker_data_{get_india_now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No data to display yet. Start tracking to see reports!")

with tabs[2]:
    st.subheader("Categories")
    new_category = st.text_input("Add new category")
    if st.button("Add Category") and new_category:
        if new_category not in data["categories"]:
            data["categories"].append(new_category)
            save_data(data)
            st.rerun()

    st.write("Current categories:")
    for i, category in enumerate(data["categories"]):
        col1, col2 = st.columns([3, 1])
        col1.write(category)
        if col2.button("Remove", key=f"remove_{i}") and len(data["categories"]) > 1:
            data["categories"].remove(category)
            save_data(data)
            st.rerun()

# Keyboard shortcuts info
st.markdown("---")
st.markdown("**Keyboard Shortcuts:** Press Space to Start/Stop timer")
st.markdown("**Timezone:** All times are in India Standard Time (IST)")

# Auto-refresh
if st.session_state.timer_running:
    time.sleep(1)
    st.rerun()

# Handle keyboard shortcuts with JavaScript
st.markdown("""
<script>
document.addEventListener('keydown', function(e) {
    if (e.code === 'Space' && !e.target.matches('input, textarea')) {
        e.preventDefault();
        // Find start/stop buttons and click them
        const buttons = document.querySelectorAll('button');
        for (let button of buttons) {
            if (button.textContent.includes('▶️ Start') || button.textContent.includes('⏹ Stop')) {
                button.click();
                break;
            }
        }
    }
});
</script>
""", unsafe_allow_html=True)