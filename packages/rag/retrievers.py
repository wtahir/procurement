from packages.core.models.supplier import SupplierDescriptor
from packages.rag.store import filter_suppliers


def retrieve_candidate_suppliers(
    suppliers: list[SupplierDescriptor], material_code: str, region: str, quantity: float
) -> list[SupplierDescriptor]:
    ranked = sorted(
        filter_suppliers(suppliers, material_code, region, quantity),
        key=lambda supplier: supplier.reliability_score,
        reverse=True,
    )
    return ranked[:12]
