from packages.core.models.order import ProcurementOrder

_ORDERS: dict[str, ProcurementOrder] = {}


def save_order(order: ProcurementOrder) -> ProcurementOrder:
    _ORDERS[order.identity.order_id] = order
    return order


def get_order(order_id: str) -> ProcurementOrder | None:
    return _ORDERS.get(order_id)


def list_orders() -> list[ProcurementOrder]:
    return sorted(_ORDERS.values(), key=lambda order: order.identity.created_at, reverse=True)
