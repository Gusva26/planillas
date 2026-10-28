"""Generador de la Hoja de Trabajo de Remuneraciones CAFAE (Etapa 12).

Reproduce con fidelidad absoluta la plantilla oficial de 4 columnas:
PROGRAMA | ASIGNACION A FONDOS PARA PERSONAL (META, 21.11.21) | TOTAL EJECUT.
Con colores institucionales, celdas de subtotales, bandas de grupo y fórmulas.
"""
from collections import defaultdict
from decimal import Decimal
import io
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

# Colores oficiales idénticos a la plantilla de referencia
AZUL_NAVY = PatternFill(start_color="002060", end_color="002060", fill_type="solid")
NARANJA_GESTION = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
VERDE_FILA = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
AMARILLO_TOTAL = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
AMARILLO_ESPECIAL = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")

# Tipografías oficiales
FONT_TITLE = Font(name="Calibri", size=14, bold=True, underline="single", color="002060")
FONT_HEADER_WHITE = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
FONT_HEADER_ITALIC = Font(name="Calibri", size=10, bold=True, italic=True, color="FFFFFF")
FONT_PROGRAMA_BOLD = Font(name="Calibri", size=10, bold=True)
FONT_PROGRAMA_UNDERLINE = Font(name="Calibri", size=10, bold=True, underline="single")
FONT_PROGRAMA_REGULAR = Font(name="Calibri", size=10)
FONT_META = Font(name="Calibri", size=10, bold=True, underline="single", color="0000FF")
FONT_MONEY = Font(name="Calibri", size=10)
FONT_MONEY_BOLD = Font(name="Calibri", size=10, bold=True)
FONT_MONEY_UNDERLINE = Font(name="Calibri", size=10, bold=True, underline="single")
FONT_TOTAL_WHITE = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
FONT_TOTAL_BLACK = Font(name="Calibri", size=11, bold=True, color="000000")

# Bordes
THIN = Side(border_style="thin", color="000000")
DOUBLE = Side(border_style="double", color="000000")
BORDER_ALL = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
BORDER_TOTAL_YELLOW = Border(left=THIN, right=THIN, top=THIN, bottom=DOUBLE)

FORMATO_MONEDA = '#,##0.00'


def generar_excel_remuneraciones(info_planilla: dict, filas_detalle: list[dict], monto_gestion_externo: float = None) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "CAFAE - REMUNERACIONES"
    ws.views.sheetView[0].showGridLines = True

    # 1. Agrupar montos por código de meta
    metas_dict = defaultdict(Decimal)
    metas_info = {}
    for f in filas_detalle:
        raw_m = str(f.get('meta_codigo') or '').strip()
        m = raw_m.lstrip('0') or raw_m
        metas_dict[m] += Decimal(str(f.get('importe') or 0.00))
        if m not in metas_info:
            metas_info[m] = {
                'raw_codigo': raw_m or m,
                'descripcion': f.get('meta_descripcion') or ''
            }

    tipo = str(info_planilla.get('tipo') or 'IIEE').upper()

    # Título oficial
    ws['A1'] = "HOJA DE TRABAJO DE REMUNERACIONES - PLANILLA  CAFAE"
    ws['A1'].font = FONT_TITLE
    ws.row_dimensions[1].height = 28

    # Espaciador
    ws.row_dimensions[2].height = 10

    # Encabezados (Filas 3 y 4)
    ws.merge_cells('A3:A4')
    ws['A3'] = "PROGRAMA"
    ws['A3'].font = FONT_HEADER_WHITE
    ws['A3'].fill = AZUL_NAVY
    ws['A3'].alignment = Alignment(horizontal="center", vertical="center")
    ws['A3'].border = BORDER_ALL
    ws['A4'].border = BORDER_ALL

    ws.merge_cells('B3:C3')
    ws['B3'] = "ASIGNACION A FONDOS\nPARA PERSONAL"
    ws['B3'].font = FONT_HEADER_WHITE
    ws['B3'].fill = AZUL_NAVY
    ws['B3'].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws['B3'].border = BORDER_ALL
    ws['C3'].border = BORDER_ALL

    ws['B4'] = "META"
    ws['B4'].font = FONT_HEADER_WHITE
    ws['B4'].fill = AZUL_NAVY
    ws['B4'].alignment = Alignment(horizontal="center", vertical="center")
    ws['B4'].border = BORDER_ALL

    ws['C4'] = "21.11.21"
    ws['C4'].font = FONT_HEADER_WHITE
    ws['C4'].fill = AZUL_NAVY
    ws['C4'].alignment = Alignment(horizontal="center", vertical="center")
    ws['C4'].border = BORDER_ALL

    ws.merge_cells('D3:D4')
    ws['D3'] = "TOTAL\nEJECUT."
    ws['D3'].font = FONT_HEADER_ITALIC
    ws['D3'].fill = AZUL_NAVY
    ws['D3'].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws['D3'].border = BORDER_ALL
    ws['D4'].border = BORDER_ALL

    ws.row_dimensions[3].height = 22
    ws.row_dimensions[4].height = 20

    row_idx = 5
    subtotal_cells = []

    if tipo == 'SEDE':
        val_gestion = float(sum(metas_dict.values())) if monto_gestion_externo is None else float(monto_gestion_externo)
        meta_gestion = '33'
        for m in metas_dict.keys():
            if m in ('1', '33'):
                meta_gestion = '33' if m == '33' else '01'

        ws[f'A{row_idx}'] = "006 GESTION"
        ws[f'A{row_idx}'].font = FONT_PROGRAMA_BOLD
        ws[f'B{row_idx}'] = int(meta_gestion) if meta_gestion.isdigit() else meta_gestion
        ws[f'B{row_idx}'].font = FONT_META
        ws[f'B{row_idx}'].alignment = Alignment(horizontal="center")
        ws[f'C{row_idx}'] = val_gestion
        ws[f'C{row_idx}'].font = FONT_MONEY_BOLD
        ws[f'C{row_idx}'].number_format = FORMATO_MONEDA
        ws[f'C{row_idx}'].alignment = Alignment(horizontal="right")
        ws[f'D{row_idx}'] = f"=C{row_idx}"
        ws[f'D{row_idx}'].font = FONT_MONEY_BOLD
        ws[f'D{row_idx}'].number_format = FORMATO_MONEDA
        ws[f'D{row_idx}'].alignment = Alignment(horizontal="right")
        for col in ['A', 'B', 'C', 'D']:
            ws[f'{col}{row_idx}'].fill = NARANJA_GESTION
            ws[f'{col}{row_idx}'].border = BORDER_ALL
        subtotal_cells.append(f'C{row_idx}')
        row_idx += 1
    else:
        # IIEE: Agrupación oficial omitiendo completamente filas sin meta registrada o sin ejecución

        # 1. Grupo Educación Básica (047 EDUCAC.BASICA)
        basica_children = []
        if float(metas_dict.get('11', 0.0)) > 0:
            basica_children.append(('103 EDUC.INICIAL', 11, float(metas_dict['11'])))
        if float(metas_dict.get('12', 0.0)) > 0:
            basica_children.append(('104 PRIMARIA', 12, float(metas_dict['12'])))
        if float(metas_dict.get('14', 0.0)) > 0:
            basica_children.append(('105 EDUCACION SECUNDARIA', 14, float(metas_dict['14'])))

        if basica_children:
            header_row = row_idx
            ws[f'A{header_row}'] = "047 EDUCAC.BASICA"
            ws[f'A{header_row}'].font = FONT_PROGRAMA_UNDERLINE
            row_idx += 1
            first_child = row_idx
            for nombre, meta_cod, monto in basica_children:
                ws[f'A{row_idx}'] = nombre
                ws[f'A{row_idx}'].font = FONT_PROGRAMA_REGULAR
                ws[f'B{row_idx}'] = meta_cod
                ws[f'B{row_idx}'].font = FONT_META
                ws[f'B{row_idx}'].alignment = Alignment(horizontal="center")
                ws[f'C{row_idx}'] = monto
                ws[f'C{row_idx}'].font = FONT_MONEY
                ws[f'C{row_idx}'].number_format = FORMATO_MONEDA
                ws[f'C{row_idx}'].alignment = Alignment(horizontal="right")
                ws[f'D{row_idx}'] = f"=C{row_idx}"
                ws[f'D{row_idx}'].font = FONT_MONEY
                ws[f'D{row_idx}'].number_format = FORMATO_MONEDA
                ws[f'D{row_idx}'].alignment = Alignment(horizontal="right")
                for col in ['A', 'B', 'C', 'D']:
                    ws[f'{col}{row_idx}'].fill = VERDE_FILA
                    ws[f'{col}{row_idx}'].border = BORDER_ALL
                row_idx += 1
            last_child = row_idx - 1

            ws[f'C{header_row}'] = f"=SUM(C{first_child}:C{last_child})"
            ws[f'C{header_row}'].font = FONT_MONEY_BOLD
            ws[f'C{header_row}'].number_format = FORMATO_MONEDA
            ws[f'C{header_row}'].alignment = Alignment(horizontal="right")
            ws[f'D{header_row}'] = f"=C{header_row}"
            ws[f'D{header_row}'].font = FONT_MONEY_BOLD
            ws[f'D{header_row}'].number_format = FORMATO_MONEDA
            ws[f'D{header_row}'].alignment = Alignment(horizontal="right")
            for col in ['A', 'B', 'C', 'D']:
                ws[f'{col}{header_row}'].border = BORDER_ALL
            subtotal_cells.append(f'C{header_row}')

        # 2. Grupo Básica Alternativa (106 EDUC.BASICA ALTER.)
        eba_children = []
        if float(metas_dict.get('43', 0.0)) > 0:
            eba_children.append(('EBA Ciclo Inicial e Intermedio', 43, float(metas_dict['43'])))
        if float(metas_dict.get('44', 0.0)) > 0:
            eba_children.append(('EBA Ciclo Avanzado', 44, float(metas_dict['44'])))

        if eba_children:
            header_row = row_idx
            ws[f'A{header_row}'] = "106 EDUC.BASICA ALTER."
            ws[f'A{header_row}'].font = FONT_PROGRAMA_UNDERLINE
            row_idx += 1
            first_child = row_idx
            for nombre, meta_cod, monto in eba_children:
                ws[f'A{row_idx}'] = nombre
                ws[f'A{row_idx}'].font = FONT_PROGRAMA_REGULAR
                ws[f'B{row_idx}'] = meta_cod
                ws[f'B{row_idx}'].font = FONT_META
                ws[f'B{row_idx}'].alignment = Alignment(horizontal="center")
                ws[f'C{row_idx}'] = monto
                ws[f'C{row_idx}'].font = FONT_MONEY
                ws[f'C{row_idx}'].number_format = FORMATO_MONEDA
                ws[f'C{row_idx}'].alignment = Alignment(horizontal="right")
                ws[f'D{row_idx}'] = f"=C{row_idx}"
                ws[f'D{row_idx}'].font = FONT_MONEY
                ws[f'D{row_idx}'].number_format = FORMATO_MONEDA
                ws[f'D{row_idx}'].alignment = Alignment(horizontal="right")
                for col in ['A', 'B', 'C', 'D']:
                    ws[f'{col}{row_idx}'].fill = VERDE_FILA
                    ws[f'{col}{row_idx}'].border = BORDER_ALL
                row_idx += 1
            last_child = row_idx - 1

            ws[f'C{header_row}'] = f"=SUM(C{first_child}:C{last_child})"
            ws[f'C{header_row}'].font = FONT_MONEY_BOLD
            ws[f'C{header_row}'].number_format = FORMATO_MONEDA
            ws[f'C{header_row}'].alignment = Alignment(horizontal="right")
            ws[f'D{header_row}'] = f"=C{header_row}"
            ws[f'D{header_row}'].font = FONT_MONEY_BOLD
            ws[f'D{header_row}'].number_format = FORMATO_MONEDA
            ws[f'D{header_row}'].alignment = Alignment(horizontal="right")
            for col in ['A', 'B', 'C', 'D']:
                ws[f'{col}{header_row}'].border = BORDER_ALL
            subtotal_cells.append(f'C{header_row}')

        # 3. Grupo Educación Especial (107 EDUCAC. ESPECIAL)
        esp_children = []
        if float(metas_dict.get('29', 0.0)) > 0:
            esp_children.append(('Especial Inicial', 29, float(metas_dict['29'])))
        if float(metas_dict.get('30', 0.0)) > 0:
            esp_children.append(('Especial Primaria', 30, float(metas_dict['30'])))

        if esp_children:
            header_row = row_idx
            ws[f'A{header_row}'] = "107 EDUCAC. ESPECIAL"
            ws[f'A{header_row}'].font = FONT_PROGRAMA_UNDERLINE
            row_idx += 1
            first_child = row_idx
            for nombre, meta_cod, monto in esp_children:
                ws[f'A{row_idx}'] = nombre
                ws[f'A{row_idx}'].font = FONT_PROGRAMA_REGULAR
                ws[f'B{row_idx}'] = meta_cod
                ws[f'B{row_idx}'].font = FONT_META
                ws[f'B{row_idx}'].alignment = Alignment(horizontal="center")
                ws[f'C{row_idx}'] = monto
                ws[f'C{row_idx}'].font = FONT_MONEY
                ws[f'C{row_idx}'].number_format = FORMATO_MONEDA
                ws[f'C{row_idx}'].alignment = Alignment(horizontal="right")
                ws[f'D{row_idx}'] = f"=C{row_idx}"
                ws[f'D{row_idx}'].font = FONT_MONEY
                ws[f'D{row_idx}'].number_format = FORMATO_MONEDA
                ws[f'D{row_idx}'].alignment = Alignment(horizontal="right")
                for col in ['A', 'B', 'C', 'D']:
                    ws[f'{col}{row_idx}'].fill = VERDE_FILA
                    ws[f'{col}{row_idx}'].border = BORDER_ALL
                row_idx += 1
            last_child = row_idx - 1

            ws[f'C{header_row}'] = f"=SUM(C{first_child}:C{last_child})"
            ws[f'C{header_row}'].font = FONT_MONEY_UNDERLINE
            ws[f'C{header_row}'].number_format = FORMATO_MONEDA
            ws[f'C{header_row}'].alignment = Alignment(horizontal="right")
            ws[f'D{header_row}'] = f"=C{header_row}"
            ws[f'D{header_row}'].font = FONT_MONEY_UNDERLINE
            ws[f'D{header_row}'].fill = AMARILLO_ESPECIAL
            ws[f'D{header_row}'].number_format = FORMATO_MONEDA
            ws[f'D{header_row}'].alignment = Alignment(horizontal="right")
            for col in ['A', 'B', 'C', 'D']:
                ws[f'{col}{header_row}'].border = BORDER_ALL
            subtotal_cells.append(f'C{header_row}')

        # 4. Educación Técnico Productiva (049 EDUCAC. TEC.PRODUCT.)
        val_cetpro = float(metas_dict.get('42', 0.0))
        if val_cetpro > 0:
            ws[f'A{row_idx}'] = "049 EDUCAC. TEC.PRODUCT."
            ws[f'A{row_idx}'].font = FONT_PROGRAMA_BOLD
            ws[f'B{row_idx}'] = 42
            ws[f'B{row_idx}'].font = FONT_META
            ws[f'B{row_idx}'].alignment = Alignment(horizontal="center")
            ws[f'C{row_idx}'] = val_cetpro
            ws[f'C{row_idx}'].font = FONT_MONEY_UNDERLINE
            ws[f'C{row_idx}'].number_format = FORMATO_MONEDA
            ws[f'C{row_idx}'].alignment = Alignment(horizontal="right")
            ws[f'D{row_idx}'] = f"=C{row_idx}"
            ws[f'D{row_idx}'].font = FONT_MONEY_UNDERLINE
            ws[f'D{row_idx}'].number_format = FORMATO_MONEDA
            ws[f'D{row_idx}'].alignment = Alignment(horizontal="right")
            for col in ['A', 'B', 'C', 'D']:
                ws[f'{col}{row_idx}'].fill = VERDE_FILA
                ws[f'{col}{row_idx}'].border = BORDER_ALL
            subtotal_cells.append(f'C{row_idx}')
            row_idx += 1

        # 5. Otras metas adicionales registradas
        codigos_estandar = {'11', '12', '14', '43', '44', '29', '30', '42'}
        for m, monto_dec in metas_dict.items():
            if m not in codigos_estandar and float(monto_dec) > 0:
                info = metas_info.get(m, {})
                desc = info.get('descripcion') or f"Meta {info.get('raw_codigo', m)}"
                ws[f'A{row_idx}'] = desc
                ws[f'A{row_idx}'].font = FONT_PROGRAMA_REGULAR
                ws[f'B{row_idx}'] = info.get('raw_codigo', m)
                ws[f'B{row_idx}'].font = FONT_META
                ws[f'B{row_idx}'].alignment = Alignment(horizontal="center")
                ws[f'C{row_idx}'] = float(monto_dec)
                ws[f'C{row_idx}'].font = FONT_MONEY
                ws[f'C{row_idx}'].number_format = FORMATO_MONEDA
                ws[f'C{row_idx}'].alignment = Alignment(horizontal="right")
                ws[f'D{row_idx}'] = f"=C{row_idx}"
                ws[f'D{row_idx}'].font = FONT_MONEY
                ws[f'D{row_idx}'].number_format = FORMATO_MONEDA
                ws[f'D{row_idx}'].alignment = Alignment(horizontal="right")
                for col in ['A', 'B', 'C', 'D']:
                    ws[f'{col}{row_idx}'].fill = VERDE_FILA
                    ws[f'{col}{row_idx}'].border = BORDER_ALL
                subtotal_cells.append(f'C{row_idx}')
                row_idx += 1

    # Fila TOTAL
    ws[f'A{row_idx}'] = "TOTAL"
    ws[f'A{row_idx}'].font = FONT_TOTAL_WHITE
    ws[f'A{row_idx}'].fill = AZUL_NAVY
    ws[f'A{row_idx}'].alignment = Alignment(horizontal="center")
    ws[f'B{row_idx}'].fill = AZUL_NAVY

    formula_total = f"={'+'.join(subtotal_cells)}" if subtotal_cells else "=0"
    ws[f'C{row_idx}'] = formula_total
    ws[f'C{row_idx}'].font = FONT_TOTAL_WHITE
    ws[f'C{row_idx}'].fill = AZUL_NAVY
    ws[f'C{row_idx}'].number_format = FORMATO_MONEDA
    ws[f'C{row_idx}'].alignment = Alignment(horizontal="right")

    ws[f'D{row_idx}'] = f"=C{row_idx}"
    ws[f'D{row_idx}'].font = FONT_TOTAL_BLACK
    ws[f'D{row_idx}'].fill = AMARILLO_TOTAL
    ws[f'D{row_idx}'].number_format = FORMATO_MONEDA
    ws[f'D{row_idx}'].alignment = Alignment(horizontal="right")

    for col in ['A', 'B', 'C']:
        ws[f'{col}{row_idx}'].border = BORDER_ALL
    ws[f'D{row_idx}'].border = BORDER_TOTAL_YELLOW

    for r in range(5, row_idx + 1):
        ws.row_dimensions[r].height = 20

    # Dimensiones de columna
    ws.column_dimensions['A'].width = 34
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 18
    ws.column_dimensions['D'].width = 18

    # Ajustes de página
    ws.page_setup.orientation = ws.ORIENTATION_PORTRAIT
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()
