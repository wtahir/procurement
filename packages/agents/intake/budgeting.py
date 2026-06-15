from packages.core.models.order import ProcurementOrder


def mark_budget_pending(order: ProcurementOrder) -> ProcurementOrder:
    order.intake.budget_ok = bool(order.intake.budget_ok)
    return order
