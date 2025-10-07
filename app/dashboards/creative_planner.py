import streamlit as st
import json
from app.utils.db_manager import init_db, insert_name
from app.ai.generate_creative_name_node import generate_creative_name_step
from app.ai.validate_creative_name_node import validate_creative_name_step
from app.config import creative_rules


def render():
    st.session_state.page = "Creative Planner"  # lock to this page during reruns
    st.title("🎨 Creative Naming Planner")
    st.caption("Create creative-level names manually or generate them automatically with AI.")

    init_db()

    # --- CONTEXT: Active Campaign & Placements ---
    active_campaign = st.session_state.get("current_campaign", None)
    selected_placements = st.session_state.get("selected_placements", [])

    st.markdown("## 🧱 Active Context")
    if active_campaign:
        st.markdown(f"**📢 ACTIVE CAMPAIGN:** `{active_campaign}`")
    else:
        st.warning("⚠️ No campaign selected. Please go back to the Campaign Planner.")
        st.stop()

    if selected_placements:
        st.markdown("**🎯 ACTIVE PLACEMENTS:**")
        for placement in selected_placements:
            st.markdown(f"- `{placement}`")
    else:
        st.warning("⚠️ No placements selected. Please go back to the Placement Planner.")
        st.stop()

    # --- Initialize session state ---
    if "current_session_creatives" not in st.session_state:
        st.session_state.current_session_creatives = []

    rules = creative_rules or {}
    mode = st.radio("Choose Mode", ["Manual Entry", "AI Assisted", "Creative Mix Generator"], horizontal=True)

    # -------------------------------------------------
    # 1️⃣ MANUAL MODE
    # -------------------------------------------------
    if mode == "Manual Entry":
        st.subheader("🧍 MANUAL CREATIVE NAME BUILDER")

        col1, col2 = st.columns(2)
        with col1:
            creative_message = st.text_input("Creative Message / Tagline", "DIWALI OFFER 15 PERCENT OFF").upper()
            duration = st.text_input("Duration / Format", "30S").upper()
            version = st.text_input("Version / Variant", "A").upper()
        with col2:
            language = st.text_input("Language / Market", "EN_NZ").upper()
            creative_type = st.selectbox("Creative Type", ["STATIC", "VIDEO", "CAROUSEL"])

        st.markdown("### OPTIONAL FREE-FORM TEXT")
        extras = []
        n_extras = st.number_input("Number of extra fields", 0, 10, 0, 1)
        for i in range(n_extras):
            val = st.text_input(f"Extra Field {i+1}").strip().upper()
            if val:
                extras.append(val.replace(" ", "_"))

        selected_base = st.selectbox("Select Base Placement to Link Creative:", selected_placements)

        if st.button("🪄 Generate Creative Name"):
            parts = [
                active_campaign,
                selected_base,
                creative_message,
                duration,
                version,
                language,
                creative_type
            ] + extras
            name = "_".join([p.replace(" ", "_") for p in parts if p])
            name = name.upper().replace("__", "_")

            validation_state = validate_creative_name_step({
                "creative_names": [name],
                "creative_rules": rules
            })
            result = validation_state["validation_result"][0]

            if not result["is_valid"]:
                st.error("❌ Validation Failed:")
                for issue in result["issues"]:
                    st.markdown(f"- {issue}")
            else:
                st.success(f"✅ Valid Creative Name: **{name}**")

                insert_name({
                    "planner_type": "creative",
                    "name": name,
                    "creative_message": creative_message,
                    "size_format": duration,
                    "free_form": json.dumps(extras),
                    "source": "manual",
                    "validation_status": "pending",
                    "campaign": active_campaign,
                    "media_type": creative_type,
                })

                st.session_state.current_session_creatives.append(name)
                st.success(f"💾 Saved `{name}` for this session.")

    # -----------------------------
    # 2️⃣ AI-ASSISTED MODE (SELECT + REVIEW UNIFIED)
    # -----------------------------
    elif mode == "AI Assisted":
        st.subheader("🤖 AI-Assisted Creative Name Generator")
        st.markdown("""
        Provide creative context such as message, duration, and tone.  
        The AI will generate standardized creative names linked to your active campaign and placements.
        """)

        creative_context = st.text_area(
            "Describe the creative context (e.g., festive offer, product focus, language variants):",
            key="ai_creative_context"
        ).strip().upper()

        if st.button("✨ GENERATE CREATIVE NAMES WITH AI"):
            if not creative_context:
                st.warning("Please enter some creative context before generating.")
                st.stop()

            with st.spinner("Generating creative name suggestions..."):
                state = {
                    "context": creative_context,
                    "creative_rules": rules,
                    "base_placements": selected_placements,
                    "campaign": active_campaign
                }
                ai_output = generate_creative_name_step(state)

            if not ai_output or "creative_names" not in ai_output:
                st.error("⚠️ AI generation failed. Please try again.")
                st.stop()

            creative_output = ai_output.get("creative_names", [])
            all_generated = []

            if isinstance(creative_output, dict):
                for placement, names in creative_output.items():
                    for suggestion in names:
                        name = suggestion["name"].upper() if isinstance(suggestion, dict) else str(suggestion).upper()
                        all_generated.append(name)
            elif isinstance(creative_output, list):
                for suggestion in creative_output:
                    name = suggestion["name"].upper() if isinstance(suggestion, dict) else str(suggestion).upper()
                    all_generated.append(name)

            st.session_state.generated_ai_creatives = all_generated
            st.success(f"✅ Generated {len(all_generated)} creative options!")

        # --- Let user select which ones to keep (no DB save yet)
        if "generated_ai_creatives" in st.session_state and st.session_state.generated_ai_creatives:
            ai_creatives = st.session_state.generated_ai_creatives
            selected = st.multiselect(
                "Select which creative names you want to keep for this session:",
                ai_creatives,
                key="selected_ai_creatives"
            )

            if selected:
                st.session_state.current_session_creatives.extend(
                    [s for s in selected if s not in st.session_state.current_session_creatives]
                )
                st.success(f"{len(selected)} creative(s) added to your session.")


    # -------------------------------------------------
    # 3️⃣ CREATIVE MIX GENERATOR
    # -------------------------------------------------
    else:
        st.subheader("🎛️ CREATIVE MIX GENERATOR")
        st.markdown("""
        Generate multiple creative variations across all selected placements.  
        Then select which ones to keep or retry generation.
        """)

        mix_context = st.text_area(
            "Add general campaign/creative context for generating the mix (AUTO-UPPERCASE):",
            key="mix_context"
        ).strip().upper()

        if st.button("🧩 GENERATE CREATIVE MIX"):
            if not mix_context:
                st.warning("Please provide at least some campaign or creative context.")
                st.stop()

            with st.spinner("Generating creative mix combinations..."):
                state = {
                    "context": mix_context,
                    "creative_rules": rules,
                    "base_placements": selected_placements,
                    "campaign": active_campaign
                }
                ai_output = generate_creative_name_step(state)

            if not ai_output or "creative_names" not in ai_output:
                st.error("⚠️ AI generation failed. Please try again.")
                st.stop()

            creative_output = ai_output["creative_names"]
            all_mix_creatives = []

            if isinstance(creative_output, dict):
                for placement, names in creative_output.items():
                    for suggestion in names:
                        name = suggestion["name"].upper() if isinstance(suggestion, dict) else str(suggestion).upper()
                        all_mix_creatives.append(name)
            elif isinstance(creative_output, list):
                for suggestion in creative_output:
                    name = suggestion["name"].upper() if isinstance(suggestion, dict) else str(suggestion).upper()
                    all_mix_creatives.append(name)

            st.session_state.generated_mix_creatives = all_mix_creatives
            st.success(f"✅ Generated {len(all_mix_creatives)} creative options across placements!")

        # --- Display mix results if exist ---
        if "generated_mix_creatives" in st.session_state and st.session_state.generated_mix_creatives:
            mix_creatives = st.session_state.generated_mix_creatives
            selected = st.multiselect(
                "Select creatives to keep:",
                mix_creatives,
                key="selected_mix_creatives"
            )

            if selected:
                st.success(f"{len(selected)} creative(s) selected to save.")
                if st.button("💾 Save Selected Creatives"):
                    for name in selected:
                        insert_name({
                            "planner_type": "creative",
                            "name": name,
                            "campaign": active_campaign,
                            "source": "ai_mix",
                            "validation_status": "pending"
                        })
                        if name not in st.session_state.current_session_creatives:
                            st.session_state.current_session_creatives.append(name)
                    st.success("✅ Selected creatives saved successfully!")
            else:
                st.info("Select at least one creative to save.")

            if st.button("🔁 Try Again with New Mix"):
                del st.session_state.generated_mix_creatives
                st.experimental_rerun()

    # -----------------------------
    # FINAL REVIEW & SAVE SECTION
    # -----------------------------
    if st.session_state.current_session_creatives:
        st.markdown("---")
        st.subheader("✅ Review & Finalize Session Creatives")

        all_creatives = st.session_state.current_session_creatives
        selected_final = st.multiselect(
            "Select one or more creatives to save to database:",
            all_creatives,
            default=all_creatives,
            key="final_selected_creatives"
        )

        if selected_final:
            st.success(f"{len(selected_final)} creative(s) selected for saving.")
            if st.button("💾 Save Selected to Database"):
                for name in selected_final:
                    insert_name({
                        "planner_type": "creative",
                        "name": name,
                        "campaign": active_campaign,
                        "source": "finalized",
                        "validation_status": "pending"
                    })
                st.success("✅ All selected creatives saved successfully!")
        else:
            st.info("Select at least one creative to save.")
