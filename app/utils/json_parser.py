# app/utils/json_parser.py
import json
import re

def safe_json_parse(text: str):
    """
    Extracts and parses JSON from messy LLM output.
    """
    # Extract the first JSON-like substring
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("No JSON found in LLM output.")

    json_str = match.group(0)
    # Replace lowercase true/false/null if present
    json_str = (
        json_str.replace("true", "True")
        .replace("false", "False")
        .replace("null", "None")
    )

    try:
        # Try JSON first
        return json.loads(json_str)
    except Exception:
        # Fallback to literal_eval
        import ast
        return ast.literal_eval(json_str)
