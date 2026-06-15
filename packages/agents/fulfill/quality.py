from packages.core.models.order import ProcurementOrder


def mark_quality_pending(order: ProcurementOrder) -> ProcurementOrder:
    order.fulfilment.quality.result = order.fulfilment.quality.result or "pending"
    return order
