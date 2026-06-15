from packages.core.enums import ApprovalLevel
from packages.core.models.order import ProcurementOrder


def determine_approval_level(order: ProcurementOrder) -> ApprovalLevel:
    total_value = 0.0
    if order.bidding.recommended_bid:
        total_value = float(order.bidding.recommended_bid.get("total", 0.0))
    if total_value > 500000:
        return ApprovalLevel.DIRECTOR
    if total_value >= 50000:
        return ApprovalLevel.PROJECT_MANAGER
    return ApprovalLevel.AUTO
