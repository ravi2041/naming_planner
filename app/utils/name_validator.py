# app/utils/name_validator.py
def validate_campaign_inputs(advertiser, plan_number, product, objective, campaign):
    """Validates required fields for campaign planner."""
    missing = []
    if not advertiser:
        missing.append("Advertiser")
    if not plan_number:
        missing.append("Plan Number")
    if not product:
        missing.append("Product")
    if not objective:
        missing.append("Objective")
    if not campaign:
        missing.append("Campaign Name")

    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"

    if not plan_number.isdigit():
        return False, "Plan number should be numeric."

    return True, "All required fields valid."
