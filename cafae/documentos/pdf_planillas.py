"""Generador oficial de Planillas en formato PDF (A4 apaisado).
Réplica visual idéntica a la planilla oficial de UGEL Chepén:
- Títulos institucionales centrados y subrayados.
- Encabezado de dos niveles: celeste institucional y verde vivo para el grupo DESCUENTOS.
- Sub-encabezados con colores pastel idénticos al Excel para cada descuento.
- Agrupación por Metas con filas de subtotales (TOTAL META 14, TOTAL META 42, etc.).
- Fila general SUB - TOTAL en celeste.
- Tablita consolidada de descuentos en la parte inferior izquierda con colores idénticos.
- Bloque de firmas de conformidad en la base.
- Tipografía nítida y equilibrada para lectura clara en 1 sola página.
"""
from decimal import Decimal
import io
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)

# Colores oficiales idénticos a la plantilla de Excel
C_AZUL_CAB = colors.HexColor("#BDD7EE")       # Celeste institucional
C_VERDE_DESC = colors.HexColor("#92D050")     # Verde vivo DESCUENTOS
C_AZUL_NETO = colors.HexColor("#8EA9DB")      # Azul pizarra neto

C_PICHINCHA = colors.HexColor("#D5C578")      # Ocre / mostaza
C_SULLANA = colors.HexColor("#8EA9DB")        # Azul pizarra
C_SUBCAFAE = colors.HexColor("#70AD47")       # Verde azulado / teal
C_BRENTA = colors.HexColor("#B4A7D6")         # Lavanda
C_SITRASE = colors.HexColor("#A6A6A6")        # Gris
C_SITASE = colors.HexColor("#D6D090")         # Dorado
C_LICENCIA = colors.HexColor("#BDD7EE")       # Celeste
C_OTROS = colors.HexColor("#BDD7EE")          # Celeste

C_NEGRO = colors.black
C_BORDE_NEGRO = colors.black
C_BORDE_GRIS = colors.HexColor("#B2B2B2")


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


def generar_pdf_planilla(info_planilla: dict, filas_detalle: list[dict], firmas: list[dict] = None) -> bytes:
    firmas = firmas or []
    buffer = io.BytesIO()

    # A4 horizontal: 841.89 pt de ancho x 595.27 pt de alto
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=14,
        rightMargin=14,
        topMargin=12,
        bottomMargin=12
    )

    tipo = info_planilla['tipo']
    anio = info_planilla['anio']
    mes = info_planilla['mes']
    meses_nom = ['', 'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
                 'JULIO', 'AGOSTO', 'SETIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
    nombre_mes = meses_nom[mes]

    styles = getSampleStyleSheet()
    style_tit_principal = ParagraphStyle(
        'TitPrincipal',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=C_NEGRO,
        alignment=1
    )
    style_hdr = ParagraphStyle(
        'HdrPlan',
        fontName='Helvetica-Bold',
        fontSize=5.8,
        leading=6.8,
        textColor=C_NEGRO,
        alignment=1
    )
    style_hdr_desc = ParagraphStyle(
        'HdrDescCol',
        fontName='Helvetica-Bold',
        fontSize=5.2,
        leading=6.2,
        textColor=C_NEGRO,
        alignment=1
    )
    style_cell = ParagraphStyle(
        'CellPlan',
        fontName='Helvetica',
        fontSize=5.8,
        leading=6.8,
        textColor=C_NEGRO
    )
    style_cell_c = ParagraphStyle('CellC', parent=style_cell, alignment=1)
    style_cell_r = ParagraphStyle('CellR', parent=style_cell, alignment=2)
    style_cell_bold_r = ParagraphStyle('CellBR', parent=style_cell, fontName='Helvetica-Bold', alignment=2)
    style_cell_bold_c = ParagraphStyle('CellBC', parent=style_cell, fontName='Helvetica-Bold', alignment=1)

    story = []

    # 1. TÍTULOS SUPERIORES OFICIALES (Centrados y subrayados)
    if tipo == 'IIEE':
        tit_texto = "<u>PLANILLA CAFAE PERSONAL ADMINISTRATIVO DL. Nº 276 DE LAS INSTITUCIONES EDUCATIVAS</u>"
    else:
        tit_texto = "<u>PLANILLA CAFAE PERSONAL ADMINISTRATIVO DL. Nº 276 DE LA SEDE CENTRAL</u>"
    sub_texto = f"<u>JURISDICCIÓN UGEL CHEPEN - {nombre_mes} {anio}</u>"

    story.append(Paragraph(f"<b>{tit_texto}</b>", style_tit_principal))
    story.append(Spacer(1, 1))
    story.append(Paragraph(f"<b>{sub_texto}</b>", style_tit_principal))
    story.append(Spacer(1, 5))

    # 2. DEFINICIÓN DE COLUMNAS (Total 23 columnas que suman exactamente 813 pt)
    col_widths = [
        14,   # 0: N°
        34,   # 1: DNI
        36,   # 2: NIVEL / ÁREA
        122,  # 3: APELLIDOS Y NOMBRES
        105,  # 4: INSTITUCIÓN / DEPENDENCIA
        62,   # 5: CARGO
        20,   # 6: SIT.
        34,   # 7: F. NAC.
        13,   # 8: LEY
        13,   # 9: CAT
        13,   # 10: JORN
        38,   # 11: MULTIRED
        36,   # 12: IMPORTE
        25,   # 13: PICHINCHA
        25,   # 14: CAJA SULLANA
        25,   # 15: SUB-CAFAE
        25,   # 16: BRENTA
        25,   # 17: SITRASE
        25,   # 18: SITASE
        25,   # 19: LICENCIA S/G
        25,   # 20: OTROS
        35,   # 21: TOTAL DCTOS.
        38,   # 22: NETO A PAGAR
    ]

    # FILA DE ENCABEZADO 1 (Nivel superior con DESCUENTOS agrupado)
    hdr_row1 = [
        Paragraph("N°", style_hdr),
        Paragraph("N° DNI", style_hdr),
        Paragraph("NIVEL" if tipo == 'IIEE' else "ÁREA SEDE", style_hdr),
        Paragraph("APELLIDOS Y NOMBRES", style_hdr),
        Paragraph("INSTITUCIÓN EDUCATIVA" if tipo == 'IIEE' else "DEPENDENCIA", style_hdr),
        Paragraph("CARGO", style_hdr),
        Paragraph("SIT.", style_hdr),
        Paragraph("FECHA DE NACIM.", style_hdr),
        Paragraph("Ley", style_hdr),
        Paragraph("Cat.", style_hdr),
        Paragraph("Jorn.", style_hdr),
        Paragraph("MULTIRED", style_hdr),
        Paragraph("IMPORTE", style_hdr),
        Paragraph("DESCUENTOS", style_hdr),
        "", "", "", "", "", "", "",  # Espacios para span de DESCUENTOS (cols 13 a 20)
        Paragraph("TOTAL DCTOS.", style_hdr),
        Paragraph("NETO A PAGAR", style_hdr),
    ]

    # FILA DE ENCABEZADO 2 (Sub-encabezados de los 8 descuentos con sus colores pastel)
    hdr_row2 = [
        "", "", "", "", "", "", "", "", "", "", "", "", "",
        Paragraph("PICHINCHA", style_hdr_desc),
        Paragraph("CAJA SULLAN.", style_hdr_desc),
        Paragraph("SUB-CAFAE", style_hdr_desc),
        Paragraph("CONV. BRENTA", style_hdr_desc),
        Paragraph("SITRASE", style_hdr_desc),
        Paragraph("SITASE", style_hdr_desc),
        Paragraph("LICENCIA S/G", style_hdr_desc),
        Paragraph("OTROS", style_hdr_desc),
        "", ""
    ]

    table_data = [hdr_row1, hdr_row2]

    metas_dict = {}
    for f in filas_detalle:
        m_cod = str(f.get('meta_codigo') or f.get('meta_descripcion') or '0001').strip()
        metas_dict.setdefault(m_cod, []).append(f)

    estilos_tabla = [
        # Spans de la cabecera de 2 niveles
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (1, 0), (1, 1)),
        ('SPAN', (2, 0), (2, 1)),
        ('SPAN', (3, 0), (3, 1)),
        ('SPAN', (4, 0), (4, 1)),
        ('SPAN', (5, 0), (5, 1)),
        ('SPAN', (6, 0), (6, 1)),
        ('SPAN', (7, 0), (7, 1)),
        ('SPAN', (8, 0), (8, 1)),
        ('SPAN', (9, 0), (9, 1)),
        ('SPAN', (10, 0), (10, 1)),
        ('SPAN', (11, 0), (11, 1)),
        ('SPAN', (12, 0), (12, 1)),
        ('SPAN', (13, 0), (20, 0)),  # Span horizontal del grupo DESCUENTOS
        ('SPAN', (21, 0), (21, 1)),
        ('SPAN', (22, 0), (22, 1)),

        # Fondos de color en cabecera
        ('BACKGROUND', (0, 0), (12, 1), C_AZUL_CAB),
        ('BACKGROUND', (13, 0), (20, 0), C_VERDE_DESC),
        ('BACKGROUND', (13, 1), (13, 1), C_PICHINCHA),
        ('BACKGROUND', (14, 1), (14, 1), C_SULLANA),
        ('BACKGROUND', (15, 1), (15, 1), C_SUBCAFAE),
        ('BACKGROUND', (16, 1), (16, 1), C_BRENTA),
        ('BACKGROUND', (17, 1), (17, 1), C_SITRASE),
        ('BACKGROUND', (18, 1), (18, 1), C_SITASE),
        ('BACKGROUND', (19, 1), (19, 1), C_LICENCIA),
        ('BACKGROUND', (20, 1), (20, 1), C_OTROS),
        ('BACKGROUND', (21, 0), (21, 1), C_AZUL_CAB),
        ('BACKGROUND', (22, 0), (22, 1), C_AZUL_NETO),

        ('GRID', (0, 0), (-1, -1), 0.5, C_BORDE_NEGRO),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.1),
        ('TOPPADDING', (0, 0), (-1, -1), 1.1),
        ('LEFTPADDING', (0, 0), (-1, -1), 1),
        ('RIGHTPADDING', (0, 0), (-1, -1), 1),
    ]

    tot_general_imp = Decimal('0.00')
    tot_general_pich = Decimal('0.00')
    tot_general_sull = Decimal('0.00')
    tot_general_subc = Decimal('0.00')
    tot_general_bren = Decimal('0.00')
    tot_general_sitr = Decimal('0.00')
    tot_general_fent = Decimal('0.00')
    tot_general_lic = Decimal('0.00')
    tot_general_otro = Decimal('0.00')
    tot_general_desc = Decimal('0.00')
    tot_general_neto = Decimal('0.00')

    idx_global = 1
    fila_actual = 2

    for m_cod, lista_m in metas_dict.items():
        m_imp = Decimal('0.00')
        m_pich = Decimal('0.00')
        m_sull = Decimal('0.00')
        m_subc = Decimal('0.00')
        m_bren = Decimal('0.00')
        m_sitr = Decimal('0.00')
        m_fent = Decimal('0.00')
        m_lic = Decimal('0.00')
        m_otro = Decimal('0.00')
        m_desc = Decimal('0.00')
        m_neto = Decimal('0.00')

        meta_label = _format_meta_label(m_cod)

        for idx_f, f in enumerate(lista_m):
            imp_d = Decimal(str(f.get('importe') or 0))
            pich_d = Decimal(str(f.get('pichincha') or 0))
            sull_d = Decimal(str(f.get('caja_sullana') or 0))
            subc_d = Decimal(str(f.get('sub_cafae') or 0))
            bren_d = Decimal(str(f.get('brenta') or 0))
            sitr_d = Decimal(str(f.get('sitrase') or 0))
            fent_d = Decimal(str(f.get('sitase_fentase') or 0))
            lic_d = Decimal(str(f.get('monto_licencia') or 0))
            otro_d = Decimal(str(f.get('otros') or 0))
            desc_d = Decimal(str(f.get('total_descuentos') or 0))
            neto_d = Decimal(str(f.get('neto') or 0))

            m_imp += imp_d
            m_pich += pich_d
            m_sull += sull_d
            m_subc += subc_d
            m_bren += bren_d
            m_sitr += sitr_d
            m_fent += fent_d
            m_lic += lic_d
            m_otro += otro_d
            m_desc += desc_d
            m_neto += neto_d

            dep_nom = f"{f.get('codigo_modular') or ''} {f.get('institucion_nombre') or ''}".strip() if tipo == 'IIEE' else (f.get('area_nombre') or 'UGEL CHEPÉN')
            apellidos_nombres = f"{f.get('apellidos', '')}, {f.get('nombres', '')}".upper()

            row_data = [
                Paragraph(str(idx_global), style_cell_c),
                Paragraph(str(f['dni']), style_cell_c),
                Paragraph(str(f.get('nivel_nombre') or f.get('area_nombre') or '')[:14], style_cell),
                Paragraph(apellidos_nombres[:32], style_cell),
                Paragraph(dep_nom[:32], style_cell),
                Paragraph(str(f.get('cargo') or '')[:20], style_cell),
                Paragraph(str(f.get('situacion') or 'NOM')[:4], style_cell_c),
                Paragraph(_format_fecha(f.get('fecha_nacimiento')), style_cell_c),
                Paragraph(str(f.get('ley') or '276'), style_cell_c),
                Paragraph(str(f.get('categoria') or 'AE'), style_cell_c),
                Paragraph(str(f.get('jornada_laboral') or '40'), style_cell_c),
                Paragraph(str(f.get('cuenta_multired') or '-'), style_cell_c),
                Paragraph(f"{imp_d:,.2f}", style_cell_r),
                Paragraph(f"{pich_d:,.2f}", style_cell_r),
                Paragraph(f"{sull_d:,.2f}", style_cell_r),
                Paragraph(f"{subc_d:,.2f}", style_cell_r),
                Paragraph(f"{bren_d:,.2f}", style_cell_r),
                Paragraph(f"{sitr_d:,.2f}", style_cell_r),
                Paragraph(f"{fent_d:,.2f}", style_cell_r),
                Paragraph(f"{lic_d:,.2f}", style_cell_r),
                Paragraph(f"{otro_d:,.2f}", style_cell_r),
                Paragraph(f"{desc_d:,.2f}", style_cell_bold_r),
                Paragraph(f"{neto_d:,.2f}", style_cell_bold_r),
            ]
            table_data.append(row_data)
            idx_global += 1
            fila_actual += 1

        tot_general_imp += m_imp
        tot_general_pich += m_pich
        tot_general_sull += m_sull
        tot_general_subc += m_subc
        tot_general_bren += m_bren
        tot_general_sitr += m_sitr
        tot_general_fent += m_fent
        tot_general_lic += m_lic
        tot_general_otro += m_otro
        tot_general_desc += m_desc
        tot_general_neto += m_neto

        # Fila de SUBTOTAL DE META (Texto en índice 0 para que se muestre en la celda combinada 0..11)
        row_sub_meta = [
            Paragraph(f"<i><b>TOTAL {meta_label}</b></i>", style_cell_bold_r),
            "", "", "", "", "", "", "", "", "", "", "",
            Paragraph(f"<b>{m_imp:,.2f}</b>", style_cell_bold_r),
            Paragraph(f"<b>{m_pich:,.2f}</b>", style_cell_bold_r),
            Paragraph(f"<b>{m_sull:,.2f}</b>", style_cell_bold_r),
            Paragraph(f"<b>{m_subc:,.2f}</b>", style_cell_bold_r),
            Paragraph(f"<b>{m_bren:,.2f}</b>", style_cell_bold_r),
            Paragraph(f"<b>{m_sitr:,.2f}</b>", style_cell_bold_r),
            Paragraph(f"<b>{m_fent:,.2f}</b>", style_cell_bold_r),
            Paragraph(f"<b>{m_lic:,.2f}</b>", style_cell_bold_r),
            Paragraph(f"<b>{m_otro:,.2f}</b>", style_cell_bold_r),
            Paragraph(f"<b>{m_desc:,.2f}</b>", style_cell_bold_r),
            Paragraph(f"<b>{m_neto:,.2f}</b>", style_cell_bold_r),
        ]
        table_data.append(row_sub_meta)
        estilos_tabla.extend([
            ('SPAN', (0, fila_actual), (11, fila_actual)),
            ('BACKGROUND', (0, fila_actual), (-1, fila_actual), C_AZUL_CAB),
        ])
        fila_actual += 1

    # Fila SUB - TOTAL GENERAL (Texto en índice 0 para que se muestre en la celda combinada 0..11)
    row_subtotal = [
        Paragraph("<b>SUB - TOTAL</b>", style_cell_bold_c),
        "", "", "", "", "", "", "", "", "", "", "",
        Paragraph(f"<b>{tot_general_imp:,.2f}</b>", style_cell_bold_r),
        Paragraph(f"<b>{tot_general_pich:,.2f}</b>", style_cell_bold_r),
        Paragraph(f"<b>{tot_general_sull:,.2f}</b>", style_cell_bold_r),
        Paragraph(f"<b>{tot_general_subc:,.2f}</b>", style_cell_bold_r),
        Paragraph(f"<b>{tot_general_bren:,.2f}</b>", style_cell_bold_r),
        Paragraph(f"<b>{tot_general_sitr:,.2f}</b>", style_cell_bold_r),
        Paragraph(f"<b>{tot_general_fent:,.2f}</b>", style_cell_bold_r),
        Paragraph(f"<b>{tot_general_lic:,.2f}</b>", style_cell_bold_r),
        Paragraph(f"<b>{tot_general_otro:,.2f}</b>", style_cell_bold_r),
        Paragraph(f"<b>{tot_general_desc:,.2f}</b>", style_cell_bold_r),
        Paragraph(f"<b>{tot_general_neto:,.2f}</b>", style_cell_bold_r),
    ]
    table_data.append(row_subtotal)
    estilos_tabla.extend([
        ('SPAN', (0, fila_actual), (11, fila_actual)),
        ('BACKGROUND', (0, fila_actual), (-1, fila_actual), C_AZUL_CAB),
    ])

    main_table = Table(table_data, colWidths=col_widths, repeatRows=2)
    main_table.setStyle(TableStyle(estilos_tabla))
    story.append(main_table)
    story.append(Spacer(1, 6))

    # =========================================================================
    # 3. BLOQUE FINAL DE CIERRE (Tablita de descuentos a la izquierda + Firmas)
    # =========================================================================
    bloque_cierre = []

    style_th_desc = ParagraphStyle('ThDesc', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7, leading=8.5, textColor=C_NEGRO, alignment=1)
    style_lbl_desc = ParagraphStyle('LblDesc', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=6.8, leading=8, textColor=C_NEGRO)
    style_val_desc = ParagraphStyle('ValDesc', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=6.8, leading=8, textColor=C_NEGRO, alignment=2)
    style_date_lbl = ParagraphStyle('DateLbl', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=7.5, leading=9, textColor=C_NEGRO, alignment=2)

    t_desc_data = [
        [Paragraph("<b>DESCUENTOS</b>", style_th_desc), Paragraph("", style_th_desc)],
        [Paragraph("* PICHINCHA:", style_lbl_desc), Paragraph(f"S/. {tot_general_pich:,.2f}", style_val_desc)],
        [Paragraph("* CAJA SULLAN:", style_lbl_desc), Paragraph(f"S/. {tot_general_sull:,.2f}", style_val_desc)],
        [Paragraph("* BRENTA:", style_lbl_desc), Paragraph(f"S/. {tot_general_bren:,.2f}", style_val_desc)],
        [Paragraph("* SITASE:", style_lbl_desc), Paragraph(f"S/. {tot_general_fent:,.2f}", style_val_desc)],
        [Paragraph("* SUBCAFAE:", style_lbl_desc), Paragraph(f"S/. {tot_general_subc:,.2f}", style_val_desc)],
        [Paragraph("* SITRASE:", style_lbl_desc), Paragraph(f"S/. {tot_general_sitr:,.2f}", style_val_desc)],
        [Paragraph("* LIC. S/G:", style_lbl_desc), Paragraph(f"S/. {tot_general_lic:,.2f}", style_val_desc)],
        [Paragraph("", style_lbl_desc), Paragraph(f"S/. {tot_general_desc:,.2f}", style_val_desc)],
    ]
    tabla_descs = Table(t_desc_data, colWidths=[85, 70])
    tabla_descs.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('BACKGROUND', (0, 0), (1, 0), C_AZUL_CAB),
        ('BACKGROUND', (1, 1), (1, 1), C_PICHINCHA),
        ('BACKGROUND', (1, 2), (1, 2), C_SULLANA),
        ('BACKGROUND', (1, 4), (1, 4), C_SITASE),
        ('BACKGROUND', (1, 5), (1, 5), C_SUBCAFAE),
        ('BACKGROUND', (1, 6), (1, 6), C_SITRASE),
        ('BACKGROUND', (1, 8), (1, 8), C_AZUL_CAB),
        ('GRID', (0, 0), (-1, -1), 0.5, C_BORDE_NEGRO),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
    ]))

    fila_inferior = [
        [tabla_descs, Paragraph(f"<i>Chepén, {nombre_mes.lower()} {anio}</i>", style_date_lbl)]
    ]
    t_bloque_inf = Table(fila_inferior, colWidths=[165, 645])
    t_bloque_inf.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    bloque_cierre.append(t_bloque_inf)
    bloque_cierre.append(Spacer(1, 40))

    # Firmas institucionales (4 en II.EE. / 3 en Sede)
    firmas_data = [[], [], []]
    cant_firmas = len(firmas)
    ancho_f = 813 // max(cant_firmas, 1)

    style_firma_line = ParagraphStyle('FirmaLine', parent=styles['Normal'], fontName='Helvetica', fontSize=6, leading=7, textColor=C_NEGRO, alignment=1)
    style_firma_nom = ParagraphStyle('FirmaNom', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=6, leading=7, textColor=C_NEGRO, alignment=1)
    style_firma_cargo = ParagraphStyle('FirmaCargo', parent=styles['Normal'], fontName='Helvetica', fontSize=5.5, leading=6.5, textColor=C_NEGRO, alignment=1)

    for f in firmas:
        firmas_data[0].append(Paragraph("___________________________________", style_firma_line))
        firmas_data[1].append(Paragraph(f"<b>{f['nombre_completo']}</b>", style_firma_nom))
        firmas_data[2].append(Paragraph(f"{f['cargo']}", style_firma_cargo))

    tabla_firmas = Table(firmas_data, colWidths=[ancho_f] * cant_firmas)
    tabla_firmas.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0.8),
        ('TOPPADDING', (0, 0), (-1, -1), 0.8),
    ]))

    bloque_cierre.append(tabla_firmas)
    story.append(KeepTogether(bloque_cierre))

    doc.build(story)
    return buffer.getvalue()
