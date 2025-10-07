def validate_placement_name_step(state: dict):
    """
    Validate placement/media buy names using format and rule checks.
    Allows additional characters: -, *, space, /, \, |
    """

    names = state.get("placement_names", [])
    rules = state.get("placement_rules", {}).get("validation", {})

    results = []

    # Define allowed characters (A–Z, 0–9, underscore, dash, star, space, slash, backslash, pipe)
    allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_ -*\\/|")

    for name in names:
        issues = []

        # Basic structural validations
        if rules.get("no_spaces_allowed") and " " in name:
            issues.append("Contains spaces (not allowed by rules).")
        if rules.get("force_uppercase") and not name.isupper():
            issues.append("Must be in uppercase.")
        if rules.get("use_underscores") and "_" not in name:
            issues.append("Missing underscore delimiters.")
        if "__" in name:
            issues.append("Multiple consecutive underscores found.")

        # Character validation
        for ch in name:
            if ch not in allowed_chars:
                issues.append(f"Invalid character found: '{ch}'")

        # Final validation flag
        is_valid = len(issues) == 0
        results.append({
            "name": name,
            "is_valid": is_valid,
            "issues": issues,
            "reasoning": "Valid format" if is_valid else "; ".join(issues)
        })

    return {"validation_result": results}
