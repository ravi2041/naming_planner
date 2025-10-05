# app/dashboards/placement_planner.py
import streamlit as st
import json
from app.utils.db_manager import init_db, insert_name, fetch_all_names
from app.utils.fuzzy_matcher import find_similar_names
from app.utils.name_generator import generate_campaign_name  # same generator, flexible

def render():
    st.title("📺 Placement / Media Buy Planner")
    init_db()

    advertiser = st.text_input("Advertiser", "PM")
    plan_number = st.text_input("Plan Number", "1001")
    strategy_tactic = st.selectbox("Strategy Tactic", ["cons", "conv", "awar"])
    publisher = st.text_input("Publisher / Media Agency Name")
    site = st.selectbox("Site", ["ytb", "meta", "tiktok"])
    media_type = st.selectbox("Media Type", ["vid", "dis"])
    targeting = st.text_input("Targeting Audience", "AP25-54")
    size_format = st.text_input("Size / Format / Duration", "1080x720, 30 sec")

    # Dynamic free-form
    st.markdown("### Optional Free-Form Text")
    free_forms = []
    num_extra = st.number_input("Number of extra fields", 0, 10, 0, 1)
    for i in range(num_extra):
        extra = st.text_input(f"Free-form {i+1}")
        if extra.strip():
            free_forms.append(extra.strip().replace(" ", "_"))

    if st.button("Generate Placement Name"):
        name_parts = [advertiser, plan_number, strategy_tactic, publisher, site, media_type, targeting, size_format]
        if free_forms:
            name_parts.extend(free_forms)
        name = "_".join([str(p).strip().replace(" ", "").title() for p in name_parts if p])

        st.success(f"Generated Name: **{name}**")

        existing_names = fetch_all_names("placement")
        matches = find_similar_names(name, existing_names)
        if matches:
            st.warning(f"⚠️ Similar names found: {matches}")
        else:
            insert_name({
                "planner_type": "placement",
                "plan_number": plan_number,
                "name": name,
                "advertiser": advertiser,
                "strategy_tactic": strategy_tactic,
                "publisher": publisher,
                "site": site,
                "media_type": media_type,
                "targeting": targeting,
                "size_format": size_format,
                "free_form": json.dumps(free_forms)
            })
            st.success("✅ Saved successfully — no duplicates found!")
