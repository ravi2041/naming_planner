import streamlit as st
import json
from app.utils.db_manager import init_db, insert_name, fetch_all_names
from app.utils.name_generator import generate_campaign_name
from app.utils.fuzzy_matcher import find_similar_names
from app.utils.name_validator import validate_campaign_inputs
from app.ai.run_langgraph_validator import run_langgraph_validator
from app.utils.config_loader import load_rules


def render():
    st.title("📢 Campaign Name Planner")

    # Initialize DB at startup
    init_db()

    # --- MODE SELECTION ---
    mode = st.radio("Choose Mode", ["Manual Entry", "AI Assisted"], index=0, horizontal=True, key="campaign_mode")

    # --- SESSION STATE INIT ---
    if "generated_name" not in st.session_state:
        st.session_state.generated_name = None
    if "ai_suggestions" not in st.session_state:
        st.session_state.ai_suggestions = []
    if "validation_result" not in st.session_state:
        st.session_state.validation_result = None
    if "fix_suggestion" not in st.session_state:
        st.session_state.fix_suggestion = None

    # ==========================================================
    # 🧍 MANUAL ENTRY MODE
    # ==========================================================
    if mode == "Manual Entry":
        st.subheader("🧍 Manual Campaign Name Builder")

        st.markdown("### 🧱 Base Information")
        advertiser = st.text_input("Advertiser", "PM", key="manual_advertiser").upper()
        plan_number = st.text_input("Plan Number", "1001", key="manual_plan").upper()
        product = st.text_input("Product", "SAREE", key="manual_product").upper()
        objective = st.selectbox("Objective", ["AWAR", "SALES", "LEADS"], key="manual_objective")
        campaign = st.text_input("Campaign Name", "DIWALI FESTIVALS", key="manual_campaign").upper()
        month = st.text_input("Month", "OCT", key="manual_month").upper()
        year = st.text_input("Year", "2025", key="manual_year").upper()

        # --- FREE-FORM FIELDS ---
        st.markdown("### 📝 Optional Free-Form Fields")
        free_forms = []
        num_extra = st.number_input("Number of extra fields", 0, 10, 0, 1, key="manual_freeform_count")
        for i in range(num_extra):
            extra = st.text_input(f"Free-form {i + 1}", key=f"manual_freeform_{i}")
            if extra.strip():
                free_forms.append(extra.strip().replace(" ", "_").upper())

        # --- MANUAL NAME GENERATION ---
        if st.button("🪄 Generate Manual Campaign Name"):
            valid, msg = validate_campaign_inputs(advertiser, plan_number, product, objective, campaign)
            if not valid:
                st.error(msg)
                return

            name = generate_campaign_name(advertiser, plan_number, product, objective, campaign, month, year, free_forms)
            st.session_state.generated_name = name
            st.success(f"🧩 **Generated Name:** `{name}`")

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
                    "source": "manual",
                    "validation_status": "pending"
                }
                insert_name(record)
                st.success("✅ Saved successfully — no duplicates found!")

        # --- VALIDATION FOR MANUAL NAME ---
        if st.session_state.get("generated_name"):
            selected_name = st.session_state.generated_name
            st.markdown(f"### 🧾 Current Manual Campaign: `{selected_name}`")

            if st.button("🔍 Validate This Campaign Name"):
                with st.spinner("Validating campaign name..."):
                    rules = load_rules("campaign_rules.json")
                    details = {
                        "advertiser": advertiser,
                        "plan_number": plan_number,
                        "product": product,
                        "objective": objective,
                        "campaign": campaign,
                        "month": month,
                        "year": year,
                        "free_form": free_forms,
                        "generated_name": selected_name
                    }
                    result = run_langgraph_validator(details, rules)
                    st.session_state.validation_result = result.get("validation_result")
                    st.session_state.fix_suggestion = result.get("fix_suggestion")

            if st.button("✅ Confirm & Use This Campaign"):
                st.session_state.current_campaign = selected_name
                st.success(f"Campaign `{selected_name}` confirmed and ready for Placement Planner.")
                st.info("Proceed to the next step below to continue.")

    # ==========================================================
    # 🤖 AI ASSISTED MODE
    # ==========================================================
    else:
        st.subheader("🤖 AI-Assisted Campaign Name Generator")

        st.markdown("""
        Provide campaign context or fill key fields below (auto-UPPERCASE).  
        The AI will generate standardized campaign names following your naming rules.
        """)

        rules = load_rules("campaign_rules.json")

        # --- STRUCTURED CONTEXT INPUTS ---
        with st.expander("🧩 KEY CAMPAIGN DETAILS (AUTO-UPPERCASE)", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                adv_input = st.text_input("Advertiser Code", "PM", key="ai_advertiser").upper()
                plan_input = st.text_input("Plan Number", "1001", key="ai_plan").upper()
                obj_input = st.selectbox("Objective", ["AWAR", "SALES", "LEADS"], index=0, key="ai_objective")
                prod_input = st.text_input("Product", "SAREE", key="ai_product").upper()
                camp_input = st.text_input("Campaign Theme / Name", "DIWALI FESTIVALS", key="ai_theme").upper()
            with col2:
                month = st.text_input("Month", "OCT", key="ai_month").upper()
                year = st.text_input("Year", "2025", key="ai_year").upper()


        st.markdown("### ✏️ ADDITIONAL CONTEXT (AUTO-UPPERCASE)")
        context_text = st.text_area(
            "Add any extra details (e.g., region, target audience, creative type, or special notes).",
            key="ai_context"
        ).strip().upper()

        combined_context = (
            f"ADVERTISER: {adv_input}\n"
            f"PLAN_NUMBER: {plan_input}\n"
            f"PRODUCT: {prod_input}\n"
            f"OBJECTIVE: {obj_input}\n"
            f"CAMPAIGN: {camp_input}\n"
            f"MONTH: {month}\n"
            f"YEAR: {year}\n"
            f"{context_text}"
        )

        if st.button("✨ Generate AI Campaign Names"):
            if not combined_context.strip():
                st.warning("Please fill at least one field or provide context before generating.")
                st.stop()

            with st.spinner("AI is generating name options..."):
                details = {
                    "advertiser": adv_input,
                    "plan_number": plan_input,
                    "product": prod_input,
                    "objective": obj_input,
                    "campaign": camp_input,
                    "month": month,
                    "year": year,
                    "free_form": [],
                    "context": combined_context
                }
                result_state = run_langgraph_validator(details, rules)

                if result_state.get("error"):
                    st.error(f"Error: {result_state['error']}")
                else:
                    suggestions = result_state.get("generated_suggestions", [])
                    if not suggestions:
                        st.warning("No AI suggestions generated.")
                    else:
                        st.session_state.ai_suggestions = suggestions
                        st.success(f"✅ {len(suggestions)} name suggestions generated!")

        # --- DISPLAY AI SUGGESTIONS ---
        if st.session_state.ai_suggestions:
            st.subheader("🧩 Choose a Campaign Name")

            options = [s["name"].upper() for s in st.session_state.ai_suggestions]
            choice = st.radio("Select one campaign name:", options, index=0, key="ai_choice_campaign")

            reasoning = next(
                (s.get("reasoning", "").upper() for s in st.session_state.ai_suggestions if s["name"].upper() == choice),
                ""
            )
            if reasoning:
                st.caption(f"💡 {reasoning}")

            if st.button("🔍 Validate Selected Name"):
                with st.spinner("Validating selected campaign name..."):
                    rules = load_rules("campaign_rules.json")
                    details = {
                        "advertiser": adv_input,
                        "plan_number": plan_input,
                        "product": prod_input,
                        "objective": obj_input,
                        "campaign": camp_input,
                        "month": month,
                        "year": year,
                        "free_form": [],
                        "generated_name": choice
                    }
                    result = run_langgraph_validator(details, rules)
                    st.session_state.validation_result = result.get("validation_result")
                    st.session_state.fix_suggestion = result.get("fix_suggestion")

            if st.button("✅ Confirm Selection"):
                st.session_state.generated_name = choice
                st.success(f"Selected: `{choice}`")

                record = {
                    "planner_type": "campaign",
                    "plan_number": plan_input,
                    "name": choice,
                    "advertiser": adv_input,
                    "product": prod_input,
                    "objective": obj_input,
                    "campaign": camp_input,
                    "month": month,
                    "year": year,
                    "free_form": json.dumps([]),
                    "source": "ai",
                    "validation_status": "pending"
                }
                insert_name(record)
                st.info("💾 Saved successfully!")

    # ==========================================================
    # ✅ VALIDATION RESULTS + FIX SUGGESTIONS
    # ==========================================================
    if st.session_state.get("validation_result"):
        st.markdown("### ✅ Validation Results")
        results = st.session_state.validation_result
        if isinstance(results, dict):
            results = [results]

        for item in results:
            name = item.get("name", "Unnamed Campaign")
            is_valid = item.get("is_valid", False)
            issues = item.get("issues", [])
            reasoning = item.get("reasoning", "")

            if is_valid:
                st.success(f"✅ **{name}** — Valid and follows all naming rules.")
            else:
                st.error(f"❌ **{name}** — Issues detected.")
                if issues:
                    st.markdown(f"- **Issues:** {', '.join(issues)}")
                if reasoning:
                    st.caption(f"💡 {reasoning}")

    if st.session_state.fix_suggestion:
        st.markdown("### 🧩 AI Fix Suggestions")
        fix = st.session_state.fix_suggestion
        if isinstance(fix, list):
            for f in fix:
                st.info(f"**Suggested Fix:** {f.get('suggested_name')} — {f.get('explanation', '')}")

    # ==========================================================
    # 🚀 MOVE TO NEXT PLANNER
    # ==========================================================
    st.markdown("### 🚀 Proceed to Placement Planner")

    current_campaign = (
        st.session_state.get("generated_name")
        or st.session_state.get("current_campaign")
    )

    if not current_campaign:
        existing_names = fetch_all_names("campaign")
        if existing_names:
            current_campaign = existing_names[-1]

    if current_campaign:
        st.markdown(f"✅ **Selected Campaign:** `{current_campaign}`")

        if st.button("➡️ Next: Placement Planner"):
            st.session_state.current_campaign = current_campaign
            st.session_state.page = "Placement Planner"
            st.rerun()
    else:
        st.info("No campaign selected yet. Generate or validate one first.")
