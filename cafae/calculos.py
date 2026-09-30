"""Motor único de cálculos monetarios para el sistema de planillas CAFAE.

Garantiza exactitud absoluta usando Decimal con ROUND_HALF_UP, idéntico
a las restricciones y disparadores de PostgreSQL.
Nunca utiliza números en punto flotante (float).
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from cafae.security import UserError

CENTAVO = Decimal('0.01')
DIAS_MES = Decimal(30)

CONCEPTOS_DESCUENTO = (
    'PICHINCHA',
    'CAJA_SULLANA',
    'SUB_CAFAE',
    'BRENTA',
    'SITRASE',
    'SITASE_FENTASE',
    'OTROS'
)


def a_decimal(val, nombre='Monto') -> Decimal:
    """Convierte de forma segura y estricta cualquier entrada a Decimal(12,2)."""
    if isinstance(val, float):
        raise UserError(f'El campo "{nombre}" no puede ser float por riesgo de imprecisión monetaria.')
    if val is None or (isinstance(val, str) and not val.strip()):
        return Decimal('0.00')
    try:
        d = Decimal(str(val).strip().replace(',', '')).quantize(CENTAVO, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        raise UserError(f'El valor "{val}" en "{nombre}" no es un número monetario válido.')
    if not d.is_finite():
        raise UserError(f'El campo "{nombre}" contiene un valor no finito.')
    return d


def calcular_licencia(importe: Decimal, dias_licencia: int) -> Decimal:
    """Calcula el descuento por licencia sin goce de haber: (importe / 30) * dias.

    Casos exactos:
    - 0 días -> 0.00
    - 30 días -> importe completo
    - 1 a 29 días -> (importe / 30) * dias antes de redondear a 2 decimales (D04).
    """
    if not isinstance(dias_licencia, int):
        try:
            dias_licencia = int(dias_licencia)
        except (ValueError, TypeError):
            raise UserError('Los días de licencia deben ser un número entero entre 0 y 30.')
    if dias_licencia < 0 or dias_licencia > 30:
        raise UserError('Los días de licencia deben estar en el rango de 0 a 30.')
    if importe < Decimal('0.00'):
        raise UserError('El importe no puede ser negativo.')

    if dias_licencia == 0:
        return Decimal('0.00')
    if dias_licencia == 30:
        return importe

    # Cálculo sin redondeo intermedio del jornal (D04):
    monto = (importe * Decimal(dias_licencia)) / DIAS_MES
    return monto.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def calcular_liquidacion_trabajador(importe: Decimal, dias_licencia: int,
                                    descuentos: dict) -> dict:
    """Calcula la liquidación completa de un trabajador para el periodo.

    Retorna:
    - importe
    - dias_licencia
    - monto_licencia
    - descuentos_conceptos (los 7 editables)
    - total_descuentos (monto_licencia + 7 editables = 8 conceptos)
    - neto (importe - total_descuentos)
    - es_neto_negativo (booleano informativo para borrador)
    """
    imp = a_decimal(importe, 'Importe')
    m_lic = calcular_licencia(imp, dias_licencia)

    desc_conceptos = {}
    suma_conceptos = Decimal('0.00')

    for c in CONCEPTOS_DESCUENTO:
        val = a_decimal(descuentos.get(c, Decimal('0.00')), f'Descuento {c}')
        if val < Decimal('0.00'):
            raise UserError(f'El descuento "{c}" no puede ser negativo.')
        desc_conceptos[c] = val
        suma_conceptos += val

    total_desc = m_lic + suma_conceptos
    neto = imp - total_desc

    return {
        'importe': imp,
        'dias_licencia': dias_licencia,
        'monto_licencia': m_lic,
        'descuentos': desc_conceptos,
        'total_descuentos': total_desc,
        'neto': neto,
        'es_neto_negativo': (neto < Decimal('0.00'))
    }


def calcular_totales_planilla(filas: list[dict]) -> dict:
    """Calcula la consolidación general y por conceptos para una versión de planilla."""
    total_trabajadores = len(filas)
    total_importe = Decimal('0.00')
    total_licencia = Decimal('0.00')
    totales_conceptos = {c: Decimal('0.00') for c in CONCEPTOS_DESCUENTO}
    total_descuentos = Decimal('0.00')
    total_neto = Decimal('0.00')
    personas_neto_negativo = 0

    for f in filas:
        total_importe += f['importe']
        total_licencia += f['monto_licencia']
        for c in CONCEPTOS_DESCUENTO:
            totales_conceptos[c] += f['descuentos'][c]
        total_descuentos += f['total_descuentos']
        total_neto += f['neto']
        if f['neto'] < Decimal('0.00'):
            personas_neto_negativo += 1

    return {
        'total_trabajadores': total_trabajadores,
        'total_importe': total_importe,
        'total_licencia': total_licencia,
        'totales_conceptos': totales_conceptos,
        'total_descuentos': total_descuentos,
        'total_neto': total_neto,
        'personas_neto_negativo': personas_neto_negativo
    }
