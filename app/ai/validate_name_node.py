# app/ai/validate_name_node.py
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.utils.json_parser import safe_json_parse
from dotenv import load_dotenv

load_dotenv()


def validate_name_step(state: dict):
    """
    Validates one or multiple campaign names against provided rules.

    Handles two scenarios:
    - Single name (manual mode)
    - Multiple names (AI-generated suggestions)

    Enforces uppercase normalization if 'force_uppercase' is True in rules.

    Returns consistent structured result:
    {
      "validation_result": [
        {"name": "...", "is_valid": True, "issues": [], "reasoning": "..."}
      ]
    }
    """

    llm = ChatOpenAI(model="o4-mini-2025-04-16", temperature=1)  # deterministic validation output
    prompt = ChatPromptTemplate.from_template("""
    You are a strict campaign naming validator.
    For each campaign name, check if it follows the rules below.
    Ensure names use underscores (_) and are in uppercase if required.

    **Rules:**
    {rules}

    **Campaign Names to Validate:**
    {names}

    Respond ONLY in valid JSON (no markdown, no text).
    Example format:
    {{
      "validations": [
        {{
          "name": "PM_1001_SAREE_AWAR_DIWALIFESTIVALS_OCT_2025",
          "is_valid": true,
          "issues": [],
          "reasoning": "Follows all required naming rules."
        }},
        {{
          "name": "PM_1001_SAREE_AWAR_DIWALIFESTIVALS",
          "is_valid": false,
          "issues": ["Missing month and year"],
          "reasoning": "The name lacks required time components."
        }}
      ]
    }}
    """)

    try:
        # ✅ Extract campaign names
        suggestions = state.get("generated_suggestions", [])
        single_name = state.get("generated_name") or state.get("details", {}).get("generated_name")

        if suggestions:
            names_list = [s["name"] for s in suggestions if "name" in s]
        elif single_name:
            names_list = [single_name]
        else:
            return {"error": "No campaign names provided for validation."}

        # ✅ Apply uppercase normalization if rule enabled
        force_uppercase = (
            isinstance(state.get("rules"), dict)
            and state["rules"].get("validation", {}).get("force_uppercase", True)
        )
        if force_uppercase:
            names_list = [n.upper() for n in names_list]

        names_block = "\n".join(names_list)

        # ✅ Run validation LLM
        response = (prompt | llm).invoke({
            "rules": state["rules"],
            "names": names_block
        })

        # ✅ Parse LLM JSON output safely
        data = safe_json_parse(response.content)

        # ✅ Extract results in consistent structure
        results = data.get("validations", [])
        if not results and isinstance(data, dict):
            # Fallback for single name
            single = {
                "name": names_list[0] if names_list else "UNKNOWN",
                "is_valid": data.get("is_valid", False),
                "issues": data.get("issues", []),
                "reasoning": data.get("reasoning", "")
            }
            results = [single]

        # ✅ Enforce uppercase in result payload
        for r in results:
            if "name" in r:
                r["name"] = r["name"].upper()

        return {"validation_result": results}

    except Exception as e:
        return {"error": str(e)}
