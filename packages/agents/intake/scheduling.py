from packages.core.models.order import ProcurementOrder


def mark_schedule_pending(order: ProcurementOrder) -> ProcurementOrder:
    order.intake.schedule_ok = order.intake.schedule_ok if order.intake.schedule_ok is not None else False
    return order
