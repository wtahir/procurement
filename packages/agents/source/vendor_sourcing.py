from packages.core.models.order import ProcurementOrder
from packages.core.models.supplier import SupplierDescriptor


def shortlist_suppliers(order: ProcurementOrder, suppliers: list[SupplierDescriptor]) -> ProcurementOrder:
    order.sourcing.candidate_supplier_ids = [supplier.supplier_id for supplier in suppliers]
    return order
