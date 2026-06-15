from packages.core.models.order import AuditEntry, ProcurementOrder


def append_audit_entry(
    order: ProcurementOrder,
    *,
    agent: str,
    action: str,
    reason: str | None = None,
    before_ref: str | None = None,
    after_ref: str | None = None,
) -> ProcurementOrder:
    order.audit_log.append(
        AuditEntry(
            agent=agent,
            action=action,
            reason=reason,
            before_ref=before_ref,
            after_ref=after_ref,
        )
    )
    return order
