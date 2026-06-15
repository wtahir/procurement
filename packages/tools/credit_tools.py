def bnpl_credit_allowed(*, requested_total: float, available_limit: float) -> bool:
    return requested_total <= available_limit
