# app/dashboards/campaign_planner.py
import streamlit as st
import json
from app.utils.db_manager import init_db, insert_name, fetch_all_names
from app.utils.name_generator import generate_campaign_name
from app.utils.fuzzy_matcher import find_similar_names
from app.utils.name_validator import validate_campaign_inputs


def render():
    st.title("📢 Campaign Name Planner")

    init_db()

    st.markdown("### 🧱 Base Information")
    advertiser = st.text_input("Advertiser", "PM")
    plan_number = st.text_input("Plan Number", "1001")
    product = st.text_input("Product", "Saree")
    objective = st.selectbox("Objective", ["awar", "sales", "leads"])
    campaign = st.text_input("Campaign Name", "Diwali Festivals")
    month = st.text_input("Month", "Oct")
    year = st.text_input("Year", "2025")

    st.markdown("### 📝 Optional Free-Form Fields")
    free_forms = []
    num_extra = st.number_input("Number of extra fields", 0, 10, 0, 1)
    for i in range(num_extra):
        extra = st.text_input(f"Free-form {i+1}")
        if extra.strip():
            free_forms.append(extra.strip().replace(" ", "_"))

    # --- Validation + Generation ---
    if st.button("Generate Campaign Name"):
        valid, msg = validate_campaign_inputs(advertiser, plan_number, product, objective, campaign)
        if not valid:
            st.error(msg)
            return

        name = generate_campaign_name(advertiser, plan_number, product, objective, campaign, month, year, free_forms)
        st.success(f"🪄 Generated Name: **{name}**")

        # --- Duplicate detection ---
        existing_names = fetch_all_names("campaign")
        matches = find_similar_names(name, existing_names)
        if matches:
            st.warning(f"⚠️ Similar names found:\n\n{matches}")
        else:
            record = {
                "planner_type": "campaign",
                "plan_number": plan_number,
                "name": name,
                "advertiser": advertiser,
                "product": product,
                "objective": objective,
                "campaign": campaign,
                "month": month,
                "year": year,
                "free_form": json.dumps(free_forms),
            }
            insert_name(record)
            st.success("✅ Saved successfully — no duplicates found!")

    # --- Display saved names ---
    st.markdown("### 📋 Saved Campaign Names")
    all_names = fetch_all_names("campaign")
    if all_names:
        st.dataframe({"Campaign Names": all_names})
    else:
        st.info("No campaign names created yet.")
