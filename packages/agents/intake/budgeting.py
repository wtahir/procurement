from packages.core.models.order import ProcurementOrder


def mark_budget_pending(order: ProcurementOrder) -> ProcurementOrder:
    order.intake.budget_ok = order.intake.budget_ok if order.intake.budget_ok is not None else False
    return order
