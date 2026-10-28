"""Rutas para la generación y descarga de documentos oficiales."""
import os
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response, status

from cafae.api.deps import require_permission
from cafae.catalogos import CatalogoService
from cafae.documentos.banco_txt import generar_txt_banco
from cafae.documentos.boletas import generar_boleta_pdf, generar_cuadernillo_boletas_pdf
from cafae.documentos.excel_planillas import generar_excel_planilla
from cafae.documentos.pdf_planillas import generar_pdf_planilla
from cafae.documentos.remuneraciones import generar_excel_remuneraciones
from cafae.planillas import PlanillaService

router = APIRouter(prefix='/documentos', tags=['Documentos'])
pln_service = PlanillaService()
cat_service = CatalogoService()

# ADR-006: los documentos oficiales exigen permiso propio, no solo sesión.
PERMISO_DOCUMENTOS = 'generar_documentos'
PERMISO_TXT = 'txt_bancario'


def _txt_bancario_habilitado() -> bool:
    """Decisión D.5: el TXT permanece bloqueado salvo habilitación explícita."""
    return os.environ.get('CAFAE_TXT_BANCARIO', '0') == '1'


def _exigir_txt_habilitado() -> None:
    if not _txt_bancario_habilitado():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=('El archivo bancario está bloqueado hasta contar con la '
                    'especificación oficial (decisión D.5).'),
        )


def _exigir_version_cerrada(v_info: dict) -> None:
    if v_info.get('estado') != 'CERRADA':
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='El archivo bancario solo se genera desde una planilla cerrada.',
        )


def _get_contexto_version(token: str, version_id: int, *, permission: str = 'consultar'):
    """Cabecera y líneas de la versión en una sola transacción (D-04).

    El catálogo de firmas se lee aparte a propósito: no es estado de la versión
    y cambia con muy poca frecuencia.
    """
    datos = pln_service.get_version_completa(token, version_id, permiso=permission)
    v_info = datos['version']
    filas = datos['lineas']
    firmas = cat_service.list_firmas(token, solo_activas=True)
    firmas_doc = firmas[:v_info['cantidad_firmas']]

    return v_info, filas, firmas_doc


@router.get('/planilla-pdf/{version_id}')
def descargar_planilla_pdf(version_id: int, user: Annotated[dict, Depends(require_permission(PERMISO_DOCUMENTOS))]):
    v_info, filas, firmas = _get_contexto_version(user['token'], version_id, permission=PERMISO_DOCUMENTOS)
    pdf_bytes = generar_pdf_planilla(v_info, filas, firmas)
    filename = f"Planilla_{v_info['tipo']}_{v_info['anio']}_{v_info['mes']:02d}_v{v_info['numero']}.pdf"
    return Response(
        content=pdf_bytes,
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@router.get('/planilla-excel/{version_id}')
def descargar_planilla_excel(version_id: int, user: Annotated[dict, Depends(require_permission(PERMISO_DOCUMENTOS))]):
    v_info, filas, firmas = _get_contexto_version(user['token'], version_id, permission=PERMISO_DOCUMENTOS)
    excel_bytes = generar_excel_planilla(v_info, filas, firmas)
    filename = f"Planilla_{v_info['tipo']}_{v_info['anio']}_{v_info['mes']:02d}_v{v_info['numero']}.xlsx"
    return Response(
        content=excel_bytes,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@router.get('/remuneraciones-excel/{version_id}')
def descargar_remuneraciones_excel(version_id: int, user: Annotated[dict, Depends(require_permission(PERMISO_DOCUMENTOS))]):
    v_info, filas, _ = _get_contexto_version(user['token'], version_id, permission=PERMISO_DOCUMENTOS)
    excel_bytes = generar_excel_remuneraciones(v_info, filas)
    filename = f"Hoja_Remuneraciones_{v_info['tipo']}_{v_info['anio']}_{v_info['mes']:02d}.xlsx"
    return Response(
        content=excel_bytes,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@router.get('/boleta-individual/{linea_id}')
def descargar_boleta_individual(linea_id: int, user: Annotated[dict, Depends(require_permission(PERMISO_DOCUMENTOS))]):
    v_info, fila = pln_service.get_linea_con_version(user['token'], linea_id, permiso=PERMISO_DOCUMENTOS)

    pdf_bytes = generar_boleta_pdf(fila, v_info)
    filename = f"Boleta_{fila['dni']}_{v_info['anio']}_{v_info['mes']:02d}.pdf"
    return Response(
        content=pdf_bytes,
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@router.get('/boleta-dni/{version_id}/{dni}')
def descargar_boleta_por_dni(version_id: int, dni: str, user: Annotated[dict, Depends(require_permission(PERMISO_DOCUMENTOS))]):
    token = user['token']
    v_info, filas, _ = _get_contexto_version(token, version_id, permission=PERMISO_DOCUMENTOS)
    fila = next((f for f in filas if str(f['dni']).strip() == str(dni).strip()), None)
    if not fila:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Trabajador con DNI {dni} no encontrado en esta planilla.')

    pdf_bytes = generar_boleta_pdf(fila, v_info)
    filename = f"Boleta_{fila['dni']}_{v_info['anio']}_{v_info['mes']:02d}.pdf"
    return Response(
        content=pdf_bytes,
        media_type='application/pdf',
        headers={'Content-Disposition': f'inline; filename="{filename}"'},
    )


@router.get('/cuadernillo-boletas/{version_id}')
def descargar_cuadernillo_boletas(version_id: int, user: Annotated[dict, Depends(require_permission(PERMISO_DOCUMENTOS))]):
    v_info, filas, _ = _get_contexto_version(user['token'], version_id, permission=PERMISO_DOCUMENTOS)
    pdf_bytes = generar_cuadernillo_boletas_pdf(filas, v_info)
    filename = f"Cuadernillo_Boletas_{v_info['tipo']}_{v_info['anio']}_{v_info['mes']:02d}_v{v_info['numero']}.pdf"
    return Response(
        content=pdf_bytes,
        media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@router.get('/banco-txt/{version_id}')
def descargar_banco_txt(
    version_id: int,
    user: Annotated[dict, Depends(require_permission(PERMISO_TXT))],
    tipo_transaccion: str = '041'
):
    """Genera y descarga el archivo TXT para el Banco de la Nación (28 caracteres por fila)."""
    _exigir_txt_habilitado()
    if tipo_transaccion not in ('041', '341'):
        tipo_transaccion = '041'

    v_info, filas, _ = _get_contexto_version(
        user['token'], version_id, permission=PERMISO_TXT)
    _exigir_version_cerrada(v_info)
    txt_bytes, _ = generar_txt_banco(filas, tipo_transaccion=tipo_transaccion)
    filename = f"Abono_BN_{v_info['tipo']}_{v_info['anio']}_{v_info['mes']:02d}_{tipo_transaccion}.txt"
    return Response(
        content=txt_bytes,
        media_type='text/plain; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@router.get('/banco-txt-resumen/{version_id}')
def obtener_resumen_banco_txt(
    version_id: int,
    user: Annotated[dict, Depends(require_permission(PERMISO_TXT))],
    tipo_transaccion: str = '041'
):
    """Retorna las estadísticas del archivo bancario sin descargar el archivo."""
    _exigir_txt_habilitado()
    if tipo_transaccion not in ('041', '341'):
        tipo_transaccion = '041'

    v_info, filas, _ = _get_contexto_version(
        user['token'], version_id, permission=PERMISO_TXT)
    _exigir_version_cerrada(v_info)
    _, resumen = generar_txt_banco(filas, tipo_transaccion=tipo_transaccion)
    return resumen
