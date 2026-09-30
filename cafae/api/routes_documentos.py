"""Rutas para la generación y descarga de documentos oficiales."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response, status

from cafae.api.deps import get_current_user
from cafae.catalogos import CatalogoService
from cafae.documentos.boletas import generar_boleta_pdf, generar_cuadernillo_boletas_pdf
from cafae.documentos.excel_planillas import generar_excel_planilla
from cafae.documentos.pdf_planillas import generar_pdf_planilla
from cafae.documentos.remuneraciones import generar_excel_remuneraciones
from cafae.planillas import PlanillaService
from cafae.security import UserError

router = APIRouter(prefix='/documentos', tags=['Documentos'])
pln_service = PlanillaService()
cat_service = CatalogoService()


def _get_contexto_version(token: str, version_id: int):
    with pln_service.auth.data_transaction(token, 'consultar') as (conn, _):
        v_info = conn.execute(
            '''SELECT pv.*, p.tipo, p.cantidad_firmas, per.anio, per.mes
               FROM planilla_versiones pv
               JOIN planillas p ON p.id = pv.planilla_id
               JOIN periodos per ON per.id = p.periodo_id
               WHERE pv.id = %s''',
            (version_id,)
        ).fetchone()

    if not v_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Versión de planilla no encontrada.')

    filas = pln_service.get_detalle_version(token, version_id)
    firmas = cat_service.list_firmas(token, solo_activas=True)
    firmas_doc = firmas[:v_info['cantidad_firmas']]

    return v_info, filas, firmas_doc


@router.get('/planilla-pdf/{version_id}')
def descargar_planilla_pdf(version_id: int, user: Annotated[dict, Depends(get_current_user)]):
    try:
        v_info, filas, firmas = _get_contexto_version(user['token'], version_id)
        pdf_bytes = generar_pdf_planilla(v_info, filas, firmas)
        filename = f"Planilla_{v_info['tipo']}_{v_info['anio']}_{v_info['mes']:02d}_v{v_info['numero']}.pdf"
        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'},
        )
    except UserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get('/planilla-excel/{version_id}')
def descargar_planilla_excel(version_id: int, user: Annotated[dict, Depends(get_current_user)]):
    try:
        v_info, filas, firmas = _get_contexto_version(user['token'], version_id)
        excel_bytes = generar_excel_planilla(v_info, filas, firmas)
        filename = f"Planilla_{v_info['tipo']}_{v_info['anio']}_{v_info['mes']:02d}_v{v_info['numero']}.xlsx"
        return Response(
            content=excel_bytes,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'},
        )
    except UserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get('/remuneraciones-excel/{version_id}')
def descargar_remuneraciones_excel(version_id: int, user: Annotated[dict, Depends(get_current_user)]):
    try:
        v_info, filas, _ = _get_contexto_version(user['token'], version_id)
        excel_bytes = generar_excel_remuneraciones(v_info, filas)
        filename = f"Remuneraciones_{v_info['tipo']}_{v_info['anio']}_{v_info['mes']:02d}_v{v_info['numero']}.xlsx"
        return Response(
            content=excel_bytes,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'},
        )
    except UserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get('/boleta-individual/{linea_id}')
def descargar_boleta_individual(linea_id: int, user: Annotated[dict, Depends(get_current_user)]):
    try:
        token = user['token']
        with pln_service.auth.data_transaction(token, 'consultar') as (conn, _):
            fila_det = conn.execute('SELECT version_id, dni FROM planilla_detalle WHERE id = %s', (linea_id,)).fetchone()
            if not fila_det:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Línea de trabajador no encontrada.')
            v_info, filas, _ = _get_contexto_version(token, fila_det['version_id'])
            fila = next((f for f in filas if f['id'] == linea_id), None)
            if not fila:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Trabajador no encontrado en la versión.')

        pdf_bytes = generar_boleta_pdf(fila, v_info)
        filename = f"Boleta_{fila['dni']}_{v_info['anio']}_{v_info['mes']:02d}.pdf"
        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'},
        )
    except UserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get('/boleta-dni/{version_id}/{dni}')
def descargar_boleta_por_dni(version_id: int, dni: str, user: Annotated[dict, Depends(get_current_user)]):
    try:
        token = user['token']
        v_info, filas, _ = _get_contexto_version(token, version_id)
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
    except UserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get('/cuadernillo-boletas/{version_id}')
def descargar_cuadernillo_boletas(version_id: int, user: Annotated[dict, Depends(get_current_user)]):
    try:
        v_info, filas, _ = _get_contexto_version(user['token'], version_id)
        pdf_bytes = generar_cuadernillo_boletas_pdf(filas, v_info)
        filename = f"Cuadernillo_Boletas_{v_info['tipo']}_{v_info['anio']}_{v_info['mes']:02d}_v{v_info['numero']}.pdf"
        return Response(
            content=pdf_bytes,
            media_type='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'},
        )
    except UserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
