"""LLM-backed pipeline nodes.

Per ADR 0003 the LLM only operates at the edges: parsing ambiguous input and
generating explanatory prose. All pricing, ranking, and approval routing stay
deterministic in `packages.agents.pipeline`. Each node loads its system prompt
from `packages/agents/prompts/` so prompt text lives outside code.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from packages.core.models.order import ProcurementOrder
from packages.llm.client import LLMClient

_PROMPT_DIR = Path(__file__).parent / "prompts"


@dataclass(frozen=True)
class ParsedRequest:
    material_code: str
    quantity: float
    unit: str
    region: str
    confidence: float


@dataclass(frozen=True)
class FeasibilityAssessment:
    score: float
    notes: str


def _load_prompt(name: str) -> str:
    return (_PROMPT_DIR / name).read_text(encoding="utf-8").strip()


def _coerce_float(value: object, fallback: float) -> float:
    if isinstance(value, bool):
        return fallback
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return fallback
    return fallback


def parse_site_request(
    llm: LLMClient,
    *,
    raw_input: str,
    fallback_material: str,
    fallback_quantity: float,
    fallback_region: str,
) -> ParsedRequest:
    """Extract structured request fields from free-form text."""

    system = _load_prompt("site_request.md")
    user = (
        f"Raw procurement request:\n{raw_input!r}\n\n"
        "Return a JSON object with keys: material_code (snake_case string), "
        "quantity (number), unit (string), region (lowercase city name), "
        "confidence (number between 0 and 1)."
    )
    data = llm.complete_json(system=system, user=user)
    return ParsedRequest(
        material_code=str(data.get("material_code") or fallback_material),
        quantity=_coerce_float(data.get("quantity"), fallback_quantity),
        unit=str(data.get("unit") or "ton"),
        region=str(data.get("region") or fallback_region).lower(),
        confidence=_coerce_float(data.get("confidence"), 0.9),
    )


def assess_feasibility(llm: LLMClient, order: ProcurementOrder) -> FeasibilityAssessment:
    """Produce a feasibility score and short risk note."""

    system = _load_prompt("feasibility.md")
    user = (
        f"Material: {order.request.material_code}\n"
        f"Quantity: {order.request.quantity} {order.request.unit}\n"
        f"Region: {order.request.region}\n\n"
        "Return a JSON object with keys: score (number between 0 and 1) and "
        "notes (one or two sentences explaining the main feasibility risks)."
    )
    data = llm.complete_json(system=system, user=user)
    score = min(max(_coerce_float(data.get("score"), 0.8), 0.0), 1.0)
    return FeasibilityAssessment(
        score=score,
        notes=str(data.get("notes") or "Feasibility assessed."),
    )


def explain_recommendation(llm: LLMClient, order: ProcurementOrder) -> str:
    """Explain the awarded bid using only the deterministic ranking matrix."""

    system = _load_prompt("bid_explanation.md")
    quotes_lines = "\n".join(
        f"- {quote.supplier_id}: total {quote.total}, lead {quote.lead_time_days}d, "
        f"reliability {quote.reliability_score}"
        for quote in order.bidding.quotes_received
    )
    recommended = order.bidding.recommended_bid
    user = (
        f"Ranked quotes (lowest total first is the deterministic winner):\n{quotes_lines}\n\n"
        f"Recommended supplier: {recommended.get('supplier_id')} "
        f"at total {recommended.get('total')}.\n\n"
        "Write two or three sentences explaining why this is the recommended bid. "
        "Do not invent numbers beyond those provided."
    )
    return llm.complete(system=system, user=user)


def write_contract_cover(llm: LLMClient, order: ProcurementOrder) -> str:
    """Draft a short professional contract cover note for the award."""

    system = _load_prompt("contract_cover.md")
    recommended = order.bidding.recommended_bid
    user = (
        f"Awarded supplier: {recommended.get('supplier_id')}\n"
        f"Material: {order.request.material_code}, quantity {order.request.quantity} "
        f"{order.request.unit}, region {order.request.region}\n"
        f"Total: {recommended.get('total')}, lead time {recommended.get('lead_time_days')} days\n\n"
        "Write a concise, professional contract cover note (3-5 sentences)."
    )
    return llm.complete(system=system, user=user)
