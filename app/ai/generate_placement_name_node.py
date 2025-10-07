# app/ai/generate_placement_name_node.py
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.utils.json_parser import safe_json_parse
import json

def generate_placement_name_step(state: dict):
    """
    Generate placement/media buy naming suggestions using AI rules.
    """

    rules = state.get("placement_rules", {})
    user_context = state.get("context", "")

    llm = ChatOpenAI(model="o4-mini-2025-04-16", temperature=1)
    prompt = ChatPromptTemplate.from_template("""
    You are an expert in media naming conventions.
    Generate 3 placement/media buy name suggestions following these rules:
    {rules}

    User context:
    {user_context}

    Return JSON:
    {{
      "placement_names": [
        {{"name": "...", "reasoning": "..."}},
        {{"name": "...", "reasoning": "..."}},
        {{"name": "...", "reasoning": "..."}}
      ]
    }}
    """)

    response = llm.invoke(prompt.format(
        rules=json.dumps(rules, indent=2),
        user_context=user_context
    ))

    return safe_json_parse(response.content)
