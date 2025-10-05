# app/utils/name_generator.py
def generate_campaign_name(advertiser, plan_number, product, objective, campaign, month, year, free_forms=None):
    """
    Builds standardized campaign name.
    Example: PM_1001_Saree_Sales_DiwaliFestivals_Oct_2025_TestVariant
    """
    parts = [
        advertiser, plan_number, product, objective, campaign, month, year
    ]
    if free_forms:
        parts.extend(free_forms)
    # Remove empty/None parts and format cleanly
    clean = [str(p).strip().replace(" ", "").title() for p in parts if p]
    return "_".join(clean)
