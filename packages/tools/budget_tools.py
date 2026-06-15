def budget_allows_purchase(*, budget_remaining: float, proposed_total: float) -> bool:
    return proposed_total <= budget_remaining
