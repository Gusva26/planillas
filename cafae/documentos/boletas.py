"""Generador de Boletas de Pago CAFAE individuales y mensuales en PDF.
Réplica fiel del formato oficial de la boleta institucional de UGEL Chepén.
"""
from decimal import Decimal
import io
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, portrait
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
)


def _dibujar_marca_agua(canvas, doc, ruta_logo=None):
    """Dibuja la marca de agua oficial (UGEL Chepén, Escudo Regional y Gobierno Regional La Libertad)."""
    canvas.saveState()
    # Buscar imagen de marca de agua institucional
    if not ruta_logo:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        candidatos = [
            os.path.join(base_dir, 'assets', 'marca_agua_boleta.png'),
            'assets/marca_agua_boleta.png',
            '/app/assets/marca_agua_boleta.png',
            os.path.join(base_dir, 'assets', 'identidad_ugel.jpeg'),
            os.path.join(base_dir, 'assets', 'logo_ugel.png'),
            'assets/identidad_ugel.jpeg',
            'assets/logo_ugel.png',
            '/app/assets/identidad_ugel.jpeg',
            '/app/assets/logo_ugel.png',
        ]
        for c in candidatos:
            if os.path.exists(c):
                ruta_logo = c
                break

    # Dibujar marca de agua oficial si existe el archivo
    if ruta_logo and os.path.exists(ruta_logo):
        try:
            # Opacidad atenuada oficial para no entorpecer la legibilidad de importes
            canvas.setFillAlpha(0.20)
            
            # Dimensiones calibradas: el gráfico oficial mide 795x1024 (aspect ratio 0.776)
            # Centrado en página A4 (595.27 x 841.89 pt) abarcando encabezado, datos y conceptos
            img_w = 440
            img_h = 567
            x_pos = (595.27 - img_w) / 2
            y_pos = 250
            
            canvas.drawImage(
                ruta_logo,
                x=x_pos,
                y=y_pos,
                width=img_w,
                height=img_h,
                mask='auto',
                preserveAspectRatio=True
            )
        except Exception:
            pass

    canvas.restoreState()


def generar_boleta_pdf(datos_trabajador: dict, info_planilla: dict, ruta_logo=None) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=portrait(A4),
        leftMargin=40,
        rightMargin=40,
        topMargin=35,
        bottomMargin=35
    )

    story = _construir_story_boleta(datos_trabajador, info_planilla)
    doc.build(
        story,
        onFirstPage=lambda c, d: _dibujar_marca_agua(c, d, ruta_logo),
        onLaterPages=lambda c, d: _dibujar_marca_agua(c, d, ruta_logo)
    )
    return buffer.getvalue()


def generar_cuadernillo_boletas_pdf(filas_trabajadores: list[dict], info_planilla: dict, ruta_logo=None) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=portrait(A4),
        leftMargin=40,
        rightMargin=40,
        topMargin=35,
        bottomMargin=35
    )

    story = []
    for idx, t in enumerate(filas_trabajadores):
        sub_story = _construir_story_boleta(t, info_planilla)
        story.extend(sub_story)
        if idx < len(filas_trabajadores) - 1:
            story.append(PageBreak())

    doc.build(
        story,
        onFirstPage=lambda c, d: _dibujar_marca_agua(c, d, ruta_logo),
        onLaterPages=lambda c, d: _dibujar_marca_agua(c, d, ruta_logo)
    )
    return buffer.getvalue()


def _format_fecha(val, default='-'):
    if not val:
        return default
    if hasattr(val, 'strftime'):
        return val.strftime('%d/%m/%Y')
    val_str = str(val).split('T')[0].strip()
    if '-' in val_str:
        partes = val_str.split('-')
        if len(partes) == 3 and len(partes[0]) == 4:
            return f"{partes[2]}/{partes[1]}/{partes[0]}"
    return val_str or default


def _construir_story_boleta(t: dict, info_p: dict) -> list:
    meses_nom = ['', 'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
                 'JULIO', 'AGOSTO', 'SETIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
    mes_str = meses_nom[info_p['mes']]
    anio_str = str(info_p['anio'])

    # Estilos tipográficos compactos fieles al formato impreso
    style_tit_boleta = ParagraphStyle(
        'TitBoleta', fontName='Helvetica-Bold', fontSize=13, leading=15, textColor=colors.black
    )
    style_tit_inst = ParagraphStyle(
        'TitInst', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.black
    )
    style_tit_sub = ParagraphStyle(
        'TitSub', fontName='Helvetica-Bold', fontSize=7.5, leading=9, textColor=colors.HexColor('#333333')
    )
    style_dni_hdr = ParagraphStyle(
        'DniHdr', fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=colors.black, alignment=2
    )

    style_fld_lbl = ParagraphStyle(
        'FldLbl', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=colors.black
    )
    style_fld_val = ParagraphStyle(
        'FldVal', fontName='Helvetica', fontSize=7.5, leading=9.5, textColor=colors.black
    )

    style_conc_nom = ParagraphStyle(
        'ConcNom', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=colors.black
    )
    style_conc_sgn = ParagraphStyle(
        'ConcSgn', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=colors.black, alignment=1
    )
    style_conc_mto = ParagraphStyle(
        'ConcMto', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=colors.black, alignment=2
    )

    style_tot_lbl = ParagraphStyle(
        'TotLbl', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.black
    )
    style_tot_val = ParagraphStyle(
        'TotVal', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.black, alignment=2
    )
    style_pie = ParagraphStyle(
        'PieAviso', fontName='Helvetica-Oblique', fontSize=6.5, leading=8.5, textColor=colors.HexColor('#444444'), alignment=1
    )

    story = []

    # 1. ENCABEZADO OFICIAL
    col_izq = [
        Paragraph("<b>Boleta de Pago CAFAE</b>", style_tit_boleta),
        Spacer(1, 4),
        Paragraph("<b>UNIDAD DE GESTIÓN EDUCATIVA LOCAL CHEPÉN</b>", style_tit_inst),
        Paragraph("<b>*BB UGEL CHEPEN</b>", style_tit_sub),
        Paragraph(f"<b>RUC &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:</b> 20038727748", style_fld_val),
        Paragraph(f"<b>Mes &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:</b> {mes_str} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>{anio_str}</b>", style_fld_val)
    ]
    col_der = [
        Paragraph(f"<b>DNI :</b> {t['dni']}", style_dni_hdr)
    ]

    t_header = Table([[col_izq, col_der]], colWidths=[365, 150])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 8))

    # 2. DATOS DEL SERVIDOR (Ficha idéntica a la imagen)
    adscripcion = t.get('institucion_nombre') or t.get('area_nombre') or 'UGEL CHEPÉN'
    cod_mod = t.get('codigo_modular') or '-'
    cargo_str = (t.get('cargo') or '-').upper()
    tipo_serv = (t.get('situacion') or 'Nombrado').capitalize()
    ley_str = t.get('ley') or '276'
    cat_str = t.get('categoria') or '-'
    jornada_str = str(t.get('jornada_laboral') or '40')
    tiempo_serv = t.get('tiempo_servicio_texto') or ''
    
    f_nac_str = _format_fecha(t.get('fecha_nacimiento'), '-')
    f_ingr_str = _format_fecha(t.get('fecha_ingreso'), '')
    f_term_str = _format_fecha(t.get('fecha_termino'), '')
    
    cta_str = t.get('cuenta_multired') or (f"CHEQUE {t.get('numero_cheque')}" if t.get('tipo_pago') == 'CHEQUE' else '-')
    leyenda_perm = t.get('leyenda_permanente') or '-'
    reg_pension = t.get('regimen_pensionario') or '-'

    filas_datos = [
        [Paragraph("Apellidos", style_fld_lbl), Paragraph(f": {t['apellidos'].upper()}", style_fld_val)],
        [Paragraph("Nombres", style_fld_lbl), Paragraph(f": {t['nombres'].upper()}", style_fld_val)],
        [Paragraph("Fecha de Nacimiento", style_fld_lbl), Paragraph(f": {f_nac_str}", style_fld_val)],
        [Paragraph("Documento de Indetidad", style_fld_lbl), Paragraph(f": {t['dni']}", style_fld_val)],
        [Paragraph("Establecimiento", style_fld_lbl), Paragraph(f": {adscripcion.upper()}", style_fld_val)],
        [Paragraph("Codigo Modular", style_fld_lbl), Paragraph(f": {cod_mod}", style_fld_val)],
        [Paragraph("Cargo", style_fld_lbl), Paragraph(f": {cargo_str}", style_fld_val)],
        [Paragraph("Tipo de Servidor", style_fld_lbl), Paragraph(f": {tipo_serv}", style_fld_val)],
        [Paragraph("Regimen Laboral Nº", style_fld_lbl), Paragraph(f": {ley_str}", style_fld_val)],
        [Paragraph("Grupo Ocup/HrsAdd", style_fld_lbl), Paragraph(f": {cat_str} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {jornada_str}", style_fld_val)],
        [Paragraph("Tiempo de Servicio (AA-MM-DD)", style_fld_lbl), Paragraph(f": {tiempo_serv}", style_fld_val)],
        [Paragraph("Fecha de Registro", style_fld_lbl), Paragraph(f": Ingr: {f_ingr_str} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Termino: {f_term_str}", style_fld_val)],
        [Paragraph("Cta. TeleAhorro o Nro Cheque", style_fld_lbl), Paragraph(f": {cta_str}", style_fld_val)],
        [Paragraph("Leyenda Permanente", style_fld_lbl), Paragraph(f": {leyenda_perm}", style_fld_val)],
        [Paragraph("Leyenda Mensual", style_fld_lbl), Paragraph(": -", style_fld_val)],
        [Paragraph("Regimen Pensionario", style_fld_lbl), Paragraph(f": {reg_pension}", style_fld_val)],
    ]

    t_servidor = Table(filas_datos, colWidths=[155, 360])
    t_servidor.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0.5),
        ('TOPPADDING', (0, 0), (-1, -1), 0.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_servidor)
    story.append(Spacer(1, 4))

    # 3. LÍNEA DIVISORIA OFICIAL (Doble barra)
    div_line = Table([[Paragraph("=" * 95, style_fld_lbl)]], colWidths=[515])
    div_line.setStyle(TableStyle([
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(div_line)
    story.append(Spacer(1, 2))

    # 4. HABERES Y DESCUENTOS
    # Extraer valores numéricos
    imp = Decimal(str(t.get('importe', '0.00')))
    lic = Decimal(str(t.get('monto_licencia', '0.00')))
    pich = Decimal(str(t.get('pichincha', '0.00')))
    sull = Decimal(str(t.get('caja_sullana', t.get('sullana', '0.00'))))
    subc = Decimal(str(t.get('sub_cafae', t.get('subcafae', '0.00'))))
    bren = Decimal(str(t.get('brenta', '0.00')))
    sitr = Decimal(str(t.get('sitrase', '0.00')))
    fent = Decimal(str(t.get('sitase_fentase', t.get('fentase', '0.00'))))
    otros = Decimal(str(t.get('otros', '0.00')))
    
    tot_desc = Decimal(str(t.get('total_descuentos', '0.00')))
    neto = Decimal(str(t.get('neto', '0.00')))

    # Filas con estructura exacta a la imagen
    conceptos = [
        ("001 Ley Nº29874; RER Nº 1205-2013-GRLL/PRE", "+", imp),
        ("Otros Ingresos + (*)", "+", Decimal('0.00')),
        ("PICHINCHA", "-", pich),
        ("CAJA SULLANA", "-", sull),
        ("SUB-CAFAE", "-", subc),
        ("CONV. BRENTA", "-", bren),
        ("SITRASE", "-", sitr),
        ("SITASE / FENTASE", "-", fent),
        ("LICENCIA S/G", "-", lic),
        ("OTROS DCTOS", "-", otros),
    ]

    filas_conceptos = []
    for c_nom, c_sgn, c_mto in conceptos:
        filas_conceptos.append([
            Paragraph(c_nom, style_conc_nom),
            Paragraph(c_sgn, style_conc_sgn),
            Paragraph(f"{c_mto:,.2f}", style_conc_mto)
        ])

    t_conceptos = Table(filas_conceptos, colWidths=[420, 25, 70])
    t_conceptos.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0.75),
        ('TOPPADDING', (0, 0), (-1, -1), 0.75),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_conceptos)
    story.append(Spacer(1, 2))

    # 5. LÍNEA DIVISORIA INFERIOR
    story.append(div_line)
    story.append(Spacer(1, 3))

    # 6. TOTALES EN LÍNEA HORIZONTAL (Distribución equilibrada y espaciosa sin colisiones)
    totales_data = [
        [
            Paragraph("T-INGRESOS", style_tot_lbl),
            Paragraph(f"{imp:,.2f}", style_tot_val),
            Paragraph("", style_tot_lbl),
            Paragraph("T-DSCTO", style_tot_lbl),
            Paragraph(f"{tot_desc:,.2f}", style_tot_val),
            Paragraph("", style_tot_lbl),
            Paragraph("T-LIQUI", style_tot_lbl),
            Paragraph(f"{neto:,.2f}", style_tot_val),
        ]
    ]

    t_totales = Table(totales_data, colWidths=[75, 75, 35, 65, 70, 40, 65, 90])
    t_totales.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_totales)
    story.append(Spacer(1, 6))

    # 7. PIE DE PÁGINA INSTITUCIONAL
    story.append(Paragraph(
        "*cualquier consulta escribir al correo electrónico 2155@gmail.com / whatsapp 95620544",
        style_pie
    ))

    return story
