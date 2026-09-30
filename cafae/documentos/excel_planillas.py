"""Generador oficial de Planillas en formato Excel (.xlsx).
Réplica fiel de la plantilla institucional de la UGEL Chepén:
- Títulos oficiales centrados y subrayados.
- Encabezados con códigos de color exactos por concepto de descuento.
- Agrupación por Metas con subtotales (TOTAL META 14, TOTAL META 42, etc.).
- Tablita consolidada de descuentos en la parte inferior izquierda con colores idénticos.
- Bloque de firmas institucionales distribuidas en la parte inferior.
"""
from decimal import Decimal
import io
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

# Paleta de colores exacta de la plantilla oficial de UGEL Chepén
AZUL_CABECERA = PatternFill(start_color="BDD7EE", end_color="BDD7EE", fill_type="solid")      # Azul suave columnas fijas
VERDE_DESCUENTOS = PatternFill(start_color="92D050", end_color="92D050", fill_type="solid")   # Verde brillante grupo DESCUENTOS
AZUL_NETO = PatternFill(start_color="8EA9DB", end_color="8EA9DB", fill_type="solid")          # Azul medio neto

# Colores de cada concepto de descuento en la cabecera y en la tablita resumen
COLOR_PICHINCHA = PatternFill(start_color="D5C578", end_color="D5C578", fill_type="solid")    # Ocre / mostaza suave
COLOR_SULLANA = PatternFill(start_color="8EA9DB", end_color="8EA9DB", fill_type="solid")      # Azul pizarra
COLOR_SUBCAFAE = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")     # Verde azulado / teal
COLOR_BRENTA = PatternFill(start_color="B4A7D6", end_color="B4A7D6", fill_type="solid")       # Lavanda / morado suave
COLOR_SITRASE = PatternFill(start_color="A6A6A6", end_color="A6A6A6", fill_type="solid")      # Gris
COLOR_SITASE = PatternFill(start_color="D6D090", end_color="D6D090", fill_type="solid")       # Dorado suave
COLOR_LICENCIA = PatternFill(start_color="BDD7EE", end_color="BDD7EE", fill_type="solid")     # Celeste claro
COLOR_OTROS = PatternFill(start_color="BDD7EE", end_color="BDD7EE", fill_type="solid")        # Celeste claro

# Tipografías
FONT_TITLE = Font(name="Arial", size=10, bold=True, underline="single")
FONT_HDR = Font(name="Arial", size=7.5, bold=True, color="000000")
FONT_DATA = Font(name="Arial", size=7.5)
FONT_BOLD = Font(name="Arial", size=7.5, bold=True)
FONT_DATE = Font(name="Arial", size=8.5, italic=True)

# Bordes
THIN_GRAY = Side(border_style="thin", color="B2B2B2")
THIN_BLACK = Side(border_style="thin", color="000000")
MEDIUM_BLACK = Side(border_style="medium", color="000000")
BORDER_CELL = Border(left=THIN_GRAY, right=THIN_GRAY, top=THIN_GRAY, bottom=THIN_GRAY)
BORDER_BLACK = Border(left=THIN_BLACK, right=THIN_BLACK, top=THIN_BLACK, bottom=THIN_BLACK)

FORMATO_NUMERO = '#,##0.00'
FORMATO_SOLES = '"S/. "#,##0.00'


def _format_fecha(val):
    if not val:
        return ''
    if hasattr(val, 'strftime'):
        return val.strftime('%d/%m/%Y')
    val_str = str(val).split('T')[0].strip()
    if '-' in val_str:
        partes = val_str.split('-')
        if len(partes) == 3 and len(partes[0]) == 4:
            return f"{partes[2]}/{partes[1]}/{partes[0]}"
    return val_str


def _format_meta_label(m_cod):
    if not m_cod:
        return ''
    m_clean = str(m_cod).strip().upper()
    if m_clean.startswith('META'):
        m_clean = m_clean.replace('META', '').strip()
    try:
        return f"META {int(m_clean)}"
    except (ValueError, TypeError):
        return f"META {m_clean}"


def generar_excel_planilla(info_planilla: dict, filas_detalle: list[dict], firmas: list[dict] = None) -> bytes:
    firmas = firmas or []
    wb = openpyxl.Workbook()
    ws = wb.active

    tipo = info_planilla['tipo']
    anio = info_planilla['anio']
    mes = info_planilla['mes']
    meses_nom = ['', 'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
                 'JULIO', 'AGOSTO', 'SETIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
    nombre_mes = meses_nom[mes]
    ws.title = f"PLANILLA {tipo} {nombre_mes[:3]}_{anio % 100}"

    # 1. TÍTULOS SUPERIORES INSTITUCIONALES (Centrados)
    if tipo == 'IIEE':
        ws['A2'] = "PLANILLA CAFAE PERSONAL ADMINISTRATIVO DL. Nº 276 DE LAS INSTITUCIONES EDUCATIVAS"
    else:
        ws['A2'] = "PLANILLA CAFAE PERSONAL ADMINISTRATIVO DL. Nº 276 DE LA SEDE CENTRAL"
    ws['A3'] = f"JURISDICCIÓN UGEL CHEPEN - {nombre_mes} {anio}"

    ws.merge_cells('A2:AA2')
    ws.merge_cells('A3:AA3')
    ws['A2'].font = FONT_TITLE
    ws['A3'].font = FONT_TITLE
    ws['A2'].alignment = Alignment(horizontal="center", vertical="center")
    ws['A3'].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 18
    ws.row_dimensions[3].height = 18

    # 2. DEFINICIÓN DE COLUMNAS
    # Total 27 columnas (A..AA)
    columnas_fijas = [
        ("N°", 5),
        ("N° DNI", 11),
        ("NIVEL" if tipo == 'IIEE' else "ÁREA SEDE", 14),
        ("APELLIDOS", 18),
        ("NOMBRES", 18),
        ("COD. MOD.IIEE" if tipo == 'IIEE' else "DISTRIBUCIÓN", 12),
        ("INSTITUCION EDUCATIVA" if tipo == 'IIEE' else "DEPENDENCIA", 26),
        ("SUBTIPO DE TRABAJADOR", 14),
        ("CARGO", 18),
        ("SITUACIÓN", 12),
        ("FECHA DE NACIMIENTO", 12),
        ("Ley N°", 7),
        ("Cat.", 7),
        ("Jornada Laboral", 9),
        ("MULTIRED", 14),
        ("IMPORTE", 12),
        ("IMPORTE ADICIONAL", 11),
    ]

    descuentos_cols = [
        ("PICHINCHA", 11, COLOR_PICHINCHA),
        ("CAJA SULLANA", 11, COLOR_SULLANA),
        ("SUB-CAFAE", 11, COLOR_SUBCAFAE),
        ("CONV. BRENTA", 11, COLOR_BRENTA),
        ("SITRASE", 11, COLOR_SITRASE),
        ("SITASE", 11, COLOR_SITASE),
        ("LICENCIA S/G", 11, COLOR_LICENCIA),
        ("OTROS DCTOS", 11, COLOR_OTROS),
    ]

    totales_cols = [
        ("TOTAL DCTOS.", 12, AZUL_CABECERA),
        ("NETO A PAGAR", 13, AZUL_NETO),
    ]

    row_hdr1 = 5
    row_hdr2 = 6
    ws.row_dimensions[row_hdr1].height = 20
    ws.row_dimensions[row_hdr2].height = 24

    # Escribir columnas fijas (A..Q: columnas 1..17) con celdas fusionadas filas 5 y 6
    for col_idx, (col_nombre, ancho) in enumerate(columnas_fijas, start=1):
        cell = ws.cell(row=row_hdr1, column=col_idx, value=col_nombre)
        cell.font = FONT_HDR
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.fill = AZUL_CABECERA
        cell.border = BORDER_BLACK

        c2 = ws.cell(row=row_hdr2, column=col_idx)
        c2.fill = AZUL_CABECERA
        c2.border = BORDER_BLACK
        ws.merge_cells(start_row=row_hdr1, start_column=col_idx, end_row=row_hdr2, end_column=col_idx)

        col_let = get_column_letter(col_idx)
        ws.column_dimensions[col_let].width = ancho

    # Escribir grupo "DESCUENTOS" (R..Y: columnas 18..25)
    c_desc_start = len(columnas_fijas) + 1
    c_desc_end = c_desc_start + len(descuentos_cols) - 1

    ws.merge_cells(start_row=row_hdr1, start_column=c_desc_start, end_row=row_hdr1, end_column=c_desc_end)
    hdr_desc = ws.cell(row=row_hdr1, column=c_desc_start, value="DESCUENTOS")
    hdr_desc.font = FONT_HDR
    hdr_desc.alignment = Alignment(horizontal="center", vertical="center")
    hdr_desc.fill = VERDE_DESCUENTOS
    hdr_desc.border = BORDER_BLACK

    for c_i in range(c_desc_start, c_desc_end + 1):
        ws.cell(row=row_hdr1, column=c_i).border = BORDER_BLACK

    # Sub-encabezados de cada descuento (Fila 6)
    for idx_d, (nom_d, ancho_d, fill_d) in enumerate(descuentos_cols):
        c_num = c_desc_start + idx_d
        cell = ws.cell(row=row_hdr2, column=c_num, value=nom_d)
        cell.font = FONT_HDR
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.fill = fill_d
        cell.border = BORDER_BLACK
        col_let = get_column_letter(c_num)
        ws.column_dimensions[col_let].width = ancho_d

    # Escribir TOTAL DCTOS y NETO A PAGAR (Z..AA: columnas 26..27)
    for idx_t, (nom_t, ancho_t, fill_t) in enumerate(totales_cols):
        c_num = c_desc_end + 1 + idx_t
        cell = ws.cell(row=row_hdr1, column=c_num, value=nom_t)
        cell.font = FONT_HDR
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.fill = fill_t
        cell.border = BORDER_BLACK

        c2 = ws.cell(row=row_hdr2, column=c_num)
        c2.fill = fill_t
        c2.border = BORDER_BLACK
        ws.merge_cells(start_row=row_hdr1, start_column=c_num, end_row=row_hdr2, end_column=c_num)

        col_let = get_column_letter(c_num)
        ws.column_dimensions[col_let].width = ancho_t

    # 3. ESCRITURA DE DATOS AGRUPADOS POR META
    # Separar filas por meta para crear los bloques de subtotales
    metas_dict = {}
    for f in filas_detalle:
        m_cod = str(f.get('meta_codigo') or f.get('meta_descripcion') or '0001').strip()
        metas_dict.setdefault(m_cod, []).append(f)

    fila_actual = 7
    todas_filas_subtotales = []
    primer_fila_datos = fila_actual
    total_general_filas = len(filas_detalle)

    num_trab = 1
    for m_cod, lista_m in metas_dict.items():
        inicio_bloque_meta = fila_actual
        meta_label = _format_meta_label(m_cod)

        for idx_f, f in enumerate(lista_m):
            ws.row_dimensions[fila_actual].height = 24 if (idx_f == 0 and meta_label) else 17
            f_nac_str = _format_fecha(f.get('fecha_nacimiento'))
            imp_val = float(f.get('importe') or 0)
            pich_val = float(f.get('pichincha') or 0)
            sull_val = float(f.get('caja_sullana') or 0)
            subc_val = float(f.get('sub_cafae') or 0)
            bren_val = float(f.get('brenta') or 0)
            sitr_val = float(f.get('sitrase') or 0)
            fent_val = float(f.get('sitase_fentase') or 0)
            lic_val = float(f.get('monto_licencia') or 0)
            otro_val = float(f.get('otros') or 0)

            nivel_base = str(f.get('nivel_nombre') or f.get('area_nombre') or '').strip()
            if idx_f == 0 and meta_label:
                nivel_val = f"{nivel_base}\n{meta_label}" if nivel_base else meta_label
            else:
                nivel_val = nivel_base

            r_idx = fila_actual
            row_vals = [
                num_trab,
                str(f['dni']),
                f.get('nivel_nombre') or f.get('area_nombre') or '',
                str(f.get('apellidos', '')).upper(),
                str(f.get('nombres', '')).upper(),
                f.get('codigo_modular') or '',
                f.get('institucion_nombre') or f.get('area_nombre') or 'UGEL CHEPÉN',
                str(f.get('subtipo') or 'AUXILIAR').upper(),
                str(f.get('cargo') or '').upper(),
                str(f.get('situacion') or 'NOMBRADO').upper(),
                f_nac_str,
                str(f.get('ley') or '276'),
                str(f.get('categoria') or 'AE'),
                str(f.get('jornada_laboral') or '40'),
                str(f.get('cuenta_multired') or ''),
                imp_val,
                0.00,  # IMPORTE ADICIONAL
                pich_val,
                sull_val,
                subc_val,
                bren_val,
                sitr_val,
                fent_val,
                lic_val,
                otro_val,
                f"=SUM(R{r_idx}:Y{r_idx})",  # TOTAL DCTOS
                f"=P{r_idx}+Q{r_idx}-Z{r_idx}"  # NETO A PAGAR
            ]

            for c_i, v in enumerate(row_vals, start=1):
                c_cell = ws.cell(row=r_idx, column=c_i, value=v)
                c_cell.font = FONT_DATA
                c_cell.border = BORDER_CELL

                # Formatos de alineación y numéricos
                if c_i in (1, 2, 11, 12, 13, 14):
                    c_cell.alignment = Alignment(horizontal="center", vertical="center")
                    if c_i == 2:
                        c_cell.number_format = '@'
                elif c_i >= 16:
                    c_cell.alignment = Alignment(horizontal="right", vertical="center")
                    c_cell.number_format = FORMATO_NUMERO
                else:
                    c_cell.alignment = Alignment(horizontal="left", vertical="center")

            num_trab += 1
            fila_actual += 1

        fin_bloque_meta = fila_actual - 1

        # FILA DE SUBTOTAL POR META: Celdas combinadas de 1 a 15 con "TOTAL META XX"
        ws.row_dimensions[fila_actual].height = 19
        for c_i in range(1, 28):
            c_tmp = ws.cell(row=fila_actual, column=c_i)
            c_tmp.fill = AZUL_CABECERA
            c_tmp.border = BORDER_BLACK

        ws.merge_cells(start_row=fila_actual, start_column=1, end_row=fila_actual, end_column=15)
        c_lbl_meta = ws.cell(row=fila_actual, column=1, value=f"TOTAL {meta_label}")
        c_lbl_meta.font = Font(name="Arial", size=7.5, bold=True, italic=True)
        c_lbl_meta.alignment = Alignment(horizontal="right", vertical="center")

        # Fórmulas de sumas del bloque meta
        for c_i in range(16, 28):
            col_letter = get_column_letter(c_i)
            if c_i == 26:
                c_formula = f"=SUM(R{fila_actual}:Y{fila_actual})"
            elif c_i == 27:
                c_formula = f"=P{fila_actual}+Q{fila_actual}-Z{fila_actual}"
            else:
                c_formula = f"=SUM({col_letter}{inicio_bloque_meta}:{col_letter}{fin_bloque_meta})"
            
            c_tot = ws.cell(row=fila_actual, column=c_i, value=c_formula)
            c_tot.font = FONT_BOLD
            c_tot.alignment = Alignment(horizontal="right", vertical="center")
            c_tot.number_format = FORMATO_NUMERO

        todas_filas_subtotales.append(fila_actual)
        fila_actual += 1

    # 4. FILA DE SUB-TOTAL GENERAL: Celdas combinadas de 1 a 15 con "SUB - TOTAL"
    ws.row_dimensions[fila_actual].height = 20
    for c_i in range(1, 28):
        c_sub = ws.cell(row=fila_actual, column=c_i)
        c_sub.fill = AZUL_CABECERA
        c_sub.border = BORDER_BLACK

    ws.merge_cells(start_row=fila_actual, start_column=1, end_row=fila_actual, end_column=15)
    c_sub_lbl = ws.cell(row=fila_actual, column=1, value="SUB - TOTAL")
    c_sub_lbl.font = FONT_BOLD
    c_sub_lbl.alignment = Alignment(horizontal="center", vertical="center")

    for c_i in range(16, 28):
        col_letter = get_column_letter(c_i)
        if len(todas_filas_subtotales) > 1:
            partes_sub = [f"{col_letter}{rf}" for rf in todas_filas_subtotales]
            formula_sub = f"={'+'.join(partes_sub)}"
        elif len(todas_filas_subtotales) == 1:
            formula_sub = f"={col_letter}{todas_filas_subtotales[0]}"
        else:
            formula_sub = f"=SUM({col_letter}{primer_fila_datos}:{col_letter}{fila_actual-1})"

        c_val = ws.cell(row=fila_actual, column=c_i, value=formula_sub)
        c_val.font = FONT_BOLD
        c_val.alignment = Alignment(horizontal="right", vertical="center")
        c_val.number_format = FORMATO_NUMERO

    fila_subtotal_final = fila_actual
    fila_actual += 1

    # Fila de Total Neto General destacado
    ws.row_dimensions[fila_actual].height = 20
    ws.cell(row=fila_actual, column=16, value=f"=P{fila_subtotal_final}").number_format = FORMATO_NUMERO
    ws.cell(row=fila_actual, column=16).font = FONT_BOLD
    ws.cell(row=fila_actual, column=16).alignment = Alignment(horizontal="right", vertical="center")
    ws.cell(row=fila_actual, column=16).border = BORDER_BLACK
    ws.cell(row=fila_actual, column=16).fill = AZUL_CABECERA

    fila_actual += 3

    # =========================================================================
    # 5. TABLITA DE DESCUENTOS AL FINAL (IDÉNTICA A LA IMAGEN)
    # =========================================================================
    r_desc = fila_actual

    # Fila 1: Encabezado "DESCUENTOS"
    ws.merge_cells(start_row=r_desc, start_column=2, end_row=r_desc, end_column=3)
    c_th = ws.cell(row=r_desc, column=2, value="DESCUENTOS")
    c_th.font = FONT_BOLD
    c_th.alignment = Alignment(horizontal="center", vertical="center")
    c_th.fill = AZUL_CABECERA
    c_th.border = BORDER_BLACK
    ws.cell(row=r_desc, column=3).border = BORDER_BLACK
    ws.row_dimensions[r_desc].height = 18

    # Filas con cada concepto y su color distintivo
    conceptos_resumen = [
        ("* PICHINCHA:", "R", COLOR_PICHINCHA),
        ("* CAJA SULLAN:", "S", COLOR_SULLANA),
        ("* BRENTA:", "U", COLOR_BRENTA),
        ("* SITASE:", "W", COLOR_SITASE),
        ("* SUBCAFAE:", "T", COLOR_SUBCAFAE),
        ("* SITRASE:", "V", COLOR_SITRASE),
        ("* LIC. S/G:", "X", COLOR_LICENCIA),
    ]

    for idx_cr, (lbl_cr, col_let, fill_cr) in enumerate(conceptos_resumen, start=1):
        cur_r = r_desc + idx_cr
        ws.row_dimensions[cur_r].height = 16

        c_lbl = ws.cell(row=cur_r, column=2, value=lbl_cr)
        c_lbl.font = FONT_BOLD
        c_lbl.alignment = Alignment(horizontal="left", vertical="center")
        c_lbl.border = BORDER_BLACK

        # Referencia exacta a la suma total de esa columna en la fila subtotal
        c_val = ws.cell(row=cur_r, column=3, value=f"={col_let}{fila_subtotal_final}")
        c_val.font = FONT_BOLD
        c_val.alignment = Alignment(horizontal="right", vertical="center")
        c_val.number_format = FORMATO_SOLES
        c_val.fill = fill_cr
        c_val.border = BORDER_BLACK

    # Fila final de la tablita: Total Descuentos
    r_desc_tot = r_desc + len(conceptos_resumen) + 1
    ws.row_dimensions[r_desc_tot].height = 17
    c_vacia = ws.cell(row=r_desc_tot, column=2, value="")
    c_vacia.border = BORDER_BLACK

    c_sum_desc = ws.cell(row=r_desc_tot, column=3, value=f"=SUM(C{r_desc+1}:C{r_desc_tot-1})")
    c_sum_desc.font = FONT_BOLD
    c_sum_desc.alignment = Alignment(horizontal="right", vertical="center")
    c_sum_desc.number_format = FORMATO_SOLES
    c_sum_desc.fill = AZUL_CABECERA
    c_sum_desc.border = BORDER_BLACK

    # 6. FECHA DE EMISIÓN EN LA PARTE DERECHA: "Chepén, setiembre 2026"
    ws.cell(row=r_desc, column=20, value=f"Chepén, {nombre_mes.lower()} {anio}").font = FONT_DATE
    ws.cell(row=r_desc, column=20).alignment = Alignment(horizontal="right", vertical="center")

    # 7. FIRMAS INSTITUCIONALES EN LA BASE
    r_firmas = r_desc_tot + 4
    ws.row_dimensions[r_firmas].height = 15
    ws.row_dimensions[r_firmas + 1].height = 14
    ws.row_dimensions[r_firmas + 2].height = 14

    # 4 firmas en IIEE, 3 en Sede
    posiciones_firmas_iiee = [
        (4, 7, "Mg. ....................................", "Director de UGEL CHEPEN"),
        (9, 12, "Ing. ....................................", "Directora Gestión Institucional"),
        (15, 18, "Lic. ....................................", "Director de Gestión Administrativa"),
        (21, 24, "Eco. ....................................", "Especialista en Finanzas"),
    ]

    for idx_f, (c_ini, c_fin, fallback_nom, fallback_car) in enumerate(posiciones_firmas_iiee):
        ws.merge_cells(start_row=r_firmas, start_column=c_ini, end_row=r_firmas, end_column=c_fin)
        ws.merge_cells(start_row=r_firmas + 1, start_column=c_ini, end_row=r_firmas + 1, end_column=c_fin)
        ws.merge_cells(start_row=r_firmas + 2, start_column=c_ini, end_row=r_firmas + 2, end_column=c_fin)

        linea_cel = ws.cell(row=r_firmas, column=c_ini, value="___________________________________")
        linea_cel.alignment = Alignment(horizontal="center", vertical="bottom")

        # Usar datos de la firma si están disponibles
        if idx_f < len(firmas):
            f_nom = firmas[idx_f].get('nombre_completo') or fallback_nom
            f_car = firmas[idx_f].get('cargo') or fallback_car
        else:
            f_nom = fallback_nom
            f_car = fallback_car

        nom_cel = ws.cell(row=r_firmas + 1, column=c_ini, value=f_nom)
        nom_cel.font = FONT_BOLD
        nom_cel.alignment = Alignment(horizontal="center", vertical="center")

        car_cel = ws.cell(row=r_firmas + 2, column=c_ini, value=f_car)
        car_cel.font = FONT_DATA
        car_cel.alignment = Alignment(horizontal="center", vertical="center")

    # Configuración de página lista para impresión A4 Apaisada
    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.print_title_rows = '5:6'

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()
