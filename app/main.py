# app/main.py
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from app.dashboards import campaign_planner, placement_planner, creative_planner

# --- PAGE CONFIG ---
st.set_page_config(page_title="Naming Governance App", layout="wide", page_icon="🧩")

# --- PERSISTENT PAGE STATE ---
if "page" not in st.session_state:
    st.session_state.page = "Campaign Planner"

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("📘 Navigation")

nav_choice = st.sidebar.radio(
    "Choose a module:",
    ["Campaign Planner", "Placement Planner", "Creative Planner"],
    index=["Campaign Planner", "Placement Planner", "Creative Planner"].index(st.session_state.page),
)

# Keep sidebar selection in sync
st.session_state.page = nav_choice

# --- ROUTING MAP ---
pages = {
    "Campaign Planner": campaign_planner,
    "Placement Planner": placement_planner,
    "Creative Planner": creative_planner,
}

# --- LOAD SELECTED PAGE ---
page = pages[st.session_state.page]
page.render()

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.info("💡 Each planner generates standardized names, validates them, and links automatically.")
