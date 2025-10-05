# app/main.py
import streamlit as st
from app.dashboards import campaign_planner
# later we'll add:
# from app.dashboards import placement_planner, creative_planner, validator

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Naming Governance App",
    layout="wide",
    page_icon="🧩"
)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("📘 Navigation")

pages = {
    "Campaign Planner": campaign_planner,
    # "Placement Planner": placement_planner,
    # "Creative Planner": creative_planner,
    # "Validator (AI)": validator
}

choice = st.sidebar.radio("Choose a module:", list(pages.keys()))

# --- LOAD SELECTED PAGE ---
page = pages[choice]
page.render()

# --- FOOTER / INFO ---
st.sidebar.markdown("---")
st.sidebar.info(
    "💡 Tip: Each planner will generate standardized naming conventions, "
    "check duplicates, and validate structure automatically."
)
