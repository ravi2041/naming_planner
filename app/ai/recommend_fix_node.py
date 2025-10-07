# app/ai/recommend_fix_node.py
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.utils.json_parser import safe_json_parse
from dotenv import load_dotenv

load_dotenv()


def recommend_fix_step(state: dict):
    """
    Suggests corrected campaign names for invalid names found during validation.
    Handles both single-name and multi-name cases.

    Enforces uppercase normalization if 'force_uppercase' is True in rules.

    Expected input:
    {
        "rules": ...,
        "validation_result": [
            {"name": "...", "is_valid": false, "issues": ["..."], "reasoning": "..."}
        ]
    }

    Returns:
    {
        "fix_suggestion": [
            {"original": "...", "suggested_name": "...", "explanation": "..."}
        ]
    }
    """

    validation_result = state.get("validation_result", [])
    if not validation_result:
        return {"fix_suggestion": []}  # nothing to fix

    # Filter only invalid names
    invalid_names = [v for v in validation_result if not v.get("is_valid", False)]
    if not invalid_names:
        return {"fix_suggestion": []}

    # Detect uppercase enforcement from rules
    force_uppercase = (
        isinstance(state.get("rules"), dict)
        and state["rules"].get("validation", {}).get("force_uppercase", True)
    )

    llm = ChatOpenAI(model="o4-mini-2025-04-16", temperature=1)
    prompt = ChatPromptTemplate.from_template("""
    You are a campaign naming corrector.
    For each invalid campaign name below, suggest one corrected version that follows all naming rules.
    If 'force_uppercase' is true, ensure all names are in uppercase.

    **Rules:**
    {rules}

    **Invalid Names and Issues:**
    {invalid_list}

    Respond ONLY in valid JSON — no markdown, no explanation text.
    Example format:
    {{
      "fixes": [
        {{
          "original": "PM_1001_SAREE_AWAR_DIWALIFESTIVALS",
          "suggested_name": "PM_1001_SAREE_AWAR_DIWALIFESTIVALS_OCT_2025",
          "explanation": "Added missing month and year as per rules."
        }}
      ]
    }}
    """)

    # Build formatted invalid details string for LLM input
    invalid_list = "\n".join([
        f"{item['name']}: {', '.join(item.get('issues', []))}" for item in invalid_names
    ])

    try:
        # --- Run the LLM ---
        response = (prompt | llm).invoke({
            "rules": state["rules"],
            "invalid_list": invalid_list
        })

        # --- Parse JSON safely ---
        data = safe_json_parse(response.content)

        # Normalize fixes
        fixes = data.get("fixes", [])
        if not fixes and isinstance(data, dict) and "suggested_name" in data:
            fixes = [{
                "original": invalid_names[0]["name"],
                "suggested_name": data.get("suggested_name"),
                "explanation": data.get("explanation", "")
            }]

        # ✅ Enforce uppercase if required
        if force_uppercase:
            for f in fixes:
                if "suggested_name" in f:
                    f["suggested_name"] = f["suggested_name"].upper()
                if "original" in f:
                    f["original"] = f["original"].upper()

        return {"fix_suggestion": fixes}

    except Exception as e:
        return {"error": str(e)}
