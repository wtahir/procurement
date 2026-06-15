def get_model_name(task_name: str) -> str:
    from packages.llm.router import TASK_MODEL_ROUTING

    return TASK_MODEL_ROUTING.get(task_name, "gpt-4o-mini")
