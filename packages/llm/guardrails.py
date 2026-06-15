def strip_confidential_fields(
    payload: dict[str, object], blocked_fields: set[str]
) -> dict[str, object]:
    return {key: value for key, value in payload.items() if key not in blocked_fields}
