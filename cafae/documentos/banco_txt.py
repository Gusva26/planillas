"""Módulo para la generación del archivo de abono bancario en formato TXT del Banco de la Nación.

Especificación técnica de dispersión Banco de la Nación (Multired / Telecrédito):
- Longitud exacta por línea: 28 caracteres.
- Sin espacios, tabulaciones ni separadores (comas, barras, etc.).
- Bloque 1 (3 caracteres): Código de transacción (041: Haberes / 341: Abono No Remunerativo).
- Bloque 2 (10 caracteres): Número de cuenta de ahorros del trabajador en el Banco de la Nación.
- Bloque 3 (15 caracteres): Importe a pagar en céntimos (sin punto ni coma), rellenado con ceros a la izquierda.
- Salto de línea estándar CRLF (\\r\\n).
"""
import re
from decimal import Decimal, ROUND_HALF_UP


def formatear_linea_banco(cuenta: str, monto: Decimal | float, tipo_transaccion: str = '041') -> str:
    """Formatea una única línea de 28 caracteres para el archivo del Banco de la Nación.
    
    Args:
        cuenta: Número de cuenta del trabajador.
        monto: Monto neto a transferir.
        tipo_transaccion: '041' (Pago de Haberes) o '341' (Abono No Remunerativo).
        
    Returns:
        Cadena de 28 caracteres exactos.
    """
    codigo = str(tipo_transaccion).strip()
    if codigo not in ('041', '341'):
        codigo = '041'
        
    # Limpiar número de cuenta: solo dígitos
    digitos_cta = re.sub(r'\D', '', str(cuenta or ''))
    if len(digitos_cta) >= 10:
        # Tomar los 10 dígitos (en cuentas BN son 10 dígitos)
        cuenta_fmt = digitos_cta[-10:]
    else:
        cuenta_fmt = digitos_cta.zfill(10)
        
    # Convertir monto a céntimos (2 decimales exactos con redondeo estándar)
    dec_monto = Decimal(str(monto)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    centimos = int(dec_monto * 100)
    if centimos < 0:
        centimos = 0
        
    monto_fmt = f"{centimos:015d}"
    
    linea = f"{codigo}{cuenta_fmt}{monto_fmt}"
    if len(linea) != 28:
        raise ValueError(f"Error de formato: La línea generada tiene {len(linea)} caracteres, se requieren exactamente 28.")
        
    return linea


def generar_txt_banco(filas_detalle: list[dict], tipo_transaccion: str = '041') -> tuple[bytes, dict]:
    """Genera el contenido en bytes del archivo TXT para el Banco de la Nación y su resumen de proceso.
    
    Args:
        filas_detalle: Lista de diccionarios con el detalle de la planilla (debe incluir cuenta_multired y neto).
        tipo_transaccion: '041' o '341'.
        
    Returns:
        tuple (contenido_bytes, resumen_dict):
            - contenido_bytes: Bytes del archivo TXT con codificación ASCII / UTF-8.
            - resumen_dict: Estadísticas (procesados, monto_total, excluidos_sin_cuenta, excluidos_monto_cero, etc.)
    """
    lineas = []
    total_monto = Decimal('0.00')
    procesados = 0
    sin_cuenta = []
    monto_invalido = []
    
    for f in filas_detalle:
        dni = str(f.get('dni') or '')
        apellidos = str(f.get('apellidos') or '')
        nombres = str(f.get('nombres') or '')
        nom_completo = f"{apellidos} {nombres}".strip()
        
        cuenta_raw = str(f.get('cuenta_multired') or '').strip()
        digitos_cta = re.sub(r'\D', '', cuenta_raw)
        
        # Validar si tiene cuenta bancaria
        if not digitos_cta:
            sin_cuenta.append({'dni': dni, 'nombre': nom_completo, 'motivo': 'Sin cuenta Multired'})
            continue
            
        # Obtener monto neto
        neto = Decimal(str(f.get('neto') or 0)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if neto <= 0:
            monto_invalido.append({'dni': dni, 'nombre': nom_completo, 'neto': float(neto), 'motivo': 'Neto menor o igual a cero'})
            continue
            
        linea = formatear_linea_banco(cuenta_raw, neto, tipo_transaccion)
        lineas.append(linea)
        total_monto += neto
        procesados += 1
        
    # Unir con salto de línea estándar CRLF
    contenido_txt = "\r\n".join(lineas)
    if lineas:
        contenido_txt += "\r\n"
        
    resumen = {
        'tipo_transaccion': tipo_transaccion,
        'descripcion_transaccion': 'Pago de Haberes' if tipo_transaccion == '041' else 'Abono No Remunerativo',
        'total_registros': procesados,
        'monto_total': float(total_monto),
        'excluidos_sin_cuenta': sin_cuenta,
        'excluidos_monto_cero': monto_invalido,
        'lineas_generadas': len(lineas)
    }
    
    return contenido_txt.encode('ascii'), resumen
