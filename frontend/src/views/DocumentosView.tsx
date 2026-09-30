import React, { useState, useEffect } from 'react';
import { apiRequest, downloadFile, previewPdfInTab } from '../api/client';
import { PlanillaListItem, LineaPlanilla } from '../types';
import { Pagination } from '../components/Pagination';
import { 
  FileText, 
  FileSpreadsheet, 
  Download, 
  Printer, 
  Search, 
  UserCheck, 
  Layers, 
  Lock, 
  CheckCircle2, 
  Clock, 
  ExternalLink,
  Calendar
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

export const DocumentosView: React.FC = () => {
  const [planillas, setPlanillas] = useState<PlanillaListItem[]>([]);
  const [tipoFiltro, setTipoFiltro] = useState<'IIEE' | 'SEDE'>('IIEE');
  const [selectedAnio, setSelectedAnio] = useState<number>(2026);
  const [selectedMes, setSelectedMes] = useState<number>(3);
  const [selectedPlanilla, setSelectedPlanilla] = useState<PlanillaListItem | null>(null);
  const [lineas, setLineas] = useState<LineaPlanilla[]>([]);
  const [loadingLineas, setLoadingLineas] = useState(false);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [searchDni, setSearchDni] = useState('');
  const [directDni, setDirectDni] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Paginación
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(15);

  // 1. Cargar planillas disponibles
  useEffect(() => {
    const fetchPlanillas = async () => {
      try {
        const list = await apiRequest<PlanillaListItem[]>('/api/planillas');
        setPlanillas(list);
      } catch (err: any) {
        setErrorMsg(err.message || 'Error al cargar lista de planillas.');
      }
    };
    fetchPlanillas();
  }, []);

  // 2. Sincronizar planilla seleccionada según tipoFiltro, anio y mes
  useEffect(() => {
    const matching = planillas.find(
      (p) => p.tipo === tipoFiltro && p.anio === selectedAnio && p.mes === selectedMes
    );
    setSelectedPlanilla(matching || null);
  }, [planillas, tipoFiltro, selectedAnio, selectedMes]);

  // 3. Al cambiar la planilla seleccionada, cargar sus trabajadores para emisión individual
  useEffect(() => {
    if (!selectedPlanilla?.version_id) {
      setLineas([]);
      return;
    }

    const fetchDetalle = async () => {
      setLoadingLineas(true);
      setErrorMsg(null);
      try {
        const data = await apiRequest(`/api/planillas/versiones/${selectedPlanilla.version_id}`);
        setLineas(data.lineas || []);
      } catch (err: any) {
        setErrorMsg(err.message || 'Error al obtener personal de la planilla.');
      } finally {
        setLoadingLineas(false);
      }
    };

    fetchDetalle();
  }, [selectedPlanilla]);

  useEffect(() => {
    setCurrentPage(1);
  }, [selectedPlanilla, searchDni]);

  // Manejo de cambio de tipo IIEE vs SEDE
  const handleCambiarTipo = (tipo: 'IIEE' | 'SEDE') => {
    setTipoFiltro(tipo);
  };

  const handleDownload = async (type: string, path: string, filename: string) => {
    setDownloading(type);
    setErrorMsg(null);
    try {
      await downloadFile(path, filename);
    } catch (err: any) {
      setErrorMsg(err.message || 'Error al descargar documento.');
    } finally {
      setDownloading(null);
    }
  };

  const handleImprimirBoleta = async (dni: string) => {
    if (!selectedPlanilla) return;
    const vId = selectedPlanilla.version_id;
    try {
      await previewPdfInTab(`/api/documentos/boleta-dni/${vId}/${dni}`);
    } catch (err: any) {
      alert(err.message || `Error al visualizar la boleta del DNI ${dni}`);
    }
  };

  const handleDescargarBoleta = async (dni: string, apellidos: string) => {
    if (!selectedPlanilla) return;
    const vId = selectedPlanilla.version_id;
    const tag = `${dni}_${selectedPlanilla.anio}_${String(selectedPlanilla.mes).padStart(2, '0')}`;
    await handleDownload(`boleta-${dni}`, `/api/documentos/boleta-dni/${vId}/${dni}`, `Boleta_${tag}.pdf`);
  };

  const handleBuscarDirecto = (e: React.FormEvent) => {
    e.preventDefault();
    const clean = directDni.trim();
    if (!clean) return;
    const existe = lineas.some((l) => l.dni === clean);
    if (!existe) {
      alert(`El DNI ${clean} no se encuentra registrado en esta planilla de ${selectedPlanilla?.tipo}.`);
      return;
    }
    handleImprimirBoleta(clean);
  };

  // Obtener lista de años únicos disponibles en las planillas (con default a 2026)
  const aniosDisponibles = Array.from(new Set([2026, ...planillas.map((p) => p.anio)])).sort((a, b) => b - a);

  const vId = selectedPlanilla?.version_id;
  const pTag = selectedPlanilla 
    ? `${selectedPlanilla.tipo}_${selectedPlanilla.anio}_${String(selectedPlanilla.mes).padStart(2, '0')}_v${selectedPlanilla.version_numero}` 
    : '';

  // Filtro de trabajadores en la tabla
  const lineasFiltradas = lineas.filter((l) => {
    if (!searchDni.trim()) return true;
    const q = searchDni.toLowerCase().trim();
    return l.dni.includes(q) || l.apellidos.toLowerCase().includes(q) || l.nombres.toLowerCase().includes(q);
  });

  return (
    <div className="page-container">
      {/* 1. SELECCIÓN PREVIA: IIEE vs SEDE & FILTRO DE AÑO Y MES */}
      <div className="card" style={{ marginBottom: '1.75rem', padding: '1.5rem 1.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1.25rem' }}>
          <div>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--teal-500)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Módulo de Emisión y Boletas de Pago CAFAE
            </span>
            <h2 style={{ fontSize: '1.35rem', marginTop: '0.2rem', marginBottom: '0.25rem' }}>
              Documentos Oficiales y Boletas Individuales
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>
              Selecciona el tipo de personal (II.EE. o SEDE), año y mes para generar reportes y boletas oficiales.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', flexWrap: 'wrap' }}>
            {/* Selector de Ámbito: IIEE vs SEDE */}
            <div style={{ display: 'inline-flex', background: '#F1F5F9', padding: '0.25rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', gap: '0.25rem' }}>
              <button
                type="button"
                onClick={() => handleCambiarTipo('IIEE')}
                className={`btn ${tipoFiltro === 'IIEE' ? 'btn-primary' : 'btn-ghost'}`}
                style={{ padding: '0.45rem 1.1rem', fontSize: '0.85rem', fontWeight: 600, borderRadius: 'var(--radius-sm)' }}
              >
                🏫 II.EE.
              </button>
              <button
                type="button"
                onClick={() => handleCambiarTipo('SEDE')}
                className={`btn ${tipoFiltro === 'SEDE' ? 'btn-primary' : 'btn-ghost'}`}
                style={{ padding: '0.45rem 1.1rem', fontSize: '0.85rem', fontWeight: 600, borderRadius: 'var(--radius-sm)' }}
              >
                🏢 SEDE
              </button>
            </div>

            {/* Selector de Año */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Año:</span>
              <select
                className="form-select"
                style={{ width: '95px', fontWeight: 600 }}
                value={selectedAnio}
                onChange={(e) => setSelectedAnio(Number(e.target.value))}
              >
                {aniosDisponibles.map((a) => (
                  <option key={a} value={a}>{a}</option>
                ))}
              </select>
            </div>

            {/* Selector de Mes */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Mes:</span>
              <select
                className="form-select"
                style={{ minWidth: '175px', fontWeight: 600 }}
                value={selectedMes}
                onChange={(e) => setSelectedMes(Number(e.target.value))}
              >
                {MESES.map((m) => {
                  const plan = planillas.find((p) => p.tipo === tipoFiltro && p.anio === selectedAnio && p.mes === m.num);
                  return (
                    <option key={m.num} value={m.num}>
                      {String(m.num).padStart(2, '0')} - {m.nombre} {plan ? `(${plan.version_estado.substring(0, 3)})` : ''}
                    </option>
                  );
                })}
              </select>
            </div>

            {/* Estado de la versión seleccionada */}
            {selectedPlanilla && (
              <span className={`badge ${selectedPlanilla.version_estado === 'CERRADA' ? 'badge-emerald' : 'badge-amber'}`} style={{ fontWeight: 600 }}>
                {selectedPlanilla.version_estado === 'CERRADA' ? <CheckCircle2 size={13} /> : <Clock size={13} />}
                v{selectedPlanilla.version_numero} · {selectedPlanilla.version_estado}
              </span>
            )}
          </div>
        </div>
      </div>

      {errorMsg && (
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #EF4444', color: '#F87171', padding: '0.85rem 1.25rem', borderRadius: 'var(--radius-md)', marginBottom: '1.5rem', fontSize: '0.85rem' }}>
          {errorMsg}
        </div>
      )}

      {/* Si no existe planilla para el año/mes seleccionado */}
      {!selectedPlanilla && (
        <div className="card" style={{ textAlign: 'center', padding: '3.5rem 2rem', marginTop: '1rem', border: '1px dashed var(--border-subtle)' }}>
          <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'rgba(20, 184, 166, 0.1)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: 'var(--teal-500)', marginBottom: '1.25rem' }}>
            <Calendar size={32} />
          </div>
          <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>
            No existe planilla de {tipoFiltro === 'IIEE' ? 'Instituciones Educativas' : 'Sede UGEL'} para {MESES.find((m) => m.num === selectedMes)?.nombre} {selectedAnio}
          </h3>
          <p style={{ color: 'var(--text-muted)', maxWidth: '500px', margin: '0 auto', fontSize: '0.9rem' }}>
            Seleccione otro año o mes en los filtros superiores para emitir boletas y reportes.
          </p>
        </div>
      )}

      {selectedPlanilla && (
        <>
          {/* 2. SECCIÓN PRINCIPAL: BÚSQUEDA Y EMISIÓN INDIVIDUAL DE BOLETAS POR DNI */}
          <div className="card" style={{ marginBottom: '2rem', border: '1px solid #CBD5E1', background: '#FFFFFF' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem', borderBottom: '1px solid #E2E8F0', paddingBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{ padding: '0.65rem', borderRadius: 'var(--radius-md)', background: '#EFF6FF', color: '#1D4ED8' }}>
                  <Printer size={24} />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.15rem', margin: 0, fontWeight: 700, color: '#0F172A' }}>
                    Boletas de Pago Individuales (Formato Oficial UGEL Chepén)
                  </h3>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Búsqueda por DNI o apellidos para visualización, impresión y descarga individualizada.
                  </span>
                </div>
              </div>

              {/* Acceso Rápido por DNI */}
              <form onSubmit={handleBuscarDirecto} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <input
                  type="text"
                  className="form-input"
                  placeholder="DNI directo (8 dígitos)..."
                  maxLength={8}
                  value={directDni}
                  onChange={(e) => setDirectDni(e.target.value.replace(/\D/g, ''))}
                  style={{ width: '190px', fontFamily: 'monospace', fontWeight: 600 }}
                />
                <button
                  type="submit"
                  disabled={directDni.length !== 8}
                  className="btn btn-primary"
                  style={{ whiteSpace: 'nowrap' }}
                >
                  <Printer size={16} />
                  <span>Imprimir Boleta</span>
                </button>
              </form>
            </div>

            {/* Barra de Búsqueda y Filtro de Lista */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
              <div style={{ position: 'relative', width: '360px' }}>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Filtrar por DNI, apellidos o nombres..."
                  value={searchDni}
                  onChange={(e) => setSearchDni(e.target.value)}
                  style={{ paddingLeft: '2.5rem' }}
                />
                <Search size={16} style={{ position: 'absolute', left: '0.9rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              </div>

              <div style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
                Mostrando <strong style={{ color: 'var(--text-primary)' }}>{lineasFiltradas.length}</strong> de {lineas.length} trabajadores de {selectedPlanilla.tipo}
              </div>
            </div>

            {/* Tabla de Trabajadores con Acciones de Boleta */}
            <div className="table-container" style={{ maxHeight: '420px' }}>
              <table className="table" style={{ fontSize: '0.8rem' }}>
                <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
                  <tr>
                    <th style={{ width: 45 }}>N°</th>
                    <th style={{ width: 95 }}>DNI</th>
                    <th>Apellidos y Nombres</th>
                    <th>Establecimiento / Adscripción</th>
                    <th>Cargo</th>
                    <th style={{ textAlign: 'right', width: 110 }}>Líquido Neto</th>
                    <th style={{ textAlign: 'center', width: 220 }}>Acciones Boleta</th>
                  </tr>
                </thead>
                <tbody>
                  {loadingLineas ? (
                    <tr>
                      <td colSpan={7} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                        Cargando trabajadores de la planilla...
                      </td>
                    </tr>
                  ) : lineasFiltradas.length === 0 ? (
                    <tr>
                      <td colSpan={7} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                        No se encontraron trabajadores que coincidan con la búsqueda.
                      </td>
                    </tr>
                  ) : (
                    lineasFiltradas
                      .slice((currentPage - 1) * pageSize, currentPage * pageSize)
                      .map((t, idx) => (
                      <tr key={t.id}>
                        <td style={{ color: 'var(--text-muted)' }}>{(currentPage - 1) * pageSize + idx + 1}</td>
                        <td style={{ fontFamily: 'monospace', fontWeight: 600, color: 'var(--teal-500)' }}>
                          {t.dni}
                        </td>
                        <td style={{ fontWeight: 600 }}>
                          {t.apellidos} {t.nombres}
                        </td>
                        <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          {t.institucion_nombre || t.area_nombre || 'UGEL CHEPÉN'}
                        </td>
                        <td style={{ fontSize: '0.75rem' }}>
                          {t.cargo}
                        </td>
                        <td style={{ textAlign: 'right', fontFamily: 'monospace', fontWeight: 700, color: '#10B981' }}>
                          S/ {Number(t.neto || 0).toFixed(2)}
                        </td>
                        <td style={{ textAlign: 'center' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.4rem' }}>
                            <button
                              onClick={() => handleImprimirBoleta(t.dni)}
                              className="btn btn-primary"
                              style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
                              title="Visualizar e Imprimir Boleta individual"
                            >
                              <Printer size={13} />
                              <span>Ver / Imprimir</span>
                            </button>
                            <button
                              onClick={() => handleDescargarBoleta(t.dni, t.apellidos)}
                              disabled={downloading === `boleta-${t.dni}`}
                              className="btn btn-secondary"
                              style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
                              title="Descargar archivo PDF de la boleta"
                            >
                              <Download size={13} />
                              <span>PDF</span>
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
              {lineasFiltradas.length > 0 && (
                <Pagination
                  currentPage={currentPage}
                  totalItems={lineasFiltradas.length}
                  pageSize={pageSize}
                  onPageChange={setCurrentPage}
                  onPageSizeChange={setPageSize}
                  pageSizeOptions={[10, 15, 25, 50, 100]}
                  itemLabel="trabajadores"
                />
              )}
            </div>
          </div>

          {/* 3. DOCUMENTOS CONSOLIDADOS MASIVOS */}
          <h3 style={{ fontSize: '1.15rem', marginBottom: '1rem', fontWeight: 700 }}>
            Documentos Masivos y Planillas Oficiales
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
            {/* 3.1 Planilla Oficial en PDF */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                  <div style={{ padding: '0.6rem', borderRadius: 'var(--radius-md)', background: 'rgba(239, 68, 68, 0.15)', color: '#EF4444' }}>
                    <FileText size={22} />
                  </div>
                  <div>
                    <h4 style={{ fontSize: '1rem', margin: 0, fontWeight: 700 }}>Planilla Oficial en PDF</h4>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Formato A4 Apaisado con Firmas</span>
                  </div>
                </div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
                  Documento formal con encabezados por página, desglose de los 8 descuentos autorizados y recuadros de firmas institucionales.
                </p>
              </div>
              <button
                onClick={() => handleDownload('pdf', `/api/documentos/planilla-pdf/${vId}`, `Planilla_${pTag}.pdf`)}
                disabled={downloading === 'pdf'}
                className="btn btn-primary"
              >
                <Download size={15} />
                <span>{downloading === 'pdf' ? 'Generando PDF...' : 'Descargar Planilla PDF'}</span>
              </button>
            </div>

            {/* 3.2 Planilla Oficial en Excel */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                  <div style={{ padding: '0.6rem', borderRadius: 'var(--radius-md)', background: 'rgba(16, 185, 129, 0.15)', color: 'var(--emerald-500)' }}>
                    <FileSpreadsheet size={22} />
                  </div>
                  <div>
                    <h4 style={{ fontSize: '1rem', margin: 0, fontWeight: 700 }}>Planilla Oficial en Excel (.xlsx)</h4>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Fidelidad a la Plantilla de Cálculo</span>
                  </div>
                </div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
                  Hoja de cálculo con celdas numéricas formateadas y fórmulas íntegras, óptima para fiscalización y control financiero.
                </p>
              </div>
              <button
                onClick={() => handleDownload('excel', `/api/documentos/planilla-excel/${vId}`, `Planilla_${pTag}.xlsx`)}
                disabled={downloading === 'excel'}
                className="btn btn-secondary"
              >
                <Download size={15} />
                <span>{downloading === 'excel' ? 'Generando Excel...' : 'Descargar Planilla Excel'}</span>
              </button>
            </div>

            {/* 3.3 Cuadernillo Mensual de Boletas */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                  <div style={{ padding: '0.6rem', borderRadius: 'var(--radius-md)', background: 'rgba(20, 184, 166, 0.15)', color: 'var(--teal-500)' }}>
                    <FileText size={22} />
                  </div>
                  <div>
                    <h4 style={{ fontSize: '1rem', margin: 0, fontWeight: 700 }}>Cuadernillo Mensual de Boletas</h4>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Todas las Boletas en un solo PDF</span>
                  </div>
                </div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
                  Compilación de las boletas individuales de todo el personal de la planilla seleccionada, listas para impresión en lote.
                </p>
              </div>
              <button
                onClick={() => handleDownload('boletas', `/api/documentos/cuadernillo-boletas/${vId}`, `Cuadernillo_${pTag}.pdf`)}
                disabled={downloading === 'boletas'}
                className="btn btn-primary"
              >
                <Download size={15} />
                <span>{downloading === 'boletas' ? 'Compilando...' : 'Descargar Todas las Boletas'}</span>
              </button>
            </div>

            {/* 3.4 Hoja de Remuneraciones */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                  <div style={{ padding: '0.6rem', borderRadius: 'var(--radius-md)', background: 'rgba(99, 102, 241, 0.15)', color: 'var(--indigo-500)' }}>
                    <Layers size={22} />
                  </div>
                  <div>
                    <h4 style={{ fontSize: '1rem', margin: 0, fontWeight: 700 }}>Hoja de Remuneraciones</h4>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Agrupada por Metas Presupuestarias</span>
                  </div>
                </div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
                  Resumen de importes brutos agrupados por meta presupuestal conforme a la estructura de UGEL Chepén.
                </p>
              </div>
              <button
                onClick={() => handleDownload('remun', `/api/documentos/remuneraciones-excel/${vId}`, `Remuneraciones_${pTag}.xlsx`)}
                disabled={downloading === 'remun'}
                className="btn btn-secondary"
              >
                <Download size={15} />
                <span>{downloading === 'remun' ? 'Generando...' : 'Descargar Remuneraciones'}</span>
              </button>
            </div>
          </div>

          {/* Nota Banco Bloqueado */}
          <div className="card" style={{ background: '#FFFBEB', border: '1px solid #FDE68A', borderLeft: '4px solid #D97706', padding: '1rem 1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Lock size={18} style={{ color: '#D97706' }} />
              <div>
                <h5 style={{ fontSize: '0.875rem', margin: 0, color: '#92400E' }}>Módulo de Archivo Bancario (TXT) Bloqueado Preventivamente</h5>
                <p style={{ fontSize: '0.775rem', margin: '0.2rem 0 0 0', color: '#B45309' }}>
                  Conforme a la Decisión Confirmada 4.5, la generación de archivos bancarios permanece bloqueada hasta validar la especificación técnica con el Banco de la Nación.
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
