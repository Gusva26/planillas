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
  UploadCloud,
  FileText,
  BarChart3,
  TrendingUp,
  CreditCard,
  RefreshCw,
  Landmark
} from 'lucide-react';

interface DashboardViewProps {
  onNavigate: (tab: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigate }) => {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchSummary = async () => {
    try {
      const res = await apiRequest<DashboardSummary>('/api/reportes/dashboard');
      setData(res);
    } catch (err) {
      console.error('Error fetching dashboard summary:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchSummary();
  };

  const formatMoney = (val?: number) => {
    return Number(val || 0).toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  const getMonthName = (m: number) => {
    const months = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre'];
    return months[m - 1] || `Mes ${m}`;
  };

  if (loading) {
    return (
      <div className="page-container" style={{ textAlign: 'center', padding: '5rem 2rem' }}>
        <div style={{
          width: 44,
          height: 44,
          border: '3px solid #E2E8F0',
          borderTopColor: '#2563EB',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          margin: '0 auto 1.25rem',
        }} />
        <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
        <p style={{ color: '#64748B', fontSize: '0.9rem', fontWeight: 500 }}>
          Sincronizando indicadores institucionales con PostgreSQL...
        </p>
      </div>
    );
  }

  const masaBrutaTotal = (data?.iiee?.total_importe || 0) + (data?.sede?.total_importe || 0);
  const totalDescuentos = (data?.iiee?.total_descuentos || 0) + (data?.sede?.total_descuentos || 0);
  const masaNetaTotal = (data?.iiee?.total_neto || 0) + (data?.sede?.total_neto || 0);

  return (
    <div className="page-container">
      {/* Encabezado del Dashboard con Acción de Recarga */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
        marginBottom: '1.75rem'
      }}>
        <div>
          <h2 style={{ fontSize: '1.35rem', color: '#0F172A', fontWeight: 800, margin: 0, letterSpacing: '-0.02em' }}>
            Tablero de Control CAFAE
          </h2>
          <p style={{ fontSize: '0.85rem', color: '#64748B', margin: '0.2rem 0 0' }}>
            Consolidado general de nómina, retenciones de ley y estado mensual de planillas.
          </p>
        </div>

        <button 
          onClick={handleRefresh}
          className="btn btn-secondary btn-sm"
          disabled={refreshing}
          style={{ gap: '0.45rem' }}
          title="Actualizar datos en tiempo real"
        >
          <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} style={{ color: '#2563EB' }} />
          <span>{refreshing ? 'Actualizando...' : 'Actualizar Métricas'}</span>
        </button>
      </div>

      {/* Alerta Destacada de Netos Negativos */}
      {data && data.alertas_neto_negativo > 0 && (
        <div style={{
          background: '#FEF2F2',
          border: '1.5px solid #FCA5A5',
          borderRadius: 'var(--radius-lg)',
          padding: '1.25rem 1.5rem',
          marginBottom: '2rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
          boxShadow: '0 4px 12px rgba(239, 68, 68, 0.08)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{
              padding: '0.65rem',
              borderRadius: 'var(--radius-md)',
              background: '#FEE2E2',
              color: '#DC2626',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '1px solid #FECACA'
            }}>
              <AlertTriangle size={24} />
            </div>
            <div>
              <h3 style={{ fontSize: '0.975rem', color: '#991B1B', margin: 0, fontWeight: 700 }}>
                {data.alertas_neto_negativo} Alerta(s) de Líquido Neto Negativo
              </h3>
              <p style={{ fontSize: '0.825rem', color: '#B91C1C', margin: '0.2rem 0 0' }}>
                Existen servidores públicos con descuentos mayores al haber disponible. Deben subsanarse antes del cierre formal de planilla.
              </p>
            </div>
          </div>
          <button 
            onClick={() => onNavigate('planillas')} 
            className="btn btn-danger btn-sm"
            style={{ fontWeight: 700, padding: '0.5rem 1.1rem' }}
          >
            Auditar y Corregir Planilla
          </button>
        </div>
      )}

      {/* Grid de Métricas Principales (KPIs) */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
        gap: '1.25rem',
        marginBottom: '2.25rem'
      }}>
        {/* Personal Activo */}
        <div className="kpi-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Personal Activo
            </span>
            <div className="kpi-icon-wrap" style={{ background: '#EFF6FF', color: '#1D4ED8', border: '1px solid #DBEAFE' }}>
              <Users size={20} />
            </div>
          </div>
          <div style={{ fontSize: '2.1rem', fontWeight: 800, color: '#0F172A', fontFamily: 'var(--font-heading)', lineHeight: 1.1 }}>
            {data?.trabajadores_activos ?? 0}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.65rem', fontSize: '0.775rem', color: '#059669', fontWeight: 600 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#10B981' }} />
            <span>Maestro Oficial II.EE. y Sede Central</span>
          </div>
        </div>

        {/* Instituciones Educativas */}
        <div className="kpi-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Instituciones Registradas
            </span>
            <div className="kpi-icon-wrap" style={{ background: '#F0F9FF', color: '#0284C7', border: '1px solid #BAE6FD' }}>
              <Building2 size={20} />
            </div>
          </div>
          <div style={{ fontSize: '2.1rem', fontWeight: 800, color: '#0F172A', fontFamily: 'var(--font-heading)', lineHeight: 1.1 }}>
            {data?.instituciones_activas ?? 0}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.65rem', fontSize: '0.775rem', color: '#64748B' }}>
            <Landmark size={13} style={{ color: '#0284C7' }} />
            <span>Ámbito provincial UGEL Chepén</span>
          </div>
        </div>

        {/* Masa Salarial Neta Consolidada */}
        <div className="kpi-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Masa Líquida Neta
            </span>
            <div className="kpi-icon-wrap" style={{ background: '#ECFDF5', color: '#059669', border: '1px solid #A7F3D0' }}>
              <FileSpreadsheet size={20} />
            </div>
          </div>
          <div className="mono-amount" style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0F172A', lineHeight: 1.1 }}>
            S/ {formatMoney(masaNetaTotal)}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.65rem', fontSize: '0.775rem', color: '#059669', fontWeight: 600 }}>
            <TrendingUp size={13} />
            <span>Suma de líquidos versión activa</span>
          </div>
        </div>

        {/* Retenciones Totales */}
        <div className="kpi-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Retenciones & Descuentos
            </span>
            <div className="kpi-icon-wrap" style={{ background: '#FEF2F2', color: '#DC2626', border: '1px solid #FECACA' }}>
              <CreditCard size={20} />
            </div>
          </div>
          <div className="mono-amount" style={{ fontSize: '1.75rem', fontWeight: 800, color: '#DC2626', lineHeight: 1.1 }}>
            S/ {formatMoney(totalDescuentos)}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.65rem', fontSize: '0.775rem', color: '#64748B' }}>
            <span>Bancos, sindicatos y judiciales</span>
          </div>
        </div>
      </div>

      {/* Tarjetas de Planillas del Mes en Curso (II.EE. y Sede Central) */}
      <div style={{ marginBottom: '2.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.15rem' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', color: '#0F172A', fontWeight: 700, margin: 0 }}>
              Estado de las Planillas del Mes
            </h3>
            <p style={{ fontSize: '0.825rem', color: '#64748B', margin: '0.15rem 0 0' }}>
              Versiones operativas en trámite para el personal docente, administrativo y de sede.
            </p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '1.5rem' }}>
          {/* II.EE. */}
          <div 
            className="card card-interactive" 
            onClick={() => onNavigate('planillas')}
            style={{
              padding: '1.5rem',
              borderRadius: 'var(--radius-lg)',
              border: '1.5px solid #E2E8F0',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between'
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
                <span className="badge badge-indigo">
                  Instituciones Educativas (II.EE.)
                </span>
                {data?.iiee?.estado === 'CERRADA' ? (
                  <span className="badge badge-emerald"><CheckCircle2 size={13} /> CERRADA</span>
                ) : (
                  <span className="badge badge-amber"><Clock size={13} /> EN EDICIÓN</span>
                )}
              </div>

              <h4 style={{ fontSize: '1.35rem', color: '#0F172A', marginBottom: '0.25rem', fontWeight: 800 }}>
                {data?.iiee ? `${getMonthName(data.iiee.mes)} ${data.iiee.anio}` : 'Sin planilla creada'}
              </h4>

              {data?.iiee && (
                <div style={{ fontSize: '0.8rem', color: '#64748B', marginBottom: '1.25rem' }}>
                  Versión N° <strong>{data.iiee.numero}</strong> • <strong>{data.iiee.total_trabajadores}</strong> servidores registrados
                </div>
              )}

              {data?.iiee ? (
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr 1fr',
                  gap: '0.85rem',
                  background: '#F8FAFC',
                  border: '1px solid #E2E8F0',
                  padding: '1rem',
                  borderRadius: 'var(--radius-md)',
                }}>
                  <div>
                    <span style={{ fontSize: '0.675rem', color: '#64748B', textTransform: 'uppercase', fontWeight: 600, display: 'block', marginBottom: '0.2rem' }}>
                      Importe Bruto
                    </span>
                    <div className="mono-amount" style={{ fontSize: '0.95rem', color: '#0F172A' }}>
                      S/ {formatMoney(data.iiee.total_importe)}
                    </div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.675rem', color: '#64748B', textTransform: 'uppercase', fontWeight: 600, display: 'block', marginBottom: '0.2rem' }}>
                      Descuentos
                    </span>
                    <div className="mono-amount" style={{ fontSize: '0.95rem', color: '#DC2626' }}>
                      -S/ {formatMoney(data.iiee.total_descuentos)}
                    </div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.675rem', color: '#64748B', textTransform: 'uppercase', fontWeight: 600, display: 'block', marginBottom: '0.2rem' }}>
                      Líquido Neto
                    </span>
                    <div className="mono-amount" style={{ fontSize: '1.05rem', color: '#1D4ED8', fontWeight: 700 }}>
                      S/ {formatMoney(data.iiee.total_neto)}
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ padding: '1.5rem', textAlign: 'center', background: '#F8FAFC', borderRadius: 'var(--radius-md)', border: '1px dashed #CBD5E1' }}>
                  <p style={{ fontSize: '0.85rem', color: '#64748B', margin: 0 }}>
                    No existe planilla de II.EE. para el mes en curso. Puedes crearla desde el módulo de Planillas.
                  </p>
                </div>
              )}
            </div>

            <div style={{ marginTop: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
              <span style={{ fontSize: '0.825rem', color: '#2563EB', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
                Gestionar Planilla II.EE. <ArrowUpRight size={16} />
              </span>
            </div>
          </div>

          {/* SEDE CENTRAL */}
          <div 
            className="card card-interactive" 
            onClick={() => onNavigate('planillas')}
            style={{
              padding: '1.5rem',
              borderRadius: 'var(--radius-lg)',
              border: '1.5px solid #E2E8F0',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between'
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
                <span className="badge badge-teal">
                  Sede Central UGEL Chepén
                </span>
                {data?.sede?.estado === 'CERRADA' ? (
                  <span className="badge badge-emerald"><CheckCircle2 size={13} /> CERRADA</span>
                ) : (
                  <span className="badge badge-amber"><Clock size={13} /> EN EDICIÓN</span>
                )}
              </div>

              <h4 style={{ fontSize: '1.35rem', color: '#0F172A', marginBottom: '0.25rem', fontWeight: 800 }}>
                {data?.sede ? `${getMonthName(data.sede.mes)} ${data.sede.anio}` : 'Sin planilla creada'}
              </h4>

              {data?.sede && (
                <div style={{ fontSize: '0.8rem', color: '#64748B', marginBottom: '1.25rem' }}>
                  Versión N° <strong>{data.sede.numero}</strong> • <strong>{data.sede.total_trabajadores}</strong> servidores registrados
                </div>
              )}

              {data?.sede ? (
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr 1fr',
                  gap: '0.85rem',
                  background: '#F8FAFC',
                  border: '1px solid #E2E8F0',
                  padding: '1rem',
                  borderRadius: 'var(--radius-md)',
                }}>
                  <div>
                    <span style={{ fontSize: '0.675rem', color: '#64748B', textTransform: 'uppercase', fontWeight: 600, display: 'block', marginBottom: '0.2rem' }}>
                      Importe Bruto
                    </span>
                    <div className="mono-amount" style={{ fontSize: '0.95rem', color: '#0F172A' }}>
                      S/ {formatMoney(data.sede.total_importe)}
                    </div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.675rem', color: '#64748B', textTransform: 'uppercase', fontWeight: 600, display: 'block', marginBottom: '0.2rem' }}>
                      Descuentos
                    </span>
                    <div className="mono-amount" style={{ fontSize: '0.95rem', color: '#DC2626' }}>
                      -S/ {formatMoney(data.sede.total_descuentos)}
                    </div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.675rem', color: '#64748B', textTransform: 'uppercase', fontWeight: 600, display: 'block', marginBottom: '0.2rem' }}>
                      Líquido Neto
                    </span>
                    <div className="mono-amount" style={{ fontSize: '1.05rem', color: '#1D4ED8', fontWeight: 700 }}>
                      S/ {formatMoney(data.sede.total_neto)}
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ padding: '1.5rem', textAlign: 'center', background: '#F8FAFC', borderRadius: 'var(--radius-md)', border: '1px dashed #CBD5E1' }}>
                  <p style={{ fontSize: '0.85rem', color: '#64748B', margin: 0 }}>
                    No existe planilla de Sede para el mes en curso. Puedes crearla desde el módulo de Planillas.
                  </p>
                </div>
              )}
            </div>

            <div style={{ marginTop: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
              <span style={{ fontSize: '0.825rem', color: '#2563EB', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
                Gestionar Planilla Sede <ArrowUpRight size={16} />
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Módulo de Accesos Directos Institucionales */}
      <div>
        <h3 style={{ fontSize: '1.15rem', color: '#0F172A', fontWeight: 700, marginBottom: '0.35rem' }}>
          Flujos y Accesos Rápidos
        </h3>
        <p style={{ fontSize: '0.825rem', color: '#64748B', marginBottom: '1.25rem' }}>
          Acceso inmediato a los procesos más frecuentes del ciclo de planilla.
        </p>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))',
          gap: '1rem',
        }}>
          <button 
            onClick={() => onNavigate('personal')} 
            className="card card-interactive"
            style={{
              padding: '1.15rem 1.25rem',
              display: 'flex',
              alignItems: 'center',
              gap: '1rem',
              textAlign: 'left',
              border: '1px solid #E2E8F0',
              background: '#FFFFFF',
            }}
          >
            <div style={{ padding: '0.65rem', borderRadius: 'var(--radius-md)', background: '#EFF6FF', color: '#1D4ED8' }}>
              <Users size={20} />
            </div>
            <div>
              <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#0F172A' }}>Maestro de Personal</div>
              <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '2px' }}>Filiación, cuentas y cargos</div>
            </div>
          </button>

          <button 
            onClick={() => onNavigate('importaciones')} 
            className="card card-interactive"
            style={{
              padding: '1.15rem 1.25rem',
              display: 'flex',
              alignItems: 'center',
              gap: '1rem',
              textAlign: 'left',
              border: '1px solid #E2E8F0',
              background: '#FFFFFF',
            }}
          >
            <div style={{ padding: '0.65rem', borderRadius: 'var(--radius-md)', background: '#F0F9FF', color: '#0284C7' }}>
              <UploadCloud size={20} />
            </div>
            <div>
              <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#0F172A' }}>Importar Archivo Excel</div>
              <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '2px' }}>Pichincha, Sullana y gremios</div>
            </div>
          </button>

          <button 
            onClick={() => onNavigate('documentos')} 
            className="card card-interactive"
            style={{
              padding: '1.15rem 1.25rem',
              display: 'flex',
              alignItems: 'center',
              gap: '1rem',
              textAlign: 'left',
              border: '1px solid #E2E8F0',
              background: '#FFFFFF',
            }}
          >
            <div style={{ padding: '0.65rem', borderRadius: 'var(--radius-md)', background: '#ECFDF5', color: '#059669' }}>
              <FileText size={20} />
            </div>
            <div>
              <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#0F172A' }}>Boletas y Archivos BN</div>
              <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '2px' }}>PDFs y telecrédito 041/341</div>
            </div>
          </button>

          <button 
            onClick={() => onNavigate('reportes')} 
            className="card card-interactive"
            style={{
              padding: '1.15rem 1.25rem',
              display: 'flex',
              alignItems: 'center',
              gap: '1rem',
              textAlign: 'left',
              border: '1px solid #E2E8F0',
              background: '#FFFFFF',
            }}
          >
            <div style={{ padding: '0.65rem', borderRadius: 'var(--radius-md)', background: '#EEF2FF', color: '#4F46E5' }}>
              <BarChart3 size={20} />
            </div>
            <div>
              <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#0F172A' }}>Reportes Oficiales</div>
              <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '2px' }}>Masa presupuestal y padrón</div>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};
