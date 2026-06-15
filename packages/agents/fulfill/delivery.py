from packages.core.models.order import ProcurementOrder


def mark_delivery_created(order: ProcurementOrder) -> ProcurementOrder:
    order.fulfilment.delivery_events.append({"event": "delivery_scheduled"})
    return order
