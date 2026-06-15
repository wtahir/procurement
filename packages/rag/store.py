from packages.core.models.supplier import SupplierDescriptor


def filter_suppliers(
    suppliers: list[SupplierDescriptor], material_code: str, region: str, quantity: float
) -> list[SupplierDescriptor]:
    region_lower = region.lower()
    return [
        supplier
        for supplier in suppliers
        if material_code in supplier.materials
        and region_lower in [value.lower() for value in supplier.regions]
        and quantity >= supplier.min_order
    ]
