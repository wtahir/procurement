def parse_fixed_width(line: str) -> dict[str, str]:
    return {
        "supplier_code": line[:12].strip(),
        "material_code": line[12:28].strip(),
        "price": line[28:38].strip(),
    }
