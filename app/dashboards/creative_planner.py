# app/dashboards/creative_planner.py
import streamlit as st
import json
from app.utils.db_manager import init_db, insert_name, fetch_all_names
from app.utils.fuzzy_matcher import find_similar_names

def render():
    st.title("🎨 Creative Name Planner")
    init_db()

    advertiser = st.text_input("Advertiser", "PM")
    plan_number = st.text_input("Plan Number", "1001")
    media_type = st.selectbox("Media Type", ["dis", "vod", "soc"])
    size_format = st.text_input("Size / Format / Duration", "1080x1080, 15 sec")
    creative_message = st.text_input("Creative Message / Free Text", "Festive offer up to 30% off")

    # Dynamic free-form
    st.markdown("### Optional Free-Form Text")
    free_forms = []
    num_extra = st.number_input("Number of extra fields", 0, 10, 0, 1)
    for i in range(num_extra):
        extra = st.text_input(f"Free-form {i+1}")
        if extra.strip():
            free_forms.append(extra.strip().replace(" ", "_"))

    if st.button("Generate Creative Name"):
        name_parts = [advertiser, plan_number, media_type, size_format, creative_message]
        if free_forms:
            name_parts.extend(free_forms)
        name = "_".join([str(p).strip().replace(" ", "").title() for p in name_parts if p])

        st.success(f"Generated Name: **{name}**")

        existing_names = fetch_all_names("creative")
        matches = find_similar_names(name, existing_names)
        if matches:
            st.warning(f"⚠️ Similar names found: {matches}")
        else:
            insert_name({
                "planner_type": "creative",
                "plan_number": plan_number,
                "name": name,
                "advertiser": advertiser,
                "media_type": media_type,
                "size_format": size_format,
                "creative_message": creative_message,
                "free_form": json.dumps(free_forms)
            })
            st.success("✅ Saved successfully — no duplicates found!")
