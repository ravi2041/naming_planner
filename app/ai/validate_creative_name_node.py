def validate_creative_name_step(state: dict):
    names = state.get("creative_names", [])
    rules = state.get("creative_rules", {}).get("validation", {})
    results = []

    for name in names:
        issues = []
        if " " in name:
            issues.append("Contains spaces.")
        if not name.isupper():
            issues.append("Must be uppercase.")
        if "__" in name:
            issues.append("Multiple underscores found.")
        if not all(c.isalnum() or c in "_-*/|\\ " for c in name):
            issues.append("Invalid characters (only A-Z, 0-9, _, -, /, | allowed).")

        results.append({
            "name": name,
            "is_valid": not issues,
            "issues": issues,
            "reasoning": "Valid format" if not issues else "; ".join(issues)
        })
    return {"validation_result": results}
