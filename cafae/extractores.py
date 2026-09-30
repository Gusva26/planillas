"""Extractores de texto y tablas para importación de descuentos institucionales.
Soporta archivos Excel (.xlsx), CSV y documentos delimitados.
Preserva el origen exacto: archivo, página/hoja, fila y texto original.
"""
from decimal import Decimal
import io
import re
import openpyxl

from cafae.calculos import a_decimal
from cafae.security import UserError


def normalizar_dni(dni_raw) -> str | None:
    if not dni_raw:
        return None
    val = str(dni_raw).strip()
    # Si viene con decimales de excel (ej. 12345678.0)
    if val.endswith('.0'):
        val = val[:-2]
    # Limpiar posibles caracteres no numéricos
    solo_digitos = re.sub(r'\D', '', val)
    if len(solo_digitos) == 8:
        return solo_digitos
    return None


def extraer_filas_excel(file_bytes: bytes, sheet_name=None) -> list[dict]:
    """Extrae filas desde un libro de Excel preservando fila, texto original y montos."""
    try:
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    except Exception as exc:
        raise UserError(f'El archivo no es un Excel válido o está dañado: {exc}')

    hoja = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb.active
    filas_extraidas = []

    # Detectar encabezados en las primeras 10 filas
    col_dni = None
    col_nom = None
    col_monto = None

    filas_iter = list(hoja.iter_rows(values_only=True))
    if not filas_iter:
        return []

    # Buscar fila de encabezados
    header_idx = -1
    for r_idx, row in enumerate(filas_iter[:15]):
        row_str = [str(c).strip().upper() if c is not None else '' for c in row]
        for c_idx, val in enumerate(row_str):
            if any(term in val for term in ('DNI', 'DOCUMENTO', 'DOC_ID', 'DOC_IDENTIDAD', 'CEDULA')):
                col_dni = c_idx
            elif any(term in val for term in ('APELLIDOS', 'NOMBRES', 'TRABAJADOR', 'PERSONAL', 'SERVIDOR', 'EMPLEADO')):
                col_nom = c_idx
            elif any(term in val for term in ('IMPORTE', 'MONTO', 'DESCUENTO', 'TOTAL', 'CUOTA', 'VALOR')):
                col_monto = c_idx
        if col_dni is not None and col_monto is not None:
            header_idx = r_idx
            break

    # Si no se detectaron encabezados por nombre, intentar heurística por contenido
    inicio_fila = header_idx + 1 if header_idx >= 0 else 0

    for r_num, row in enumerate(filas_iter[inicio_fila:], start=inicio_fila + 1):
        if not row or all(c is None or str(c).strip() == '' for c in row):
            continue

        dni_raw = row[col_dni] if col_dni is not None and col_dni < len(row) else None
        nom_raw = row[col_nom] if col_nom is not None and col_nom < len(row) else None
        monto_raw = row[col_monto] if col_monto is not None and col_monto < len(row) else None

        # Si aún no tenemos columnas fijas, buscar en la fila
        if dni_raw is None or monto_raw is None:
            for val in row:
                if val is not None:
                    val_s = str(val).strip()
                    if normalizar_dni(val_s) and dni_raw is None:
                        dni_raw = val_s
                    else:
                        try:
                            # Probar si es monto monetario
                            d = Decimal(str(val_s).replace(',', ''))
                            if d > 0 and monto_raw is None:
                                monto_raw = val_s
                        except Exception:
                            pass

        if dni_raw is not None:
            filas_extraidas.append({
                'fila': r_num,
                'hoja': hoja.title,
                'dni_original': str(dni_raw).strip() if dni_raw is not None else '',
                'nombre_original': str(nom_raw).strip() if nom_raw is not None else '',
                'monto_original': str(monto_raw).strip() if monto_raw is not None else '',
                'texto_original': ' | '.join(str(c) for c in row if c is not None),
                'metodo_extraccion': 'OPENPYXL_TABULAR'
            })

    return filas_extraidas
