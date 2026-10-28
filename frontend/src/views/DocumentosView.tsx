import React, { useState, useEffect } from 'react';
import { apiRequest, downloadFile, previewPdfInTab } from '../api/client';
import { mensajeDeError } from '../api/errors';
import { usePaginacion } from '../hooks/usePaginacion';
import { useAuth } from '../context/AuthContext';
import { PlanillaListItem, LineaPlanilla, VersionDetalle } from '../types';
import { Pagination } from '../components/Pagination';
import { 
  FileText, 
  FileSpreadsheet, 
  Download, 
  Printer, 
  Search, 
  Layers, 
  CheckCircle2, 
  Clock, 
  Calendar,
  Landmark,
  Building2,
  X,
  FileCheck
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
  const { user } = useAuth();
  // ADR-006: la emisión de documentos exige el permiso generar_documentos.
  const puedeGenerar = user?.rol === 'ADMINISTRADOR' || user?.rol === 'PLANILLAS';
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
  const [tipoTxBanco, setTipoTxBanco] = useState<'041' | '341'>('041');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // 1. Cargar planillas disponibles
  useEffect(() => {
    const fetchPlanillas = async () => {
      try {
        const list = await apiRequest<PlanillaListItem[]>('/api/planillas');
        setPlanillas(list);
      } catch (err) {
        setErrorMsg(mensajeDeError(err, 'Error al cargar lista de planillas.'));
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
        const data = await apiRequest<VersionDetalle>(`/api/planillas/versiones/${selectedPlanilla.version_id}`);
        setLineas(data.lineas || []);
      } catch (err) {
        setErrorMsg(mensajeDeError(err, 'Error al obtener personal de la planilla.'));
      } finally {
        setLoadingLineas(false);
      }
    };

    fetchDetalle();
  }, [selectedPlanilla]);

  const handleDownload = async (type: string, path: string, filename: string) => {
    setDownloading(type);
    setErrorMsg(null);
    try {
      await downloadFile(path, filename);
    } catch (err) {
      setErrorMsg(mensajeDeError(err, 'Error al descargar documento.'));
    } finally {
      setDownloading(null);
    }
  };

  const handleImprimirBoleta = async (dni: string) => {
    if (!selectedPlanilla) return;
    const vId = selectedPlanilla.version_id;
    try {
      await previewPdfInTab(`/api/documentos/boleta-dni/${vId}/${dni}`);
    } catch (err) {
      alert(mensajeDeError(err, `Error al visualizar la boleta del DNI ${dni}`));
    }
  };

  const handleDescargarBoleta = async (dni: string) => {
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

  const aniosDisponibles = Array.from(new Set([2026, ...planillas.map((p) => p.anio)])).sort((a, b) => b - a);
  const vId = selectedPlanilla?.version_id;
  const pTag = selectedPlanilla 
    ? `${selectedPlanilla.tipo}_${selectedPlanilla.anio}_${String(selectedPlanilla.mes).padStart(2, '0')}_v${selectedPlanilla.version_numero}` 
    : '';

  const lineasFiltradas = lineas.filter((l) => {
    if (!searchDni.trim()) return true;
    const q = searchDni.toLowerCase().trim();
    return l.dni.includes(q) || l.apellidos.toLowerCase().includes(q) || l.nombres.toLowerCase().includes(q);
  });

  const paginacion = usePaginacion(lineasFiltradas, { tamanoInicial: 15 });

  // Al cambiar de planilla o de búsqueda se vuelve a la primera página.
  useEffect(() => {
    paginacion.irAPagina(1);
  }, [selectedPlanilla, searchDni]);

  if (!puedeGenerar) {
    return (
      <div className="page-container">
        <div className="card" style={{ padding: '2rem', textAlign: 'center' }}>
          <h2 style={{ fontSize: '1.2rem', marginBottom: '0.5rem', color: '#0F172A', fontWeight: 800 }}>
            Documentos oficiales restringidos
          </h2>
          <p style={{ fontSize: '0.9rem', color: '#64748B', margin: 0 }}>
            Tu rol puede consultar planillas, pero la emisión de PDF, Excel, boletas y archivos
            bancarios requiere el permiso <strong>generar_documentos</strong>. Solicitá la
            habilitación a administración.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      {/* 1. SELECCIÓN DE ÁMBITO Y PARÁMETROS */}
      <div className="card" style={{ marginBottom: '1.75rem', padding: '1.25rem 1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1.25rem' }}>
          <div>
            <span style={{ fontSize: '0.725rem', fontWeight: 700, color: '#2563EB', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Expedición Institucional
            </span>
            <h2 style={{ fontSize: '1.35rem', marginTop: '0.15rem', marginBottom: '0.2rem', color: '#0F172A', fontWeight: 800 }}>
              Centro de Emisión de Boletas y Documentos Oficiales
            </h2>
            <p style={{ fontSize: '0.85rem', color: '#64748B', margin: 0 }}>
              Generación de boletas individuales, planillas impresas, cuadernillos y archivos de pago para el Banco de la Nación.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', flexWrap: 'wrap' }}>
            {/* Selector de Ámbito con SVG Icons */}
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

            {/* Selector de Año */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <span style={{ fontSize: '0.8rem', color: '#475569', fontWeight: 600 }}>Año:</span>
              <select
                className="form-select"
                style={{ width: '95px', fontWeight: 700 }}
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
              <span style={{ fontSize: '0.8rem', color: '#475569', fontWeight: 600 }}>Mes:</span>
              <select
                className="form-select"
                style={{ minWidth: '160px', fontWeight: 700 }}
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
              <span className={`badge ${selectedPlanilla.version_estado === 'CERRADA' ? 'badge-emerald' : 'badge-amber'}`} style={{ fontWeight: 700 }}>
                {selectedPlanilla.version_estado === 'CERRADA' ? <CheckCircle2 size={13} /> : <Clock size={13} />}
                v{selectedPlanilla.version_numero} · {selectedPlanilla.version_estado}
              </span>
            )}
          </div>
        </div>
      </div>

      {errorMsg && (
        <div style={{
          background: '#FEF2F2',
          border: '1.5px solid #FECACA',
          color: '#991B1B',
          padding: '0.85rem 1.25rem',
          borderRadius: 'var(--radius-md)',
          marginBottom: '1.5rem',
          fontSize: '0.85rem'
        }}>
          {errorMsg}
        </div>
      )}

      {/* Si no existe planilla para el año/mes seleccionado */}
      {!selectedPlanilla && (
        <div className="card" style={{ textAlign: 'center', padding: '4rem 2rem', border: '1px dashed #CBD5E1' }}>
          <div style={{
            width: 58,
            height: 58,
            borderRadius: 'var(--radius-full)',
            background: '#EFF6FF',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#1D4ED8',
            marginBottom: '1.25rem'
          }}>
            <Calendar size={28} />
          </div>
          <h3 style={{ fontSize: '1.25rem', marginBottom: '0.35rem', color: '#0F172A', fontWeight: 800 }}>
            Sin planilla disponible para {tipoFiltro === 'IIEE' ? 'Instituciones Educativas' : 'Sede UGEL'}
          </h3>
          <p style={{ color: '#64748B', maxWidth: '480px', margin: '0 auto', fontSize: '0.875rem' }}>
            Seleccione otro año o mes en los filtros superiores para emitir boletas y reportes.
          </p>
        </div>
      )}

      {selectedPlanilla && (
        <>
          {/* 2. SECCIÓN PRINCIPAL: BÚSQUEDA Y EMISIÓN INDIVIDUAL DE BOLETAS POR DNI */}
          <div className="card" style={{ marginBottom: '2.25rem', border: '1px solid #CBD5E1', background: '#FFFFFF' }}>
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
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div style={{
                  padding: '0.65rem',
                  borderRadius: 'var(--radius-md)',
                  background: '#EFF6FF',
                  color: '#1D4ED8',
                  border: '1px solid #DBEAFE'
                }}>
                  <Printer size={22} />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.15rem', margin: 0, fontWeight: 700, color: '#0F172A' }}>
                    Boletas de Pago Individuales (Formato Oficial UGEL Chepén)
                  </h3>
                  <span style={{ fontSize: '0.8rem', color: '#64748B' }}>
                    Emisión individualizada con desglose de descuentos de ley y firmas oficiales.
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
                  style={{ width: '190px', fontFamily: 'var(--font-mono)', fontWeight: 700 }}
                />
                <button
                  type="submit"
                  disabled={directDni.length !== 8}
                  className="btn btn-primary btn-sm"
                  style={{ padding: '0.55rem 0.95rem' }}
                >
                  <Printer size={15} />
                  <span>Imprimir Boleta</span>
                </button>
              </form>
            </div>

            {/* Barra de Filtro de Lista */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '1rem',
              flexWrap: 'wrap',
              gap: '0.75rem'
            }}>
              <div className="search-input-wrap" style={{ minWidth: '320px' }}>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Filtrar por DNI o apellidos..."
                  value={searchDni}
                  onChange={(e) => setSearchDni(e.target.value)}
                />
                <Search size={16} />
                {searchDni && (
                  <button
                    type="button"
                    onClick={() => setSearchDni('')}
                    className="btn btn-ghost"
                    style={{
                      position: 'absolute',
                      right: '0.4rem',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      padding: '0.25rem',
                      color: '#94A3B8'
                    }}
                    title="Limpiar filtro"
                  >
                    <X size={14} />
                  </button>
                )}
              </div>

              <div style={{ fontSize: '0.825rem', color: '#64748B' }}>
                Mostrando <strong style={{ color: '#0F172A' }}>{lineasFiltradas.length}</strong> de {lineas.length} trabajadores en esta versión
              </div>
            </div>

            {/* Tabla de Trabajadores con Acciones de Boleta */}
            <div className="table-container" style={{ maxHeight: '430px' }}>
              <table className="table">
                <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
                  <tr>
                    <th style={{ width: 45, textAlign: 'center' }}>N°</th>
                    <th style={{ width: 95 }}>DNI</th>
                    <th>Apellidos y Nombres</th>
                    <th>Establecimiento / Adscripción</th>
                    <th>Cargo</th>
                    <th style={{ textAlign: 'right', width: 120 }}>Líquido Neto</th>
                    <th style={{ textAlign: 'center', width: 220 }}>Acciones Boleta</th>
                  </tr>
                </thead>
                <tbody>
                  {loadingLineas ? (
                    <tr>
                      <td colSpan={7} style={{ textAlign: 'center', padding: '2.5rem', color: '#64748B' }}>
                        Cargando nómina de la planilla...
                      </td>
                    </tr>
                  ) : lineasFiltradas.length === 0 ? (
                    <tr>
                      <td colSpan={7} style={{ textAlign: 'center', padding: '2.5rem', color: '#64748B' }}>
                        No se encontraron servidores con el término de búsqueda.
                      </td>
                    </tr>
                  ) : (
                    paginacion.items.map((t, idx) => (
                      <tr key={t.id}>
                        <td style={{ color: '#64748B', textAlign: 'center' }}>
                          {paginacion.desde + idx}
                        </td>
                        <td className="mono-amount" style={{ fontWeight: 700, color: '#1D4ED8' }}>
                          {t.dni}
                        </td>
                        <td style={{ fontWeight: 700, color: '#0F172A' }}>
                          {t.apellidos} {t.nombres}
                        </td>
                        <td style={{ fontSize: '0.775rem', color: '#475569' }}>
                          {t.institucion_nombre || t.area_nombre || 'UGEL CHEPÉN'}
                        </td>
                        <td style={{ fontSize: '0.775rem', color: '#64748B' }}>
                          {t.cargo || '—'}
                        </td>
                        <td className="mono-amount" style={{ textAlign: 'right', fontWeight: 800, color: Number(t.neto || 0) < 0 ? '#DC2626' : '#059669' }}>
                          S/ {Number(t.neto || 0).toFixed(2)}
                        </td>
                        <td style={{ textAlign: 'center' }}>
                          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
                            <button
                              onClick={() => handleImprimirBoleta(t.dni)}
                              className="btn btn-primary btn-sm"
                              style={{ padding: '0.3rem 0.65rem' }}
                              title="Visualizar e Imprimir Boleta individual"
                            >
                              <Printer size={13} />
                              <span>Ver / Imprimir</span>
                            </button>
                            <button
                              onClick={() => handleDescargarBoleta(t.dni)}
                              disabled={downloading === `boleta-${t.dni}`}
                              className="btn btn-secondary btn-sm"
                              style={{ padding: '0.3rem 0.65rem' }}
                              title="Descargar PDF"
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
                  currentPage={paginacion.pagina}
                  totalItems={paginacion.total}
                  pageSize={paginacion.tamano}
                  onPageChange={paginacion.irAPagina}
                  onPageSizeChange={paginacion.cambiarTamano}
                  pageSizeOptions={[15, 30, 50, 100]}
                  itemLabel="servidores"
                />
              )}
            </div>
          </div>

          {/* 3. DOCUMENTOS CONSOLIDADOS MASIVOS */}
          <div style={{ marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1.2rem', color: '#0F172A', fontWeight: 800, margin: '0 0 0.2rem' }}>
              Documentos Masivos y Archivos Oficiales
            </h3>
            <p style={{ fontSize: '0.85rem', color: '#64748B', margin: 0 }}>
              Archivos compilados para fiscalización administrativa, auditoría y abono en cuentas del Banco de la Nación.
            </p>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(310px, 1fr))',
            gap: '1.25rem',
            marginBottom: '2rem'
          }}>
            {/* 3.1 Planilla Oficial en PDF */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.85rem' }}>
                  <div style={{ padding: '0.6rem', borderRadius: 'var(--radius-md)', background: '#FEF2F2', color: '#DC2626', border: '1px solid #FECACA' }}>
                    <FileText size={22} />
                  </div>
                  <div>
                    <h4 style={{ fontSize: '0.975rem', margin: 0, fontWeight: 700, color: '#0F172A' }}>Planilla Oficial en PDF</h4>
                    <span style={{ fontSize: '0.75rem', color: '#64748B' }}>Formato A4 Apaisado con Firmas</span>
                  </div>
                </div>
                <p style={{ fontSize: '0.825rem', color: '#64748B', marginBottom: '1.25rem' }}>
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
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.85rem' }}>
                  <div style={{ padding: '0.6rem', borderRadius: 'var(--radius-md)', background: '#ECFDF5', color: '#059669', border: '1px solid #A7F3D0' }}>
                    <FileSpreadsheet size={22} />
                  </div>
                  <div>
                    <h4 style={{ fontSize: '0.975rem', margin: 0, fontWeight: 700, color: '#0F172A' }}>Planilla Oficial en Excel (.xlsx)</h4>
                    <span style={{ fontSize: '0.75rem', color: '#64748B' }}>Fidelidad a la Plantilla de Cálculo</span>
                  </div>
                </div>
                <p style={{ fontSize: '0.825rem', color: '#64748B', marginBottom: '1.25rem' }}>
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
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.85rem' }}>
                  <div style={{ padding: '0.6rem', borderRadius: 'var(--radius-md)', background: '#F0F9FF', color: '#0284C7', border: '1px solid #BAE6FD' }}>
                    <FileText size={22} />
                  </div>
                  <div>
                    <h4 style={{ fontSize: '0.975rem', margin: 0, fontWeight: 700, color: '#0F172A' }}>Cuadernillo Mensual de Boletas</h4>
                    <span style={{ fontSize: '0.75rem', color: '#64748B' }}>Todas las Boletas en un solo PDF</span>
                  </div>
                </div>
                <p style={{ fontSize: '0.825rem', color: '#64748B', marginBottom: '1.25rem' }}>
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
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.85rem' }}>
                  <div style={{ padding: '0.6rem', borderRadius: 'var(--radius-md)', background: '#EEF2FF', color: '#4F46E5', border: '1px solid #C7D2FE' }}>
                    <Layers size={22} />
                  </div>
                  <div>
                    <h4 style={{ fontSize: '0.975rem', margin: 0, fontWeight: 700, color: '#0F172A' }}>Hoja de Remuneraciones CAFAE</h4>
                    <span style={{ fontSize: '0.75rem', color: '#64748B' }}>Agrupada por Metas Presupuestarias</span>
                  </div>
                </div>
                <p style={{ fontSize: '0.825rem', color: '#64748B', marginBottom: '1.25rem' }}>
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

            {/* 3.5 Archivo Bancario TXT (Banco de la Nación) */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', border: '1.5px solid #FED7AA' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.85rem' }}>
                  <div style={{ padding: '0.6rem', borderRadius: 'var(--radius-md)', background: '#FFF7ED', color: '#EA580C', border: '1px solid #FFEDD5' }}>
                    <Landmark size={22} />
                  </div>
                  <div>
                    <h4 style={{ fontSize: '0.975rem', margin: 0, fontWeight: 700, color: '#0F172A' }}>Archivo Bancario TXT (BN)</h4>
                    <span style={{ fontSize: '0.75rem', color: '#64748B' }}>Formato Multired 28 caracteres</span>
                  </div>
                </div>
                <p style={{ fontSize: '0.825rem', color: '#64748B', marginBottom: '0.85rem' }}>
                  Dispersión oficial de pagos Banco de la Nación: Código (3) + Cuenta (10) + Céntimos (15). Total 28 caracteres.
                </p>
                <div style={{ marginBottom: '1.15rem' }}>
                  <label className="form-label" style={{ fontSize: '0.775rem' }}>
                    Tipo de Transacción BN:
                  </label>
                  <select
                    className="form-select"
                    style={{ fontSize: '0.825rem', padding: '0.45rem 0.65rem' }}
                    value={tipoTxBanco}
                    onChange={(e) => setTipoTxBanco(e.target.value as '041' | '341')}
                  >
                    <option value="041">041 - Pago de Haberes (Remunerativo)</option>
                    <option value="341">341 - Abono No Remunerativo</option>
                  </select>
                </div>
              </div>
              <button
                onClick={() => handleDownload('txt', `/api/documentos/banco-txt/${vId}?tipo_transaccion=${tipoTxBanco}`, `Abono_BN_${pTag}_${tipoTxBanco}.txt`)}
                disabled={downloading === 'txt'}
                className="btn btn-primary"
                style={{ background: '#EA580C', borderColor: '#EA580C' }}
              >
                <Download size={15} />
                <span>{downloading === 'txt' ? 'Generando TXT...' : 'Descargar Archivo Bancario TXT'}</span>
              </button>
            </div>
          </div>

          {/* Información Técnica Estructura Banco de la Nación */}
          <div className="card" style={{ background: '#F0FDF4', border: '1px solid #BBF7D0', borderLeft: '4px solid #16A34A', padding: '1.15rem 1.35rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
              <CheckCircle2 size={22} style={{ color: '#16A34A', flexShrink: 0 }} />
              <div>
                <h5 style={{ fontSize: '0.9rem', margin: 0, color: '#15803D', fontWeight: 700 }}>
                  Estructura Certificada para Banco de la Nación (Multired / Telecrédito)
                </h5>
                <p style={{ fontSize: '0.8rem', margin: '0.25rem 0 0', color: '#166534', lineHeight: 1.45 }}>
                  Cada registro del archivo cumple con la longitud estricta de <strong>28 caracteres continuos</strong> sin separadores:
                  <strong> Transacción</strong> (3 caracteres: <code>041</code> o <code>341</code>) + 
                  <strong> Cuenta</strong> (10 caracteres de cuenta de ahorros) + 
                  <strong> Importe</strong> (15 caracteres numéricos en céntimos sin puntos ni comas, con ceros iniciales).
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
