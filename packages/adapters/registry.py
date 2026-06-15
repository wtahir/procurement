from packages.core.models.supplier import SupplierDescriptor
from packages.rag.retrievers import retrieve_candidate_suppliers


class SupplierRegistry:
    def __init__(self, suppliers: list[SupplierDescriptor]) -> None:
        self.suppliers = suppliers

    def search(self, material_code: str, region: str, quantity: float) -> list[SupplierDescriptor]:
        return retrieve_candidate_suppliers(self.suppliers, material_code, region, quantity)
