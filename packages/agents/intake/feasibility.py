from packages.core.models.order import ProcurementOrder


def seed_feasibility(order: ProcurementOrder) -> ProcurementOrder:
    order.intake.feasibility_score = order.intake.feasibility_score or 0.5
    return order
