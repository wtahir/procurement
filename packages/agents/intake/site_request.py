from packages.core.models.order import ProcurementOrder


def mark_request_for_parsing(order: ProcurementOrder) -> ProcurementOrder:
    order.pipeline_control.active_agent = "site_request"
    return order
