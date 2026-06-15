from packages.core.models.order import ProcurementOrder


def mark_payment_pending(order: ProcurementOrder) -> ProcurementOrder:
    order.fulfilment.payment.status = order.fulfilment.payment.status or "pending"
    return order
