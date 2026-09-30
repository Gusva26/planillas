"""Generador de la Hoja de Trabajo de Remuneraciones CAFAE (Etapa 12).

Agrupa por metas presupuestarias, programas y partidas,
sumando EXCLUSIVAMENTE el importe bruto (nunca netos ni descuentos).
"""
from collections import defaultdict
from decimal import Decimal
import io
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

AZUL_HEADER = PatternFill(start_color="16324F", end_color="16324F", fill_type="solid")
GRIS_SUBTOTAL = PatternFill(start_color="E9ECEF", end_color="E9ECEF", fill_type="solid")
GRIS_TOTAL = PatternFill(start_color="CED4DA", end_color="CED4DA", fill_type="solid")

FONT_HEADER = Font(name="Arial", size=9, bold=True, color="FFFFFF")
FONT_DATA = Font(name="Arial", size=8)
FONT_BOLD = Font(name="Arial", size=8, bold=True)
FONT_TITLE = Font(name="Arial", size=11, bold=True, color="16324F")

THIN_SIDE = Side(border_style="thin", color="CCCCCC")
THICK_SIDE = Side(border_style="medium", color="16324F")
BORDER_CELL = Border(left=THIN_SIDE, right=THIN_SIDE, top=THIN_SIDE, bottom=THIN_SIDE)
BORDER_TOP_BOTTOM = Border(top=THICK_SIDE, bottom=THICK_SIDE)

FORMATO_MONEDA = '#,##0.00'


def generar_excel_remuneraciones(info_planilla: dict, filas_detalle: list[dict]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    tipo = info_planilla['tipo']
    anio = info_planilla['anio']
    mes = info_planilla['mes']
    meses_nom = ['', 'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
                 'JULIO', 'AGOSTO', 'SETIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
    nombre_mes = meses_nom[mes]
    ws.title = f"REMUNERACIONES {nombre_mes[:3]}_{anio % 100}"

    # Encabezado oficial
    ws['A1'] = "GOBIERNO REGIONAL LA LIBERTAD"
    ws['A2'] = "GERENCIA REGIONAL DE EDUCACIÓN - UNIDAD DE GESTIÓN EDUCATIVA LOCAL CHEPÉN"
    ws['A3'] = f"HOJA DE TRABAJO DE REMUNERACIONES - PLANILLA CAFAE {tipo} - {nombre_mes} {anio}"
    ws['A1'].font = Font(name="Arial", size=9, bold=True)
    ws['A2'].font = Font(name="Arial", size=9, bold=True)
    ws['A3'].font = FONT_TITLE

    # Agrupar exclusivamente por Meta presupuestaria y sumar IMPORTE BRUTO
    grupos_meta = defaultdict(list)
    for f in filas_detalle:
        m_cod = f.get('meta_codigo') or 'SIN_META'
        grupos_meta[m_cod].append(f)

    fila_inicio = 5
    columnas = [
        ("N°", 5), ("META", 10), ("DESCRIPCIÓN DE META", 32),
        ("PARTIDA", 14), ("DNI", 10), ("APELLIDOS Y NOMBRES", 30),
        ("DEPENDENCIA / ESTABLECIMIENTO", 28), ("CARGO", 20),
        ("REMUNERACIÓN TOTAL / IMPORTE (S/)", 22)
    ]

    for col_idx, (col_nombre, ancho) in enumerate(columnas, start=1):
        cell = ws.cell(row=fila_inicio, column=col_idx, value=col_nombre)
        cell.font = FONT_HEADER
        cell.fill = AZUL_HEADER
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER_CELL
        ws.column_dimensions[get_column_letter(col_idx)].width = ancho

    ws.row_dimensions[fila_inicio].height = 28
    fila_actual = fila_inicio + 1
    item_num = 1
    total_general_importe = Decimal('0.00')

    # Ordenar metas
    for m_cod in sorted(grupos_meta.keys()):
        trabajadores_meta = grupos_meta[m_cod]
        subtotal_meta_importe = Decimal('0.00')
        desc_meta = trabajadores_meta[0].get('meta_descripcion') or 'Meta Presupuestaria'
        partida = trabajadores_meta[0].get('partida_codigo') or '2.1.11.21'

        for t in trabajadores_meta:
            imp = t['importe']
            subtotal_meta_importe += imp
            total_general_importe += imp

            dep = t.get('institucion_nombre') or t.get('area_nombre') or ''

            ws.cell(row=fila_actual, column=1, value=item_num).alignment = Alignment(horizontal="center")
            ws.cell(row=fila_actual, column=2, value=m_cod).alignment = Alignment(horizontal="center")
            ws.cell(row=fila_actual, column=3, value=desc_meta)
            ws.cell(row=fila_actual, column=4, value=partida).alignment = Alignment(horizontal="center")
            dni_cell = ws.cell(row=fila_actual, column=5, value=t['dni'])
            dni_cell.number_format = '@'
            dni_cell.alignment = Alignment(horizontal="center")
            ws.cell(row=fila_actual, column=6, value=f"{t['apellidos']}, {t['nombres']}")
            ws.cell(row=fila_actual, column=7, value=dep)
            ws.cell(row=fila_actual, column=8, value=t.get('cargo') or '')
            c_imp = ws.cell(row=fila_actual, column=9, value=float(imp))
            c_imp.number_format = FORMATO_MONEDA
            c_imp.alignment = Alignment(horizontal="right")

            for ci in range(1, 10):
                ws.cell(row=fila_actual, column=ci).font = FONT_DATA
                ws.cell(row=fila_actual, column=ci).border = BORDER_CELL

            item_num += 1
            fila_actual += 1

        # Fila de Subtotal por Meta
        ws.row_dimensions[fila_actual].height = 20
        c_sub_lbl = ws.cell(row=fila_actual, column=1, value=f"SUBTOTAL META {m_cod} ({len(trabajadores_meta)} personas)")
        c_sub_lbl.font = FONT_BOLD
        c_sub_lbl.alignment = Alignment(horizontal="left")

        for ci in range(1, 9):
            ws.cell(row=fila_actual, column=ci).fill = GRIS_SUBTOTAL
            ws.cell(row=fila_actual, column=ci).border = BORDER_CELL

        c_sub_val = ws.cell(row=fila_actual, column=9, value=float(subtotal_meta_importe))
        c_sub_val.font = FONT_BOLD
        c_sub_val.fill = GRIS_SUBTOTAL
        c_sub_val.number_format = FORMATO_MONEDA
        c_sub_val.alignment = Alignment(horizontal="right")
        c_sub_val.border = BORDER_CELL

        fila_actual += 1

    # Fila de Total General
    ws.row_dimensions[fila_actual].height = 24
    c_tot_lbl = ws.cell(row=fila_actual, column=1, value=f"TOTAL GENERAL REMUNERACIONES ({len(filas_detalle)} personas)")
    c_tot_lbl.font = FONT_BOLD
    c_tot_lbl.alignment = Alignment(horizontal="left")

    for ci in range(1, 9):
        ws.cell(row=fila_actual, column=ci).fill = GRIS_TOTAL
        ws.cell(row=fila_actual, column=ci).border = BORDER_TOP_BOTTOM

    c_tot_val = ws.cell(row=fila_actual, column=9, value=float(total_general_importe))
    c_tot_val.font = FONT_BOLD
    c_tot_val.fill = GRIS_TOTAL
    c_tot_val.number_format = FORMATO_MONEDA
    c_tot_val.alignment = Alignment(horizontal="right")
    c_tot_val.border = BORDER_TOP_BOTTOM

    # Configuración de página
    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToPage = True
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()
