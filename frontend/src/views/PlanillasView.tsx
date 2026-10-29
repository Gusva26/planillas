import React, { useEffect, useState } from 'react';
import { apiRequest } from '../api/client';
import { mensajeDeError } from '../api/errors';
import { usePaginacion } from '../hooks/usePaginacion';
import { useAuth } from '../context/AuthContext';
import {
  CambioLineaPlanilla,
  CatalogoBundle,
  LineaPlanilla,
  PlanillaListItem,
  PlanillaVersion,
  RespuestaCreacionPlanilla,
  ValorLinea,
  VersionDetalle,
} from '../types';
import { Modal } from '../components/Modal';
import { Pagination } from '../components/Pagination';
import { 
  FileSpreadsheet, 
  Plus, 
  Save, 
  Trash2, 
  Lock, 
  Unlock, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  Search, 
  Building2,
  Landmark,
  Calendar,
  X,
  FileCheck
} from 'lucide-react';

/** Valor editable de una celda de descuento: los conceptos son dinámicos. */
const valorEditable = (valor: ValorLinea): string | number =>
  typeof valor === 'number' || typeof valor === 'string' ? valor : '';

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

export const PlanillasView: React.FC = () => {
  const { user } = useAuth();
  const [planillas, setPlanillas] = useState<PlanillaListItem[]>([]);
  const [tipoFiltro, setTipoFiltro] = useState<'IIEE' | 'SEDE'>('IIEE');
  const [selectedAnio, setSelectedAnio] = useState<number>(2026);
  const [selectedMes, setSelectedMes] = useState<number>(3);
  const [selectedPlanillaId, setSelectedPlanillaId] = useState<number | null>(null);
  const [versionData, setVersionData] = useState<PlanillaVersion | null>(null);
  const [lineas, setLineas] = useState<LineaPlanilla[]>([]);
  const [originalLineas, setOriginalLineas] = useState<Record<number, LineaPlanilla>>({});
  const [catalogos, setCatalogos] = useState<CatalogoBundle | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState('');

  // Modales
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isCloseOpen, setIsCloseOpen] = useState(false);
  const [isReopenOpen, setIsReopenOpen] = useState(false);
  const [isClearOpen, setIsClearOpen] = useState(false);

  // Forms states
  const [createForm, setCreateForm] = useState({ anio: 2026, mes: 3, tipo: 'IIEE', origen: 'MAESTRO' });
  const [closeFirmas, setCloseFirmas] = useState<number[]>([]);
  const [reopenMotivo, setReopenMotivo] = useState('');
  const [clearConcepto, setClearConcepto] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const canEdit = user && ['ADMINISTRADOR', 'PLANILLAS'].includes(user.rol);
  const isAdmin = user && user.rol === 'ADMINISTRADOR';

  const aniosDisponibles = Array.from(
    new Set(planillas.map((p) => p.anio).concat([2026, 2025]))
  ).sort((a, b) => b - a);

  // 1. Cargar lista de planillas y catálogos
  const loadPlanillas = async () => {
    setLoading(true);
    try {
      const [list, cats] = await Promise.all([
        apiRequest<PlanillaListItem[]>('/api/planillas'),
        apiRequest<CatalogoBundle>('/api/catalogos/bundle'),
      ]);
      setPlanillas(list);
      setCatalogos(cats);
    } catch (err) {
      console.error('Error al cargar planillas:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPlanillas();
  }, []);

  // Sincronizar automáticamente la planilla seleccionada por tipo, año y mes
  useEffect(() => {
    const found = planillas.find(
      (p) => p.tipo === tipoFiltro && p.anio === selectedAnio && p.mes === selectedMes
    );
    if (found) {
      setSelectedPlanillaId(found.id);
    } else {
      setSelectedPlanillaId(null);
      setVersionData(null);
      setLineas([]);
    }
  }, [tipoFiltro, selectedAnio, selectedMes, planillas]);

  // 2. Cargar detalle de la planilla seleccionada
  const loadVersionDetalle = async (planillaId: number) => {
    const p = planillas.find((item) => item.id === planillaId);
    if (!p) return;
    try {
      const data = await apiRequest<VersionDetalle>(`/api/planillas/versiones/${p.version_id}`);
      setVersionData(data.version);
      setLineas(data.lineas);
      const map: Record<number, LineaPlanilla> = {};
      data.lineas.forEach((l) => { map[l.id] = { ...l }; });
      setOriginalLineas(map);
    } catch (err) {
      setErrorMsg(mensajeDeError(err, 'Error al cargar líneas de planilla.'));
    }
  };

  useEffect(() => {
    if (selectedPlanillaId) {
      loadVersionDetalle(selectedPlanillaId);
    }
  }, [selectedPlanillaId, planillas]);

  useEffect(() => {
    paginacion.irAPagina(1);
  }, [selectedPlanillaId, tipoFiltro, search]);

  // Conceptos de descuento aplicables al ámbito actual (IIEE o SEDE)
  const tiposDescuentoFiltrados = (catalogos?.tipos_descuento || []).filter((td) => {
    const aplicaAmbito = tipoFiltro === 'IIEE' ? td.aplica_iiee : td.aplica_sede;
    if (!aplicaAmbito) return false;
    if (td.activo) return true;
    return lineas.some((l) => {
      const cod = td.codigo;
      const codLower = cod.toLowerCase();
      const val = Number(l[cod] ?? l[codLower] ?? (l.descuentos && l.descuentos[cod]) ?? 0);
      return val > 0;
    });
  }).sort((a, b) => a.orden - b.orden);

  // Manejo de edición reactiva en la grilla
  const handleCellChange = (id: number, field: string, value: string) => {
    setLineas((prev) =>
      prev.map((line) => {
        if (line.id !== id) return line;
        const numVal = value === '' ? 0 : parseFloat(value) || 0;
        const updated: LineaPlanilla = {
          ...line,
          [field]: numVal,
          [field.toLowerCase()]: numVal,
          descuentos: {
            ...(line.descuentos || {}),
            [field]: numVal,
          },
        };

        // Recálculo dinámico de Licencia y Neto
        const imp = Number(updated.importe || 0);
        const dias = Number(updated.dias_licencia || 0);
        const lic = dias > 0 ? (imp / 30) * dias : 0;
        updated.monto_licencia = Math.round(lic * 100) / 100;

        let totDescSinLicencia = 0;
        tiposDescuentoFiltrados.forEach((td) => {
          const cod = td.codigo;
          const codLower = cod.toLowerCase();
          const val = Number(
            updated[cod] ??
              updated[codLower] ??
              (updated.descuentos && updated.descuentos[cod]) ??
              0
          );
          totDescSinLicencia += val;
        });

        updated.total_descuentos = Math.round((updated.monto_licencia + totDescSinLicencia) * 100) / 100;
        updated.neto = Math.round((imp - updated.total_descuentos) * 100) / 100;

        return updated;
      })
    );
  };

  // Detectar filas modificadas
  const getModifiedRows = () => {
    const changes: CambioLineaPlanilla[] = [];
    lineas.forEach((l) => {
      const orig = originalLineas[l.id];
      if (!orig) return;

      const hasBaseChange =
        l.importe !== orig.importe || l.dias_licencia !== orig.dias_licencia;

      const descsPayload: Record<string, number> = {};
      let hasDescChange = false;

      tiposDescuentoFiltrados.forEach((td) => {
        const cod = td.codigo;
        const codLower = cod.toLowerCase();
        const currVal = Number(
          l[cod] ?? l[codLower] ?? (l.descuentos && l.descuentos[cod]) ?? 0
        );
        const origVal = Number(
          orig[cod] ?? orig[codLower] ?? (orig.descuentos && orig.descuentos[cod]) ?? 0
        );
        if (currVal !== origVal) {
          hasDescChange = true;
        }
        descsPayload[cod] = currVal;
      });

      if (hasBaseChange || hasDescChange) {
        changes.push({
          detalle_id: l.id,
          importe: l.importe,
          dias_licencia: l.dias_licencia,
          descuentos: descsPayload,
          ...descsPayload,
        });
      }
    });
    return changes;
  };

  const modifiedChanges = getModifiedRows();
  const hasChanges = modifiedChanges.length > 0;

  // Guardar Cambios en Lote
  const handleSaveBatch = async () => {
    if (!versionData || modifiedChanges.length === 0) return;
    setSaving(true);
    setErrorMsg(null);
    try {
      await apiRequest(`/api/planillas/versiones/${versionData.id}/lineas`, {
        method: 'PUT',
        body: JSON.stringify({
          revision_esperada: versionData.revision_edicion,
          cambios: modifiedChanges,
        }),
      });
      await loadPlanillas();
      if (selectedPlanillaId) loadVersionDetalle(selectedPlanillaId);
    } catch (err) {
      setErrorMsg(mensajeDeError(err, 'Error al guardar cambios de planilla.'));
    } finally {
      setSaving(false);
    }
  };

  // Crear Nueva Planilla
  const handleCreatePlanilla = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    try {
      const res = await apiRequest<RespuestaCreacionPlanilla>('/api/planillas', {
        method: 'POST',
        body: JSON.stringify(createForm),
      });
      setIsCreateOpen(false);
      await loadPlanillas();
      if (res.planilla?.planilla_id) {
        setSelectedPlanillaId(res.planilla.planilla_id);
      }
    } catch (err) {
      setErrorMsg(mensajeDeError(err, 'Error al crear planilla.'));
    }
  };

  // Limpiar Descuentos
  const handleClearDescuentos = async () => {
    if (!versionData) return;
    try {
      await apiRequest(`/api/planillas/versiones/${versionData.id}/limpiar`, {
        method: 'POST',
        body: JSON.stringify({
          revision_esperada: versionData.revision_edicion,
          concepto_codigo: clearConcepto || null,
        }),
      });
      setIsClearOpen(false);
      await loadPlanillas();
      if (selectedPlanillaId) loadVersionDetalle(selectedPlanillaId);
    } catch (err) {
      alert(mensajeDeError(err, 'Error al limpiar descuentos.'));
    }
  };

  // Cierre Formal
  const handleOpenCloseModal = () => {
    if (!versionData || !catalogos) return;
    const reqSignatures = versionData.tipo === 'IIEE' ? 4 : 3;
    // El catálogo no distingue ámbito: se proponen las primeras firmas activas
    // y el backend valida que sean exactamente las requeridas.
    const available = catalogos.firmas.filter((f) => f.activo);
    setCloseFirmas(available.slice(0, reqSignatures).map((f) => f.id));
    setIsCloseOpen(true);
  };

  const handleConfirmClose = async () => {
    if (!versionData) return;
    try {
      await apiRequest(`/api/planillas/versiones/${versionData.id}/cerrar`, {
        method: 'POST',
        body: JSON.stringify({
          revision_esperada: versionData.revision_edicion,
          firmas_ids: closeFirmas,
        }),
      });
      setIsCloseOpen(false);
      await loadPlanillas();
      if (selectedPlanillaId) loadVersionDetalle(selectedPlanillaId);
    } catch (err) {
      alert(mensajeDeError(err, 'Error al cerrar planilla.'));
    }
  };

  // Reapertura
  const handleConfirmReopen = async () => {
    if (!versionData || !reopenMotivo.trim()) return;
    try {
      await apiRequest(`/api/planillas/versiones/${versionData.id}/reabrir`, {
        method: 'POST',
        body: JSON.stringify({ motivo: reopenMotivo.trim() }),
      });
      setIsReopenOpen(false);
      setReopenMotivo('');
      await loadPlanillas();
      if (selectedPlanillaId) loadVersionDetalle(selectedPlanillaId);
    } catch (err) {
      alert(mensajeDeError(err, 'Error al reabrir planilla.'));
    }
  };

  const filteredLineas = lineas.filter(
    (l) =>
      !search ||
      l.dni.includes(search) ||
      l.apellidos.toLowerCase().includes(search.toLowerCase()) ||
      l.nombres.toLowerCase().includes(search.toLowerCase())
  );

  // La paginación se calcula sobre las filas ya filtradas.
  const paginacion = usePaginacion(filteredLineas, { tamanoInicial: 150 });

  const isClosed = versionData?.estado === 'CERRADA';
  const hasNegativeNet = lineas.some((l) => l.neto < 0);

  return (
    <div className="page-container">
      {/* Barra de Navegación y Parámetros del Periodo */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
        marginBottom: '1.25rem'
      }}>
        {/* Controles de Ámbito, Periodo y Mes */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem', flexWrap: 'wrap' }}>
          {/* Segmented Switcher IIEE vs SEDE con SVG Icons */}
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
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>Año:</span>
            <select
              className="form-select"
              style={{ width: 'auto', minWidth: '95px', fontWeight: 700 }}
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
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#475569' }}>Mes:</span>
            <select
              className="form-select"
              style={{ width: 'auto', minWidth: '160px', fontWeight: 700 }}
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

          {/* Badge de Estado de la Versión */}
          {versionData && (
            <span className={`badge ${isClosed ? 'badge-emerald' : 'badge-amber'}`} style={{ fontWeight: 700 }}>
              {isClosed ? <CheckCircle2 size={13} /> : <Clock size={13} />}
              v{versionData.numero} · {versionData.estado}
            </span>
          )}

          {canEdit && (
            <button 
              onClick={() => {
                setCreateForm({ anio: selectedAnio, mes: selectedMes, tipo: tipoFiltro, origen: 'MAESTRO' });
                setIsCreateOpen(true);
              }} 
              className="btn btn-secondary btn-sm"
              style={{ gap: '0.35rem' }}
            >
              <Plus size={15} />
              <span>Nueva Planilla</span>
            </button>
          )}
        </div>

        {/* Acciones de Edición, Guardado y Cierre */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          {hasChanges && (
            <button 
              onClick={handleSaveBatch} 
              disabled={saving} 
              className="btn btn-primary"
              style={{ fontWeight: 700, gap: '0.45rem', boxShadow: '0 2px 8px rgba(29, 78, 216, 0.25)' }}
            >
              <Save size={16} />
              <span>{saving ? 'Guardando...' : `Guardar Cambios (${modifiedChanges.length})`}</span>
            </button>
          )}

          {!isClosed && canEdit && (
            <button 
              onClick={() => setIsClearOpen(true)} 
              className="btn btn-ghost btn-sm" 
              title="Limpiar descuentos masivamente"
              style={{ color: '#DC2626' }}
            >
              <Trash2 size={15} />
              <span>Limpiar Valores</span>
            </button>
          )}

          {isAdmin && !isClosed && (
            <button 
              onClick={handleOpenCloseModal} 
              className="btn btn-success" 
              disabled={hasNegativeNet}
              title={hasNegativeNet ? 'No puede cerrar con netos negativos' : 'Congelar versión oficial'}
            >
              <Lock size={15} />
              <span>Cerrar Planilla</span>
            </button>
          )}

          {isAdmin && isClosed && (
            <button onClick={() => setIsReopenOpen(true)} className="btn btn-secondary">
              <Unlock size={15} />
              <span>Reabrir Versión</span>
            </button>
          )}
        </div>
      </div>

      {errorMsg && (
        <div style={{
          background: '#FEF2F2',
          border: '1.5px solid #FECACA',
          padding: '0.85rem 1.25rem',
          borderRadius: 'var(--radius-md)',
          color: '#991B1B',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.65rem'
        }}>
          <AlertTriangle size={18} style={{ color: '#DC2626' }} />
          <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>{errorMsg}</span>
        </div>
      )}

      {/* Contenido condicional: no hay planilla vs grilla de datos */}
      {!selectedPlanillaId ? (
        <div className="card" style={{ textAlign: 'center', padding: '4rem 2rem', border: '1px dashed #CBD5E1' }}>
          <div style={{
            width: 60,
            height: 60,
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
            Sin planilla generada para {tipoFiltro === 'IIEE' ? 'Instituciones Educativas' : 'Sede UGEL'}
          </h3>
          <p style={{ color: '#64748B', maxWidth: '480px', margin: '0 auto 1.5rem', fontSize: '0.875rem' }}>
            No existe versión en el periodo {MESES.find(m => m.num === selectedMes)?.nombre} {selectedAnio}.
            Puedes crearla directamente con el personal registrado en el maestro.
          </p>
          {canEdit && (
            <button
              onClick={() => {
                setCreateForm({ anio: selectedAnio, mes: selectedMes, tipo: tipoFiltro, origen: 'MAESTRO' });
                setIsCreateOpen(true);
              }}
              className="btn btn-primary"
              style={{ fontWeight: 700 }}
            >
              <Plus size={16} />
              <span>Generar Planilla {MESES.find(m => m.num === selectedMes)?.nombre} {selectedAnio}</span>
            </button>
          )}
        </div>
      ) : (
        <>
          {/* Ficha Resumen Ejecutivo de la Planilla Activa */}
          {versionData && (
            <div className="card" style={{ marginBottom: '1.25rem', padding: '1.25rem 1.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1.25rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
                      <span className={`badge ${versionData.tipo === 'IIEE' ? 'badge-indigo' : 'badge-teal'}`}>
                        {versionData.tipo === 'IIEE' ? 'Instituciones Educativas' : 'Sede UGEL'}
                      </span>
                      <span className={`badge ${isClosed ? 'badge-emerald' : 'badge-amber'}`}>
                        {versionData.estado}
                      </span>
                    </div>
                    <h3 style={{ fontSize: '1.2rem', color: '#0F172A', fontWeight: 800, margin: 0 }}>
                      Periodo {versionData.anio}-{String(versionData.mes).padStart(2, '0')} · Versión N° {versionData.numero}
                    </h3>
                    <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '0.2rem' }}>
                      Origen: <strong>{versionData.origen}</strong> • Responsable: <strong>{versionData.creada_por_nombre || 'Sistema'}</strong>
                    </div>
                  </div>
                </div>

                {/* Métricas Consolidadas Rápidas */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '2rem', flexWrap: 'wrap' }}>
                  <div>
                    <span style={{ fontSize: '0.7rem', color: '#64748B', textTransform: 'uppercase', fontWeight: 600, display: 'block' }}>
                      Servidores
                    </span>
                    <div style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0F172A' }}>
                      {lineas.length}
                    </div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.7rem', color: '#64748B', textTransform: 'uppercase', fontWeight: 600, display: 'block' }}>
                      Masa Bruta
                    </span>
                    <div className="mono-amount" style={{ fontSize: '1.15rem', fontWeight: 700, color: '#0F172A' }}>
                      S/ {lineas.reduce((acc, l) => acc + Number(l.importe || 0), 0).toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.7rem', color: '#64748B', textTransform: 'uppercase', fontWeight: 600, display: 'block' }}>
                      Descuentos
                    </span>
                    <div className="mono-amount" style={{ fontSize: '1.15rem', fontWeight: 700, color: '#DC2626' }}>
                      -S/ {lineas.reduce((acc, l) => acc + Number(l.total_descuentos || 0), 0).toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.7rem', color: '#64748B', textTransform: 'uppercase', fontWeight: 600, display: 'block' }}>
                      Líquido Neto
                    </span>
                    <div className="mono-amount" style={{ fontSize: '1.25rem', fontWeight: 800, color: '#1D4ED8' }}>
                      S/ {lineas.reduce((acc, l) => acc + Number(l.neto || 0), 0).toFixed(2)}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Barra de Filtro Rápido en Grilla */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '0.85rem',
            flexWrap: 'wrap',
            gap: '0.75rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
              <div className="search-input-wrap" style={{ minWidth: '300px' }}>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Filtrar por DNI o apellidos..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <Search size={16} />
                {search && (
                  <button
                    type="button"
                    onClick={() => setSearch('')}
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
              <span style={{ fontSize: '0.8rem', color: '#64748B' }}>
                Mostrando <strong>{filteredLineas.length}</strong> de {lineas.length} registros
              </span>
            </div>

            <div>
              {isClosed ? (
                <span style={{
                  fontSize: '0.8rem',
                  color: '#166534',
                  background: '#DCFCE7',
                  border: '1px solid #BBF7D0',
                  padding: '0.35rem 0.75rem',
                  borderRadius: 'var(--radius-sm)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  fontWeight: 600
                }}>
                  <Lock size={14} /> Planilla Inmutable
                </span>
              ) : (
                <span style={{
                  fontSize: '0.8rem',
                  color: '#92400E',
                  background: '#FEF3C7',
                  border: '1px solid #FDE68A',
                  padding: '0.35rem 0.75rem',
                  borderRadius: 'var(--radius-sm)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  fontWeight: 600
                }}>
                  <Clock size={14} /> Cuadrícula Editable en Tiempo Real
                </span>
              )}
            </div>
          </div>

          {/* Grilla Jerárquica de Edición de Planilla */}
          <div className="table-container" style={{ maxHeight: '68vh' }}>
            <table className="table">
              <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
                {/* Nivel 1: Macro-grupos de la Planilla */}
                <tr>
                  <th colSpan={4} className="th-group-personal">
                    DATOS DEL SERVIDOR PÚBLICO
                  </th>
                  <th colSpan={1} className="th-group-base">
                    BASE IMPONIBLE
                  </th>
                  <th colSpan={2} className="th-group-licencias">
                    LICENCIAS S/G
                  </th>
                  <th colSpan={tiposDescuentoFiltrados.length || 1} className="th-group-descuentos">
                    DESCUENTOS POR PLANILLA ({tiposDescuentoFiltrados.length} CONCEPTOS)
                  </th>
                  <th colSpan={2} className="th-group-neto">
                    LIQUIDACIÓN FINAL
                  </th>
                </tr>
                {/* Nivel 2: Columnas Específicas */}
                <tr>
                  <th style={{ width: 40, textAlign: 'center' }}>N°</th>
                  <th style={{ width: 95 }}>DNI</th>
                  <th>Apellidos y Nombres</th>
                  <th>Centro Laboral / Área</th>
                  <th style={{ textAlign: 'right', width: 105 }}>Haber Base</th>
                  <th style={{ textAlign: 'center', width: 65 }}>Días</th>
                  <th style={{ textAlign: 'right', width: 90 }}>Monto S/G</th>
                  {tiposDescuentoFiltrados.map((td) => (
                    <th key={td.id} style={{ textAlign: 'right', minWidth: 85 }} title={`Código: ${td.codigo}`}>
                      {td.nombre}
                    </th>
                  ))}
                  <th style={{ textAlign: 'right', width: 110 }} className="col-highlight-desc">Total Desc.</th>
                  <th style={{ textAlign: 'right', width: 120 }} className="col-highlight-neto">Líquido Neto</th>
                </tr>
              </thead>
              <tbody>
                {paginacion.items
                  .map((l, index) => {
                    const rowIndex = paginacion.desde + index;
                    const origRow = originalLineas[l.id];
                    const isModified =
                      !!origRow &&
                      (l.importe !== origRow.importe ||
                        l.dias_licencia !== origRow.dias_licencia ||
                        tiposDescuentoFiltrados.some((td) => {
                          const cod = td.codigo;
                          const codLower = cod.toLowerCase();
                          const curr = Number(l[cod] ?? l[codLower] ?? (l.descuentos && l.descuentos[cod]) ?? 0);
                          const orig = Number(
                            origRow[cod] ??
                              origRow[codLower] ??
                              (origRow.descuentos && origRow.descuentos[cod]) ??
                              0
                          );
                          return curr !== orig;
                        }));

                    const isNeg = l.neto < 0;

                    return (
                      <tr key={l.id} style={{ background: isNeg ? '#FEE2E2' : isModified ? '#ECFDF5' : undefined }}>
                        <td style={{ color: '#64748B', textAlign: 'center', fontWeight: 600 }}>{rowIndex}</td>
                        <td className="mono-amount" style={{ fontWeight: 600 }}>
                          <span style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', padding: '0.15rem 0.45rem', borderRadius: 'var(--radius-sm)' }}>
                            {l.dni}
                          </span>
                        </td>
                        <td style={{ fontWeight: 700, color: '#0F172A', whiteSpace: 'nowrap' }}>
                          {l.apellidos}, {l.nombres}
                        </td>
                        <td style={{ fontSize: '0.775rem', color: '#475569' }}>
                          {l.institucion_nombre || l.area_nombre || '—'}
                        </td>

                        {/* Importe Base */}
                        <td style={{ textAlign: 'right' }}>
                          {isClosed ? (
                            <span className="mono-amount" style={{ fontWeight: 700, color: '#0F172A' }}>
                              S/ {Number(l.importe).toFixed(2)}
                            </span>
                          ) : (
                            <input
                              type="number"
                              step="0.01"
                              className="grid-input"
                              value={l.importe}
                              onChange={(e) => handleCellChange(l.id, 'importe', e.target.value)}
                            />
                          )}
                        </td>

                        {/* Días Licencia */}
                        <td style={{ textAlign: 'center' }}>
                          {isClosed ? (
                            l.dias_licencia > 0 ? (
                              <span className="badge badge-amber" style={{ padding: '0.15rem 0.5rem', fontWeight: 700 }}>
                                {l.dias_licencia} d
                              </span>
                            ) : (
                              <span style={{ color: '#CBD5E1' }}>0</span>
                            )
                          ) : (
                            <input
                              type="number"
                              min="0"
                              max="30"
                              className="grid-input"
                              style={{ width: 55, textAlign: 'center' }}
                              value={l.dias_licencia}
                              onChange={(e) => handleCellChange(l.id, 'dias_licencia', e.target.value)}
                            />
                          )}
                        </td>

                        {/* Monto Licencia Calculado */}
                        <td className="mono-amount" style={{ textAlign: 'right' }}>
                          {Number(l.monto_licencia || 0) > 0 ? (
                            <span style={{ color: '#DC2626', fontWeight: 700 }}>
                              S/ {Number(l.monto_licencia).toFixed(2)}
                            </span>
                          ) : (
                            <span style={{ color: '#CBD5E1' }}>—</span>
                          )}
                        </td>

                        {/* Descuentos Dinámicos según Configuración y Ámbito */}
                        {tiposDescuentoFiltrados.map((td) => {
                          const cod = td.codigo;
                          const codLower = cod.toLowerCase();
                          const val = Number(l[cod] ?? l[codLower] ?? (l.descuentos && l.descuentos[cod]) ?? 0);
                          return (
                            <td key={td.id} style={{ textAlign: 'right' }}>
                              {isClosed ? (
                                val > 0 ? (
                                  <span className="mono-amount" style={{ fontWeight: 700, color: '#0F172A' }}>
                                    {val.toFixed(2)}
                                  </span>
                                ) : (
                                  <span style={{ color: '#CBD5E1' }}>—</span>
                                )
                              ) : (
                                <input
                                  type="number"
                                  step="0.01"
                                  className="grid-input"
                                  value={valorEditable(l[cod] ?? l[codLower])}
                                  placeholder="0.00"
                                  onChange={(e) => handleCellChange(l.id, cod, e.target.value)}
                                />
                              )}
                            </td>
                          );
                        })}

                        {/* Total Descuentos */}
                        <td className="mono-amount col-highlight-desc" style={{ textAlign: 'right', color: '#DC2626', fontWeight: 700 }}>
                          S/ {Number(l.total_descuentos || 0).toFixed(2)}
                        </td>

                        {/* Líquido Neto */}
                        <td className="mono-amount col-highlight-neto" style={{ textAlign: 'right', color: isNeg ? '#DC2626' : '#1D4ED8', fontWeight: 800, fontSize: '0.875rem' }}>
                          S/ {Number(l.neto || 0).toFixed(2)}
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
              <tfoot style={{ position: 'sticky', bottom: 0, zIndex: 9 }}>
                <tr className="tfoot-totals">
                  <td colSpan={4} style={{ textAlign: 'right', fontWeight: 800, textTransform: 'uppercase', fontSize: '0.75rem', letterSpacing: '0.04em' }}>
                    TOTAL GENERAL ({filteredLineas.length} Servidores):
                  </td>
                  <td className="mono-amount" style={{ textAlign: 'right', fontWeight: 800, color: '#166534' }}>
                    S/ {filteredLineas.reduce((acc, l) => acc + Number(l.importe || 0), 0).toFixed(2)}
                  </td>
                  <td style={{ textAlign: 'center', fontWeight: 700 }}>
                    {filteredLineas.reduce((acc, l) => acc + Number(l.dias_licencia || 0), 0) > 0 
                      ? `${filteredLineas.reduce((acc, l) => acc + Number(l.dias_licencia || 0), 0)} d` 
                      : '0 d'}
                  </td>
                  <td className="mono-amount" style={{ textAlign: 'right', fontWeight: 700, color: '#DC2626' }}>
                    S/ {filteredLineas.reduce((acc, l) => acc + Number(l.monto_licencia || 0), 0).toFixed(2)}
                  </td>
                  <td className="mono-amount" style={{ textAlign: 'right', fontWeight: 700 }}>
                    S/ {filteredLineas.reduce((acc, l) => acc + Number(l.pichincha || 0), 0).toFixed(2)}
                  </td>
                  <td className="mono-amount" style={{ textAlign: 'right', fontWeight: 700 }}>
                    S/ {filteredLineas.reduce((acc, l) => acc + Number(l.sullana || 0), 0).toFixed(2)}
                  </td>
                  <td className="mono-amount" style={{ textAlign: 'right', fontWeight: 700 }}>
                    S/ {filteredLineas.reduce((acc, l) => acc + Number(l.subcafae || 0), 0).toFixed(2)}
                  </td>
                  <td className="mono-amount" style={{ textAlign: 'right', fontWeight: 700 }}>
                    S/ {filteredLineas.reduce((acc, l) => acc + Number(l.brenta || 0), 0).toFixed(2)}
                  </td>
                  <td className="mono-amount" style={{ textAlign: 'right', fontWeight: 700 }}>
                    S/ {filteredLineas.reduce((acc, l) => acc + Number(l.sitrase || 0), 0).toFixed(2)}
                  </td>
                  <td className="mono-amount" style={{ textAlign: 'right', fontWeight: 700 }}>
                    S/ {filteredLineas.reduce((acc, l) => acc + Number(l.fentase || 0), 0).toFixed(2)}
                  </td>
                  <td className="mono-amount" style={{ textAlign: 'right', fontWeight: 700 }}>
                    S/ {filteredLineas.reduce((acc, l) => acc + Number(l.otros || 0), 0).toFixed(2)}
                  </td>
                  <td className="mono-amount col-highlight-desc" style={{ textAlign: 'right', fontWeight: 800, color: '#DC2626' }}>
                    S/ {filteredLineas.reduce((acc, l) => acc + Number(l.total_descuentos || 0), 0).toFixed(2)}
                  </td>
                  <td className="mono-amount col-highlight-neto" style={{ textAlign: 'right', fontWeight: 800, color: '#1D4ED8', fontSize: '0.95rem' }}>
                    S/ {filteredLineas.reduce((acc, l) => acc + Number(l.neto || 0), 0).toFixed(2)}
                  </td>
                </tr>
              </tfoot>
            </table>
            {filteredLineas.length > 0 && (
              <Pagination
                currentPage={paginacion.pagina}
                totalItems={paginacion.total}
                pageSize={paginacion.tamano}
                onPageChange={paginacion.irAPagina}
                onPageSizeChange={paginacion.cambiarTamano}
                pageSizeOptions={[25, 50, 100, 150, 200]}
                itemLabel="servidores"
              />
            )}
          </div>
        </>
      )}

      {/* Modal Crear Planilla */}
      <Modal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Generar Nueva Versión de Planilla">
        <form onSubmit={handleCreatePlanilla}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Año</label>
              <input
                type="number"
                className="form-input"
                value={createForm.anio}
                onChange={(e) => setCreateForm({ ...createForm, anio: Number(e.target.value) })}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Mes</label>
              <select
                className="form-select"
                value={createForm.mes}
                onChange={(e) => setCreateForm({ ...createForm, mes: Number(e.target.value) })}
              >
                {MESES.map((m) => (
                  <option key={m.num} value={m.num}>
                    {m.num} - {m.nombre}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Ámbito de la Planilla</label>
            <select
              className="form-select"
              value={createForm.tipo}
              onChange={(e) => setCreateForm({ ...createForm, tipo: e.target.value })}
            >
              <option value="IIEE">Instituciones Educativas (II.EE.)</option>
              <option value="SEDE">Sede Central UGEL Chepén</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Origen de la Planilla</label>
            <select
              className="form-select"
              value={createForm.origen}
              onChange={(e) => setCreateForm({ ...createForm, origen: e.target.value })}
            >
              <option value="MAESTRO">Crear desde Maestro de Personal (descuentos iniciales en cero)</option>
              <option value="COPIA">Copiar del Mes Anterior (mantiene importes y descuentos anteriores)</option>
            </select>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1.5rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '1.25rem' }}>
            <button type="button" onClick={() => setIsCreateOpen(false)} className="btn btn-secondary">Cancelar</button>
            <button type="submit" className="btn btn-primary">Generar Planilla</button>
          </div>
        </form>
      </Modal>

      {/* Modal Cierre Formal */}
      <Modal isOpen={isCloseOpen} onClose={() => setIsCloseOpen(false)} title="Cierre Formal e Inmutable de Planilla">
        <p style={{ fontSize: '0.85rem', color: '#475569', marginBottom: '1.25rem' }}>
          El cierre formal congela la planilla y le otorga valor oficial inmutable. Requiere la asignación de las firmas institucionales ({versionData?.tipo === 'IIEE' ? '4 firmas' : '3 firmas'}).
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.5rem' }}>
          {catalogos?.firmas
            ?.filter((firma) => firma.activo && closeFirmas.includes(firma.id))
            .map((firma, idx) => (
              <div key={firma.id} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', background: '#F8FAFC', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', border: '1px solid #E2E8F0' }}>
                <span className="badge badge-teal">Firma {idx + 1}</span>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#0F172A' }}>{firma.nombre_completo}</div>
                  <div style={{ fontSize: '0.75rem', color: '#64748B' }}>{firma.cargo}</div>
                </div>
              </div>
            ))}
          {closeFirmas.length < (versionData?.tipo === 'IIEE' ? 4 : 3) && (
            <div style={{
              background: '#FEF3C7',
              border: '1px solid #FDE68A',
              color: '#92400E',
              padding: '0.75rem 1rem',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.8rem',
            }}>
              El catálogo de firmas activas no alcanza para cerrar esta planilla.
              Registrá {versionData?.tipo === 'IIEE' ? '4' : '3'} firmas activas en Catálogos.
            </div>
          )}
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
          <button onClick={() => setIsCloseOpen(false)} className="btn btn-secondary">Cancelar</button>
          <button onClick={handleConfirmClose} className="btn btn-success">Confirmar Cierre Oficial</button>
        </div>
      </Modal>

      {/* Modal Reabrir Planilla */}
      <Modal isOpen={isReopenOpen} onClose={() => setIsReopenOpen(false)} title="Reapertura Versionada de Planilla">
        <p style={{ fontSize: '0.85rem', color: '#475569', marginBottom: '1rem' }}>
          La reapertura creará una nueva versión editable (versión {(versionData?.numero || 1) + 1}), manteniendo la versión {versionData?.numero} inmutable para fines de trazabilidad.
        </p>
        <div className="form-group">
          <label className="form-label">Motivo Justificado de Reapertura *</label>
          <textarea
            className="form-input"
            rows={3}
            placeholder="Ingrese la justificación administrativa (ej. Corrección de descuento según memo...)"
            value={reopenMotivo}
            onChange={(e) => setReopenMotivo(e.target.value)}
          />
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
          <button onClick={() => setIsReopenOpen(false)} className="btn btn-secondary">Cancelar</button>
          <button onClick={handleConfirmReopen} className="btn btn-primary" disabled={reopenMotivo.trim().length < 5}>
            Confirmar Reapertura
          </button>
        </div>
      </Modal>

      {/* Modal Limpiar Descuentos */}
      <Modal isOpen={isClearOpen} onClose={() => setIsClearOpen(false)} title="Limpiar Descuentos en Masa">
        <p style={{ fontSize: '0.85rem', color: '#475569', marginBottom: '1.25rem' }}>
          Seleccione si desea poner en cero todos los descuentos o un concepto en particular:
        </p>
        <div className="form-group">
          <label className="form-label">Concepto a Limpiar</label>
          <select className="form-select" value={clearConcepto} onChange={(e) => setClearConcepto(e.target.value)}>
            <option value="">-- Todos los Descuentos y Licencias --</option>
            <option value="LICENCIA">Días de Licencia sin Goce</option>
            {tiposDescuentoFiltrados.map((td) => (
              <option key={td.id} value={td.codigo}>{td.nombre}</option>
            ))}
          </select>
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
          <button onClick={() => setIsClearOpen(false)} className="btn btn-secondary">Cancelar</button>
          <button onClick={handleClearDescuentos} className="btn btn-danger">Limpiar Valores</button>
        </div>
      </Modal>
    </div>
  );
};
