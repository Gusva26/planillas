import React, { useState, useEffect } from 'react';
import { apiRequest } from '../api/client';
import { mensajeDeError } from '../api/errors';
import {
  ImportacionDetalle,
  PlanillaListItem,
  RespuestaProcesarImportacion,
  TipoDescuento,
} from '../types';
import { 
  UploadCloud, 
  FileSpreadsheet, 
  CheckCircle2, 
  AlertCircle, 
  CheckSquare, 
  Square,
  FileCheck,
  Building2,
  Landmark,
  X,
  CreditCard,
  FileUp
} from 'lucide-react';

export const ImportacionesView: React.FC = () => {
  const [planillas, setPlanillas] = useState<PlanillaListItem[]>([]);
  const [tiposDescuento, setTiposDescuento] = useState<TipoDescuento[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<number | null>(null);
  const [selectedConceptoId, setSelectedConceptoId] = useState<number>(1);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [importacionData, setImportacionData] = useState<ImportacionDetalle | null>(null);
  const [modalidad, setModalidad] = useState<'ACTUALIZAR' | 'REEMPLAZAR'>('ACTUALIZAR');
  const [applying, setApplying] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [list, tipos] = await Promise.all([
          apiRequest<PlanillaListItem[]>('/api/planillas'),
          apiRequest<TipoDescuento[]>('/api/catalogos/tipos-descuento'),
        ]);
        const openList = list.filter((p) => p.version_estado !== 'CERRADA');
        setPlanillas(openList);
        setTiposDescuento(tipos);
        if (openList.length > 0) {
          setSelectedVersionId(openList[0].version_id);
        }
      } catch (err) {
        setErrorMsg(mensajeDeError(err, 'Error al cargar las planillas abiertas.'));
      }
    };
    fetchInitialData();
  }, []);

  const currentPlanilla = planillas.find((p) => p.version_id === selectedVersionId);

  const conceptos = tiposDescuento
    .filter((td) => {
      if (!td.activo) return false;
      if (!currentPlanilla) return true;
      return currentPlanilla.tipo === 'IIEE' ? td.aplica_iiee : td.aplica_sede;
    })
    .sort((a, b) => a.orden - b.orden);

  useEffect(() => {
    if (conceptos.length > 0) {
      if (!conceptos.some((c) => c.id === selectedConceptoId)) {
        setSelectedConceptoId(conceptos[0].id);
      }
    }
  }, [selectedVersionId, tiposDescuento]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setErrorMsg(null);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !selectedVersionId) return;

    setUploading(true);
    setSuccessMsg(null);
    setErrorMsg(null);
    try {
      const formData = new FormData();
      formData.append('version_id', String(selectedVersionId));
      formData.append('tipo_descuento_id', String(selectedConceptoId));
      formData.append('archivo', file);

      const res = await apiRequest<RespuestaProcesarImportacion>('/api/importaciones/procesar', {
        method: 'POST',
        body: formData,
      });

      // Cargar detalle clasificado
      const detalle = await apiRequest<ImportacionDetalle>(`/api/importaciones/${res.resumen.importacion_id}`);
      setImportacionData(detalle);
    } catch (err) {
      setErrorMsg(mensajeDeError(err, 'Error al procesar el archivo Excel.'));
    } finally {
      setUploading(false);
    }
  };

  const handleToggleFila = async (filaNum: number, currentSelected: boolean) => {
    if (!importacionData) return;
    try {
      await apiRequest(`/api/importaciones/${importacionData.resumen.id}/filas`, {
        method: 'PATCH',
        body: JSON.stringify({
          fila: filaNum,
          seleccionado: !currentSelected,
        }),
      });

      // Actualizar estado local
      setImportacionData((prev) => prev ? ({
        ...prev,
        filas: prev.filas.map((f) =>
          f.fila === filaNum ? { ...f, seleccionado: !currentSelected } : f
        ),
      }) : prev);
    } catch (err) {
      alert(mensajeDeError(err, 'Error al modificar selección de la fila.'));
    }
  };

  const handleAplicar = async () => {
    if (!importacionData) return;
    setApplying(true);
    try {
      const res = await apiRequest<{ ok: boolean; mensaje: string }>(`/api/importaciones/${importacionData.resumen.id}/aplicar`, {
        method: 'POST',
        body: JSON.stringify({
          modalidad,
          revision_esperada: importacionData.resumen.revision_edicion || 1,
        }),
      });
      setSuccessMsg(res.mensaje || 'Descuentos aplicados correctamente a la planilla activa.');
      setImportacionData(null);
      setFile(null);
    } catch (err) {
      alert(mensajeDeError(err, 'Error al aplicar descuentos a la planilla.'));
    } finally {
      setApplying(false);
    }
  };

  const getFormatSize = (bytes?: number) => {
    if (!bytes) return '';
    return `${(bytes / 1024).toFixed(1)} KB`;
  };

  return (
    <div className="page-container">
      {/* Encabezado */}
      <div style={{ marginBottom: '1.75rem' }}>
        <span style={{ fontSize: '0.725rem', fontWeight: 700, color: '#2563EB', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Carga Masiva Asistida
        </span>
        <h2 style={{ fontSize: '1.35rem', marginTop: '0.15rem', marginBottom: '0.2rem', color: '#0F172A', fontWeight: 800 }}>
          Asistente de Importación de Descuentos Excel
        </h2>
        <p style={{ fontSize: '0.85rem', color: '#64748B', margin: 0 }}>
          Procesamiento automático de listas de descuentos bancarios, cuotas gremiales y retenciones de ley.
        </p>
      </div>

      {successMsg && (
        <div style={{
          background: '#ECFDF5',
          border: '1.5px solid #A7F3D0',
          padding: '0.95rem 1.25rem',
          borderRadius: 'var(--radius-md)',
          color: '#065F46',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.65rem'
        }}>
          <CheckCircle2 size={18} style={{ color: '#059669', flexShrink: 0 }} />
          <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div style={{
          background: '#FEF2F2',
          border: '1.5px solid #FECACA',
          padding: '0.95rem 1.25rem',
          borderRadius: 'var(--radius-md)',
          color: '#991B1B',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.65rem'
        }}>
          <AlertCircle size={18} style={{ color: '#DC2626', flexShrink: 0 }} />
          <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>{errorMsg}</span>
        </div>
      )}

      {/* Tarjeta de Configuración y Carga */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <form onSubmit={handleUpload}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem', marginBottom: '1.5rem' }}>
            {/* Planilla Destino */}
            <div className="form-group">
              <label className="form-label">
                Planilla Abierta de Destino *
              </label>
              <select
                className="form-select"
                value={selectedVersionId || ''}
                onChange={(e) => setSelectedVersionId(Number(e.target.value))}
                required
              >
                {planillas.length === 0 ? (
                  <option value="">No hay planillas abiertas en edición</option>
                ) : (
                  planillas.map((p) => (
                    <option key={p.version_id} value={p.version_id}>
                      {p.tipo === 'IIEE' ? 'II.EE.' : 'SEDE'} · Periodo {p.anio}-{String(p.mes).padStart(2, '0')} (v{p.version_numero})
                    </option>
                  ))
                )}
              </select>
            </div>

            {/* Concepto de Descuento */}
            <div className="form-group">
              <label className="form-label">
                Concepto de Descuento Institucional *
              </label>
              <select
                className="form-select"
                value={selectedConceptoId}
                onChange={(e) => setSelectedConceptoId(Number(e.target.value))}
              >
                {conceptos.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nombre} ({c.codigo})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Zona Drag & Drop Elegante */}
          <div style={{
            border: file ? '2px solid #2563EB' : '2px dashed #CBD5E1',
            borderRadius: 'var(--radius-lg)',
            padding: '2.5rem 1.5rem',
            textAlign: 'center',
            background: file ? '#F0F9FF' : '#F8FAFC',
            marginBottom: '1.5rem',
            position: 'relative',
            transition: 'all var(--transition-fast)',
            cursor: 'pointer'
          }}>
            <div style={{
              width: 52,
              height: 52,
              borderRadius: 'var(--radius-full)',
              background: file ? '#DBEAFE' : '#EFF6FF',
              color: '#1D4ED8',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '0.85rem'
            }}>
              {file ? <FileSpreadsheet size={26} /> : <UploadCloud size={26} />}
            </div>

            <h3 style={{ fontSize: '1.05rem', marginBottom: '0.35rem', color: '#0F172A', fontWeight: 700 }}>
              {file ? file.name : 'Arrastra o selecciona el archivo Excel de descuentos'}
            </h3>
            <p style={{ fontSize: '0.8rem', color: '#64748B', maxWidth: '420px', margin: '0 auto' }}>
              Formatos aceptados: .xlsx o .xls. El motor identificará automáticamente las columnas de DNI y Monto.
              {file && <span style={{ display: 'block', marginTop: '0.35rem', color: '#2563EB', fontWeight: 600 }}>Tamaño: {getFormatSize(file.size)}</span>}
            </p>

            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={handleFileChange}
              style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer' }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            {file && (
              <button 
                type="button" 
                onClick={() => setFile(null)} 
                className="btn btn-secondary btn-sm"
              >
                Quitar Archivo
              </button>
            )}
            <button 
              type="submit" 
              className="btn btn-primary" 
              disabled={!file || !selectedVersionId || uploading}
              style={{ fontWeight: 700 }}
            >
              <FileUp size={16} />
              <span>{uploading ? 'Analizando estructura Excel...' : 'Analizar y Previsualizar'}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Previsualización de Registros Clasificados */}
      {importacionData && (
        <div className="card">
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '1rem',
            marginBottom: '1.25rem',
            borderBottom: '1px solid #E2E8F0',
            paddingBottom: '1.15rem'
          }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
                <span className="badge badge-indigo">Resultado del Análisis</span>
                <span style={{ fontSize: '0.8rem', color: '#64748B' }}>
                  {importacionData.filas.length} registros detectados
                </span>
              </div>
              <h3 style={{ fontSize: '1.2rem', color: '#0F172A', fontWeight: 800, margin: 0 }}>
                {importacionData.resumen.archivo_nombre}
              </h3>
            </div>

            {/* Modalidad de Aplicación y Botón Confirmar */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
              <div className="segmented-control">
                <button
                  type="button"
                  onClick={() => setModalidad('ACTUALIZAR')}
                  className={`segmented-item ${modalidad === 'ACTUALIZAR' ? 'active' : ''}`}
                >
                  <span>ACTUALIZAR (Solo seleccionados)</span>
                </button>
                <button
                  type="button"
                  onClick={() => setModalidad('REEMPLAZAR')}
                  className={`segmented-item ${modalidad === 'REEMPLAZAR' ? 'active' : ''}`}
                  style={{ color: modalidad === 'REEMPLAZAR' ? '#DC2626' : undefined }}
                >
                  <span>REEMPLAZAR (Limpia y aplica)</span>
                </button>
              </div>

              <button 
                onClick={handleAplicar} 
                disabled={applying} 
                className="btn btn-success"
                style={{ fontWeight: 700 }}
              >
                <FileCheck size={16} />
                <span>{applying ? 'Aplicando a nómina...' : 'Aplicar a Planilla'}</span>
              </button>
            </div>
          </div>

          {/* Grilla Clasificada */}
          <div className="table-container" style={{ maxHeight: '55vh' }}>
            <table className="table">
              <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
                <tr>
                  <th style={{ width: 45, textAlign: 'center' }}>Sel.</th>
                  <th style={{ width: 50, textAlign: 'center' }}>Fila</th>
                  <th style={{ width: 95 }}>DNI Archivo</th>
                  <th>Nombre en Archivo</th>
                  <th style={{ textAlign: 'right', width: 110 }}>Monto</th>
                  <th style={{ width: 120, textAlign: 'center' }}>Estado DNI</th>
                  <th>Servidor Vinculado en Planilla</th>
                  <th>Observación</th>
                </tr>
              </thead>
              <tbody>
                {importacionData.filas.map((f) => {
                  const isSelectable = f.estado === 'IDENTIFICADO' || f.estado === 'REVISAR';
                  return (
                    <tr key={f.fila} style={{ opacity: f.seleccionado ? 1 : 0.55 }}>
                      <td style={{ textAlign: 'center' }}>
                        <button
                          type="button"
                          onClick={() => handleToggleFila(f.fila, f.seleccionado)}
                          className="btn btn-ghost btn-sm"
                          style={{ padding: '0.2rem' }}
                          disabled={!isSelectable}
                          title={f.seleccionado ? 'Deseleccionar fila' : 'Seleccionar fila'}
                        >
                          {f.seleccionado ? (
                            <CheckSquare size={17} style={{ color: '#1D4ED8' }} />
                          ) : (
                            <Square size={17} style={{ color: '#94A3B8' }} />
                          )}
                        </button>
                      </td>
                      <td style={{ color: '#64748B', textAlign: 'center' }}>{f.fila}</td>
                      <td className="mono-amount" style={{ fontWeight: 600, color: '#0F172A' }}>
                        {f.dni_original || '—'}
                      </td>
                      <td style={{ color: '#334155' }}>{f.nombre_original || '—'}</td>
                      <td className="mono-amount" style={{ textAlign: 'right', fontWeight: 700, color: '#DC2626' }}>
                        S/ {Number(f.monto_validado || f.monto_original || 0).toFixed(2)}
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <span className={`badge ${
                          f.estado === 'IDENTIFICADO' ? 'badge-emerald' :
                          f.estado === 'REVISAR' ? 'badge-amber' :
                          f.estado === 'DNI_DUPLICADO' ? 'badge-amber' : 'badge-crimson'
                        }`}>
                          {f.estado}
                        </span>
                      </td>
                      <td style={{ fontWeight: 600, color: '#0F172A' }}>
                        {f.trabajador_apellidos ? `${f.trabajador_apellidos}, ${f.trabajador_nombres}` : '—'}
                      </td>
                      <td style={{ fontSize: '0.775rem', color: '#64748B' }}>
                        {f.observacion || '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
