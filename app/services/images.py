import base64
import io
import requests
from PIL import Image

def fetch_raster_image(url: str):
    """
    Descarga una imagen (PNG/JPEG/WEBP/ICO) y devuelve (bytes, content_type).
    Lanza ValueError si el Content-Type no es uno de los permitidos.
    """
    r = requests.get(url, timeout=8)
    r.raise_for_status()
    ctype = r.headers.get("Content-Type", "").lower()
    if not any(fmt in ctype for fmt in ("image/png", "image/jpeg", "image/webp", "image/x-icon")):
        raise ValueError("img_logo debe ser PNG/JPEG/WEBP/ICO.")
    if "png" in ctype:
        c = "image/png"
    elif "jpeg" in ctype or "jpg" in ctype:
        c = "image/jpeg"
    elif "webp" in ctype:
        c = "image/webp"
    else:
        c = "image/x-icon"
    return r.content, c

def to_data_uri(img_bytes: bytes, content_type: str) -> str:
    """
    Codifica bytes de imagen a data URI (base64) para incrustar en HTML.
    """
    b64 = base64.b64encode(img_bytes).decode("utf-8")
    return f"data:{content_type};base64,{b64}"

def download_image_bytes(url: str) -> bytes:
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.content

def normalize_png_for_favicon(img_bytes: bytes, size: int = 64, remove_alpha: bool = False, bg=(255,255,255)):
    """
    - Reescala manteniendo aspecto
    - Elimina metadatos (gAMA, tEXt, etc.) al re-guardar
    - Opción de aplanar alpha sobre un fondo (blanco por defecto)
    - Devuelve bytes PNG 8-bit
    """
    im = Image.open(io.BytesIO(img_bytes))
    im.load()  # asegura que los datos estén leídos, no solo lazy

    # Convertimos a RGBA para unificar tratamiento
    if im.mode != "RGBA":
        im = im.convert("RGBA")

    # Reescalado “favicon”
    im = im.copy()
    im.thumbnail((size, size))

    # Opción: aplanar alpha (muchas veces evita rarezas en tab)
    if remove_alpha:
        flat = Image.new("RGB", im.size, bg)
        flat.paste(im, mask=im.split()[-1])  # usa el canal A como máscara
        im_out = flat  # sin alpha
        fmt = "PNG"
    else:
        im_out = im  # mantiene RGBA
        fmt = "PNG"

    # Re-guardar SIN copiar pnginfo (así no arrastra gAMA ni textos)
    bio = io.BytesIO()
    im_out.save(bio, format=fmt, optimize=True)  # no pasamos pnginfo → se limpia
    return bio.getvalue()

