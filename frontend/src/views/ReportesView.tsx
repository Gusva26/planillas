import React, { useState, useEffect } from 'react';
import { apiRequest } from '../api/client';
import { PlanillaListItem } from '../types';
import { BarChart3, FileText, ChevronRight, Layers } from 'lucide-react';

export const ReportesView: React.FC = () => {
  const [planillas, setPlanillas] = useState<PlanillaListItem[]>([]);
  const [selectedVersionId, setSelectedVersionId] = useState<number | null>(null);
  const [selectedReporte, setSelectedReporte] = useState<string>('resumen-mensual');
  const [reportData, setReportData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const reportesList = [
    { id: 'resumen-mensual', title: '1. Resumen Mensual Consolidado' },
    { id: 'por-institucion', title: '2. Importe por Institución Educativa' },
    { id: 'por-meta', title: '3. Importe por Meta Presupuestaria' },
    { id: 'descuentos-por-entidad', title: '4. Descuentos por Entidad' },
    { id: 'general-descuentos', title: '5. General de Descuentos Detallado' },
    { id: 'licencias-sin-goce', title: '6. Licencias sin Goce de Haber' },
    { id: 'modalidad-pago', title: '7. Modalidad de Pago (Cuentas vs Cheques)' },
    { id: 'comparativo-anterior', title: '8. Comparativo con Mes Anterior' },
    { id: 'padron-alfabetico', title: '9. Padrón Alfabético Oficial' },
  ];

  useEffect(() => {
    const fetchPlanillas = async () => {
      try {
        const list = await apiRequest<PlanillaListItem[]>('/api/planillas');
        setPlanillas(list);
        if (list.length > 0) {
          setSelectedVersionId(list[0].version_id);
        }
      } catch (err) {
        console.error('Error fetching planillas:', err);
      }
    };
    fetchPlanillas();
  }, []);

  const loadReporte = async () => {
    if (!selectedVersionId || !selectedReporte) return;
    setLoading(true);
    try {
      const data = await apiRequest(`/api/reportes/${selectedReporte}/${selectedVersionId}`);
      setReportData(data);
    } catch (err: any) {
      alert(err.message || 'Error al obtener reporte.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReporte();
  }, [selectedVersionId, selectedReporte]);

  return (
    <div className="page-container">
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '2rem' }}>
        {/* Selector Lateral de Reportes */}
        <div>
          <div className="card" style={{ marginBottom: '1.5rem', padding: '1rem' }}>
            <label className="form-label" style={{ marginBottom: '0.5rem', display: 'block' }}>Planilla / Versión</label>
            <select
              className="form-select"
              value={selectedVersionId || ''}
              onChange={(e) => setSelectedVersionId(Number(e.target.value))}
            >
              {planillas.map((p) => (
                <option key={p.version_id} value={p.version_id}>
                  {p.tipo === 'IIEE' ? 'II.EE.' : 'SEDE'} · {p.anio}-{String(p.mes).padStart(2, '0')} (v{p.version_numero})
                </option>
              ))}
            </select>
          </div>

          <div className="card" style={{ padding: '0.75rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
            {reportesList.map((r) => {
              const isSelected = selectedReporte === r.id;
              return (
                <button
                  key={r.id}
                  onClick={() => setSelectedReporte(r.id)}
                  className="btn btn-ghost"
                  style={{
                    justifyContent: 'flex-start',
                    textAlign: 'left',
                    background: isSelected ? 'rgba(20, 184, 166, 0.15)' : 'transparent',
                    color: isSelected ? 'var(--teal-500)' : 'var(--text-secondary)',
                    fontWeight: isSelected ? 600 : 500,
                    padding: '0.75rem 0.85rem',
                  }}
                >
                  <FileText size={16} />
                  <span style={{ fontSize: '0.8rem', whiteSpace: 'normal' }}>{r.title}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Contenido del Reporte */}
        <div>
          <div className="card" style={{ minHeight: '500px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem' }}>
              <div>
                <h2 style={{ fontSize: '1.25rem', margin: 0 }}>
                  {reportesList.find((r) => r.id === selectedReporte)?.title}
                </h2>
                <span style={{ fontSize: '0.775rem', color: 'var(--text-muted)' }}>
                  Reporte oficial generado desde la versión exacta seleccionada
                </span>
              </div>
            </div>

            {loading ? (
              <div style={{ textAlign: 'center', padding: '4rem' }}>Cargando datos del reporte...</div>
            ) : !reportData ? (
              <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>Sin datos disponibles.</div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <pre style={{
                  background: '#F1F5F9',
                  border: '1px solid #E2E8F0',
                  padding: '1.25rem',
                  borderRadius: 'var(--radius-md)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.825rem',
                  color: '#0F172A',
                  maxHeight: '600px',
                  overflow: 'auto',
                }}>
                  {JSON.stringify(reportData, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
