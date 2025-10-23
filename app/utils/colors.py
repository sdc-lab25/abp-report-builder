import re

HEX_RE = re.compile(r"^#?[0-9A-Fa-f]{6}$")

def as_hex(v: str) -> str:
    """
    Valida colores en formato HEX (#RRGGBB); admite entrada con o sin '#'
    y devuelve siempre con '#'. Lanza ValueError si no es válido.
    """
    if not isinstance(v, str):
        raise ValueError("Color inválido: no es string")
    v2 = v.strip()
    if not HEX_RE.match(v2):
        raise ValueError(f"Color inválido: {v}")
    return v2 if v2.startswith("#") else f"#{v2}"
