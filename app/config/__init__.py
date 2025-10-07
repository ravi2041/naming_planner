from app.utils.config_loader import load_rules

_all_rules = load_rules("campaign_rules.json")

campaign_rules = _all_rules["campaign_planner"]
placement_rules = _all_rules["placement_planner"]
creative_rules = _all_rules.get("creative_planner", {})
