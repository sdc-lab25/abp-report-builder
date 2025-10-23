# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
import json, io, zipfile, tempfile, shutil, os, time
from typing import List, Dict, Any, Optional

import pythoncom
from pywintypes import com_error
from win32com.client import gencache, constants as c, Dispatch, DispatchEx
from PyPDF2 import PdfMerger

import pandas as pd
from app.table_builders import (
    mk_set_pieces, mk_corners, mk_dfk, mk_ifk, mk_throwins,
    _summ_corners, _summ_ifks, _summ_throwins, _pk_corners,
    _pc_corners, _pk_ifks, _pc_ifks, _pk_throwins,
    _pc_throwins, players_overview, team_stats_detailed
)

from app.image_builders import (
    team_square_image, bars_heights_coach, bars_heights_rival,
    builder_plot_shot_creating_actions, builder_plot_shot_actions,
    plot_team_overview
)


# =================== Utilidades de reintento COM ===================

def _is_call_rejected(exc: Exception) -> bool:
    # -2147418111 == 0x80010001 RPC_E_CALL_REJECTED
    return isinstance(exc, com_error) and (
        getattr(exc, "hresult", None) == -2147418111 or
        "RPC_E_CALL_REJECTED" in str(exc)
    )

def com_retry(fn, *args, _tries: int = 12, _base_wait: float = 0.15, _factor: float = 1.6, **kwargs):
    """
    Ejecuta fn(*args, **kwargs) con reintentos si Word rechaza la llamada por estar ocupado.
    Backoff exponencial: 0.15s, 0.24s, 0.38s, ... ~7s total por defecto.
    """
    for i in range(_tries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if _is_call_rejected(e) and i < _tries - 1:
                try:
                    pythoncom.PumpWaitingMessages()
                except Exception:
                    pass
                time.sleep(_base_wait * (_factor ** i))
                continue
            raise


# =================== Utilidades Word ===================

def cm_to_points(cm: float) -> float:
    return float(cm) * 28.3464567

def _replace_everywhere(doc, target: str, replacement: str, match_case: bool = True):
    for story in doc.StoryRanges:
        rng = story
        while rng is not None:
            f = rng.Find
            f.ClearFormatting(); f.Replacement.ClearFormatting()
            f.Text = target
            f.Replacement.Text = replacement
            f.Forward = True
            f.Wrap = c.wdFindContinue
            f.MatchCase = bool(match_case)
            f.MatchWholeWord = False
            f.MatchWildcards = False
            # Reintento en la llamada COM sensible
            com_retry(f.Execute, Replace=c.wdReplaceAll)
            rng = rng.NextStoryRange

    def _in_shapes(shapes):
        try:
            count = shapes.Count
        except Exception:
            return
        for i in range(1, count + 1):
            shp = shapes.Item(i)
            try:
                if shp.TextFrame.HasText:
                    f = shp.TextFrame.TextRange.Find
                    f.ClearFormatting(); f.Replacement.ClearFormatting()
                    f.Text = target
                    f.Replacement.Text = replacement
                    f.Forward = True
                    f.Wrap = c.wdFindContinue
                    f.MatchCase = bool(match_case)
                    f.MatchWholeWord = False
                    f.MatchWildcards = False
                    com_retry(f.Execute, Replace=c.wdReplaceAll)
            except Exception:
                pass
            # Grupos
            try:
                gi = shp.GroupItems
                for j in range(1, gi.Count + 1):
                    sub = gi.Item(j)
                    try:
                        if sub.TextFrame.HasText:
                            f = sub.TextFrame.TextRange.Find
                            f.ClearFormatting(); f.Replacement.ClearFormatting()
                            f.Text = target
                            f.Replacement.Text = replacement
                            f.Forward = True
                            f.Wrap = c.wdFindContinue
                            f.MatchCase = bool(match_case)
                            f.MatchWholeWord = False
                            f.MatchWildcards = False
                            com_retry(f.Execute, Replace=c.wdReplaceAll)
                    except Exception:
                        pass
            except Exception:
                pass

    _in_shapes(doc.Shapes)
    for sec in doc.Sections:
        for hdr in sec.Headers: _in_shapes(hdr.Shapes)
        for ftr in sec.Footers: _in_shapes(ftr.Shapes)

def _replace_first_bold_upper(doc, target: str, replacement: str, match_case: bool = False) -> bool:
    """
    Reemplaza SOLO la primera coincidencia de 'target' por replacement.upper()
    y aplica negrita a ese rango. Devuelve True si hubo reemplazo.
    """
    repl_text = (replacement or "").upper()

    # 1) Historias de texto
    for story in doc.StoryRanges:
        rng = story.Duplicate
        f = rng.Find
        f.ClearFormatting(); f.Replacement.ClearFormatting()
        f.Text = target
        f.Replacement.Text = repl_text
        f.Forward = True
        f.Wrap = c.wdFindStop
        f.MatchCase = bool(match_case)
        f.MatchWildcards = False
        if com_retry(f.Execute):
            # Poner el texto y formatear negrita manualmente
            sel = rng.Duplicate
            sel.Text = repl_text
            try: sel.Font.Bold = True
            except Exception: pass
            return True

    # 2) Shapes
    try:
        for i in range(1, doc.Shapes.Count + 1):
            shp = doc.Shapes.Item(i)
            try:
                if shp.TextFrame.HasText:
                    rng = shp.TextFrame.TextRange.Duplicate
                    f = rng.Find
                    f.ClearFormatting(); f.Replacement.ClearFormatting()
                    f.Text = target
                    f.Replacement.Text = repl_text
                    f.Forward = True
                    f.Wrap = c.wdFindStop
                    f.MatchCase = bool(match_case)
                    f.MatchWildcards = False
                    if com_retry(f.Execute):
                        sel = rng.Duplicate
                        sel.Text = repl_text
                        try: sel.Font.Bold = True
                        except Exception: pass
                        return True
            except Exception:
                pass
    except Exception:
        pass
    return False

def _clear_body_row_format(row) -> None:
    """
    Limpia sombreado/fuente de una fila (para evitar heredar la cabecera negra).
    """
    try:
        for j in range(1, row.Cells.Count + 1):
            cell = row.Cells(j)
            try:
                # Quitar color de fondo / devolver a automático
                cell.Shading.BackgroundPatternColor = c.wdColorAutomatic
            except Exception: pass
            try:
                cell.Range.Shading.BackgroundPatternColor = c.wdColorAutomatic
            except Exception: pass
            try:
                cell.Range.Font.ColorIndex = c.wdAuto
            except Exception: pass
            try:
                cell.Range.Font.Bold = False
            except Exception: pass
    except Exception:
        pass

def _ensure_body_template_row(tbl) -> None:
    """
    Garantiza que exista al menos UNA fila de cuerpo (fila 2) con formato de cuerpo,
    no de cabecera. Si no existe, la crea y limpia su formato.
    """
    try:
        if tbl.Rows.Count == 1:
            tbl.Rows.Add()
        # Asegurar limpieza de la fila 2 (plantilla de cuerpo)
        _clear_body_row_format(tbl.Rows(2))
    except Exception:
        pass


def _replace_everywhere_bold_upper(doc, target: str, replacement: str, match_case: bool = False):
    """
    Reemplaza target por replacement.upper() y aplica negrita al texto reemplazado.
    """
    repl_text = (replacement or "").upper()
    for story in doc.StoryRanges:
        rng = story
        while rng is not None:
            f = rng.Find
            f.ClearFormatting(); f.Replacement.ClearFormatting()
            f.Text = target
            f.Replacement.Text = repl_text
            f.Forward = True
            f.Wrap = c.wdFindContinue
            f.MatchCase = bool(match_case)
            f.MatchWildcards = False
            try:
                # Formato en la sustitución
                f.Replacement.Font.Bold = True
            except Exception:
                pass
            com_retry(f.Execute, Replace=c.wdReplaceAll)
            rng = rng.NextStoryRange

    def _in_shapes_bold(shapes):
        try:
            count = shapes.Count
        except Exception:
            return
        for i in range(1, count + 1):
            shp = shapes.Item(i)
            try:
                if shp.TextFrame.HasText:
                    f = shp.TextFrame.TextRange.Find
                    f.ClearFormatting(); f.Replacement.ClearFormatting()
                    f.Text = target
                    f.Replacement.Text = repl_text
                    f.Forward = True
                    f.Wrap = c.wdFindContinue
                    f.MatchCase = bool(match_case)
                    f.MatchWildcards = False
                    try:
                        f.Replacement.Font.Bold = True
                    except Exception:
                        pass
                    com_retry(f.Execute, Replace=c.wdReplaceAll)
            except Exception:
                pass
            try:
                gi = shp.GroupItems
                for j in range(1, gi.Count + 1):
                    sub = gi.Item(j)
                    try:
                        if sub.TextFrame.HasText:
                            f = sub.TextFrame.TextRange.Find
                            f.ClearFormatting(); f.Replacement.ClearFormatting()
                            f.Text = target
                            f.Replacement.Text = repl_text
                            f.Forward = True
                            f.Wrap = c.wdFindContinue
                            f.MatchCase = bool(match_case)
                            f.MatchWildcards = False
                            try:
                                f.Replacement.Font.Bold = True
                            except Exception:
                                pass
                            com_retry(f.Execute, Replace=c.wdReplaceAll)
                    except Exception:
                        pass
            except Exception:
                pass

    _in_shapes_bold(doc.Shapes)
    for sec in doc.Sections:
        for hdr in sec.Headers: _in_shapes_bold(hdr.Shapes)
        for ftr in sec.Footers: _in_shapes_bold(ftr.Shapes)


def _replace_first_in_doc(doc, target: str, replacement: str, match_case: bool = False):
    """
    Reemplaza solo la PRIMERA ocurrencia.
    """
    # 1) Cuerpo/historias
    for story in doc.StoryRanges:
        f = story.Find
        f.ClearFormatting(); f.Replacement.ClearFormatting()
        f.Text = target
        f.Replacement.Text = replacement
        f.Forward = True
        f.Wrap = c.wdFindStop
        f.MatchCase = bool(match_case)
        f.MatchWildcards = False
        if com_retry(f.Execute, Replace=c.wdReplaceOne):
            return True

    # 2) Shapes (si no se encontró antes)
    try:
        count = doc.Shapes.Count
    except Exception:
        count = 0
    for i in range(1, count + 1):
        shp = doc.Shapes.Item(i)
        try:
            if shp.TextFrame.HasText:
                f = shp.TextFrame.TextRange.Find
                f.ClearFormatting(); f.Replacement.ClearFormatting()
                f.Text = target
                f.Replacement.Text = replacement
                f.Forward = True
                f.Wrap = c.wdFindStop
                f.MatchCase = bool(match_case)
                f.MatchWildcards = False
                if com_retry(f.Execute, Replace=c.wdReplaceOne):
                    return True
        except Exception:
            pass
    return False


def _delete_paragraphs_containing(doc, needle: str, skip_first: bool):
    """
    Elimina PÁRRAFOS que contengan 'needle'. Si skip_first=True, deja el primer párrafo que lo contenga.
    Asunción: las 'frases' con (*) están en párrafos/bullets separados (plantilla).
    """
    seen = False
    # Cuerpo principal
    try:
        # Recorremos al revés para borrar sin saltos
        for i in range(doc.Paragraphs.Count, 0, -1):
            p = doc.Paragraphs(i)
            try:
                txt = str(p.Range.Text or "")
                if needle in txt:
                    if skip_first and not seen:
                        seen = True
                        continue
                    p.Range.Delete()
            except Exception:
                pass
    except Exception:
        pass

    # Shapes
    try:
        for si in range(1, doc.Shapes.Count + 1):
            shp = doc.Shapes.Item(si)
            try:
                if shp.TextFrame.HasText:
                    rng = shp.TextFrame.TextRange
                    # Párrafos del shape
                    for j in range(rng.Paragraphs.Count, 0, -1):
                        pj = rng.Paragraphs(j)
                        try:
                            txt = str(pj.Range.Text or "")
                            if needle in txt:
                                if skip_first and not seen:
                                    seen = True
                                    continue
                                pj.Range.Delete()
                        except Exception:
                            pass
            except Exception:
                pass
    except Exception:
        pass


def _shorten_name(name: str, limit: int):
    name = (name or "").strip()
    if len(name) <= limit:
        return name
    parts = name.split()
    return parts[0] if parts else name[:limit]


def _fill_first_table_with_rows(doc, rows: List[Dict[str, Any]], rival_name: str, n: int):
    """
    Llena la PRIMERA tabla dejando la cabecera intacta, con estética de la plantilla:
    - Mantiene una fila 'plantilla' de cuerpo (fila 2) para heredar estilos.
    - Limpia sombreado/color en las filas de cuerpo (evita fondo negro).
    - Escribe n filas (o las que haya en rows).
    Columnas: Team | Date | Field | Season | Competition | Opposition
    """
    if n <= 0:
        return
    try:
        tbl = doc.Tables(1)
    except Exception:
        return

    # Garantizar fila de cuerpo y estilo de cuerpo
    _ensure_body_template_row(tbl)

    # Ajustar nº de filas de cuerpo a n
    header_rows = 1
    body_rows = tbl.Rows.Count - header_rows
    # Reducir
    while body_rows > n:
        try:
            tbl.Rows(tbl.Rows.Count).Delete()
            body_rows -= 1
        except Exception:
            break
    # Ampliar
    while body_rows < n:
        try:
            tbl.Rows.Add()
            _clear_body_row_format(tbl.Rows(tbl.Rows.Count))
            body_rows += 1
        except Exception:
            break

    # Limpiar formato de TODAS las filas de cuerpo (por si heredaron cabecera)
    try:
        for i in range(2, tbl.Rows.Count + 1):
            _clear_body_row_format(tbl.Rows(i))
    except Exception:
        pass

    use_rows = (rows or [])[:n]
    RIVAL = (rival_name or "").strip()

    # Volcar datos
    for idx, row in enumerate(use_rows, start=2):
        # Col 1: rival (negrita, recorte >15)
        rival_cell = _shorten_name(RIVAL, 15)
        try:
            r1 = tbl.Cell(idx, 1).Range
            r1.Text = rival_cell
            try: r1.Font.Bold = True
            except Exception: pass
        except Exception:
            pass

        # Col 2: fecha (localDate, YYYY-MM-DD tal cual)
        try:
            tbl.Cell(idx, 2).Range.Text = str(row.get("localDate", "") or "")
        except Exception:
            pass

        # Col 3: home/away
        hname_full  = str(row.get("home_name", "") or "")
        aname_full  = str(row.get("away_name", "") or "")
        hname_short = str(row.get("home_shortName", "") or hname_full)
        aname_short = str(row.get("away_shortName", "") or aname_full)

        # Col 3: Field (home/away) -> comparar SIEMPRE con full, no con short
        side = "home" if hname_full.lower() == RIVAL.lower() else ("away" if aname_full.lower() == RIVAL.lower() else "")
        try:
            tbl.Cell(idx, 3).Range.Text = side
        except Exception:
            pass

        # Col 1: Team (el rival). Si quieres que sea short, usa el short de la fila cuando haya match:
        team_disp = (
            hname_short if hname_full.lower() == RIVAL.lower() else
            aname_short if aname_full.lower() == RIVAL.lower() else
            RIVAL
        )
        team_disp = _shorten_name(team_disp, 15)
        try:
            r1 = tbl.Cell(idx, 1).Range
            r1.Text = team_disp
            try: r1.Font.Bold = True
            except Exception: pass
        except Exception:
            pass

        # Col 6: Opposition -> usa SHORT y luego tu recorte habitual
        opponent = aname_short if hname_full.lower() == RIVAL.lower() else hname_short if aname_full.lower() == RIVAL.lower() else ""
        opp_disp = _shorten_name(opponent, 21)
        try:
            c6 = tbl.Cell(idx, 6).Range
            c6.Text = opp_disp
            try: c6.Font.Bold = True
            except Exception: pass
        except Exception:
            pass
            

def _copy_row_style(src_row, dst_row):
    """
    Copia sombreado y formato de fuente de src_row -> dst_row (mismo nº de celdas o se ajusta al mínimo).
    """
    try:
        n = min(src_row.Cells.Count, dst_row.Cells.Count)
        for j in range(1, n + 1):
            s = src_row.Cells(j).Range
            d = dst_row.Cells(j).Range

            # Sombreado/fondo
            try:
                d.Shading.BackgroundPatternColor = s.Shading.BackgroundPatternColor
                d.Shading.ForegroundPatternColor = s.Shading.ForegroundPatternColor
                d.Shading.Texture = s.Shading.Texture
            except Exception:
                pass

            # Fuente
            try:
                d.Font.Name = s.Font.Name
                d.Font.Size = s.Font.Size
                d.Font.Bold = s.Font.Bold
                d.Font.Italic = s.Font.Italic
                d.Font.Color = s.Font.Color
                d.Font.ColorIndex = s.Font.ColorIndex
                d.ParagraphFormat.Alignment = s.ParagraphFormat.Alignment
            except Exception:
                pass
    except Exception:
        pass

def _fill_player_table_preserving_styles_and_total_core(tbl, body_rows, total_row):
    """
    La versión 'core' que trabaja directamente con el objeto Word.Table (tbl),
    una lista de filas de cuerpo (body_rows) y la fila TOTAL (total_row).
    """
    if tbl is None:
        return
    num_cols = tbl.Columns.Count
    if num_cols <= 0:
        return

    # Asegurar al menos cabecera, plantilla y TOTAL
    while tbl.Rows.Count < 3:
        tbl.Rows.Add()

    header_row_idx = 1
    template_row_idx = 2

    def _current_body_count():
        return max(tbl.Rows.Count - 2, 0)

    needed = len(body_rows) - _current_body_count()
    if needed > 0:
        for _ in range(needed):
            tbl.Rows.Add(BeforeRow=tbl.Rows(tbl.Rows.Count))  # antes de TOTAL
            _copy_row_style(tbl.Rows(template_row_idx), tbl.Rows(tbl.Rows.Count - 1))
    elif needed < 0:
        for _ in range(-needed):
            if tbl.Rows.Count > 3:
                tbl.Rows(tbl.Rows.Count - 1).Delete()

    last_row_idx = tbl.Rows.Count  # TOTAL

    # Volcar cuerpo
    for i, row_values in enumerate(body_rows):
        target_row_idx = 1 + i + 1  # 2,3,4...
        for j in range(1, num_cols + 1):
            val = ""
            if j <= len(row_values):
                val = "" if row_values[j - 1] is None else str(row_values[j - 1])
                rng = tbl.Cell(target_row_idx, j).Range
                rng.Text = val
                # Reglas de formato del CUERPO:
                # - Columna 1 SIEMPRE en negrita
                # - Resto de columnas SIN negrita
                try:
                    if j == 1:
                        rng.Font.Bold = True
                    else:
                        rng.Font.Bold = False
                    # (no tocamos la alineación del cuerpo)
                except Exception:
                    pass

    # TOTAL
    for j in range(1, num_cols + 1):
        val = ""
        if j <= len(total_row):
            val = "" if total_row[j - 1] is None else str(total_row[j - 1])
        rng_tot = tbl.Cell(last_row_idx, j).Range
        rng_tot.Text = val
    # Estilo TOTAL = cabecera
    _copy_row_style(tbl.Rows(header_row_idx), tbl.Rows(last_row_idx))
    # …y centramos + negrita explícita en TODAS las celdas del TOTAL
    try:
        for j in range(1, num_cols + 1):
            cell_rng = tbl.Cell(last_row_idx, j).Range
            cell_rng.ParagraphFormat.Alignment = c.wdAlignParagraphCenter
            cell_rng.Font.Bold = True    
    except Exception:
        pass

def _fill_player_table_preserving_styles_and_total(doc, df: pd.DataFrame, total_label: str = "TOTAL", table_idx: int = 1):
    """
    Wrapper compatible con el código existente:
      - Recibe doc + df + total_label + table_idx
      - Construye body_rows (lista de listas) y total_row
      - Llama a la versión core que opera con Word.Table
    """
    import pandas as pd
    if df is None or df.empty:
        return

    # Obtener la tabla destino
    try:
        tbl = doc.Tables(table_idx)
    except Exception:
        return

    # Aseguramos que exista la fila 2 como plantilla de cuerpo "limpia"
    _ensure_body_template_row(tbl)

    cols = list(df.columns)

    # Cuerpo: convertir DF -> lista de listas con formateo numérico
    body_rows = []
    for _, row in df.iterrows():
        values = []
        for j, col in enumerate(cols, start=1):
            val = row[col]
            if j == 1:
                # primera columna suele ser texto (jugador)
                values.append("" if pd.isna(val) else str(val))
            else:
                values.append("" if pd.isna(val) else _fmt_number_cell(val))
        body_rows.append(values)

    # TOTAL: primera celda = etiqueta; resto = sumas numéricas formateadas
    df_num = df.copy()
    for c in cols[1:]:
        df_num[c] = pd.to_numeric(df_num[c], errors="coerce")
    sums = df_num[cols[1:]].sum(axis=0, skipna=True)

    total_row = [total_label]
    for c in cols[1:]:
        total_row.append(_fmt_number_cell(sums.get(c, "")))

    # Llamamos a la core (la que trabaja con Word.Table)
    _fill_player_table_preserving_styles_and_total_core(tbl, body_rows, total_row)


def _insert_badge_centered(doc, image_path: Path, width_cm: float, height_cm: float,
                           top_cm: float, offx_cm: float, offy_cm: float):
    ps = doc.PageSetup
    page_w = float(ps.PageWidth)
    left_m = float(ps.LeftMargin)
    right_m = float(ps.RightMargin)
    top_m = float(ps.TopMargin)

    W = cm_to_points(width_cm)
    H = cm_to_points(height_cm)
    usable_w = page_w - left_m - right_m

    L = left_m + (usable_w - W) / 2 + cm_to_points(offx_cm)
    T = top_m + cm_to_points(top_cm + offy_cm)

    shp = com_retry(
        doc.Shapes.AddPicture,
        FileName=str(image_path), LinkToFile=False, SaveWithDocument=True,
        Left=L, Top=T, Width=W, Height=H
    )
    try: shp.LockAspectRatio = True
    except Exception: pass
    return shp

def _insert_badge_precise(doc, image_path: Path, width_cm: float, height_cm: float,
                          pos_h_cm: float, pos_v_cm: float):
    W = cm_to_points(width_cm)
    H = cm_to_points(height_cm)
    shp = com_retry(
        doc.Shapes.AddPicture,
        FileName=str(image_path), LinkToFile=False, SaveWithDocument=True,
        Left=cm_to_points(pos_h_cm), Top=cm_to_points(pos_v_cm), Width=W, Height=H
    )
    try:
        shp.LockAspectRatio = True
        shp.RelativeHorizontalPosition = c.wdRelativeHorizontalPositionColumn
        shp.RelativeVerticalPosition   = c.wdRelativeVerticalPositionParagraph
        shp.WrapFormat.Type = c.wdWrapFront
        shp.WrapFormat.AllowOverlap = True
        shp.LayoutInCell = True
        shp.LockAnchor = False
        try:
            shp.ZOrder(getattr(c, "msoBringToFront", 0))
        except Exception:
            pass
    except Exception:
        pass
    return shp

def _export_pdf(word_app, doc, out_pdf_path: Path):
    com_retry(
        doc.ExportAsFixedFormat,
        OutputFileName=str(out_pdf_path),
        ExportFormat=c.wdExportFormatPDF,
        OpenAfterExport=False,
        OptimizeFor=c.wdExportOptimizeForPrint,
        Range=c.wdExportAllDocument,
        Item=c.wdExportDocumentContent,
        IncludeDocProps=True,
        KeepIRM=True,
        CreateBookmarks=c.wdExportCreateNoBookmarks,
        DocStructureTags=True,
        BitmapMissingFonts=True,
        UseISO19005_1=False
    )


# =================== Plantillas dentro del ZIP ===================

def _find_template_path(base_dir: Path, filename: str) -> Optional[Path]:
    """
    Devuelve la ruta al template dentro de base_dir o de cualquiera de sus subcarpetas.
    """
    p = (base_dir / filename)
    if p.exists():
        return p
    for cand in base_dir.rglob(filename):
        if cand.is_file():
            return cand
    return None


# =================== Manejo robusto de COM/Word ===================

WORD_GUID = "{00020905-0000-0000-C000-000000000046}"  # Microsoft Word
LCID = 0  # neutro
WORD_VERSIONS_TO_TRY = [(8, 7), (8, 6), (8, 5), (8, 4), (8, 3)]

def _clear_word_genpy_cache():
    try:
        gen_dir = gencache.GetGeneratePath()
        if os.path.isdir(gen_dir):
            for name in os.listdir(gen_dir):
                if name.lower().startswith(WORD_GUID.strip("{}").lower()):
                    shutil.rmtree(os.path.join(gen_dir, name), ignore_errors=True)
        try:
            gencache.CleanUp()
        except Exception:
            pass
    except Exception:
        try:
            shutil.rmtree(gencache.GetGeneratePath(), ignore_errors=True)
        except Exception:
            pass

def _ensure_word_wrappers():
    for major, minor in WORD_VERSIONS_TO_TRY:
        try:
            gencache.EnsureModule(WORD_GUID, LCID, major, minor)
            return True
        except Exception:
            continue
    return False

def _get_word_app():
    try:
        return gencache.EnsureDispatch("Word.Application")
    except Exception:
        _clear_word_genpy_cache()
        _ensure_word_wrappers()
        try:
            return gencache.EnsureDispatch("Word.Application")
        except Exception:
            try:
                return DispatchEx("Word.Application")
            except Exception:
                return Dispatch("Word.Application")


# =================== Núcleo: generación “simple” ===================

def _apply_badge_from_json(doc, badge_cfg: Dict[str, Any], image_path: Path):
    """
    Inserta el escudo usando EXCLUSIVAMENTE coordenadas absolutas declaradas en JSON.
    Requiere: width_cm, height_cm, pos_h_cm, pos_v_cm.
    (Sin centrado ni defaults.)
    """
    b = badge_cfg or {}
    required = ("width_cm", "height_cm", "pos_h_cm", "pos_v_cm")
    missing = [k for k in required if b.get(k) is None]
    if missing:
        raise RuntimeError(f"badge incompleto; faltan claves: {', '.join(missing)}")

    return _insert_badge_precise(
        doc,
        image_path,
        float(b["width_cm"]),
        float(b["height_cm"]),
        float(b["pos_h_cm"]),
        float(b["pos_v_cm"]),
    )

def _insert_images_from_config(doc, images_cfg: Dict[str, Any], ctx: Dict[str, Any]):
    items = (images_cfg or {}).get("items", []) or []
    for it in items:
        builder_name = it.get("builder")
        fn = IMAGE_BUILDERS.get(builder_name)
        if not fn:
            continue

        args = it.get("args", {}) or {}
        try:
            out_path = fn(ctx, **args)
        except Exception:
            continue
        if not out_path or not os.path.exists(out_path):
            continue

        left  = cm_to_points(float(it.get("pos_h_cm", 0.0)))
        top   = cm_to_points(float(it.get("pos_v_cm", 0.0)))
        w_pt  = cm_to_points(float(it.get("width_cm", 0.0)))
        h_pt  = cm_to_points(float(it.get("height_cm", 0.0)))

        try:
            shp = doc.Shapes.AddPicture(
                FileName=out_path,
                LinkToFile=False,
                SaveWithDocument=True,
                Left=left,
                Top=top
            )
            shp.LockAspectRatio = False
            if w_pt > 0: shp.Width  = w_pt
            if h_pt > 0: shp.Height = h_pt
            shp.RelativeHorizontalPosition = c.wdRelativeHorizontalPositionColumn
            shp.RelativeVerticalPosition   = c.wdRelativeVerticalPositionParagraph
            shp.WrapFormat.Type = c.wdWrapBehind
            shp.WrapFormat.AllowOverlap = True
            shp.LayoutInCell = True
            shp.LockAnchor = False
            try:
                shp.ZOrder(getattr(c, "msoSendToBack", 0))
            except Exception:
                pass
        except Exception:
            pass

def _load_config_docs(config_path: Path) -> List[Dict[str, Any]]:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    return list(cfg.get("docs", []))

BUILDERS = {
    "mk_set_pieces": mk_set_pieces,
    "mk_corners": mk_corners,
    "mk_dfk": mk_dfk,
    "mk_ifk": mk_ifk,
    "mk_throwins": mk_throwins,
    "_summ_corners": _summ_corners,
    "_summ_ifks": _summ_ifks,
    "_summ_throwins": _summ_throwins,
    "_pk_corners": _pk_corners,
    "_pc_corners": _pc_corners,
    "_pk_ifks": _pk_ifks,
    "_pc_ifks": _pc_ifks,
    "_pk_throwins": _pk_throwins,
    "_pc_throwins": _pc_throwins,
    "team_stats_detailed": team_stats_detailed,
    "players_overview": players_overview
}

IMAGE_BUILDERS = {
    "team_square_image": team_square_image,
    "plot_team_overview": plot_team_overview,
    "bars_heights_coach": bars_heights_coach,
    "bars_heights_rival": bars_heights_rival,
    "plot_shot_creating_actions": builder_plot_shot_creating_actions,
    "plot_shot_actions": builder_plot_shot_actions,
}

def _hex_to_vba_rgb(hex_str: str) -> int:
    hex_str = hex_str.lstrip("#")
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return r + 256*g + 65536*b

def _highlight_rows_first_table(doc, team_name: str, opp_name: str, team_hex: str, opp_hex: str):
    tbl = doc.Tables(1)
    rgb_team = _hex_to_vba_rgb(team_hex)
    rgb_opp  = _hex_to_vba_rgb(opp_hex)
    for i in range(2, tbl.Rows.Count + 1):  # asumiendo cabecera en 1
        val = str(tbl.Cell(i, 1).Range.Text).replace('\r\x07','').strip()
        if val.lower() == team_name.lower():
            tbl.Rows(i).Shading.BackgroundPatternColor = rgb_team
        elif val.lower() == opp_name.lower():
            tbl.Rows(i).Shading.BackgroundPatternColor = rgb_opp

def _fill_first_table_from_df(doc, df: pd.DataFrame, include_header: bool = True):
    """
    Escribe un DataFrame en la PRIMERA tabla del documento:
    - Conserva la cabecera existente (fila 1). Si include_header=True, sobrescribe textos con df.columns.
    - Usa la fila 2 como plantilla de estilo para el cuerpo (se duplica/limpia).
    - Expande o reduce filas para ajustarse a len(df).
    """
    if df is None or df.empty:
        return
    try:
        tbl = doc.Tables(1)
    except Exception:
        return

    _ensure_body_template_row(tbl)

    n_rows = len(df)
    header_rows = 1
    body_rows = max(tbl.Rows.Count - header_rows, 0)

    # Reducir
    while body_rows > n_rows:
        try:
            tbl.Rows(tbl.Rows.Count).Delete()
            body_rows -= 1
        except Exception:
            break

    # Ampliar
    while body_rows < n_rows:
        try:
            tbl.Rows.Add()
            _clear_body_row_format(tbl.Rows(tbl.Rows.Count))
            body_rows += 1
        except Exception:
            break

    # Cabecera (opcional): escribir df.columns
    if include_header:
        for j, col in enumerate(df.columns, start=1):
            try:
                tbl.Cell(1, j).Range.Text = str(col)
            except Exception:
                pass

    # Cuerpo: escribir valores
    for i, (_, row) in enumerate(df.iterrows(), start=2):
        for j, col in enumerate(df.columns, start=1):
            try:
                val = row[col]
                txt = "" if pd.isna(val) else str(val)
                tbl.Cell(i, j).Range.Text = txt
            except Exception:
                pass

    # Limpiar estilo de todas las filas de cuerpo
    try:
        for i in range(2, tbl.Rows.Count + 1):
            _clear_body_row_format(tbl.Rows(i))
    except Exception:
        pass

def _build_table_df_from_config(df_team: pd.DataFrame, table_cfg: Dict[str, Any]) -> pd.DataFrame:
    """
    A partir de la entrada JSON 'table' con:
      { "builder": "mk_set_pieces", "defensive": true }
    invoca el builder apropiado y devuelve el DF resultante.
    """
    if df_team is None or df_team.empty:
        return pd.DataFrame()

    if not table_cfg:
        return pd.DataFrame()

    bname = table_cfg.get("builder")
    defensive = bool(table_cfg.get("defensive", False))

    fn = BUILDERS.get(bname)
    if fn is None:
        # builder desconocido; devolvemos el propio df_team (fallback)
        return df_team.copy()

    try:
        # Los builders de tu app aceptan (df, defensive=bool)
        return fn(df_team, defensive=defensive)
    except TypeError:
        # por si el builder no acepta 'defensive'
        return fn(df_team)

def _fmt_number_cell(x):
    """
    Devuelve texto:
    - entero sin decimales si es un 'count' (p.ej. 3.0 -> '3')
    - si tiene decimales, 2 decimales con coma como separador (p.ej. 0.47 -> '0,47')
    """
    try:
        val = float(x)
    except Exception:
        return str(x)

    if abs(val - round(val)) < 1e-9:
        return str(int(round(val)))
    return f"{val:.2f}".replace('.', ',')  # coma decimal

def _fill_dfk_table_with_headers_and_totals(doc, df_out, table_idx=1):
    """
    Reemplaza SOLO texto:
    - Cabeceras intermedias (equipos) en la fila de cabecera de la tabla WORD.
    - Celdas del cuerpo con los valores por equipo.
    - Última columna (TOTAL) calculada (suma por fila).
    Respeta:
    - Columna 1 (rótulos) del Word tal cual.
    - Última cabecera 'TOTAL' del Word (no se cambia el texto).
    """
    import pandas as pd

    # 1) Obtener tabla COM (índice 1-based)
    try:
        tbl = doc.Tables(table_idx)
    except Exception:
        return

    n_cols_word = int(tbl.Columns.Count)
    if n_cols_word < 2:
        return

    # 2) Rótulos de la primera columna del Word (filas 2..N)
    word_row_labels = []
    try:
        for i in range(2, tbl.Rows.Count + 1):
            # Quita los caracteres finales de Word '\r\x07'
            raw = str(tbl.Cell(i, 1).Range.Text or "")
            lab = raw.replace('\r\x07', '').strip()
            word_row_labels.append(lab)
    except Exception:
        pass

    if not word_row_labels:
        return

    # 3) Preparar DF del builder
    df = df_out.copy()

    # Detectar etiqueta de rótulos de fila
    label_candidates = ["Per Opposition", "Per Player"]
    label_col = next((c for c in label_candidates if c in df.columns), None)

    # Si ninguna está, insertamos "Per Opposition" por compatibilidad
    if label_col is None:
        label_col = "Per Opposition"
        df.insert(0, label_col, df.index.astype(str))
        df = df.reset_index(drop=True)

    team_cols = [c for c in df.columns if c != label_col]

    # Reindexar filas del DF al orden de la plantilla Word 
    df_idxed = df.set_index(label_col) 
    df_idxed = df_idxed.reindex(word_row_labels) 

    # Nº de columnas intermedias disponibles (entre la 1ª y la última TOTAL) 
    n_mid_slots = max(n_cols_word - 2, 0) 
    team_cols = team_cols[:n_mid_slots]

    # 4) CABECERA: escribir nombres de equipos en columnas 2..(1+n_mid_slots)
    try:
        for j, colname in enumerate(team_cols, start=2):
            tbl.Cell(1, j).Range.Text = str(colname)
        # La última cabecera (TOTAL) se deja tal cual
    except Exception:
        pass

    # 5) CUERPO: valores por equipo + TOTAL
    df_num = df_idxed.copy()
    for c in team_cols:
        df_num[c] = pd.to_numeric(df_num[c], errors='coerce')

    totals = df_num[team_cols].sum(axis=1, skipna=True)

    for row_idx, row_label in enumerate(word_row_labels, start=2):
        row_vals = df_idxed.loc[row_label] if row_label in df_idxed.index else None

        # columnas intermedias (equipos)
        for j, colname in enumerate(team_cols, start=2):
            val = "" if row_vals is None else row_vals.get(colname, "")
            try:
                tbl.Cell(row_idx, j).Range.Text = _fmt_number_cell(val)
            except Exception:
                pass

        # última columna = TOTAL
        try:
            tot = totals.loc[row_label] if row_label in totals.index else ""
            tbl.Cell(row_idx, n_cols_word).Range.Text = _fmt_number_cell(tot)
        except Exception:
            pass


from pathlib import Path
import pandas as pd

def generate_report_pdf(
    zip_bytes: bytes,
    texto_abreviado: str,
    rival_badge_bytes: bytes,
    *,
    texto_completo: str | None = None,
    rival_name: str | None = None,
    ha: str | None = None,  # "H" o "A"
    n_selected: int | None = None,
    fixture_idx_asc: int | None = None,
    page2_table_rows: Optional[List[Dict[str, Any]]] = None,
    df_team_path: str, 
    base_team: str, 
    highlight_team: str, 
    highlight_opp: str,
    base_badge_bytes: bytes | None = None,
    season: str | None = None, 
    config_path: Path = Path("app/config/doc_pages.json"),
) -> bytes:
    """
    Procesa SOLO páginas cuyo pipeline sea exactamente:
        ["page_common_replace_header_md_code_ha","insert_badge"]
    - Descomprime el ZIP (admite subcarpetas).
    - Abre cada .docx, reemplaza 'Matchday 1 | CHA (A)' por 'texto_abreviado'.
    - Inserta el ESCUDO DEL RIVAL (bytes recibidos) según JSON.
    - Exporta PDFs y concatena en un único PDF en memoria.
    Devuelve los bytes del PDF combinado.
    """

    # === Resolver carpeta de datos a partir de df_team_path ===
    from pathlib import Path
    cache_dir = Path(df_team_path).resolve().parent

    # Cargar df.csv de la misma carpeta de cache
    df_main = pd.read_csv(cache_dir / "df.csv")

    docs_cfg = _load_config_docs(config_path)
    # Incluir páginas "simples" y también la portada (page1)
    pipeline_simple = ["page_common_replace_header_md_code_ha", "insert_badge"]
    pipeline_page1  = ["page1_replace_title", "page1_replace_matchday", "insert_badge"]
    pipeline_page2  = ["page_common_replace_header_md_code_ha","page2_replace_paragraphs","page2_fill_table","insert_badge"]
    pipeline_table = ["page_common_replace_header_md_code_ha",
                    "page_fill_table_from_config",
                    "page_highlight_both_teams",
                    "insert_badge"]
    # Procesar todas las páginas definidas en el JSON
    docs = list(docs_cfg)

    if not docs:
        raise RuntimeError("No hay páginas con el pipeline simple en la configuración.")

    # Temporales
    tmp_root = Path(tempfile.mkdtemp(prefix="docgen_"))
    tmp_zip = tmp_root / "in.zip"
    tmp_docs = tmp_root / "docs"
    tmp_pdfs = tmp_root / "pdfs"
    tmp_badge = tmp_root / "badge_rival.png"
    tmp_docs.mkdir(parents=True, exist_ok=True)
    tmp_pdfs.mkdir(parents=True, exist_ok=True)
    tmp_zip.write_bytes(zip_bytes)
    tmp_badge.write_bytes(rival_badge_bytes)

    tmp_badge = tmp_root / "badge_rival.png"
    with open(tmp_badge, "wb") as f:
        f.write(rival_badge_bytes)

    tmp_badge_coach = tmp_root / "badge_coach.png"
    if base_badge_bytes:
        with open(tmp_badge_coach, "wb") as f:
            f.write(base_badge_bytes)
    else:
        tmp_badge_coach = None

    try:
        # 1) Descomprimir ZIP
        with zipfile.ZipFile(tmp_zip, "r") as zf:
            zf.extractall(tmp_docs)

        # 2) COM STA en este hilo
        pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)
        try:
            word = _get_word_app()
            word.Visible = False
            word.DisplayAlerts = 0

            created: List[Path] = []
            missing: List[str] = []

            try:
                for d in docs:
                    tpl = d.get("template")
                    if not tpl:
                        continue
                    tpl_path = _find_template_path(tmp_docs, tpl)
                    if tpl_path is None:
                        missing.append(tpl)
                        continue
                    tpl_path = tpl_path.resolve()

                    doc = com_retry(word.Documents.Open, str(tpl_path))

                    try:
                        pl = d.get("pipeline", [])
                        if pl == pipeline_simple:
                            # Páginas 3,5,9,13,16,18,23,28 → cabecera abreviada
                            _replace_everywhere(doc, "Matchday 1 | CHA (A)", texto_abreviado, match_case=False)
                            _apply_badge_from_json(doc, d.get("badge", {}) or {}, tmp_badge)

                        elif pl == pipeline_page1:
                            # Portada (page1): dos reemplazos + escudo
                            # 1) Título grande con nombre rival + HOME/AWAY
                            title_text = ""
                            if rival_name and ha:
                                title_text = f"{rival_name} ({ha})"
                                    
                            _replace_everywhere(doc, "CHARLTON^tATHLETIC^t(A)", title_text, match_case=False)

                            print(f"[DEBUG] page1 → title_text = '{title_text}' (rival_name={rival_name}, ha={ha})")
                            # 2) Línea de fecha/venue con el texto completo del debug
                            if texto_completo:
                                _replace_everywhere(
                                    doc,
                                    "Matchday 1 | 2025-08-09 13:30 h | The Valley (London)",
                                    texto_completo,
                                    match_case=False
                                )
                            # 3) Escudo en la posición/tamaño del JSON
                            _apply_badge_from_json(doc, d.get("badge", {}) or {}, tmp_badge)

                        elif pl == pipeline_page2:
                            # 1) Cabecera común abreviada
                            _replace_everywhere(doc, "Matchday 1 | CHA (A)", texto_abreviado, match_case=False)

                            # 2) Reemplazar "10" por n
                            n_val = int(n_selected or 0)
                            _replace_everywhere(doc, "10", str(n_val), match_case=False)

                            # 3) "CHARLTON ATHLETIC" -> NOMBRE RIVAL en MAYÚSCULAS y NEGRITA
                            if rival_name:
                                _replace_first_bold_upper(doc, "CHARLTON ATHLETIC", rival_name, match_case=False)

                            # 4) Lógica del "(*)"
                            if fixture_idx_asc is not None and n_val < int(fixture_idx_asc):
                                # 4.1 "competition (*)." -> "competition."
                                _replace_everywhere(doc, "competition (*).", "competition.", match_case=False)
                                # 4.2 Eliminar TODAS las frases que contengan "(*)"
                                _delete_paragraphs_containing(doc, "(*)", skip_first=False)
                            else:
                                # NO eliminar nada si n >= índice
                                pass

                            # 5) Rellenar tabla (primera)
                            if n_val > 0:
                                _fill_first_table_with_rows(doc, page2_table_rows or [], rival_name or "", n_val)

                            # 6) Escudo según JSON
                            _apply_badge_from_json(doc, d.get("badge", {}) or {}, tmp_badge)

                        else:
                            replaced_header = False
                            if "page_common_replace_header_md_code_ha" in pl:
                                _replace_everywhere(doc, "Matchday 1 | CHA (A)", texto_abreviado, match_case=False)
                                replaced_header = True

                            did_table = False
                            if "page_fill_table_from_config" in pl:
                                # 1) cargar CSV base (df_team.csv por defecto)
                                df_team = None
                                try:
                                    if df_team_path:
                                        df_team = pd.read_csv(df_team_path)
                                except Exception:
                                    df_team = None

                                # 2) Preparar lista de configs (soporta 'tables' y 'table')
                                tables_cfg = d.get("tables")
                                if tables_cfg:
                                    cfg_list = tables_cfg
                                else:
                                    single = d.get("table", {}) or {}
                                    cfg_list = [single] if single else []

                                for table_cfg in cfg_list:
                                    if not table_cfg:
                                        continue

                                    builder_name = (table_cfg.get("builder") or "").strip()
                                    defensive    = bool(table_cfg.get("defensive", False))
                                    side         = table_cfg.get("side") or table_cfg.get("subtype")
                                    target       = (table_cfg.get("target") or "first").strip().lower()
                                    table_idx    = 1 if target in ("first","1") else 2

                                    # 3) Selección del DF de entrada al builder
                                    if builder_name.startswith("_summ"):
                                        df_agr_pair = None
                                        try:
                                            if df_team_path:
                                                agg_path = str((Path(df_team_path)).with_name("df_agr_pair.csv"))
                                                df_agr_pair = pd.read_csv(agg_path)
                                        except Exception:
                                            df_agr_pair = None

                                        want_players = (
                                            (builder_name == "_summ_corners"  and not defensive) or
                                            (builder_name == "_summ_ifks"     and not defensive) or
                                            (builder_name == "_summ_throwins" and not defensive)
                                        )
                                        if want_players:
                                            df_jug_team = None
                                            try:
                                                if df_team_path:
                                                    jug_path = str((Path(df_team_path)).with_name("df_jug_team.csv"))
                                                    df_jug_team = pd.read_csv(jug_path)
                                            except Exception:
                                                df_jug_team = None
                                            base_df = df_jug_team if df_jug_team is not None else df_agr_pair
                                        else:
                                            base_df = df_agr_pair
                                    elif builder_name in ("_pk_corners", "_pc_corners", "_pk_ifks", "_pc_ifks", "_pk_throwins", "_pc_throwins"):
                                        df_jug_team = None
                                        try:
                                            if df_team_path:
                                                jug_path = str((Path(df_team_path)).with_name("df_jug_team.csv"))
                                                df_jug_team = pd.read_csv(jug_path)
                                        except Exception:
                                            df_jug_team = None
                                        base_df = df_jug_team
                                    elif builder_name == "players_overview":
                                        # Cargar df_players.csv junto a df_team.csv
                                        df_players = None
                                        try:
                                            if df_team_path:
                                                players_path = str((Path(df_team_path)).with_name("df_players.csv"))
                                                df_players = pd.read_csv(players_path)
                                        except Exception:
                                            df_players = None
                                        base_df = df_players
                                    elif builder_name == "team_stats_detailed":
                                        # Usar el DF que replica el notebook
                                        df_team_system = None
                                        try:
                                            if df_team_path:
                                                sys_path = str((Path(df_team_path)).with_name("df_team_system.csv"))
                                                if os.path.exists(sys_path):
                                                    df_team_system = pd.read_csv(sys_path)
                                        except Exception:
                                            df_team_system = None

                                        base_df = df_team_system if df_team_system is not None else df_team
                                    else:
                                        base_df = df_team

                                    # 4) Ejecutar el builder
                                    df_out = None
                                    try:
                                        if builder_name == "_summ_corners":
                                            df_out = _summ_corners(base_df, side=side, defensive=defensive, rival=rival_name)
                                        elif builder_name == "_summ_ifks":
                                            df_out = _summ_ifks(base_df, defensive=defensive, rival=rival_name)
                                        elif builder_name == "_summ_throwins":
                                            df_out = _summ_throwins(base_df, side=side, defensive=defensive, rival=rival_name)
                                        elif builder_name == "_pk_corners":
                                            df_out = _pk_corners(base_df, side)
                                        elif builder_name == "_pc_corners":
                                            df_out = _pc_corners(base_df)
                                        elif builder_name == "_pk_ifks":
                                            df_out = _pk_ifks(base_df)
                                        elif builder_name == "_pc_ifks":
                                            df_out = _pc_ifks(base_df)
                                        elif builder_name == "_pk_throwins":
                                            df_out = _pk_throwins(base_df, side)
                                        elif builder_name == "_pc_throwins":
                                            df_out = _pc_throwins(base_df)
                                        elif builder_name == "players_overview":
                                            df_out = players_overview(base_df, rival=rival_name)
                                        else:
                                            df_out = _build_table_df_from_config(base_df, table_cfg)
                                    except Exception:
                                        df_out = None

                                    # 5) Volcar DF en la tabla indicada (1ª o 2ª)
                                    if df_out is not None and not df_out.empty:
                                        if builder_name.startswith("_summ"):
                                            _fill_dfk_table_with_headers_and_totals(doc, df_out, table_idx=table_idx)
                                        elif builder_name in ("_pk_corners", "_pc_corners", "_pk_ifks", "_pc_ifks", "_pk_throwins", "_pc_throwins"):
                                            _fill_player_table_preserving_styles_and_total(doc, df_out, total_label="TOTAL", table_idx=table_idx)
                                        else:
                                            _fill_first_table_from_df(doc, df_out, include_header=False)
                                        did_table = True
                            if "page_highlight_both_teams" in pl:
                                # Subraya filas cuyo valor en 1ª columna == base_team o == rival_name
                                if base_team and rival_name and highlight_team and highlight_opp:
                                    try:
                                        _highlight_rows_first_table(doc, base_team, rival_name, highlight_team, highlight_opp)
                                    except Exception:
                                        pass

                            if "insert_badge" in pl:
                                _apply_badge_from_json(doc, d.get("badge", {}) or {}, tmp_badge)

                            if "page_insert_images_from_config" in pl:
                                _insert_images_from_config(
                                    doc,
                                    d.get("images", {}) or {},
                                    ctx=dict(
                                        tmpdir=str(tmp_root / "imgs"),
                                        team=base_team,
                                        opponent=rival_name,
                                        data_dir=str(cache_dir), 
                                        badge_coach_path=(str(tmp_badge_coach) if tmp_badge_coach else None),
                                        badge_rival_path=str(tmp_badge),
                                        season=season,
                                        df=df_main,
                                    )
                                )

                        # Exportar a PDF temporal
                        out_pdf = tmp_pdfs / (Path(tpl).stem + "_def.pdf")
                        _export_pdf(word, doc, out_pdf)
                        created.append(out_pdf)
                    finally:
                        com_retry(doc.Close, SaveChanges=False)
            finally:
                try:
                    com_retry(word.Quit)
                except Exception:
                    pass

        finally:
            # Siempre cerrar COM en este hilo
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass

        if not created:
            if missing:
                raise RuntimeError("No se generó ningún PDF. Faltan plantillas: " + ", ".join(missing))
            raise RuntimeError("No se generó ningún PDF (¿faltan plantillas en el ZIP?).")

        # 3) Unir PDFs
        merger = PdfMerger()
        buf = io.BytesIO()
        try:
            for p in created:
                merger.append(str(p))
            merger.write(buf)
        finally:
            merger.close()

        return buf.getvalue()

    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)
