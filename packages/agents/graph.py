from packages.agents.state import AgentState


def build_state_graph() -> dict[str, str]:
    return {
        "entrypoint": "site_request",
        "note": "LangGraph wiring lands here in the next implementation phase.",
        "state_type": AgentState.__name__,
    }
