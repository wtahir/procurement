from fastapi import APIRouter

from apps.api.errors import ProcuraError
from apps.api.store import get_order, save_order
from packages.core.enums import ApprovalStatus, PipelineStatus
from packages.core.models.order import AuditEntry, ProcurementOrder, utc_now

router = APIRouter()


def _require_order(order_id: str) -> ProcurementOrder:
    order = get_order(order_id)
    if order is None:
        raise ProcuraError(f"Order {order_id} not found", status_code=404)
    return order


@router.post("/{order_id}/approve")
async def approve_order(order_id: str) -> ProcurementOrder:
    order = _require_order(order_id)
    order.approval.status = ApprovalStatus.APPROVED
    order.approval.approver_id = "demo-director"
    order.approval.decided_at = utc_now()
    order.approval.decision_reason = "Approved via approvals inbox"
    order.contract.sign_status = "signed"
    order.pipeline_control.status = PipelineStatus.COMPLETED
    order.audit_log.append(AuditEntry(agent="approvals", action="Human approved order"))
    return save_order(order)


@router.post("/{order_id}/reject")
async def reject_order(order_id: str) -> ProcurementOrder:
    order = _require_order(order_id)
    order.approval.status = ApprovalStatus.REJECTED
    order.approval.approver_id = "demo-director"
    order.approval.decided_at = utc_now()
    order.approval.decision_reason = "Rejected via approvals inbox"
    order.pipeline_control.status = PipelineStatus.CANCELLED
    order.audit_log.append(AuditEntry(agent="approvals", action="Human rejected order"))
    return save_order(order)
