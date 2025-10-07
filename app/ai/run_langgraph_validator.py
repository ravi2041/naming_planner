# app/ai/run_langgraph_validator.py
from langgraph.graph import StateGraph, END
from app.ai.graph_state import ValidationState
from app.ai.generate_name_node import generate_name_step
from app.ai.validate_name_node import validate_name_step
from app.ai.recommend_fix_node import recommend_fix_step


def run_langgraph_validator(details, rules):
    """
    LangGraph pipeline for campaign name governance.

    Supports both phases:

    Phase 1 (AI mode):
        generate_step → validate_step → recommend_fix_step → END

    Phase 2 (Manual or selected name):
        validate_step → recommend_fix_step → END
    """

    # Initialize the graph
    graph = StateGraph(ValidationState)

    # Add nodes
    graph.add_node("generate_step", generate_name_step)
    graph.add_node("validate_step", validate_name_step)
    graph.add_node("recommend_fix_step", recommend_fix_step)

    # --- Flow Control ---
    if "generated_name" in details:
        # ✅ Manual or user-selected campaign name
        graph.set_entry_point("validate_step")
        graph.add_edge("validate_step", "recommend_fix_step")
        graph.add_edge("recommend_fix_step", END)
    else:
        # ✅ Full AI generation → validation → fix chain
        graph.set_entry_point("generate_step")
        graph.add_edge("generate_step", "validate_step")
        graph.add_edge("validate_step", "recommend_fix_step")
        graph.add_edge("recommend_fix_step", END)

    # Compile graph executor
    executor = graph.compile()

    # ✅ Flatten details so all keys (like generated_name) are accessible directly in state
    initial_state = {
        "details": details,   # keep structured version for reference
        "rules": rules,
        **details             # flatten all keys (advertiser, product, generated_name, etc.)
    }

    # Run the graph and return final state
    result_state = executor.invoke(initial_state)
    return result_state
