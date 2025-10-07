# app/ai/generate_name_node.py
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from app.utils.json_parser import safe_json_parse

load_dotenv()


def generate_name_step(state: dict):
    """
    LangGraph node — generates 3–5 AI-based campaign name suggestions
    using provided rules and campaign details.
    Enforces uppercase normalization if 'force_uppercase' is enabled in rules.
    """

    llm = ChatOpenAI(model="o4-mini-2025-04-16", temperature=1)

    prompt = ChatPromptTemplate.from_template("""
    You are an expert campaign naming assistant.

    Based on the campaign details and naming rules below, generate 3 to 5
    valid campaign name suggestions. Each name MUST strictly follow the 
    provided format and rules, but you can vary the campaign descriptor 
    (e.g., FESTIVAL, LAUNCH, PROMO, OFFER, COLLECTION).

    IMPORTANT:
    - All names must be in UPPERCASE if rules specify 'force_uppercase': true.
    - Use underscores (_) as separators.
    - No spaces or special characters allowed.

    **Rules:**
    {rules}

    **Details:**
    {details}

    Return ONLY valid JSON — no explanation text, no Markdown.

    Example Response:
    {{
      "suggestions": [
        {{
          "name": "PM_1001_SAREE_SALES_DIWALIFESTIVALS_OCT_2025",
          "reasoning": "Follows all fields with 'FESTIVALS' descriptor."
        }},
        {{
          "name": "PM_1001_SAREE_SALES_FESTIVESEASONLAUNCH_OCT_2025",
          "reasoning": "Uses 'LAUNCH' as campaign variant for variety."
        }}
      ]
    }}
    """)

    try:
        # Convert campaign details into a readable key:value string
        details_str = "\n".join([f"{k}: {v}" for k, v in state["details"].items()])

        # Run the LLM with prompt
        response = (prompt | llm).invoke({
            "rules": state["rules"],
            "details": details_str
        })

        # Parse JSON output safely
        data = safe_json_parse(response.content)
        suggestions = data.get("suggestions", [])

        # Backward-compatible fallback (if model outputs a single name)
        if not suggestions and "generated_name" in data:
            suggestions = [{
                "name": data.get("generated_name"),
                "reasoning": data.get("reasoning", "Single name generated.")
            }]

        # ✅ Enforce uppercase if rules specify
        force_uppercase = (
            isinstance(state.get("rules"), dict)
            and state["rules"].get("validation", {}).get("force_uppercase", True)
        )

        if force_uppercase:
            for s in suggestions:
                if "name" in s:
                    s["name"] = s["name"].upper()

        return {
            "generated_suggestions": suggestions,
            "error": None
        }

    except Exception as e:
        return {
            "generated_suggestions": [],
            "error": str(e)
        }
