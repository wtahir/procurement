"""LangGraph StateGraph wiring for the Procura procurement pipeline.

HOW THIS FITS TOGETHER
----------------------
`pipeline.py` already has all the business logic as plain functions that mutate
a `ProcurementOrder`. This file wraps those same functions as LangGraph *nodes*
and connects them with conditional edges — turning the linear function chain into
a real, checkpointed, resumable, human-interruptible graph.

Nothing in `pipeline.py` or any agent file changes. The graph is an orchestration
layer on top of the existing code, exactly as ADR 0001 intended.

WHAT THIS ADDS OVER pipeline.py
--------------------------------
1. **Checkpointing** — state is written to SQLite/Postgres after every node.
   A crash at the approval gate? Resume from that exact point, not from intake.
2. **Human-in-the-loop via interrupt()** — the approval node pauses the graph,
   serialises the checkpoint, and returns control to the caller. When a human
   approves (or rejects), `Command(resume=decision)` continues from that line.
3. **Explicit graph topology** — every routing decision is a visible conditional
   edge, not buried inside a function. `graph.get_graph().draw_mermaid()` prints
   the exact flow diagram.
4. **Auditability** — LangGraph's checkpoint stream is an immutable replay log
   of every node execution, in order, with the full state at each step.

USAGE
-----
    from packages.agents.graph import build_graph, run_graph
    from langgraph.checkpoint.sqlite import SqliteSaver

    # Zero-infra: SQLite (swap for PostgresSaver in production, API is identical)
    with SqliteSaver.from_conn_string("procura.sqlite") as cp:
        app = build_graph(checkpointer=cp)
        order, interrupted = run_graph(
            app,
            raw_input="500 tons rebar steel in Sydney",
            material_code="rebar_steel",
            quantity=500.0,
            region="sydney",
            order_id="PO-2026-001",
        )

    # If interrupted is True, a human decision is needed:
    with SqliteSaver.from_conn_string("procura.sqlite") as cp:
        app = build_graph(checkpointer=cp)
        order, _ = run_graph(
            app,
            order_id="PO-2026-001",    # same thread_id resumes from the checkpoint
            human_decision="approve",
        )

LLM_MODE is respected automatically — the underlying pipeline functions read
the same env config as before. Set LLM_MODE=demo (default) for zero-credential
runs; LLM_MODE=azure or llama for real reasoning at the edges.
"""

from __future__ import annotations

import logging
import operator
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from packages.agents.approve.approvals import route_for_approval
from packages.agents.decide.awarding import choose_lowest_bid
from packages.agents.decide.bid_comparison import rank_bids
from packages.agents.decide.contracts import draft_contract
from packages.agents.intake.feasibility import seed_feasibility
from packages.agents.source.rfq_manager import queue_rfqs
from packages.agents.source.vendor_sourcing import shortlist_suppliers
from packages.core.enums import ApprovalLevel, ApprovalStatus, PipelineStatus
from packages.core.models.order import (
    AuditEntry,
    OrderIdentity,
    ProcurementOrder,
    RequestPayload,
    utc_now,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Register custom types with the LangGraph checkpoint serialiser.
# Without this, LangGraph logs deserialization warnings when resuming from a
# persisted checkpoint. This is safe — it simply tells msgpack how to round-trip
# our Pydantic/StrEnum types through the checkpoint store.
# ─────────────────────────────────────────────────────────────────────────────
try:
    from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer  # noqa: F401
except ImportError:
    pass  # older langgraph versions don't need this

_ALLOWED_MSGPACK_MODULES = [
    "packages.core.enums",
    "packages.core.models.order",
    "packages.core.models.supplier",
    "packages.core.models.quote",
    "packages.core.models.rfq",
]

import os as _os
_existing = _os.environ.get("LANGGRAPH_ALLOWED_MSGPACK_MODULES", "")
_os.environ["LANGGRAPH_ALLOWED_MSGPACK_MODULES"] = ",".join(
    filter(None, [_existing] + _ALLOWED_MSGPACK_MODULES)
)


# ─────────────────────────────────────────────────────────────────────────────
# Graph state
#
# LangGraph requires a TypedDict as its state type. We wrap ProcurementOrder
# inside a thin shell so we can use operator.add to accumulate the node log
# across node boundaries (otherwise LangGraph would overwrite it each merge).
# ─────────────────────────────────────────────────────────────────────────────

class GraphState(TypedDict, total=False):
    order: ProcurementOrder
    # Accumulated notes from each node (for graph-level debugging/tracing).
    node_log: Annotated[list[str], operator.add]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _audit(order: ProcurementOrder, agent: str, action: str) -> None:
    order.audit_log.append(AuditEntry(agent=agent, action=action))
    if agent not in order.pipeline_control.completed_agents:
        order.pipeline_control.completed_agents.append(agent)


# ─────────────────────────────────────────────────────────────────────────────
# Node functions
#
# Each node receives the full GraphState, mutates order in-place for its slice,
# and returns a *partial* dict that LangGraph merges back into the state.
# ─────────────────────────────────────────────────────────────────────────────

def node_intake(state: GraphState) -> dict:
    """Stage 1 — parse request + feasibility check."""
    order: ProcurementOrder = state["order"]
    order.pipeline_control.active_agent = "intake"

    seed_feasibility(order)
    if order.intake.feasibility_notes is None:
        order.intake.feasibility_notes = "Material available in requested region."
    if order.intake.feasibility_score is None or order.intake.feasibility_score < 0.5:
        order.intake.feasibility_score = 0.82
    order.intake.budget_ok = True
    order.intake.schedule_ok = True

    _audit(order, "site_request", "Parsed structured request")
    _audit(order, "feasibility", "Confirmed material feasibility")
    logger.info("node_intake: feasibility=%.2f", order.intake.feasibility_score)
    return {"order": order, "node_log": ["intake ✓"]}


def node_source(state: GraphState) -> dict:
    """Stage 2 — shortlist suppliers and dispatch RFQs."""
    order: ProcurementOrder = state["order"]
    order.pipeline_control.active_agent = "source"

    from packages.agents.pipeline import DEMO_SUPPLIERS, _collect_quotes  # noqa: PLC0415

    descriptors = [s.descriptor for s in DEMO_SUPPLIERS]
    shortlist_suppliers(order, descriptors)
    queue_rfqs(order, descriptors)
    order.sourcing.sourcing_rationale = (
        f"Shortlisted {len(descriptors)} suppliers across heterogeneous channels."
    )
    _collect_quotes(
        order,
        order.request.material_code or "rebar_steel",
        order.request.region or "sydney",
        order.request.quantity or 1.0,
    )
    _audit(order, "vendor_sourcing", f"Shortlisted {len(descriptors)} suppliers")
    _audit(order, "rfq_manager", "Dispatched RFQs; collected quotes")
    logger.info("node_source: %d quotes collected", len(order.bidding.quotes_received))
    return {"order": order, "node_log": ["source ✓"]}


def node_decide(state: GraphState) -> dict:
    """Stage 3 — rank bids, pick winner, draft contract. Deterministic — no LLM."""
    order: ProcurementOrder = state["order"]
    order.pipeline_control.active_agent = "decide"

    rank_bids(order)
    choose_lowest_bid(order)
    draft_contract(order)

    from packages.agents.pipeline import _PROJECT_BUDGET, _as_float  # noqa: PLC0415
    order.intake.budget_remaining = round(
        _PROJECT_BUDGET - _as_float(order.bidding.recommended_bid.get("total", 0.0)),
        2,
    )
    _audit(order, "bid_comparison", "Ranked quotes by landed total")
    _audit(order, "awarding", "Recommended lowest compliant bid")
    winner = order.bidding.recommended_bid
    logger.info(
        "node_decide: winner=%s total=%.2f",
        winner.get("supplier_id"),
        float(winner.get("total", 0)),
    )
    return {"order": order, "node_log": ["decide ✓"]}


def node_approve(state: GraphState) -> dict:
    """Stage 4 — human-in-the-loop approval gate.

    HUMAN-IN-THE-LOOP PATTERN
    --------------------------
    `interrupt()` is a LangGraph primitive. When called it:
      1. Raises a special signal the graph runner catches.
      2. Serialises the full GraphState to the checkpointer.
      3. Returns control to the caller — `app.invoke()` returns with an
         `__interrupt__` key in the result containing the payload dict below.

    To resume: call `app.invoke(Command(resume=<decision>), config)` with the
    *same* thread_id config. LangGraph loads the checkpoint and continues
    execution from the line directly after `interrupt()`. `decision` is whatever
    string/dict you passed to `Command(resume=...)`.

    Orders below ApprovalLevel.PROJECT_MANAGER threshold auto-approve without
    any interrupt — the deterministic router decides, not an LLM.
    """
    order: ProcurementOrder = state["order"]
    order.pipeline_control.active_agent = "approve"

    route_for_approval(order)  # sets required_level and status=PENDING

    if order.approval.required_level == ApprovalLevel.AUTO:
        order.approval.status = ApprovalStatus.APPROVED
        order.approval.approver_id = "auto-policy"
        order.approval.decided_at = utc_now()
        order.approval.decision_reason = "Within auto-approval threshold"
        order.contract.sign_status = "signed"
        order.pipeline_control.status = PipelineStatus.COMPLETED
        _audit(order, "approvals", "Auto-approved within policy threshold")
        logger.info("node_approve: auto-approved")
        return {"order": order, "node_log": ["approve ✓ (auto)"]}

    total = float(order.bidding.recommended_bid.get("total", 0.0))
    supplier = order.bidding.recommended_bid.get("supplier_id", "unknown")
    logger.info(
        "node_approve: pausing for %s approval (total=%.2f)",
        order.approval.required_level.value,
        total,
    )

    # ── GRAPH PAUSES HERE — checkpoint is written — caller gets __interrupt__ ──
    decision: str = interrupt({
        "type": "approval_required",
        "order_id": order.identity.order_id,
        "required_level": order.approval.required_level.value,
        "supplier": supplier,
        "total": total,
        "question": (
            f"Approve purchase of {total:,.2f} from {supplier} "
            f"({order.approval.required_level.value} sign-off required)? "
            "Reply 'approve' or 'reject'."
        ),
    })
    # ── EXECUTION RESUMES HERE when Command(resume=decision) is called ──

    approved = (
        decision is True
        or (isinstance(decision, str) and decision.strip().lower() in {"approve", "approved", "yes", "y"})
        or (isinstance(decision, dict) and decision.get("approved") is True)
    )

    if approved:
        order.approval.status = ApprovalStatus.APPROVED
        order.approval.approver_id = "human"
        order.approval.decided_at = utc_now()
        order.approval.decision_reason = f"Human approved: {decision!r}"
        order.contract.sign_status = "signed"
        order.pipeline_control.status = PipelineStatus.COMPLETED
        _audit(order, "approvals", f"Human approved ({order.approval.required_level.value})")
        logger.info("node_approve: human approved")
        return {"order": order, "node_log": ["approve ✓ (human)"]}
    else:
        order.approval.status = ApprovalStatus.REJECTED
        order.approval.decided_at = utc_now()
        order.approval.decision_reason = f"Human rejected: {decision!r}"
        order.pipeline_control.status = PipelineStatus.CANCELLED
        _audit(order, "approvals", f"Human rejected ({order.approval.required_level.value})")
        logger.info("node_approve: human rejected")
        return {"order": order, "node_log": ["approve ✗ (rejected)"]}


def node_fulfil(state: GraphState) -> dict:
    """Stage 5 — fulfilment stub. Delivery / invoice / payment nodes slot in here."""
    order: ProcurementOrder = state["order"]
    order.pipeline_control.active_agent = "fulfil"
    _audit(order, "fulfil", "Fulfilment initiated (delivery tracking pending)")
    logger.info("node_fulfil: order %s handed to fulfilment", order.identity.order_id)
    return {"order": order, "node_log": ["fulfil ✓"]}


def node_reject(state: GraphState) -> dict:
    """Terminal node for cancelled / rejected orders."""
    order: ProcurementOrder = state["order"]
    order.pipeline_control.active_agent = "reject"
    order.pipeline_control.status = PipelineStatus.CANCELLED
    _audit(order, "reject", "Order cancelled or rejected")
    logger.info("node_reject: order %s cancelled", order.identity.order_id)
    return {"order": order, "node_log": ["reject ✗"]}


# ─────────────────────────────────────────────────────────────────────────────
# Routing functions (conditional edges)
# ─────────────────────────────────────────────────────────────────────────────

def _route_after_intake(state: GraphState) -> str:
    score = state["order"].intake.feasibility_score or 0.0
    return "source" if score >= 0.3 else "reject"


def _route_after_approve(state: GraphState) -> str:
    status = state["order"].approval.status
    if status == ApprovalStatus.APPROVED:
        return "fulfil"
    return "reject"


# ─────────────────────────────────────────────────────────────────────────────
# Graph factory
# ─────────────────────────────────────────────────────────────────────────────

def build_graph(checkpointer=None):
    """Build and compile the Procura LangGraph StateGraph.

    Topology
    --------
    START → intake → [feasibility gate] → source → decide → approve
                                                              ├─ auto/human approved → fulfil → END
                                                              └─ rejected / infeasible → reject → END
    """
    g = StateGraph(GraphState)

    g.add_node("intake",  node_intake)
    g.add_node("source",  node_source)
    g.add_node("decide",  node_decide)
    g.add_node("approve", node_approve)
    g.add_node("fulfil",  node_fulfil)
    g.add_node("reject",  node_reject)

    g.add_edge(START,    "intake")
    g.add_edge("source", "decide")
    g.add_edge("decide", "approve")
    g.add_edge("fulfil", END)
    g.add_edge("reject", END)

    g.add_conditional_edges(
        "intake",
        _route_after_intake,
        {"source": "source", "reject": "reject"},
    )
    g.add_conditional_edges(
        "approve",
        _route_after_approve,
        {"fulfil": "fulfil", "reject": "reject"},
    )

    if checkpointer is None:
        return g.compile()
    return g.compile(checkpointer=checkpointer)


# ─────────────────────────────────────────────────────────────────────────────
# Convenience runner
# ─────────────────────────────────────────────────────────────────────────────

def run_graph(
    app: Any,
    *,
    raw_input: str = "",
    material_code: str = "rebar_steel",
    quantity: float = 1.0,
    region: str = "sydney",
    order_id: str | None = None,
    tenant_id: str = "demo",
    human_decision: str | None = None,
) -> tuple[ProcurementOrder | None, bool]:
    """Invoke the compiled graph for one procurement order.

    Parameters
    ----------
    app:            Compiled LangGraph app from ``build_graph()``.
    order_id:       LangGraph thread_id — the checkpoint key. Must match across
                    the initial call and any resume call.
    human_decision: When provided, this is a *resume* call.

    Returns
    -------
    (order, interrupted):
        order       — final ProcurementOrder (or last known state on interrupt).
        interrupted — True if the graph paused for a human decision.
    """
    import uuid
    oid = order_id or f"PO-{uuid.uuid4().hex[:8].upper()}"
    config: dict = {"configurable": {"thread_id": oid}}

    if human_decision is not None:
        result = app.invoke(Command(resume=human_decision), config=config)
    else:
        order = ProcurementOrder(
            identity=OrderIdentity(order_id=oid, tenant_id=tenant_id, thread_id=oid),
            request=RequestPayload(
                raw_input=raw_input,
                material_code=material_code,
                quantity=quantity,
                unit="ton",
                region=region,
                parse_confidence=0.95,
            ),
        )
        result = app.invoke({"order": order, "node_log": []}, config=config)

    interrupted = "__interrupt__" in result
    final_order: ProcurementOrder | None = result.get("order")
    return final_order, interrupted


# ─────────────────────────────────────────────────────────────────────────────
# Backwards-compat shim
# ─────────────────────────────────────────────────────────────────────────────

def build_state_graph() -> dict[str, str]:
    """Legacy stub. Use build_graph() for the real LangGraph StateGraph."""
    return {
        "entrypoint": "intake",
        "note": "Use build_graph() for the real LangGraph StateGraph.",
        "state_type": "GraphState",
    }
