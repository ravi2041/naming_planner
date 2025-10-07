# app/ai/graph_state.py
from typing import TypedDict, Optional, Dict, Any, List


class ValidationState(TypedDict, total=False):
    """
    Represents the full state shared between LangGraph nodes
    during campaign name generation, validation, and fix recommendation.

    Supports both:
      - Single-name flows (manual or user-selected)
      - Multi-name flows (AI-generated suggestions)
    """

    # --- Input Context ---
    details: Dict[str, Any]              # Raw input context from Streamlit UI
    rules: Dict[str, Any]                # Loaded naming convention rules (JSON)

    # --- Generation Outputs ---
    generated_name: Optional[str]        # Single name (for manual or selected name validation)
    generated_suggestions: Optional[List[Dict[str, str]]]
    # Example: [{"name": "PM_1001_Saree_Awar_DiwaliFestivals_Oct_2025", "reasoning": "..."}]

    # --- Validation Outputs ---
    validation_result: Optional[List[Dict[str, Any]]]
    # Example: [
    #   {"name": "PM_1001_Saree_Awar_DiwaliFestivals_Oct_2025",
    #    "is_valid": True, "issues": [], "reasoning": "Follows rules"}
    # ]

    # --- Fix Recommendations ---
    fix_suggestion: Optional[List[Dict[str, Any]]]
    # Example: [
    #   {"original": "PM_1001_Saree_Awar_DiwaliFestivals",
    #    "suggested_name": "PM_1001_Saree_Awar_DiwaliFestivals_Oct_2025",
    #    "explanation": "Added missing month/year"}
    # ]

    # --- Governance Metadata ---
    validation_status: Optional[str]     # e.g. "valid", "invalid", "pending"
    source: Optional[str]                # e.g. "manual" or "ai"

    # --- Debug / Error Tracking ---
    reasoning: Optional[str]             # General reasoning or explanation string
    error: Optional[str]                 # Captures node-level or graph-level error messages
