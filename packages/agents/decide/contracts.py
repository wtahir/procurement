from packages.core.models.order import ProcurementOrder


def draft_contract(order: ProcurementOrder) -> ProcurementOrder:
    if order.bidding.recommended_bid:
        order.contract.template_id = "standard-procurement-v1"
        order.contract.sign_status = "draft"
    return order
