"""Staged procurement orchestration (demo + LLM modes).

Composes the per-stage agent node functions into runnable pipelines so the API
and dashboard always have real data to show.

Two entrypoints share the same deterministic core (pricing, ranking, budget,
approval routing):

- ``run_demo_pipeline`` — LLM-free; runs on a clean deployment with no
  credentials and no extra dependencies (used on Render and in tests).
- ``run_llm_pipeline``  — same workflow, but request parsing and explanatory
  prose come from a real model (Azure OpenAI or a local Llama server).

``run_pipeline`` is the mode-aware dispatcher selected by ``LLM_MODE``.
"""

from __future__ import annotations

from dataclasses import dataclass

from packages.agents.approve.approvals import route_for_approval
from packages.agents.decide.awarding import choose_lowest_bid
from packages.agents.decide.bid_comparison import rank_bids
from packages.agents.decide.contracts import draft_contract
from packages.agents.fulfill.tracking import summarize_status
from packages.agents.intake.feasibility import seed_feasibility
from packages.agents.llm_nodes import (
    assess_feasibility,
    explain_recommendation,
    parse_site_request,
    write_contract_cover,
)
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
from packages.llm.client import LLMClient, get_llm_client
from packages.llm.config import get_llm_settings

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


def _as_float(value: object) -> float:
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 0.0


def _audit(order: ProcurementOrder, agent: str, action: str, reason: str | None = None) -> None:
    order.audit_log.append(AuditEntry(agent=agent, action=action, reason=reason))
    if agent not in order.pipeline_control.completed_agents:
        order.pipeline_control.completed_agents.append(agent)


def _collect_quotes(
    order: ProcurementOrder, material_code: str, region: str, quantity: float
) -> None:
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
    _collect_quotes(order, material_code, region, quantity)

    # Stage 3 — decide.
    rank_bids(order)
    choose_lowest_bid(order)
    draft_contract(order)
    _audit(order, "bid_comparison", "Ranked quotes by landed total")
    _audit(order, "awarding", "Recommended lowest compliant bid")
    order.intake.budget_remaining = round(
        _PROJECT_BUDGET - _as_float(order.bidding.recommended_bid.get("total", 0.0)), 2
    )

    # Stage 4 — approval gate.
    _finalize_approval(order)

    return order


def _finalize_approval(order: ProcurementOrder) -> None:
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


def run_llm_pipeline(
    *,
    llm: LLMClient,
    raw_input: str,
    material_code: str,
    quantity: float,
    region: str,
    tenant_id: str = "demo",
) -> ProcurementOrder:
    """Same staged workflow as the demo, but with real LLM reasoning at the edges.

    Deterministic math (pricing, ranking, budget, approval routing) is identical
    to the demo path; only parsing and explanatory prose come from the model.
    """

    region = region or _DEFAULT_REGION

    # Stage 1 — intake (LLM parses the free-form request).
    parsed = parse_site_request(
        llm,
        raw_input=raw_input,
        fallback_material=material_code,
        fallback_quantity=quantity,
        fallback_region=region,
    )
    material_code = parsed.material_code
    quantity = parsed.quantity
    region = parsed.region

    order = ProcurementOrder(
        identity=OrderIdentity(tenant_id=tenant_id),
        request=RequestPayload(
            raw_input=raw_input,
            material_code=material_code,
            quantity=quantity,
            unit=parsed.unit,
            region=region,
            parse_confidence=parsed.confidence,
        ),
    )
    _audit(order, "site_request", "Parsed structured request via LLM")

    seed_feasibility(order)
    feasibility = assess_feasibility(llm, order)
    order.intake.feasibility_score = feasibility.score
    order.intake.feasibility_notes = feasibility.notes
    order.intake.budget_ok = True
    order.intake.schedule_ok = True
    _audit(order, "feasibility", "Assessed feasibility via LLM")

    # Stage 2 — sourcing (deterministic).
    descriptors = [supplier.descriptor for supplier in DEMO_SUPPLIERS]
    shortlist_suppliers(order, descriptors)
    queue_rfqs(order, descriptors)
    order.sourcing.sourcing_rationale = (
        f"Shortlisted {len(descriptors)} suppliers across heterogeneous channels."
    )
    _audit(order, "vendor_sourcing", f"Shortlisted {len(descriptors)} suppliers")
    _audit(order, "rfq_manager", "Dispatched RFQs across supplier channels")

    _collect_quotes(order, material_code, region, quantity)

    # Stage 3 — decide (deterministic math, LLM explanation).
    rank_bids(order)
    choose_lowest_bid(order)
    draft_contract(order)
    _audit(order, "bid_comparison", "Ranked quotes by landed total")
    _audit(order, "awarding", "Recommended lowest compliant bid")
    order.intake.budget_remaining = round(
        _PROJECT_BUDGET - _as_float(order.bidding.recommended_bid.get("total", 0.0)), 2
    )
    order.bidding.comparison_matrix["explanation"] = explain_recommendation(llm, order)
    order.contract.terms = write_contract_cover(llm, order)

    # Stage 4 — approval gate (deterministic).
    _finalize_approval(order)

    return order


def run_pipeline(
    *,
    raw_input: str,
    material_code: str,
    quantity: float,
    region: str,
    tenant_id: str = "demo",
) -> ProcurementOrder:
    """Mode-aware entrypoint.

    ``LLM_MODE=demo`` (default) runs the deterministic, credential-free pipeline.
    ``azure`` / ``llama`` run the real LLM-backed pipeline against the configured
    provider.
    """

    settings = get_llm_settings()
    if settings.llm_mode == "demo":
        return run_demo_pipeline(
            raw_input=raw_input,
            material_code=material_code,
            quantity=quantity,
            region=region,
            tenant_id=tenant_id,
        )

    llm = get_llm_client(settings)
    if llm is None:  # defensive: treat misconfiguration as demo
        return run_demo_pipeline(
            raw_input=raw_input,
            material_code=material_code,
            quantity=quantity,
            region=region,
            tenant_id=tenant_id,
        )

    return run_llm_pipeline(
        llm=llm,
        raw_input=raw_input,
        material_code=material_code,
        quantity=quantity,
        region=region,
        tenant_id=tenant_id,
    )
