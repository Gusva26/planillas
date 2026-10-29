import React, { useState, useEffect, useMemo } from 'react';
import { apiRequest } from '../api/client';
import { mensajeDeError } from '../api/errors';
import { PlanillaListItem } from '../types';
import { 
  BarChart3, 
  FileText, 
  Layers, 
  Users, 
  Building2, 
  Target, 
  CreditCard, 
  Receipt, 
  Clock, 
  Calendar, 
  ArrowUpDown, 
  Download, 
  Printer, 
  Search, 
  CheckCircle2, 
  AlertTriangle,
  ChevronRight,
  PieChart,
  Wallet,
  Landmark
} from 'lucide-react';

const MESES = [
  { num: 1, nombre: 'Enero' },
  { num: 2, nombre: 'Febrero' },
  { num: 3, nombre: 'Marzo' },
  { num: 4, nombre: 'Abril' },
  { num: 5, nombre: 'Mayo' },
  { num: 6, nombre: 'Junio' },
  { num: 7, nombre: 'Julio' },
  { num: 8, nombre: 'Agosto' },
  { num: 9, nombre: 'Setiembre' },
  { num: 10, nombre: 'Octubre' },
  { num: 11, nombre: 'Noviembre' },
  { num: 12, nombre: 'Diciembre' },
];

export const ReportesView: React.FC = () => {
  const [planillas, setPlanillas] = useState<PlanillaListItem[]>([]);
  const [tipoFiltro, setTipoFiltro] = useState<'IIEE' | 'SEDE'>('IIEE');
  const [selectedAnio, setSelectedAnio] = useState<number>(2026);
  const [selectedMes, setSelectedMes] = useState<number>(3);
  const [selectedVersionId, setSelectedVersionId] = useState<number | null>(null);
  const [selectedReporte, setSelectedReporte] = useState<string>('resumen-mensual');
  // Los 9 reportes devuelven formas distintas y su esquema todavía no está
  // publicado en el contrato del API (ver docs/11-contrato-api.md). Se tipará
  // por reporte cuando el backend exponga esos modelos.
  const [reportData, setReportData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const reportesCategorias = [
    {
      categoria: 'Consolidados y Presupuesto',
      items: [
        { id: 'resumen-mensual', title: '1. Resumen Mensual Consolidado', icon: BarChart3, desc: 'Masa salarial, descuentos y netos consolidados' },
        { id: 'por-institucion', title: '2. Importe por Institución Educativa', icon: Building2, desc: 'Distribución económica por cada I.E.' },
        { id: 'por-meta', title: '3. Hoja de Remuneraciones CAFAE', icon: Target, desc: 'Plantilla oficial de 4 columnas (Programas y Metas)' },
      ]
    },
    {
      categoria: 'Descuentos y Retenciones',
      items: [
        { id: 'descuentos-por-entidad', title: '4. Descuentos por Entidad', icon: Receipt, desc: 'Los 8 conceptos de descuento por entidad' },
        { id: 'general-descuentos', title: '5. Sábana General de Descuentos', icon: Layers, desc: 'Desglose nominal por cada trabajador' },
        { id: 'modalidad-pago', title: '6. Modalidad de Pago (Cuentas vs Cheques)', icon: Wallet, desc: 'Depósitos Multired y medios de pago' },
      ]
    },
    {
      categoria: 'Personal y Comparativas',
      items: [
        { id: 'padron-alfabetico', title: '7. Padrón Alfabético Oficial', icon: Users, desc: 'Nómina ordenada con cuentas y cargos' },
        { id: 'licencias-sin-goce', title: '8. Licencias sin Goce de Haber', icon: Clock, desc: 'Días no laborados y descuentos por 30avos' },
        { id: 'comparativo-anterior', title: '9. Comparativo Intermensual', icon: ArrowUpDown, desc: 'Variación respecto al periodo anterior' },
      ]
    }
  ];

  // Años únicos disponibles
  const aniosDisponibles = useMemo(() => {
    return Array.from(new Set([2026, ...planillas.map((p) => p.anio)])).sort((a, b) => b - a);
  }, [planillas]);

  // Planillas que coinciden con los filtros de Tipo, Año y Mes
  const matchingPlanillas = useMemo(() => {
    return planillas.filter((p) => p.tipo === tipoFiltro && p.anio === selectedAnio && p.mes === selectedMes);
  }, [planillas, tipoFiltro, selectedAnio, selectedMes]);

  useEffect(() => {
    const fetchPlanillas = async () => {
      try {
        const list = await apiRequest<PlanillaListItem[]>('/api/planillas');
        setPlanillas(list);
        if (list.length > 0) {
          // Inicializar con la planilla más reciente
          const first = list[0];
          setTipoFiltro(first.tipo);
          setSelectedAnio(first.anio);
          setSelectedMes(first.mes);
          setSelectedVersionId(first.version_id);
        }
      } catch (err) {
        console.error('Error fetching planillas:', err);
      }
    };
    fetchPlanillas();
  }, []);

  // Sincronizar selectedVersionId cada vez que cambien los filtros de Tipo, Año o Mes
  useEffect(() => {
    if (matchingPlanillas.length > 0) {
      // Si la versión actual no pertenece al grupo filtrado, seleccionar la primera
      const belongs = matchingPlanillas.some((p) => p.version_id === selectedVersionId);
      if (!belongs) {
        setSelectedVersionId(matchingPlanillas[0].version_id);
      }
    } else {
      setSelectedVersionId(null);
      setReportData(null);
    }
  }, [matchingPlanillas, selectedVersionId]);

  const loadReporte = async () => {
    if (!selectedVersionId || !selectedReporte) {
      setReportData(null);
      return;
    }
    setLoading(true);
    setSearchTerm('');
    try {
      const data = await apiRequest(`/api/reportes/${selectedReporte}/${selectedVersionId}`);
      setReportData(data);
    } catch (err) {
      alert(mensajeDeError(err, 'Error al obtener reporte.'));
      setReportData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReporte();
  }, [selectedVersionId, selectedReporte]);

  const selectedPlanillaInfo = useMemo(() => {
    return planillas.find((p) => p.version_id === selectedVersionId);
  }, [planillas, selectedVersionId]);

  const formatMoney = (val?: number | string | null) => {
    const num = Number(val || 0);
    return 'S/ ' + num.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  const formatMoneyNumber = (val?: number | string | null) => {
    if (val === null || val === undefined) return '-';
    const num = Number(val);
    if (isNaN(num)) return '-';
    return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  // Exportar reporte actual a CSV
  const handleExportCSV = () => {
    if (!reportData) return;
    let csvContent = '';
    const sep = ';';

    const getFilename = () => {
      const p = selectedPlanillaInfo;
      const pStr = p ? `${p.tipo}_${p.anio}_${p.mes}` : 'reporte';
      return `${selectedReporte}_${pStr}.csv`;
    };

    if (Array.isArray(reportData) && reportData.length > 0) {
      const headers = Object.keys(reportData[0]);
      csvContent = headers.join(sep) + '\n';
      reportData.forEach((row) => {
        csvContent += headers.map((h) => {
          let val = row[h];
          if (val === null || val === undefined) val = '';
          return `"${String(val).replace(/"/g, '""')}"`;
        }).join(sep) + '\n';
      });
    } else if (typeof reportData === 'object' && reportData !== null) {
      const keys = Object.keys(reportData);
      csvContent = 'Indicador;Valor\n';
      keys.forEach((k) => {
        csvContent += `"${k}";"${String(reportData[k])}"\n`;
      });
    }

    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', getFilename());
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="page-container">
      {/* Barra Superior de Contexto y Filtros Avanzados */}
      <div className="card" style={{ marginBottom: '1.5rem', padding: '1.25rem 1.5rem', background: '#FFFFFF', border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-sm)' }}>
        
        {/* Fila 1: Título y Acciones de Exportación */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ 
              width: '44px', 
              height: '44px', 
              borderRadius: 'var(--radius-md)', 
              background: 'linear-gradient(135deg, #1D4ED8, #0284C7)', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              color: '#FFFFFF' 
            }}>
              <BarChart3 size={24} />
            </div>
            <div>
              <h1 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700, color: 'var(--text-primary)' }}>
                Reportes y Cuadros Estadísticos Oficiales
              </h1>
              <span style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                Consultas auditadas por versión estricta de planilla sin mezcla de históricos · UGEL Chepén
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <button onClick={handleExportCSV} disabled={!reportData} className="btn btn-secondary" title="Exportar reporte a archivo CSV / Excel">
              <Download size={16} />
              <span>Exportar Excel</span>
            </button>

            <button onClick={handlePrint} disabled={!reportData} className="btn btn-secondary" title="Imprimir vista del reporte">
              <Printer size={16} />
              <span>Imprimir</span>
            </button>
          </div>
        </div>

        {/* Fila 2: Panel de Filtros Principales (Tipo IIEE vs SEDE, Año, Mes, Versión) */}
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between', 
          background: '#F8FAFC', 
          padding: '0.85rem 1.25rem', 
          borderRadius: 'var(--radius-md)', 
          border: '1px solid var(--border-subtle)',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          {/* 1. Selector de Ámbito: IIEE vs SEDE */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Ámbito:
            </span>
            <div className="segmented-control">
              <button
                type="button"
                onClick={() => setTipoFiltro('IIEE')}
                className={`segmented-item ${tipoFiltro === 'IIEE' ? 'active' : ''}`}
              >
                <Building2 size={15} />
                <span>II.EE.</span>
              </button>
              <button
                type="button"
                onClick={() => setTipoFiltro('SEDE')}
                className={`segmented-item ${tipoFiltro === 'SEDE' ? 'active' : ''}`}
              >
                <Landmark size={15} />
                <span>Sede Central</span>
              </button>
            </div>
          </div>

          {/* 2. Selector de Año */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Año:
            </span>
            <select
              className="form-select"
              style={{ width: '100px', fontWeight: 600, background: '#FFFFFF' }}
              value={selectedAnio}
              onChange={(e) => setSelectedAnio(Number(e.target.value))}
            >
              {aniosDisponibles.map((a) => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
          </div>

          {/* 3. Selector de Mes */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Mes:
            </span>
            <select
              className="form-select"
              style={{ minWidth: '160px', fontWeight: 600, background: '#FFFFFF' }}
              value={selectedMes}
              onChange={(e) => setSelectedMes(Number(e.target.value))}
            >
              {MESES.map((m) => {
                const hasData = planillas.some((p) => p.tipo === tipoFiltro && p.anio === selectedAnio && p.mes === m.num);
                return (
                  <option key={m.num} value={m.num}>
                    {m.nombre} {hasData ? '●' : '(Sin planilla)'}
                  </option>
                );
              })}
            </select>
          </div>

          {/* 4. Selector de Versión (si hay varias) */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Versión:
            </span>
            {matchingPlanillas.length > 0 ? (
              <select
                className="form-select"
                style={{ minWidth: '170px', fontWeight: 600, background: '#FFFFFF' }}
                value={selectedVersionId || ''}
                onChange={(e) => setSelectedVersionId(Number(e.target.value))}
              >
                {matchingPlanillas.map((p) => (
                  <option key={p.version_id} value={p.version_id}>
                    v{p.version_numero} ({p.version_estado})
                  </option>
                ))}
              </select>
            ) : (
              <span className="badge badge-warning" style={{ fontWeight: 600 }}>
                No disponible
              </span>
            )}
          </div>
        </div>

        {/* Fila 3: Chip Informativo de la Planilla Seleccionada */}
        {selectedPlanillaInfo ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border-subtle)', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Planilla Seleccionada:
            </span>
            <span className="badge badge-info" style={{ fontWeight: 600 }}>
              {selectedPlanillaInfo.tipo === 'IIEE' ? 'Instituciones Educativas' : 'Sede Central UGEL'}
            </span>
            <span className="badge" style={{ background: '#F1F5F9', color: '#334155', fontWeight: 600 }}>
              {MESES.find(m => m.num === selectedPlanillaInfo.mes)?.nombre} {selectedPlanillaInfo.anio}
            </span>
            <span className={`badge ${selectedPlanillaInfo.version_estado === 'CERRADA' ? 'badge-success' : selectedPlanillaInfo.version_estado === 'REVISION' ? 'badge-warning' : 'badge-neutral'}`} style={{ fontWeight: 600 }}>
              {selectedPlanillaInfo.version_estado === 'CERRADA' ? '● CERRADA FORMAL' : selectedPlanillaInfo.version_estado === 'REVISION' ? '▲ EN REVISIÓN' : '○ BORRADOR'}
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginLeft: 'auto' }}>
              Personal: <strong>{selectedPlanillaInfo.total_trabajadores || '-'}</strong> | Masa Bruta: <strong>{formatMoney(selectedPlanillaInfo.total_importe)}</strong> | Líquido Neto: <strong>{formatMoney(selectedPlanillaInfo.total_neto)}</strong>
            </span>
          </div>
        ) : (
          <div style={{ marginTop: '0.85rem', padding: '0.65rem 1rem', background: '#FEF3C7', borderRadius: 'var(--radius-sm)', border: '1px solid #FDE68A', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#92400E', fontSize: '0.825rem' }}>
              <AlertTriangle size={16} />
              <span>No existe planilla registrada para <strong>{tipoFiltro === 'IIEE' ? 'II.EE.' : 'SEDE'}</strong> en <strong>{MESES.find(m => m.num === selectedMes)?.nombre} {selectedAnio}</strong>.</span>
            </div>
            <div style={{ display: 'flex', gap: '0.35rem' }}>
              <span style={{ fontSize: '0.75rem', color: '#92400E', alignSelf: 'center' }}>Meses con datos:</span>
              {[1, 2, 3, 4, 5].map((mNum) => (
                <button
                  key={mNum}
                  type="button"
                  onClick={() => setSelectedMes(mNum)}
                  className="btn btn-ghost"
                  style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem', background: '#FFFFFF', color: '#92400E', border: '1px solid #FDE68A', borderRadius: 'var(--radius-sm)' }}
                >
                  {MESES.find(m => m.num === mNum)?.nombre.substring(0, 3)}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Grid Principal: Menú Lateral + Tablero Central */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '1.5rem', alignItems: 'start' }}>
        
        {/* Panel Lateral de Reportes */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {reportesCategorias.map((cat, idx) => (
            <div key={idx} className="card" style={{ padding: '0.875rem', background: '#FFFFFF', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem', paddingLeft: '0.5rem' }}>
                {cat.categoria}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                {cat.items.map((r) => {
                  const isSelected = selectedReporte === r.id;
                  const Icon = r.icon;
                  return (
                    <button
                      key={r.id}
                      onClick={() => setSelectedReporte(r.id)}
                      className="btn"
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'flex-start',
                        gap: '0.75rem',
                        textAlign: 'left',
                        padding: '0.75rem 0.85rem',
                        borderRadius: 'var(--radius-md)',
                        background: isSelected ? 'linear-gradient(90deg, rgba(2, 132, 199, 0.12), rgba(29, 78, 216, 0.08))' : 'transparent',
                        color: isSelected ? 'var(--primary-700)' : 'var(--text-secondary)',
                        border: isSelected ? '1px solid rgba(2, 132, 199, 0.35)' : '1px solid transparent',
                        fontWeight: isSelected ? 600 : 500,
                        transition: 'var(--transition-fast)',
                        boxShadow: isSelected ? '0 1px 3px rgba(2, 132, 199, 0.1)' : 'none',
                      }}
                    >
                      <div style={{ 
                        color: isSelected ? 'var(--primary-700)' : 'var(--text-muted)',
                        display: 'flex',
                        alignItems: 'center'
                      }}>
                        <Icon size={18} />
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
                        <span style={{ fontSize: '0.825rem', lineHeight: '1.2' }}>{r.title}</span>
                        <span style={{ fontSize: '0.675rem', color: isSelected ? 'var(--teal-600)' : 'var(--text-muted)', marginTop: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {r.desc}
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Panel Central del Reporte */}
        <div className="card" style={{ minHeight: '620px', padding: '1.75rem', background: '#FFFFFF', border: '1px solid var(--border-subtle)', boxShadow: 'var(--shadow-sm)' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '6rem 2rem', color: 'var(--text-muted)' }}>
              <div style={{ width: '40px', height: '40px', border: '3px solid #E2E8F0', borderTopColor: 'var(--teal-500)', borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 1.5rem' }} />
              <p style={{ fontWeight: 500, fontSize: '0.95rem' }}>Generando reporte y calculando agregaciones oficiales...</p>
            </div>
          ) : !reportData ? (
            <div style={{ textAlign: 'center', padding: '6rem 2rem', color: 'var(--text-muted)' }}>
              <AlertTriangle size={48} style={{ color: 'var(--amber-500)', opacity: 0.8, marginBottom: '1rem' }} />
              <h3 style={{ fontSize: '1.1rem', color: 'var(--text-primary)', marginBottom: '0.5rem' }}>Sin información para esta versión</h3>
              <p style={{ fontSize: '0.85rem', maxWidth: '400px', margin: '0 auto' }}>No se encontraron registros computados para el tipo de reporte y versión seleccionada.</p>
            </div>
          ) : (
            <div>
              {/* Encabezado del Reporte Específico */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
                <div>
                  <h2 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 700, color: 'var(--text-primary)' }}>
                    {reportesCategorias.flatMap(c => c.items).find(i => i.id === selectedReporte)?.title}
                  </h2>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {reportesCategorias.flatMap(c => c.items).find(i => i.id === selectedReporte)?.desc}
                  </span>
                </div>

                {/* Filtro en vivo para vistas tabulares */}
                {Array.isArray(reportData) && reportData.length > 5 && (
                  <div style={{ position: 'relative', width: '260px' }}>
                    <Search size={16} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                    <input
                      type="text"
                      className="form-input"
                      style={{ paddingLeft: '2.25rem', height: '36px', fontSize: '0.8rem' }}
                      placeholder="Filtrar registros..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                    />
                  </div>
                )}
              </div>

              {/* RENDERIZADO VISUAL SEGÚN EL REPORTE SELECCIONADO */}

              {/* REPORTE 1: RESUMEN MENSUAL CONSOLIDADO */}
              {selectedReporte === 'resumen-mensual' && (
                <div>
                  {/* Tarjetas KPI Superiores */}
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
                    <div className="card" style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', padding: '1.25rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Personal</span>
                        <div style={{ padding: '0.4rem', borderRadius: 'var(--radius-sm)', background: 'rgba(29, 78, 216, 0.1)', color: 'var(--primary-700)' }}>
                          <Users size={18} />
                        </div>
                      </div>
                      <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                        {reportData.total_personas}
                      </div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Trabajadores en nómina</span>
                    </div>

                    <div className="card" style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', padding: '1.25rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Importe Bruto</span>
                        <div style={{ padding: '0.4rem', borderRadius: 'var(--radius-sm)', background: 'rgba(5, 150, 105, 0.1)', color: 'var(--emerald-600)' }}>
                          <CreditCard size={18} />
                        </div>
                      </div>
                      <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--emerald-600)', fontFamily: 'var(--font-mono)' }}>
                        {formatMoney(reportData.total_importe)}
                      </div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Masa salarial asignada</span>
                    </div>

                    <div className="card" style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', padding: '1.25rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Descuentos</span>
                        <div style={{ padding: '0.4rem', borderRadius: 'var(--radius-sm)', background: 'rgba(217, 119, 6, 0.1)', color: 'var(--amber-500)' }}>
                          <Receipt size={18} />
                        </div>
                      </div>
                      <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--amber-500)', fontFamily: 'var(--font-mono)' }}>
                        {formatMoney(reportData.total_descuentos)}
                      </div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        Incluye {formatMoney(reportData.total_licencia)} en licencias
                      </span>
                    </div>

                    <div className="card" style={{ background: 'linear-gradient(135deg, rgba(2, 132, 199, 0.08), rgba(29, 78, 216, 0.05))', border: '1px solid rgba(2, 132, 199, 0.3)', padding: '1.25rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--primary-700)', textTransform: 'uppercase' }}>Líquido Neto</span>
                        <div style={{ padding: '0.4rem', borderRadius: 'var(--radius-sm)', background: 'var(--primary-700)', color: '#FFFFFF' }}>
                          <CheckCircle2 size={18} />
                        </div>
                      </div>
                      <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--primary-700)', fontFamily: 'var(--font-mono)' }}>
                        {formatMoney(reportData.total_neto)}
                      </div>
                      <span style={{ fontSize: '0.75rem', color: 'var(--teal-600)', fontWeight: 600 }}>
                        {((Number(reportData.total_neto) / Number(reportData.total_importe || 1)) * 100).toFixed(1)}% desembolso efectivo
                      </span>
                    </div>
                  </div>

                  {/* Barra de Distribución Visual */}
                  <div style={{ marginBottom: '2rem', padding: '1.5rem', background: '#F8FAFC', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>Distribución de la Masa Salarial</span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Monto Total: {formatMoney(reportData.total_importe)}</span>
                    </div>
                    <div style={{ height: '14px', width: '100%', background: '#E2E8F0', borderRadius: 'var(--radius-full)', overflow: 'hidden', display: 'flex' }}>
                      <div 
                        style={{ 
                          width: `${(Number(reportData.total_neto) / Number(reportData.total_importe || 1)) * 100}%`, 
                          background: 'linear-gradient(90deg, #1D4ED8, #0284C7)', 
                          height: '100%' 
                        }} 
                        title={`Líquido Neto: ${formatMoney(reportData.total_neto)}`}
                      />
                      <div 
                        style={{ 
                          width: `${(Number(reportData.total_descuentos) / Number(reportData.total_importe || 1)) * 100}%`, 
                          background: '#F59E0B', 
                          height: '100%' 
                        }} 
                        title={`Total Descuentos: ${formatMoney(reportData.total_descuentos)}`}
                      />
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.75rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                        <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#1D4ED8', display: 'inline-block' }} />
                        Líquido Neto a Desembolsar: <strong>{formatMoney(reportData.total_neto)}</strong> ({((Number(reportData.total_neto) / Number(reportData.total_importe || 1)) * 100).toFixed(1)}%)
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                        <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#F59E0B', display: 'inline-block' }} />
                        Retenciones y Descuentos: <strong>{formatMoney(reportData.total_descuentos)}</strong> ({((Number(reportData.total_descuentos) / Number(reportData.total_importe || 1)) * 100).toFixed(1)}%)
                      </span>
                    </div>
                  </div>

                  {/* Tabla con Atributos de Auditoría */}
                  <table className="table" style={{ width: '100%' }}>
                    <thead>
                      <tr>
                        <th>Concepto Institucional</th>
                        <th>Detalle Registrado</th>
                        <th style={{ textAlign: 'right' }}>Monto Liquidado</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><strong>Masa Salarial Bruta (Importe Base)</strong></td>
                        <td>Totalidad de remuneraciones nominales fijadas por ley</td>
                        <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{formatMoney(reportData.total_importe)}</td>
                      </tr>
                      <tr>
                        <td>Licencias sin Goce de Haber</td>
                        <td>Deducciones proporcionales por días no laborados</td>
                        <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--amber-500)' }}>- {formatMoney(reportData.total_licencia)}</td>
                      </tr>
                      <tr>
                        <td>Descuentos de Terceros (8 Conceptos)</td>
                        <td>Convenios bancarios, aportes sindicales y sub-cafae</td>
                        <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--amber-500)' }}>- {formatMoney(Number(reportData.total_descuentos) - Number(reportData.total_licencia))}</td>
                      </tr>
                      <tr style={{ background: '#F8FAFC', fontWeight: 700 }}>
                        <td>TOTAL LÍQUIDO NETO A PAGAR</td>
                        <td>Importe líquido transferido al personal del sector</td>
                        <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--primary-700)', fontSize: '1rem' }}>{formatMoney(reportData.total_neto)}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}

              {/* REPORTE 2: IMPORTE POR INSTITUCIÓN EDUCATIVA */}
              {selectedReporte === 'por-institucion' && Array.isArray(reportData) && (
                <div>
                  <div style={{ overflowX: 'auto' }}>
                    <table className="table" style={{ width: '100%' }}>
                      <thead>
                        <tr>
                          <th style={{ width: '50px' }}>#</th>
                          <th style={{ width: '110px' }}>Cód. Modular</th>
                          <th>Institución Educativa</th>
                          <th style={{ textAlign: 'center' }}>Personal</th>
                          <th style={{ textAlign: 'right' }}>Total Importe</th>
                          <th style={{ textAlign: 'right' }}>Total Descuentos</th>
                          <th style={{ textAlign: 'right' }}>Líquido Neto</th>
                          <th style={{ width: '130px', textAlign: 'center' }}>% Participación</th>
                        </tr>
                      </thead>
                      <tbody>
                        {reportData
                          .filter((row) => {
                            if (!searchTerm) return true;
                            const t = searchTerm.toLowerCase();
                            return (row.institucion_nombre || '').toLowerCase().includes(t) || (row.codigo_modular || '').includes(t);
                          })
                          .map((row, i: number) => {
                            const totGlobal = reportData.reduce((acc: number, curr) => acc + Number(curr.total_importe || 0), 0);
                            const perc = totGlobal > 0 ? (Number(row.total_importe) / totGlobal) * 100 : 0;
                            return (
                              <tr key={i}>
                                <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{i + 1}</td>
                                <td>
                                  <span className="badge" style={{ background: '#F1F5F9', color: '#1E293B', fontFamily: 'var(--font-mono)' }}>
                                    {row.codigo_modular || 'S/C'}
                                  </span>
                                </td>
                                <td><strong>{row.institucion_nombre}</strong></td>
                                <td style={{ textAlign: 'center' }}>{row.cantidad_trabajadores}</td>
                                <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{formatMoney(row.total_importe)}</td>
                                <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--amber-500)' }}>{formatMoney(row.total_descuentos)}</td>
                                <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--primary-700)' }}>{formatMoney(row.total_neto)}</td>
                                <td>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    <div style={{ flex: 1, height: '6px', background: '#E2E8F0', borderRadius: '3px', overflow: 'hidden' }}>
                                      <div style={{ width: `${perc}%`, background: '#0284C7', height: '100%' }} />
                                    </div>
                                    <span style={{ fontSize: '0.725rem', color: 'var(--text-muted)', minWidth: '35px' }}>{perc.toFixed(1)}%</span>
                                  </div>
                                </td>
                              </tr>
                            );
                          })}
                      </tbody>
                      <tfoot>
                        <tr style={{ background: '#F8FAFC', fontWeight: 700 }}>
                          <td colSpan={3}>TOTAL GENERAL ({reportData.length} I.E.)</td>
                          <td style={{ textAlign: 'center' }}>{reportData.reduce((a, b) => a + Number(b.cantidad_trabajadores || 0), 0)}</td>
                          <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                            {formatMoney(reportData.reduce((a, b) => a + Number(b.total_importe || 0), 0))}
                          </td>
                          <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--amber-500)' }}>
                            {formatMoney(reportData.reduce((a, b) => a + Number(b.total_descuentos || 0), 0))}
                          </td>
                          <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--primary-700)' }}>
                            {formatMoney(reportData.reduce((a, b) => a + Number(b.total_neto || 0), 0))}
                          </td>
                          <td style={{ textAlign: 'center' }}>100%</td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                </div>
              )}

              {/* REPORTE 3: HOJA DE TRABAJO DE REMUNERACIONES (EXACT FORMAT FROM SCREENSHOT) */}
              {selectedReporte === 'por-meta' && reportData && (
                <div style={{ maxWidth: '820px', margin: '0 auto' }}>
                  {/* Título Oficial con bloque verde institucional */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                      <div style={{ width: '12px', height: '24px', background: '#005020', borderRadius: '1px' }} />
                      <h2 style={{ 
                        fontSize: '1.25rem', 
                        fontWeight: 800, 
                        color: '#002060', 
                        textDecoration: 'underline', 
                        fontFamily: 'Calibri, Arial, sans-serif',
                        letterSpacing: '0.02em',
                        margin: 0
                      }}>
                        HOJA DE TRABAJO DE REMUNERACIONES - PLANILLA  CAFAE
                      </h2>
                    </div>

                    <button 
                      onClick={() => {
                        if (selectedVersionId) {
                          window.open(`/api/documentos/remuneraciones-excel/${selectedVersionId}`, '_blank');
                        }
                      }} 
                      className="btn btn-secondary"
                      style={{ fontSize: '0.8rem', padding: '0.4rem 0.85rem' }}
                      title="Descargar este cuadro en formato Excel oficial (.xlsx)"
                    >
                      <Download size={15} />
                      <span>Descargar Excel Oficial</span>
                    </button>
                  </div>

                  {/* Tabla 1:1 con la Plantilla Institucional */}
                  <div style={{ overflowX: 'auto', border: '2px solid #000000', background: '#FFFFFF', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'Calibri, Arial, sans-serif', fontSize: '0.9rem' }}>
                      <thead>
                        <tr style={{ background: '#002060', color: '#FFFFFF', textAlign: 'center', fontWeight: 'bold' }}>
                          <th rowSpan={2} style={{ border: '1px solid #000000', padding: '8px 12px', width: '38%', textAlign: 'center' }}>
                            PROGRAMA
                          </th>
                          <th colSpan={2} style={{ border: '1px solid #000000', padding: '6px 12px' }}>
                            ASIGNACION A FONDOS<br/>PARA PERSONAL
                          </th>
                          <th rowSpan={2} style={{ border: '1px solid #000000', padding: '8px 12px', width: '22%', fontStyle: 'italic', textAlign: 'center' }}>
                            TOTAL<br/>EJECUT.
                          </th>
                        </tr>
                        <tr style={{ background: '#002060', color: '#FFFFFF', textAlign: 'center', fontWeight: 'bold', fontSize: '0.85rem' }}>
                          <th style={{ border: '1px solid #000000', padding: '4px 8px', width: '15%' }}>META</th>
                          <th style={{ border: '1px solid #000000', padding: '4px 8px', width: '25%' }}>21.11.21</th>
                        </tr>
                      </thead>
                      <tbody>
                        {reportData.tipo === 'SEDE' ? (
                          <>
                            {/* Fila 006 GESTION (Naranja #FFC000) */}
                            <tr style={{ background: '#FFC000', fontWeight: 'bold' }}>
                              <td style={{ border: '1px solid #000000', padding: '8px 12px' }}>006 GESTION</td>
                              <td style={{ border: '1px solid #000000', padding: '8px 12px', textAlign: 'center', color: '#0000FF', textDecoration: 'underline' }}>
                                {reportData.meta_gestion || '33'}
                              </td>
                              <td style={{ border: '1px solid #000000', padding: '8px 12px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                {formatMoneyNumber(reportData.gestion)}
                              </td>
                              <td style={{ border: '1px solid #000000', padding: '8px 12px', textAlign: 'right', fontFamily: 'var(--font-mono)', textDecoration: 'underline' }}>
                                {formatMoneyNumber(reportData.gestion)}
                              </td>
                            </tr>

                            {/* TOTAL SEDE (Azul Navy #002060 y Amarillo Brillante #FFFF00) */}
                            <tr style={{ fontWeight: 'bold', fontSize: '1rem' }}>
                              <td colSpan={2} style={{ background: '#002060', color: '#FFFFFF', border: '1px solid #000000', padding: '8px 12px', textAlign: 'center' }}>
                                TOTAL
                              </td>
                              <td style={{ background: '#002060', color: '#FFFFFF', border: '1px solid #000000', padding: '8px 12px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                {formatMoneyNumber(reportData.total_general)}
                              </td>
                              <td style={{ background: '#FFFF00', color: '#000000', border: '1px solid #000000', borderBottom: '3px double #000000', padding: '8px 12px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                {formatMoneyNumber(reportData.total_general)}
                              </td>
                            </tr>
                          </>
                        ) : (
                          <>
                            {/* Fila 047 EDUCAC.BASICA (Subtotal) */}
                            {Number(reportData.basica_sub || 0) > 0 && (
                              <>
                                <tr style={{ fontWeight: 'bold' }}>
                                  <td style={{ border: '1px solid #000000', padding: '6px 10px', textDecoration: 'underline' }}>047 EDUCAC.BASICA</td>
                                  <td style={{ border: '1px solid #000000', padding: '6px 10px' }}></td>
                                  <td style={{ border: '1px solid #000000', padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)', textDecoration: 'underline' }}>
                                    {formatMoneyNumber(reportData.basica_sub)}
                                  </td>
                                  <td style={{ border: '1px solid #000000', padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)', fontStyle: 'italic', textDecoration: 'underline' }}>
                                    {formatMoneyNumber(reportData.basica_sub)}
                                  </td>
                                </tr>

                                {Number(reportData.inicial || 0) > 0 && (
                                  <tr style={{ background: '#E2EFDA' }}>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px' }}>103 EDUC.INICIAL</td>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'center', color: '#0000FF', textDecoration: 'underline', fontWeight: 'bold' }}>11</td>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                      {formatMoneyNumber(reportData.inicial)}
                                    </td>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                      {formatMoneyNumber(reportData.inicial)}
                                    </td>
                                  </tr>
                                )}

                                {Number(reportData.primaria || 0) > 0 && (
                                  <tr style={{ background: '#E2EFDA' }}>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px' }}>104 PRIMARIA</td>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'center', color: '#0000FF', textDecoration: 'underline', fontWeight: 'bold' }}>12</td>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                      {formatMoneyNumber(reportData.primaria)}
                                    </td>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                      {formatMoneyNumber(reportData.primaria)}
                                    </td>
                                  </tr>
                                )}

                                {Number(reportData.secundaria || 0) > 0 && (
                                  <tr style={{ background: '#E2EFDA' }}>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px' }}>105 EDUCACION SECUNDARIA</td>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'center', color: '#0000FF', textDecoration: 'underline', fontWeight: 'bold' }}>14</td>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                      {formatMoneyNumber(reportData.secundaria)}
                                    </td>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                      {formatMoneyNumber(reportData.secundaria)}
                                    </td>
                                  </tr>
                                )}
                              </>
                            )}

                            {/* Fila 106 EDUC.BASICA ALTER. (Subtotal) */}
                            {Number(reportData.eba_sub || 0) > 0 && (
                              <>
                                <tr style={{ fontWeight: 'bold' }}>
                                  <td style={{ border: '1px solid #000000', padding: '6px 10px', textDecoration: 'underline' }}>106 EDUC.BASICA ALTER.</td>
                                  <td style={{ border: '1px solid #000000', padding: '6px 10px' }}></td>
                                  <td style={{ border: '1px solid #000000', padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)', textDecoration: 'underline' }}>
                                    {formatMoneyNumber(reportData.eba_sub)}
                                  </td>
                                  <td style={{ border: '1px solid #000000', padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)', textDecoration: 'underline' }}>
                                    {formatMoneyNumber(reportData.eba_sub)}
                                  </td>
                                </tr>

                                {Number(reportData.eba_inicial || 0) > 0 && (
                                  <tr style={{ background: '#E2EFDA' }}>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px' }}>EBA Ciclo Inicial e Intermedio</td>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'center', color: '#0000FF', textDecoration: 'underline', fontWeight: 'bold' }}>43</td>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                      {formatMoneyNumber(reportData.eba_inicial)}
                                    </td>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                      {formatMoneyNumber(reportData.eba_inicial)}
                                    </td>
                                  </tr>
                                )}

                                {Number(reportData.eba_avanzado || 0) > 0 && (
                                  <tr style={{ background: '#E2EFDA' }}>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px' }}>EBA Ciclo Avanzado</td>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'center', color: '#0000FF', textDecoration: 'underline', fontWeight: 'bold' }}>44</td>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                      {formatMoneyNumber(reportData.eba_avanzado)}
                                    </td>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                      {formatMoneyNumber(reportData.eba_avanzado)}
                                    </td>
                                  </tr>
                                )}
                              </>
                            )}

                            {/* Fila 107 EDUCAC. ESPECIAL (Subtotal con celda amarilla) */}
                            {Number(reportData.esp_sub || 0) > 0 && (
                              <>
                                <tr style={{ fontWeight: 'bold' }}>
                                  <td style={{ border: '1px solid #000000', padding: '6px 10px', textDecoration: 'underline' }}>107 EDUCAC. ESPECIAL</td>
                                  <td style={{ border: '1px solid #000000', padding: '6px 10px' }}></td>
                                  <td style={{ border: '1px solid #000000', padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)', textDecoration: 'underline' }}>
                                    {formatMoneyNumber(reportData.esp_sub)}
                                  </td>
                                  <td style={{ border: '1px solid #000000', padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)', background: '#FFFF00', textDecoration: 'underline' }}>
                                    {formatMoneyNumber(reportData.esp_sub)}
                                  </td>
                                </tr>

                                {Number(reportData.esp_inicial || 0) > 0 && (
                                  <tr style={{ background: '#E2EFDA' }}>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px' }}>Especial Inicial</td>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'center', color: '#0000FF', textDecoration: 'underline', fontWeight: 'bold' }}>29</td>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                      {formatMoneyNumber(reportData.esp_inicial)}
                                    </td>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                      {formatMoneyNumber(reportData.esp_inicial)}
                                    </td>
                                  </tr>
                                )}

                                {Number(reportData.esp_primaria || 0) > 0 && (
                                  <tr style={{ background: '#E2EFDA' }}>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px' }}>Especial Primaria</td>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'center', color: '#0000FF', textDecoration: 'underline', fontWeight: 'bold' }}>30</td>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                      {formatMoneyNumber(reportData.esp_primaria)}
                                    </td>
                                    <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                      {formatMoneyNumber(reportData.esp_primaria)}
                                    </td>
                                  </tr>
                                )}
                              </>
                            )}

                            {/* 049 EDUCAC. TEC.PRODUCT. (Verde #E2EFDA con texto bold) */}
                            {Number(reportData.tec_prod || 0) > 0 && (
                              <tr style={{ background: '#E2EFDA', fontWeight: 'bold' }}>
                                <td style={{ border: '1px solid #000000', padding: '6px 10px' }}>049 EDUCAC. TEC.PRODUCT.</td>
                                <td style={{ border: '1px solid #000000', padding: '6px 10px', textAlign: 'center', color: '#0000FF', textDecoration: 'underline' }}>42</td>
                                <td style={{ border: '1px solid #000000', padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)', textDecoration: 'underline' }}>
                                  {formatMoneyNumber(reportData.tec_prod)}
                                </td>
                                <td style={{ border: '1px solid #000000', padding: '6px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)', textDecoration: 'underline' }}>
                                  {formatMoneyNumber(reportData.tec_prod)}
                                </td>
                              </tr>
                            )}

                            {/* Metas adicionales presentes en la planilla */}
                            {Array.isArray(reportData.otras_metas) && reportData.otras_metas.filter((om: { importe?: number | string }) => Number(om.importe || 0) > 0).map((om: { meta_descripcion?: string; meta_codigo?: string; importe?: number | string }, idx: number) => (
                              <tr key={idx} style={{ background: '#E2EFDA' }}>
                                <td style={{ border: '1px solid #000000', padding: '5px 10px' }}>{om.meta_descripcion || `Meta ${om.meta_codigo}`}</td>
                                <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'center', color: '#0000FF', textDecoration: 'underline', fontWeight: 'bold' }}>{om.meta_codigo}</td>
                                <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                  {formatMoneyNumber(om.importe)}
                                </td>
                                <td style={{ border: '1px solid #000000', padding: '5px 10px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                  {formatMoneyNumber(om.importe)}
                                </td>
                              </tr>
                            ))}

                            {/* TOTAL IIEE (Azul Navy #002060 y Amarillo Brillante #FFFF00) */}
                            <tr style={{ fontWeight: 'bold', fontSize: '1rem' }}>
                              <td colSpan={2} style={{ background: '#002060', color: '#FFFFFF', border: '1px solid #000000', padding: '8px 12px', textAlign: 'center' }}>
                                TOTAL
                              </td>
                              <td style={{ background: '#002060', color: '#FFFFFF', border: '1px solid #000000', padding: '8px 12px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                {formatMoneyNumber(reportData.total_general)}
                              </td>
                              <td style={{ background: '#FFFF00', color: '#000000', border: '1px solid #000000', borderBottom: '3px double #000000', padding: '8px 12px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                                {formatMoneyNumber(reportData.total_general)}
                              </td>
                            </tr>
                          </>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* REPORTE 4: DESCUENTOS POR ENTIDAD */}
              {selectedReporte === 'descuentos-por-entidad' && Array.isArray(reportData) && (
                <div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
                    {reportData.map((d, i: number) => {
                      const totDesc = reportData.reduce((acc: number, curr) => acc + Number(curr.total_descontado || 0), 0);
                      const perc = totDesc > 0 ? (Number(d.total_descontado) / totDesc) * 100 : 0;
                      return (
                        <div key={i} className="card" style={{ background: '#FFFFFF', border: '1px solid var(--border-subtle)', padding: '1.25rem' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                            <span className="badge" style={{ background: '#F1F5F9', color: '#0F172A', fontWeight: 700, fontSize: '0.7rem' }}>
                              {d.codigo}
                            </span>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                              {d.trabajadores_afectados} personal
                            </span>
                          </div>
                          <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                            {d.entidad_nombre}
                          </div>
                          <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--amber-500)', fontFamily: 'var(--font-mono)', marginBottom: '0.75rem' }}>
                            {formatMoney(d.total_descontado)}
                          </div>
                          <div style={{ height: '5px', background: '#E2E8F0', borderRadius: '2px', overflow: 'hidden' }}>
                            <div style={{ width: `${perc}%`, background: '#F59E0B', height: '100%' }} />
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.4rem', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                            <span>Participación: {perc.toFixed(1)}%</span>
                            <span>Promedio: {d.trabajadores_afectados > 0 ? formatMoney(Number(d.total_descontado) / Number(d.trabajadores_afectados)) : 'S/ 0.00'}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  <table className="table" style={{ width: '100%' }}>
                    <thead>
                      <tr>
                        <th>Código</th>
                        <th>Entidad o Concepto de Descuento</th>
                        <th style={{ textAlign: 'center' }}>Personal Afectado</th>
                        <th style={{ textAlign: 'right' }}>Monto Retenido</th>
                        <th style={{ textAlign: 'center' }}>% del Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reportData.map((d, i: number) => {
                        const totDesc = reportData.reduce((acc: number, curr) => acc + Number(curr.total_descontado || 0), 0);
                        const perc = totDesc > 0 ? (Number(d.total_descontado) / totDesc) * 100 : 0;
                        return (
                          <tr key={i}>
                            <td><code>{d.codigo}</code></td>
                            <td><strong>{d.entidad_nombre}</strong></td>
                            <td style={{ textAlign: 'center' }}>{d.trabajadores_afectados}</td>
                            <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{formatMoney(d.total_descontado)}</td>
                            <td style={{ textAlign: 'center' }}>{perc.toFixed(1)}%</td>
                          </tr>
                        );
                      })}
                    </tbody>
                    <tfoot>
                      <tr style={{ background: '#F8FAFC', fontWeight: 700 }}>
                        <td colSpan={2}>TOTAL RETENCIONES POR CONVENIO</td>
                        <td style={{ textAlign: 'center' }}>-</td>
                        <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--amber-500)' }}>
                          {formatMoney(reportData.reduce((a, b) => a + Number(b.total_descontado || 0), 0))}
                        </td>
                        <td style={{ textAlign: 'center' }}>100%</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              )}

              {/* REPORTE 5: SÁBANA GENERAL DE DESCUENTOS */}
              {selectedReporte === 'general-descuentos' && Array.isArray(reportData) && (
                <div>
                  <div style={{ overflowX: 'auto', maxHeight: '550px' }}>
                    <table className="table" style={{ width: '100%', fontSize: '0.785rem' }}>
                      <thead style={{ position: 'sticky', top: 0, zIndex: 1, background: '#F8FAFC' }}>
                        <tr>
                          <th>DNI</th>
                          <th>Apellidos y Nombres</th>
                          <th>Adscripción</th>
                          <th style={{ textAlign: 'right' }}>Importe</th>
                          <th style={{ textAlign: 'right' }}>Pichincha</th>
                          <th style={{ textAlign: 'right' }}>C. Sullana</th>
                          <th style={{ textAlign: 'right' }}>Sub-CAFAE</th>
                          <th style={{ textAlign: 'right' }}>BRENTA</th>
                          <th style={{ textAlign: 'right' }}>SITRASE</th>
                          <th style={{ textAlign: 'right' }}>SITASE</th>
                          <th style={{ textAlign: 'right' }}>Licencia</th>
                          <th style={{ textAlign: 'right' }}>Otros</th>
                          <th style={{ textAlign: 'right' }}>Tot. Desc.</th>
                          <th style={{ textAlign: 'right' }}>Neto</th>
                        </tr>
                      </thead>
                      <tbody>
                        {reportData
                          .filter((row) => {
                            if (!searchTerm) return true;
                            const t = searchTerm.toLowerCase();
                            return row.dni.includes(t) || (row.apellidos + ' ' + row.nombres).toLowerCase().includes(t);
                          })
                          .map((row, i: number) => (
                            <tr key={i}>
                              <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{row.dni}</td>
                              <td>{row.apellidos}, {row.nombres}</td>
                              <td style={{ fontSize: '0.725rem', color: 'var(--text-muted)' }}>{row.adscripcion}</td>
                              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{Number(row.importe).toFixed(2)}</td>
                              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: Number(row.pichincha) > 0 ? 'var(--amber-500)' : '#94A3B8' }}>{Number(row.pichincha).toFixed(2)}</td>
                              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: Number(row.caja_sullana) > 0 ? 'var(--amber-500)' : '#94A3B8' }}>{Number(row.caja_sullana).toFixed(2)}</td>
                              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: Number(row.sub_cafae) > 0 ? 'var(--amber-500)' : '#94A3B8' }}>{Number(row.sub_cafae).toFixed(2)}</td>
                              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: Number(row.brenta) > 0 ? 'var(--amber-500)' : '#94A3B8' }}>{Number(row.brenta).toFixed(2)}</td>
                              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: Number(row.sitrase) > 0 ? 'var(--amber-500)' : '#94A3B8' }}>{Number(row.sitrase).toFixed(2)}</td>
                              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: Number(row.sitase) > 0 ? 'var(--amber-500)' : '#94A3B8' }}>{Number(row.sitase).toFixed(2)}</td>
                              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: Number(row.licencia) > 0 ? '#DC2626' : '#94A3B8' }}>{Number(row.licencia).toFixed(2)}</td>
                              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: Number(row.otros) > 0 ? 'var(--amber-500)' : '#94A3B8' }}>{Number(row.otros).toFixed(2)}</td>
                              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--amber-500)' }}>{Number(row.total_descuentos).toFixed(2)}</td>
                              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--primary-700)' }}>{Number(row.neto).toFixed(2)}</td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* REPORTE 6: MODALIDAD DE PAGO */}
              {selectedReporte === 'modalidad-pago' && Array.isArray(reportData) && (
                <div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
                    {reportData.map((m, i: number) => (
                      <div key={i} className="card" style={{ padding: '1.5rem', background: '#F8FAFC', border: '1px solid var(--border-subtle)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                            Modalidad: {m.modalidad === 'CUENTA' ? 'Abono en Cuenta Multired' : m.modalidad}
                          </span>
                          <div style={{ padding: '0.5rem', borderRadius: 'var(--radius-md)', background: '#E0F2FE', color: '#0369A1' }}>
                            <Wallet size={20} />
                          </div>
                        </div>
                        <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                          {m.cantidad_personas} trabajadores
                        </div>
                        <div style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--primary-700)', fontFamily: 'var(--font-mono)' }}>
                          Neto: {formatMoney(m.total_neto)}
                        </div>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Masa Bruta: {formatMoney(m.total_importe)}</span>
                      </div>
                    ))}
                  </div>

                  <table className="table" style={{ width: '100%' }}>
                    <thead>
                      <tr>
                        <th>Tipo / Canal de Pago</th>
                        <th style={{ textAlign: 'center' }}>Cantidad de Personas</th>
                        <th style={{ textAlign: 'right' }}>Total Importe Bruto</th>
                        <th style={{ textAlign: 'right' }}>Total Descuentos</th>
                        <th style={{ textAlign: 'right' }}>Líquido Neto a Desembolsar</th>
                      </tr>
                    </thead>
                    <tbody>
                      {reportData.map((m, i: number) => (
                        <tr key={i}>
                          <td><strong>{m.modalidad === 'CUENTA' ? 'Abono en Cuenta Multired (Banco de la Nación)' : m.modalidad}</strong></td>
                          <td style={{ textAlign: 'center' }}>{m.cantidad_personas}</td>
                          <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{formatMoney(m.total_importe)}</td>
                          <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--amber-500)' }}>{formatMoney(m.total_descuentos)}</td>
                          <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--primary-700)' }}>{formatMoney(m.total_neto)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* REPORTE 7: PADRÓN ALFABÉTICO OFICIAL */}
              {selectedReporte === 'padron-alfabetico' && Array.isArray(reportData) && (
                <div>
                  <div style={{ overflowX: 'auto', maxHeight: '550px' }}>
                    <table className="table" style={{ width: '100%' }}>
                      <thead style={{ position: 'sticky', top: 0, zIndex: 1, background: '#F8FAFC' }}>
                        <tr>
                          <th style={{ width: '50px' }}>#</th>
                          <th>DNI</th>
                          <th>Apellidos y Nombres</th>
                          <th>Cargo / Categoría</th>
                          <th>Institución / Sede</th>
                          <th>Cuenta Multired</th>
                          <th style={{ textAlign: 'right' }}>Importe</th>
                          <th style={{ textAlign: 'right' }}>Descuentos</th>
                          <th style={{ textAlign: 'right' }}>Líquido Neto</th>
                        </tr>
                      </thead>
                      <tbody>
                        {reportData
                          .filter((p) => {
                            if (!searchTerm) return true;
                            const t = searchTerm.toLowerCase();
                            return p.dni.includes(t) || (p.apellidos + ' ' + p.nombres).toLowerCase().includes(t);
                          })
                          .map((p, i: number) => (
                            <tr key={i}>
                              <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{i + 1}</td>
                              <td><strong style={{ fontFamily: 'var(--font-mono)' }}>{p.dni}</strong></td>
                              <td>{p.apellidos}, {p.nombres}</td>
                              <td>
                                <span className="badge" style={{ background: '#F1F5F9', color: '#1E293B', fontSize: '0.725rem' }}>
                                  {p.cargo} ({p.categoria})
                                </span>
                              </td>
                              <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{p.adscripcion}</td>
                              <td>
                                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: '#0369A1' }}>
                                  {p.cuenta_multired || 'Sin cuenta'}
                                </span>
                              </td>
                              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{formatMoney(p.importe)}</td>
                              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--amber-500)' }}>{formatMoney(p.total_descuentos)}</td>
                              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--primary-700)' }}>{formatMoney(p.neto)}</td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* REPORTE 8: LICENCIAS SIN GOCE DE HABER */}
              {selectedReporte === 'licencias-sin-goce' && Array.isArray(reportData) && (
                <div>
                  {reportData.length === 0 ? (
                    <div style={{ textAlign: 'center', padding: '4rem 2rem', color: 'var(--text-muted)' }}>
                      <CheckCircle2 size={48} style={{ color: 'var(--emerald-500)', opacity: 0.8, marginBottom: '1rem' }} />
                      <h3 style={{ fontSize: '1.1rem', color: 'var(--text-primary)', marginBottom: '0.5rem' }}>Sin licencias registradas</h3>
                      <p style={{ fontSize: '0.85rem' }}>No existen deducciones por licencias sin goce de haber en esta planilla.</p>
                    </div>
                  ) : (
                    <div>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
                        <div className="card" style={{ padding: '1.25rem', background: '#FEF3C7', border: '1px solid #FDE68A' }}>
                          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#92400E', textTransform: 'uppercase' }}>Personal con Licencia</span>
                          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#92400E' }}>{reportData.length}</div>
                        </div>
                        <div className="card" style={{ padding: '1.25rem', background: '#F8FAFC', border: '1px solid var(--border-subtle)' }}>
                          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Días no laborados</span>
                          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                            {reportData.reduce((a, b) => a + Number(b.dias_licencia || 0), 0)} días
                          </div>
                        </div>
                        <div className="card" style={{ padding: '1.25rem', background: '#F8FAFC', border: '1px solid var(--border-subtle)' }}>
                          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Deducido por Licencias</span>
                          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#DC2626', fontFamily: 'var(--font-mono)' }}>
                            {formatMoney(reportData.reduce((a, b) => a + Number(b.monto_licencia || 0), 0))}
                          </div>
                        </div>
                      </div>

                      <table className="table" style={{ width: '100%' }}>
                        <thead>
                          <tr>
                            <th>DNI</th>
                            <th>Apellidos y Nombres</th>
                            <th>Adscripción</th>
                            <th style={{ textAlign: 'right' }}>Importe Base</th>
                            <th style={{ textAlign: 'center' }}>Días de Licencia</th>
                            <th style={{ textAlign: 'right' }}>Descuento (30avos)</th>
                            <th style={{ textAlign: 'right' }}>Líquido Neto Resultante</th>
                          </tr>
                        </thead>
                        <tbody>
                          {reportData.map((l, i: number) => (
                            <tr key={i}>
                              <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{l.dni}</td>
                              <td><strong>{l.apellidos}, {l.nombres}</strong></td>
                              <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{l.adscripcion}</td>
                              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{formatMoney(l.importe)}</td>
                              <td style={{ textAlign: 'center' }}>
                                <span className="badge badge-warning" style={{ fontWeight: 700 }}>
                                  {l.dias_licencia} día(s)
                                </span>
                              </td>
                              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: '#DC2626', fontWeight: 600 }}>
                                - {formatMoney(l.monto_licencia)}
                              </td>
                              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--primary-700)', fontWeight: 600 }}>
                                {formatMoney(l.neto)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* REPORTE 9: COMPARATIVO INTERMENSUAL */}
              {selectedReporte === 'comparativo-anterior' && Array.isArray(reportData) && (
                <div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
                    {reportData.map((c, i: number) => (
                      <div key={i} className="card" style={{ padding: '1.5rem', background: '#F8FAFC', border: '1px solid var(--border-subtle)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                          <span className="badge badge-info" style={{ fontWeight: 700 }}>
                            {c.tipo} · {c.anio}-{String(c.mes).padStart(2, '0')} (v{c.numero})
                          </span>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Versión ID: #{c.version_id}</span>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '1rem' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                            <span style={{ color: 'var(--text-muted)' }}>Personal:</span>
                            <strong>{c.total_trabajadores} trabajadores</strong>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                            <span style={{ color: 'var(--text-muted)' }}>Importe Bruto:</span>
                            <strong style={{ fontFamily: 'var(--font-mono)' }}>{formatMoney(c.total_importe)}</strong>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                            <span style={{ color: 'var(--text-muted)' }}>Total Descuentos:</span>
                            <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--amber-500)' }}>{formatMoney(c.total_descuentos)}</strong>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.95rem', borderTop: '1px solid #E2E8F0', paddingTop: '0.5rem' }}>
                            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Líquido Neto:</span>
                            <strong style={{ fontFamily: 'var(--font-mono)', color: 'var(--primary-700)' }}>{formatMoney(c.total_neto)}</strong>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Tabla Comparativa de Variaciones */}
                  {reportData.length >= 2 && (
                    <div style={{ padding: '1.5rem', background: '#FFFFFF', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)' }}>
                      <h3 style={{ fontSize: '1rem', marginBottom: '1rem', color: 'var(--text-primary)' }}>Análisis de Variación Intermensual</h3>
                      <table className="table" style={{ width: '100%' }}>
                        <thead>
                          <tr>
                            <th>Concepto</th>
                            <th style={{ textAlign: 'right' }}>Periodo Anterior</th>
                            <th style={{ textAlign: 'right' }}>Periodo Seleccionado</th>
                            <th style={{ textAlign: 'right' }}>Variación Absoluta</th>
                            <th style={{ textAlign: 'right' }}>Variación %</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(() => {
                            const p1 = reportData[0];
                            const p2 = reportData[1];
                            const calcDiff = (v1: number, v2: number) => {
                              const diff = v2 - v1;
                              const p = v1 > 0 ? (diff / v1) * 100 : 0;
                              return { diff, p };
                            };

                            const items = [
                              { name: 'Personal Total', v1: Number(p1.total_trabajadores), v2: Number(p2.total_trabajadores), isMoney: false },
                              { name: 'Masa Salarial Bruta', v1: Number(p1.total_importe), v2: Number(p2.total_importe), isMoney: true },
                              { name: 'Total Descuentos', v1: Number(p1.total_descuentos), v2: Number(p2.total_descuentos), isMoney: true },
                              { name: 'Líquido Neto a Desembolsar', v1: Number(p1.total_neto), v2: Number(p2.total_neto), isMoney: true },
                            ];

                            return items.map((it, idx) => {
                              const { diff, p } = calcDiff(it.v1, it.v2);
                              const isPositive = diff >= 0;
                              return (
                                <tr key={idx}>
                                  <td><strong>{it.name}</strong></td>
                                  <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{it.isMoney ? formatMoney(it.v1) : it.v1}</td>
                                  <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{it.isMoney ? formatMoney(it.v2) : it.v2}</td>
                                  <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 600, color: isPositive ? 'var(--emerald-600)' : '#DC2626' }}>
                                    {isPositive ? '+' : ''}{it.isMoney ? formatMoney(diff) : diff}
                                  </td>
                                  <td style={{ textAlign: 'right', fontWeight: 600, color: isPositive ? 'var(--emerald-600)' : '#DC2626' }}>
                                    {isPositive ? '+' : ''}{p.toFixed(2)}%
                                  </td>
                                </tr>
                              );
                            });
                          })()}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

            </div>
          )}
        </div>

      </div>
    </div>
  );
};
