from packages.core.models.order import ProcurementOrder


def mark_schedule_pending(order: ProcurementOrder) -> ProcurementOrder:
    order.intake.schedule_ok = bool(order.intake.schedule_ok)
    return order
