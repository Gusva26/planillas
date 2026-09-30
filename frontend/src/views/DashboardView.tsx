import React, { useEffect, useState } from 'react';
import { apiRequest } from '../api/client';
import { DashboardSummary } from '../types';
import { 
  Users, 
  Building2, 
  AlertTriangle, 
  ArrowUpRight, 
  FileSpreadsheet, 
  CheckCircle2, 
  Clock, 
  DownloadCloud 
} from 'lucide-react';

interface DashboardViewProps {
  onNavigate: (tab: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigate }) => {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const res = await apiRequest<DashboardSummary>('/api/reportes/dashboard');
        setData(res);
      } catch (err) {
        console.error('Error fetching dashboard summary:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchSummary();
  }, []);

  const formatMoney = (val?: number) => {
    return Number(val || 0).toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  const getMonthName = (m: number) => {
    const months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre'];
    return months[m - 1] || `Mes ${m}`;
  };

  if (loading) {
    return (
      <div className="page-container" style={{ textAlign: 'center', padding: '4rem' }}>
        <p>Cargando indicadores institucionales...</p>
      </div>
    );
  }

  return (
    <div className="page-container">
      {/* Alerta de Netos Negativos */}
      {data && data.alertas_neto_negativo > 0 && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid var(--crimson-500)',
          borderRadius: 'var(--radius-lg)',
          padding: '1.25rem 1.5rem',
          marginBottom: '2rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 4px 20px var(--crimson-glow)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ padding: '0.6rem', borderRadius: 'var(--radius-md)', background: 'rgba(239, 68, 68, 0.2)', color: '#EF4444' }}>
              <AlertTriangle size={24} />
            </div>
            <div>
              <h3 style={{ fontSize: '1rem', color: '#F87171', margin: 0 }}>
                {data.alertas_neto_negativo} Alerta(s) de Líquido Neto Negativo
              </h3>
              <p style={{ fontSize: '0.825rem', color: '#FECACA', margin: 0 }}>
                Existen trabajadores con descuentos superiores al ingreso en planillas abiertas. Deben corregirse antes del cierre formal.
              </p>
            </div>
          </div>
          <button onClick={() => onNavigate('planillas')} className="btn btn-danger btn-sm">
            Revisar Planilla
          </button>
        </div>
      )}

      {/* KPI Counters */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem', marginBottom: '2.5rem' }}>
        {/* Personal Activo */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <span style={{ fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Personal Activo en Maestro</span>
            <div style={{ padding: '0.5rem', borderRadius: 'var(--radius-md)', background: 'rgba(20, 184, 166, 0.15)', color: 'var(--teal-500)' }}>
              <Users size={20} />
            </div>
          </div>
          <div style={{ fontSize: '2.25rem', fontWeight: 800, color: '#0F172A', fontFamily: 'var(--font-heading)' }}>
            {data?.trabajadores_activos ?? 0}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--teal-500)' }}>
            <span>II.EE. y Sede central</span>
          </div>
        </div>

        {/* Instituciones Educativas */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <span style={{ fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Instituciones Registradas</span>
            <div style={{ padding: '0.5rem', borderRadius: 'var(--radius-md)', background: 'rgba(99, 102, 241, 0.15)', color: 'var(--indigo-500)' }}>
              <Building2 size={20} />
            </div>
          </div>
          <div style={{ fontSize: '2.25rem', fontWeight: 800, color: '#0F172A', fontFamily: 'var(--font-heading)' }}>
            {data?.instituciones_activas ?? 0}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            <span>Ámbito provincial Chepén</span>
          </div>
        </div>

        {/* Masa Salarial Neta Consolidada */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <span style={{ fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Masa Salarial Activa</span>
            <div style={{ padding: '0.5rem', borderRadius: 'var(--radius-md)', background: 'rgba(16, 185, 129, 0.15)', color: 'var(--emerald-500)' }}>
              <FileSpreadsheet size={20} />
            </div>
          </div>
          <div className="mono-amount" style={{ fontSize: '1.85rem', fontWeight: 800, color: '#0F172A' }}>
            S/ {formatMoney(((data?.iiee?.total_neto || 0) + (data?.sede?.total_neto || 0)))}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--emerald-500)' }}>
            <span>Suma de líquidos de últimas versiones</span>
          </div>
        </div>
      </div>

      {/* Tarjetas de Planillas del Mes */}
      <h2 style={{ fontSize: '1.25rem', marginBottom: '1.25rem' }}>Últimas Planillas Generadas</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '1.5rem', marginBottom: '2.5rem' }}>
        {/* II.EE. */}
        <div className="card card-interactive" onClick={() => onNavigate('planillas')}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <div>
              <span className="badge badge-indigo">Instituciones Educativas (II.EE.)</span>
              <h3 style={{ fontSize: '1.35rem', marginTop: '0.5rem', marginBottom: '0.2rem' }}>
                {data?.iiee ? `${getMonthName(data.iiee.mes)} ${data.iiee.anio}` : 'Sin planillas registradas'}
              </h3>
              {data?.iiee && (
                <span style={{ fontSize: '0.775rem', color: 'var(--text-muted)' }}>
                  Versión {data.iiee.numero} • {data.iiee.total_trabajadores} trabajadores
                </span>
              )}
            </div>
            {data?.iiee?.estado === 'CERRADA' ? (
              <span className="badge badge-emerald"><CheckCircle2 size={12} /> CERRADA</span>
            ) : (
              <span className="badge badge-amber"><Clock size={12} /> EN EDICIÓN</span>
            )}
          </div>

          {data?.iiee ? (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', background: '#F8FAFC', border: '1px solid #E2E8F0', padding: '1rem', borderRadius: 'var(--radius-md)' }}>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Importe Bruto</span>
                <div className="mono-amount" style={{ fontSize: '0.95rem', color: 'var(--text-primary)' }}>S/ {formatMoney(data.iiee.total_importe)}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Descuentos</span>
                <div className="mono-amount" style={{ fontSize: '0.95rem', color: '#DC2626' }}>-S/ {formatMoney(data.iiee.total_descuentos)}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Líquido Neto</span>
                <div className="mono-amount" style={{ fontSize: '1rem', color: '#1D4ED8', fontWeight: 700 }}>S/ {formatMoney(data.iiee.total_neto)}</div>
              </div>
            </div>
          ) : (
            <p style={{ fontSize: '0.85rem' }}>No hay planillas de II.EE. registradas. Puedes crear la primera en la sección Planillas.</p>
          )}

          <div style={{ marginTop: '1.25rem', display: 'flex', justifyContent: 'flex-end' }}>
            <span style={{ fontSize: '0.825rem', color: 'var(--teal-500)', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
              Abrir Planilla II.EE. <ArrowUpRight size={16} />
            </span>
          </div>
        </div>

        {/* SEDE UGEL */}
        <div className="card card-interactive" onClick={() => onNavigate('planillas')}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <div>
              <span className="badge badge-teal">Sede Central UGEL Chepén</span>
              <h3 style={{ fontSize: '1.35rem', marginTop: '0.5rem', marginBottom: '0.2rem' }}>
                {data?.sede ? `${getMonthName(data.sede.mes)} ${data.sede.anio}` : 'Sin planillas registradas'}
              </h3>
              {data?.sede && (
                <span style={{ fontSize: '0.775rem', color: 'var(--text-muted)' }}>
                  Versión {data.sede.numero} • {data.sede.total_trabajadores} trabajadores
                </span>
              )}
            </div>
            {data?.sede?.estado === 'CERRADA' ? (
              <span className="badge badge-emerald"><CheckCircle2 size={12} /> CERRADA</span>
            ) : (
              <span className="badge badge-amber"><Clock size={12} /> EN EDICIÓN</span>
            )}
          </div>

          {data?.sede ? (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', background: '#F8FAFC', border: '1px solid #E2E8F0', padding: '1rem', borderRadius: 'var(--radius-md)' }}>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Importe Bruto</span>
                <div className="mono-amount" style={{ fontSize: '0.95rem', color: 'var(--text-primary)' }}>S/ {formatMoney(data.sede.total_importe)}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Descuentos</span>
                <div className="mono-amount" style={{ fontSize: '0.95rem', color: '#DC2626' }}>-S/ {formatMoney(data.sede.total_descuentos)}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Líquido Neto</span>
                <div className="mono-amount" style={{ fontSize: '1rem', color: '#1D4ED8', fontWeight: 700 }}>S/ {formatMoney(data.sede.total_neto)}</div>
              </div>
            </div>
          ) : (
            <p style={{ fontSize: '0.85rem' }}>No hay planillas de Sede registradas. Puedes crear la primera en la sección Planillas.</p>
          )}

          <div style={{ marginTop: '1.25rem', display: 'flex', justifyContent: 'flex-end' }}>
            <span style={{ fontSize: '0.825rem', color: 'var(--teal-500)', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
              Abrir Planilla Sede <ArrowUpRight size={16} />
            </span>
          </div>
        </div>
      </div>

      {/* Accesos Rápidos */}
      <h2 style={{ fontSize: '1.25rem', marginBottom: '1.25rem' }}>Acciones Rápidas</h2>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
        <button onClick={() => onNavigate('personal')} className="btn btn-secondary" style={{ padding: '1rem', justifyContent: 'flex-start' }}>
          <Users size={18} style={{ color: 'var(--teal-500)' }} />
          <span>Gestionar Personal</span>
        </button>
        <button onClick={() => onNavigate('importaciones')} className="btn btn-secondary" style={{ padding: '1rem', justifyContent: 'flex-start' }}>
          <DownloadCloud size={18} style={{ color: 'var(--indigo-500)' }} />
          <span>Importar Descuentos Excel</span>
        </button>
        <button onClick={() => onNavigate('documentos')} className="btn btn-secondary" style={{ padding: '1rem', justifyContent: 'flex-start' }}>
          <FileSpreadsheet size={18} style={{ color: 'var(--emerald-500)' }} />
          <span>Emitir Boletas y Planilla</span>
        </button>
      </div>
    </div>
  );
};
