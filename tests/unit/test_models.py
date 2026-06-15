from packages.core.audit import append_audit_entry
from packages.core.enums import InputModality, Locale
from packages.core.models.order import OrderIdentity, ProcurementOrder, RequestPayload


def test_procurement_order_builds_thread_id_from_identity() -> None:
    order = ProcurementOrder(
        identity=OrderIdentity(tenant_id="watad-demo"),
        request=RequestPayload(
            raw_input="Need 500 tons of rebar in Riyadh",
            input_modality=InputModality.TEXT,
            locale=Locale.EN,
        ),
    )

    assert order.identity.thread_id == f"watad-demo:{order.identity.order_id}"
    assert order.pipeline_control.status == "running"


def test_append_audit_entry_is_append_only() -> None:
    order = ProcurementOrder(
        identity=OrderIdentity(),
        request=RequestPayload(raw_input="Need 100 pipes in Jeddah"),
    )

    append_audit_entry(order, agent="site_request", action="parsed", reason="structured input")

    assert len(order.audit_log) == 1
    assert order.audit_log[0].agent == "site_request"
    assert order.audit_log[0].action == "parsed"
