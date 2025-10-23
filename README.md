# App GPT — Refactor Limpio

Este paquete ha sido limpiado y reestructurado para mantener **exactamente** la misma lógica de front y de generación de documentos, eliminando artefactos y módulos no utilizados de versiones anteriores.

## Cambios clave

- Limpieza de `__pycache__`, `*.pyc` y módulos no referenciados (`app/logging_conf.py`, `app/utils/timezones.py`).
- Añadido **modo debug** para procesar **solo una página** (la página 3) definida en `app/config/doc_pages.json`.
- Se ha generado `requirements.txt` con las dependencias mínimas detectadas.
- Sin cambios funcionales en el front ni en los pipelines de generación.

## Requisitos

- Windows (se usa `win32com` para automatizar Word).
- Python 3.10+ recomendado.
- Microsoft Word instalado (para exportar a PDF via COM).
- Acceso a los recursos (CSV en `app_gpt/data/`, plantillas DOCX dentro del ZIP que subes por la UI).

Instala dependencias:

```bash
pip install -r requirements.txt
```

## Ejecución

```bash
streamlit run app.py
```

## Modo Debug (solo página 3)

En la **barra lateral** encontrarás el checkbox **«Debug: solo procesar la página 3»**.  
Si lo activas, `generate_report_pdf` únicamente procesará la **página 3** de `doc_pages.json` (índice 1-based).

## Variables de entorno

Edita `.env` (incluido) o exporta variables equivalentes en tu entorno.

- `THEME_URL`
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `TZ` (opcional, por defecto `Europe/Madrid`).

## Notas

- Si necesitas cambiar la página de debug, modifica el valor 3 en `app.py` (parámetro `debug_single_page_index`) o amplia la UI.
- Si usas Linux/macOS, no funcionará la exportación via COM; podrías reemplazar Word+COM por `python-docx`+`docx2pdf` (no incluido aquí).
