import streamlit as st
import json
from app.utils.db_manager import init_db, insert_name, fetch_all_names
from app.utils.fuzzy_matcher import find_similar_names
from app.ai.generate_placement_name_node import generate_placement_name_step
from app.ai.validate_placement_name_node import validate_placement_name_step
from app.config import placement_rules


def render():
    st.title("📺 Placement / Media Buy Naming Planner")
    st.caption("Define placement names manually or generate them with AI based on naming rules.")
    init_db()

    # --- CONTEXT: ACTIVE CAMPAIGN ---
    active_campaign = st.session_state.get("current_campaign", None)
    if active_campaign:
        st.markdown(f"### 📢 Active Campaign: `{active_campaign}`")
    else:
        st.warning("⚠️ No campaign selected. Please go back to Campaign Planner first.")
        st.stop()

    # ---- Mode Selector ----
    mode = st.radio("Choose Mode", ["Manual Entry", "AI Assisted"], horizontal=True)

    # Load rules
    rules = placement_rules
    validation_rules = rules.get("validation", {})

    # --- Initialize session state for this session's placements ---
    if "current_session_placements" not in st.session_state:
        st.session_state.current_session_placements = []

    # -----------------------------
    # MANUAL ENTRY MODE
    # -----------------------------
    if mode == "Manual Entry":
        st.subheader("🧍 Manual Placement Name Builder")

        col1, col2 = st.columns(2)
        with col1:
            advertiser = st.text_input("Advertiser Code", "PM").upper()
            plan_number = st.text_input("Plan Number", "1001").upper()
            strategy_tactic = st.selectbox("Strategy / Tactic", ["CONS", "CONV", "AWAR"])
            publisher = st.text_input("Publisher / Media Agency", "").upper()
            site = st.selectbox("Platform / Site", ["YTB", "META", "TIKTOK"])
        with col2:
            media_type = st.selectbox("Media Type", ["VID", "DIS"])
            targeting = st.text_input("Target Audience", "AP25-54").upper()
            size_format = st.text_input("Size / Format / Duration", "1080X720_30S").upper()

        # ---- Free Form Fields ----
        st.markdown("### Optional Free-Form Text")
        free_forms = []
        num_extra = st.number_input("Number of extra fields", 0, 10, 0, 1)
        for i in range(num_extra):
            extra = st.text_input(f"Free-form {i+1}")
            if extra.strip():
                free_forms.append(extra.strip().replace(" ", "_").upper())

        if st.button("Generate Placement Name"):
            name_parts = [
                active_campaign,
                advertiser,
                plan_number,
                strategy_tactic,
                publisher,
                site,
                media_type,
                targeting,
                size_format
            ] + free_forms

            name = "_".join([p.strip().replace(" ", "_") for p in name_parts if p])
            name = name.upper().replace("__", "_")

            # ---- Validation ----
            validation_state = validate_placement_name_step({
                "placement_names": [name],
                "placement_rules": rules
            })

            result = validation_state["validation_result"][0]
            if not result["is_valid"]:
                st.error("❌ Validation failed:")
                for issue in result["issues"]:
                    st.markdown(f"- {issue}")
            else:
                st.success(f"✅ Valid Placement Name: **{name}**")

                # ---- Duplicate Check ----
                existing_names = fetch_all_names("placement")
                matches = find_similar_names(name, existing_names)

                if matches:
                    st.warning(f"⚠️ Similar names found: {matches}")
                else:
                    insert_name({
                        "planner_type": "placement",
                        "plan_number": plan_number,
                        "campaign": active_campaign,  # <-- NEW: link to campaign
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
                    st.session_state.current_session_placements.append(name)
                    st.success(f"💾 Saved `{name}` for this session.")

    # -----------------------------
    # AI MODE
    # -----------------------------
    else:
        st.subheader("🤖 AI Placement Name Generator")

        st.markdown("""
        Provide campaign or placement details below.  
        You can either **fill key fields** or describe it in your own words — all inputs will be auto-converted to UPPERCASE.
        """)

        # --- Dynamic key fields from rules ---
        basic_fields = [
            f for f in rules.get("fields", [])
            if f["key"] in [
                "advertiser", "plan_number", "strategy_tactic",
                "publisher", "site", "media_type", "target_audience"
            ]
        ]

        user_inputs = {}
        with st.expander("🧩 KEY PLACEMENT DETAILS (AUTO-UPPERCASE)", expanded=True):
            cols = st.columns(2)
            for i, field in enumerate(basic_fields):
                col = cols[i % 2]
                with col:
                    label = field["label"].upper()
                    example = field.get("example", "").upper()
                    description = field.get("description", "")
                    placeholder = f"e.g., {example}" if example else ""
                    val = st.text_input(label, placeholder=placeholder, help=description, key=f"ai_{field['key']}")
                    user_inputs[field["key"]] = val.strip().upper()

        st.markdown("### ✏️ ADDITIONAL CONTEXT (AUTO-UPPERCASE)")
        context_text = st.text_area(
            "Add any extra details (e.g., targeting, season, creative type, etc.)",
            key="ai_context"
        ).strip().upper()

        combined_context = f"CAMPAIGN: {active_campaign}\n"
        combined_context += "\n".join(
            [f"{k.upper()}: {v}" for k, v in user_inputs.items() if v]
        )
        if context_text:
            combined_context += "\n" + context_text

        if st.button("GENERATE WITH AI"):
            if not combined_context.strip():
                st.warning("Please fill at least one field or provide context before generating.")
                st.stop()

            with st.spinner("Generating placement name suggestions..."):
                state = {
                    "context": combined_context,
                    "placement_rules": rules
                }
                ai_output = generate_placement_name_step(state)

            if not ai_output or "placement_names" not in ai_output:
                st.error("⚠️ AI generation failed. Please try again.")
                st.stop()

            names = ai_output["placement_names"]
            st.success("✅ AI GENERATED SUGGESTIONS:")

            session_names = []
            for i, suggestion in enumerate(names, start=1):
                name = suggestion["name"].upper()
                reasoning = suggestion.get("reasoning", "").upper()

                validation = validate_placement_name_step({
                    "placement_names": [name],
                    "placement_rules": rules
                })["validation_result"][0]

                valid_icon = "✅" if validation["is_valid"] else "❌"
                st.markdown(f"**{valid_icon} OPTION {i}:** `{name}`")
                if reasoning:
                    st.caption(reasoning)

                if not validation["is_valid"]:
                    for issue in validation["issues"]:
                        st.markdown(f"- {issue}")
                else:
                    insert_name({
                        "planner_type": "placement",
                        "plan_number": user_inputs.get("plan_number", ""),
                        "campaign": active_campaign,  # <-- NEW: linked campaign
                        "name": name,
                        "advertiser": user_inputs.get("advertiser", ""),
                        "strategy_tactic": user_inputs.get("strategy_tactic", ""),
                        "publisher": user_inputs.get("publisher", ""),
                        "site": user_inputs.get("site", ""),
                        "media_type": user_inputs.get("media_type", ""),
                        "targeting": user_inputs.get("target_audience", ""),
                        "size_format": "",
                        "free_form": "[]"
                    })
                    session_names.append(name)
                    st.success(f"💾 SAVED `{name}` TO DATABASE.")

            if session_names:
                st.session_state.current_session_placements.extend(session_names)

    # -----------------------------
    # SELECTION & PROCEED SECTION
    # -----------------------------
    if st.session_state.current_session_placements:
        st.markdown("---")
        st.subheader("✅ Review and Select Placements for Next Step")

        selected = st.multiselect(
            "Select one or more placements to proceed with:",
            st.session_state.current_session_placements,
            default=st.session_state.current_session_placements,
            key="session_selected_placements"
        )

        if selected:
            st.session_state.selected_placements = selected
            st.success(f"{len(selected)} placement(s) selected.")
            if st.button("➡️ Proceed to Creative Planner"):
                st.session_state.page = "Creative Planner"
                st.rerun()
        else:
            st.info("Select at least one placement to continue.")
    else:
        st.info("No placements created yet. Generate manually or via AI first.")
