"""Deterministic demo orchestration.

Composes the per-stage agent node functions into a single runnable pipeline so
the API and dashboard have real data to show. It is intentionally LLM-free so it
runs on a clean deployment without any external credentials.
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.agents.approve.approvals import route_for_approval
from packages.agents.decide.awarding import choose_lowest_bid
from packages.agents.decide.bid_comparison import rank_bids
from packages.agents.decide.contracts import draft_contract
from packages.agents.fulfill.tracking import summarize_status
from packages.agents.intake.feasibility import seed_feasibility
from packages.agents.source.rfq_manager import queue_rfqs
from packages.agents.source.vendor_sourcing import shortlist_suppliers
from packages.core.enums import (
    ApprovalLevel,
    ApprovalStatus,
    PipelineStatus,
    SupplierChannel,
)
from packages.core.models.order import (
    AuditEntry,
    OrderIdentity,
    ProcurementOrder,
    QuoteRecord,
    RequestPayload,
    utc_now,
)
from packages.core.models.supplier import SupplierDescriptor

# Base unit prices (AUD) used by the deterministic quote generator.
_BASE_PRICES: dict[str, dict[str, float]] = {
    "rebar_steel": {"sydney": 2800.0, "melbourne": 2950.0, "brisbane": 2870.0},
    "cement_bag": {"sydney": 18.0, "melbourne": 19.5, "brisbane": 18.4},
    "ready_mix_concrete": {"sydney": 240.0, "melbourne": 255.0, "brisbane": 248.0},
    "ceramic_tile": {"sydney": 65.0, "melbourne": 70.0, "brisbane": 67.0},
}

_DEFAULT_REGION = "sydney"


@dataclass(frozen=True)
class _MockSupplier:
    descriptor: SupplierDescriptor
    markup: float
    lead_time_days: int


DEMO_SUPPLIERS: list[_MockSupplier] = [
    _MockSupplier(
        SupplierDescriptor(
            supplier_id="harbour_steelworks",
            name="Harbour Steelworks",
            channel=SupplierChannel.REST,
            min_order=10,
            reliability_score=0.96,
        ),
        markup=1.01,
        lead_time_days=2,
    ),
    _MockSupplier(
        SupplierDescriptor(
            supplier_id="southern_cementworks",
            name="Southern Cementworks",
            channel=SupplierChannel.SOAP,
            min_order=50,
            reliability_score=0.91,
        ),
        markup=1.04,
        lead_time_days=5,
    ),
    _MockSupplier(
        SupplierDescriptor(
            supplier_id="coastal_supply",
            name="Coastal Supply",
            channel=SupplierChannel.GRAPHQL,
            min_order=20,
            reliability_score=0.88,
        ),
        markup=0.99,
        lead_time_days=4,
    ),
    _MockSupplier(
        SupplierDescriptor(
            supplier_id="outback_trade",
            name="Outback Trade",
            channel=SupplierChannel.SFTP_BATCH,
            min_order=30,
            reliability_score=0.84,
        ),
        markup=1.02,
        lead_time_days=3,
    ),
    _MockSupplier(
        SupplierDescriptor(
            supplier_id="metro_ceramics",
            name="Metro Ceramics",
            channel=SupplierChannel.EDI_WEBHOOK,
            min_order=40,
            reliability_score=0.9,
        ),
        markup=1.03,
        lead_time_days=6,
    ),
    _MockSupplier(
        SupplierDescriptor(
            supplier_id="summit_industrial",
            name="Summit Industrial",
            channel=SupplierChannel.MAINFRAME,
            min_order=25,
            reliability_score=0.82,
        ),
        markup=1.05,
        lead_time_days=7,
    ),
]

_PROJECT_BUDGET = 2_000_000.0


def _unit_price(material_code: str, region: str, markup: float) -> float:
    prices = _BASE_PRICES.get(material_code, {})
    base = prices.get(region.lower(), next(iter(prices.values()), 100.0))
    return round(base * markup, 2)


def _audit(order: ProcurementOrder, agent: str, action: str, reason: str | None = None) -> None:
    order.audit_log.append(AuditEntry(agent=agent, action=action, reason=reason))
    if agent not in order.pipeline_control.completed_agents:
        order.pipeline_control.completed_agents.append(agent)


def run_demo_pipeline(
    *,
    raw_input: str,
    material_code: str,
    quantity: float,
    region: str,
    tenant_id: str = "demo",
) -> ProcurementOrder:
    region = region or _DEFAULT_REGION
    order = ProcurementOrder(
        identity=OrderIdentity(tenant_id=tenant_id),
        request=RequestPayload(
            raw_input=raw_input,
            material_code=material_code,
            quantity=quantity,
            unit="ton",
            region=region,
            parse_confidence=0.95,
        ),
    )

    # Stage 1 — intake.
    _audit(order, "site_request", "Parsed structured request from raw input")
    seed_feasibility(order)
    order.intake.feasibility_score = 0.82
    order.intake.feasibility_notes = "Material available within requested region."
    order.intake.budget_ok = True
    order.intake.schedule_ok = True
    _audit(order, "feasibility", "Confirmed material feasibility")

    # Stage 2 — sourcing.
    descriptors = [supplier.descriptor for supplier in DEMO_SUPPLIERS]
    shortlist_suppliers(order, descriptors)
    queue_rfqs(order, descriptors)
    order.sourcing.sourcing_rationale = (
        f"Shortlisted {len(descriptors)} suppliers across heterogeneous channels."
    )
    _audit(order, "vendor_sourcing", f"Shortlisted {len(descriptors)} suppliers")
    _audit(order, "rfq_manager", "Dispatched RFQs across supplier channels")

    # Collect deterministic quotes.
    for supplier in DEMO_SUPPLIERS:
        unit_price = _unit_price(material_code, region, supplier.markup)
        total = round(unit_price * quantity, 2)
        order.bidding.quotes_received.append(
            QuoteRecord(
                supplier_id=supplier.descriptor.supplier_id,
                unit_price=unit_price,
                total=total,
                lead_time_days=supplier.lead_time_days,
                terms="Net 30",
                reliability_score=supplier.descriptor.reliability_score,
                raw_ref=f"quote::{supplier.descriptor.supplier_id}",
            )
        )

    # Stage 3 — decide.
    rank_bids(order)
    choose_lowest_bid(order)
    draft_contract(order)
    _audit(order, "bid_comparison", "Ranked quotes by landed total")
    _audit(order, "awarding", "Recommended lowest compliant bid")
    order.intake.budget_remaining = round(
        _PROJECT_BUDGET - float(order.bidding.recommended_bid.get("total", 0.0)), 2
    )

    # Stage 4 — approval gate.
    route_for_approval(order)
    if order.approval.required_level == ApprovalLevel.AUTO:
        order.approval.status = ApprovalStatus.APPROVED
        order.approval.approver_id = "auto-policy"
        order.approval.decided_at = utc_now()
        order.approval.decision_reason = "Within auto-approval threshold"
        order.contract.sign_status = "signed"
        order.pipeline_control.status = PipelineStatus.COMPLETED
        _audit(order, "approvals", "Auto-approved within policy threshold")
    else:
        _audit(
            order,
            "approvals",
            f"Routed for {order.approval.required_level.value} approval",
        )

    return order


def order_summary(order: ProcurementOrder) -> dict[str, object]:
    recommended = order.bidding.recommended_bid
    return {
        **summarize_status(order),
        "material_code": order.request.material_code,
        "quantity": order.request.quantity,
        "region": order.request.region,
        "approval_level": order.approval.required_level.value,
        "approval_status": order.approval.status.value,
        "recommended_supplier": recommended.get("supplier_id"),
        "recommended_total": recommended.get("total"),
        "created_at": order.identity.created_at.isoformat(),
    }
