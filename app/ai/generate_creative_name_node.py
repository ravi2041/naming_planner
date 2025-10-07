from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

def generate_creative_name_step(state: dict):
    llm = ChatOpenAI(model="o4-mini-2025-04-16", temperature=1)
    context = state.get("context", "")
    base_placements = state.get("base_placements", [])
    rules = state.get("creative_rules", {})

    prompt = ChatPromptTemplate.from_template("""
    You are a creative naming assistant.
    For each placement below, generate 2–3 creative name suggestions following these rules:
    - Use uppercase naming convention.
    - Include campaign or product context if relevant.
    - Avoid spaces, use underscores.
    - Keep names short, descriptive, and consistent.

    Context: {context}
    Placements: {base_placements}

    Return JSON in this format:
    {{
        "creative_names": {{
            "<placement_name>": [
                {{"name": "...", "reasoning": "..."}}
            ]
        }}
    }}
    """)

    msg = prompt.format_messages(context=context, base_placements=base_placements)
    response = llm.invoke(msg)
    return {"creative_names": eval(response.content)}  # assumes JSON-safe output
