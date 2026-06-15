from packages.agents.router import determine_approval_level
from packages.core.enums import ApprovalStatus, PipelineStatus
from packages.core.models.order import ProcurementOrder


def route_for_approval(order: ProcurementOrder) -> ProcurementOrder:
    order.approval.required_level = determine_approval_level(order)
    order.approval.status = ApprovalStatus.PENDING
    order.pipeline_control.status = PipelineStatus.AWAITING_HUMAN
    return order
