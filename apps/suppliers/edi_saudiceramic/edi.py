def build_edi_message(reference: str) -> str:
    return f"ISA*00*          *00*          *ZZ*PROCURA*ZZ*SUPPLIER*{reference}~"
