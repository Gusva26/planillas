import React, { useState, useEffect } from 'react';
import { apiRequest } from '../api/client';
import { PlanillaListItem } from '../types';
import { 
  UploadCloud, 
  FileSpreadsheet, 
  CheckCircle2, 
  AlertCircle, 
  HelpCircle, 
  ArrowRight, 
  CheckSquare, 
  Square 
} from 'lucide-react';

export const ImportacionesView: React.FC = () => {
  const [planillas, setPlanillas] = useState<PlanillaListItem[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<number | null>(null);
  const [selectedConceptoId, setSelectedConceptoId] = useState<number>(1);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [importacionData, setImportacionData] = useState<any | null>(null);
  const [modalidad, setModalidad] = useState<'ACTUALIZAR' | 'REEMPLAZAR'>('ACTUALIZAR');
  const [applying, setApplying] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const conceptos = [
    { id: 1, codigo: 'PICHINCHA', nombre: 'Banco Pichincha' },
    { id: 2, codigo: 'SULLANA', nombre: 'Caja Sullana' },
    { id: 3, codigo: 'SUBCAFAE', nombre: 'SUB-CAFAE Chepén' },
    { id: 4, codigo: 'BRENTA', nombre: 'BRENTA' },
    { id: 5, codigo: 'SITRASE', nombre: 'SITRASE' },
    { id: 6, codigo: 'FENTASE', nombre: 'SITASE / FENTASE' },
    { id: 7, codigo: 'OTROS', nombre: 'Otros Descuentos' },
  ];

  useEffect(() => {
    const fetchPlanillas = async () => {
      try {
        const list = await apiRequest<PlanillaListItem[]>('/api/planillas');
        const openList = list.filter((p) => p.version_estado !== 'CERRADA');
        setPlanillas(openList);
        if (openList.length > 0) {
          setSelectedVersionId(openList[0].version_id);
        }
      } catch (err) {
        console.error('Error fetching planillas:', err);
      }
    };
    fetchPlanillas();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !selectedVersionId) return;

    setUploading(true);
    setSuccessMsg(null);
    try {
      const formData = new FormData();
      formData.append('version_id', String(selectedVersionId));
      formData.append('tipo_descuento_id', String(selectedConceptoId));
      formData.append('archivo', file);

      const res = await apiRequest('/api/importaciones/procesar', {
        method: 'POST',
        body: formData,
      });

      // Cargar detalle clasificado
      const detalle = await apiRequest(`/api/importaciones/${res.resumen.importacion_id}`);
      setImportacionData(detalle);
    } catch (err: any) {
      alert(err.message || 'Error al procesar el archivo Excel.');
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
      setImportacionData((prev: any) => ({
        ...prev,
        filas: prev.filas.map((f: any) =>
          f.fila === filaNum ? { ...f, seleccionado: !currentSelected } : f
        ),
      }));
    } catch (err: any) {
      alert(err.message || 'Error al modificar selección de la fila.');
    }
  };

  const handleAplicar = async () => {
    if (!importacionData) return;
    setApplying(true);
    try {
      const res = await apiRequest(`/api/importaciones/${importacionData.resumen.id}/aplicar`, {
        method: 'POST',
        body: JSON.stringify({
          modalidad,
          revision_esperada: importacionData.resumen.revision_edicion || 1,
        }),
      });
      setSuccessMsg(res.mensaje || 'Descuentos aplicados correctamente.');
      setImportacionData(null);
      setFile(null);
    } catch (err: any) {
      alert(err.message || 'Error al aplicar descuentos a la planilla.');
    } finally {
      setApplying(false);
    }
  };

  return (
    <div className="page-container">
      {/* Selector y Carga */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.25rem', marginBottom: '1.25rem' }}>Importar Descuentos desde Excel</h2>

        {successMsg && (
          <div style={{ background: 'rgba(16, 185, 129, 0.15)', border: '1px solid var(--emerald-500)', padding: '0.85rem', borderRadius: 'var(--radius-md)', color: '#34D399', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <CheckCircle2 size={18} />
            <span>{successMsg}</span>
          </div>
        )}

        <form onSubmit={handleUpload}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem', marginBottom: '1.5rem' }}>
            <div className="form-group">
              <label className="form-label">Planilla Destino (Solo versiones abiertas)</label>
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

            <div className="form-group">
              <label className="form-label">Concepto de Descuento</label>
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

          {/* Zona de Subida de Archivo */}
          <div style={{
            border: '2px dashed #CBD5E1',
            borderRadius: 'var(--radius-lg)',
            padding: '2rem',
            textAlign: 'center',
            background: '#F8FAFC',
            marginBottom: '1.5rem',
            position: 'relative',
          }}>
            <UploadCloud size={40} style={{ color: 'var(--teal-500)', marginBottom: '0.75rem' }} />
            <h3 style={{ fontSize: '1.05rem', marginBottom: '0.25rem' }}>
              {file ? file.name : 'Arrastra o selecciona el archivo Excel (.xlsx)'}
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              El sistema identificará automáticamente las columnas de DNI y Monto.
            </p>
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={handleFileChange}
              style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer' }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button type="submit" className="btn btn-primary" disabled={!file || !selectedVersionId || uploading}>
              {uploading ? 'Procesando archivo...' : 'Analizar y Previsualizar'}
            </button>
          </div>
        </form>
      </div>

      {/* Previsualización de Registros Clasificados */}
      {importacionData && (
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
            <div>
              <h2 style={{ fontSize: '1.25rem', marginBottom: '0.25rem' }}>Registros Extraídos</h2>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                {importacionData.resumen.archivo_nombre} • {importacionData.filas.length} filas detectadas
              </span>
            </div>

            {/* Modalidad y Botón de Aplicar */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'var(--bg-input)', padding: '0.25rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <button
                  type="button"
                  onClick={() => setModalidad('ACTUALIZAR')}
                  className={`btn btn-sm ${modalidad === 'ACTUALIZAR' ? 'btn-primary' : 'btn-ghost'}`}
                >
                  ACTUALIZAR (Solo seleccionadas)
                </button>
                <button
                  type="button"
                  onClick={() => setModalidad('REEMPLAZAR')}
                  className={`btn btn-sm ${modalidad === 'REEMPLAZAR' ? 'btn-danger' : 'btn-ghost'}`}
                >
                  REEMPLAZAR (Limpia y aplica)
                </button>
              </div>

              <button onClick={handleAplicar} disabled={applying} className="btn btn-success">
                {applying ? 'Aplicando...' : 'Aplicar a Planilla'}
              </button>
            </div>
          </div>

          {/* Grilla Clasificada */}
          <div className="table-container" style={{ maxHeight: '55vh' }}>
            <table className="table" style={{ fontSize: '0.8rem' }}>
              <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
                <tr>
                  <th style={{ width: 40 }}>Sel.</th>
                  <th>Fila</th>
                  <th>DNI Original</th>
                  <th>Nombre en Archivo</th>
                  <th style={{ textAlign: 'right' }}>Monto</th>
                  <th>Estado DNI</th>
                  <th>Trabajador Vinculado</th>
                  <th>Observación</th>
                </tr>
              </thead>
              <tbody>
                {importacionData.filas.map((f: any) => {
                  const isSelectable = f.estado === 'IDENTIFICADO' || f.estado === 'REVISAR';
                  return (
                    <tr key={f.fila} style={{ opacity: f.seleccionado ? 1 : 0.6 }}>
                      <td>
                        <button
                          type="button"
                          onClick={() => handleToggleFila(f.fila, f.seleccionado)}
                          className="btn btn-ghost btn-sm"
                          style={{ padding: '0.2rem' }}
                          disabled={!isSelectable}
                        >
                          {f.seleccionado ? (
                            <CheckSquare size={16} style={{ color: 'var(--teal-500)' }} />
                          ) : (
                            <Square size={16} style={{ color: 'var(--text-muted)' }} />
                          )}
                        </button>
                      </td>
                      <td style={{ color: 'var(--text-muted)' }}>{f.fila}</td>
                      <td className="mono-amount">{f.dni_original || '—'}</td>
                      <td>{f.nombre_original || '—'}</td>
                      <td className="mono-amount" style={{ textAlign: 'right', fontWeight: 600 }}>
                        S/ {Number(f.monto_validado || f.monto_original || 0).toFixed(2)}
                      </td>
                      <td>
                        <span className={`badge ${
                          f.estado === 'IDENTIFICADO' ? 'badge-emerald' :
                          f.estado === 'REVISAR' ? 'badge-amber' :
                          f.estado === 'DNI_DUPLICADO' ? 'badge-amber' : 'badge-crimson'
                        }`}>
                          {f.estado}
                        </span>
                      </td>
                      <td>{f.trabajador_apellidos ? `${f.trabajador_apellidos}, ${f.trabajador_nombres}` : '—'}</td>
                      <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{f.observacion || '—'}</td>
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
