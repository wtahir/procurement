from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from packages.core.enums import ApprovalLevel, ApprovalStatus, InputModality, Locale, PipelineStatus


def utc_now() -> datetime:
    return datetime.now(UTC)


class OrderIdentity(BaseModel):
    order_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str = "demo"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    thread_id: str | None = None


class RequestPayload(BaseModel):
    raw_input: str
    input_modality: InputModality = InputModality.TEXT
    locale: Locale = Locale.EN
    material_code: str | None = None
    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = None
    region: str | None = None
    needed_by: datetime | None = None
    parse_confidence: float | None = Field(default=None, ge=0, le=1)


class IntakeState(BaseModel):
    feasibility_score: float | None = Field(default=None, ge=0, le=1)
    feasibility_notes: str | None = None
    budget_ok: bool | None = None
    budget_remaining: float | None = None
    schedule_ok: bool | None = None
    required_delivery_window: str | None = None


class SourcingState(BaseModel):
    candidate_supplier_ids: list[str] = Field(default_factory=list)
    sourcing_rationale: str | None = None


class RFQRecord(BaseModel):
    supplier_id: str
    channel: str
    sent_at: datetime = Field(default_factory=utc_now)
    status: str = "queued"


class QuoteRecord(BaseModel):
    supplier_id: str
    unit_price: float = Field(gt=0)
    total: float = Field(gt=0)
    lead_time_days: int = Field(ge=0)
    terms: str
    reliability_score: float = Field(ge=0, le=1)
    raw_ref: str


class BiddingState(BaseModel):
    rfqs_sent: list[RFQRecord] = Field(default_factory=list)
    quotes_received: list[QuoteRecord] = Field(default_factory=list)
    comparison_matrix: dict[str, object] = Field(default_factory=dict)
    recommended_bid: dict[str, object] = Field(default_factory=dict)


class ContractState(BaseModel):
    contract_id: str | None = None
    template_id: str | None = None
    terms: str | None = None
    penalty_clause: str | None = None
    sign_status: str = "draft"


class ApprovalState(BaseModel):
    required_level: ApprovalLevel = ApprovalLevel.AUTO
    status: ApprovalStatus = ApprovalStatus.PENDING
    approver_id: str | None = None
    decided_at: datetime | None = None
    decision_reason: str | None = None


class InvoiceState(BaseModel):
    po_qty: float | None = None
    delivery_qty: float | None = None
    invoice_qty: float | None = None
    match_result: str | None = None


class PaymentState(BaseModel):
    method: str | None = None
    status: str | None = None
    credit_decision: str | None = None


class QualityState(BaseModel):
    result: str | None = None
    disputes: list[str] = Field(default_factory=list)


class FulfilmentState(BaseModel):
    delivery_events: list[dict[str, object]] = Field(default_factory=list)
    invoice: InvoiceState = Field(default_factory=InvoiceState)
    payment: PaymentState = Field(default_factory=PaymentState)
    quality: QualityState = Field(default_factory=QualityState)


class AuditEntry(BaseModel):
    ts: datetime = Field(default_factory=utc_now)
    agent: str
    action: str
    reason: str | None = None
    before_ref: str | None = None
    after_ref: str | None = None


class PipelineControl(BaseModel):
    active_agent: str | None = None
    completed_agents: list[str] = Field(default_factory=list)
    failed_agents: list[str] = Field(default_factory=list)
    status: PipelineStatus = PipelineStatus.RUNNING


class ProcurementOrder(BaseModel):
    identity: OrderIdentity
    request: RequestPayload
    intake: IntakeState = Field(default_factory=IntakeState)
    sourcing: SourcingState = Field(default_factory=SourcingState)
    bidding: BiddingState = Field(default_factory=BiddingState)
    contract: ContractState = Field(default_factory=ContractState)
    approval: ApprovalState = Field(default_factory=ApprovalState)
    fulfilment: FulfilmentState = Field(default_factory=FulfilmentState)
    audit_log: list[AuditEntry] = Field(default_factory=list)
    pipeline_control: PipelineControl = Field(default_factory=PipelineControl)

    def model_post_init(self, __context: object) -> None:
        if self.identity.thread_id is None:
            self.identity.thread_id = f"{self.identity.tenant_id}:{self.identity.order_id}"
