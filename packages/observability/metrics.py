def completion_rate(completed: int, total: int) -> float:
    if total == 0:
        return 0.0
    return completed / total
