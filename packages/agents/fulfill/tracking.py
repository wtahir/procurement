from packages.core.models.order import ProcurementOrder


def summarize_status(order: ProcurementOrder) -> dict[str, object]:
    return {
        "order_id": order.identity.order_id,
        "status": order.pipeline_control.status.value,
        "active_agent": order.pipeline_control.active_agent,
    }
