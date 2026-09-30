import React, { useEffect, useState } from 'react';
import { apiRequest } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { PlanillaListItem, LineaPlanilla, CatalogoBundle } from '../types';
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
  ChevronRight, 
  RotateCcw,
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

export const PlanillasView: React.FC = () => {
  const { user } = useAuth();
  const [planillas, setPlanillas] = useState<PlanillaListItem[]>([]);
  const [tipoFiltro, setTipoFiltro] = useState<'IIEE' | 'SEDE'>('IIEE');
  const [selectedAnio, setSelectedAnio] = useState<number>(2026);
  const [selectedMes, setSelectedMes] = useState<number>(3);
  const [selectedPlanillaId, setSelectedPlanillaId] = useState<number | null>(null);
  const [versionData, setVersionData] = useState<any | null>(null);
  const [lineas, setLineas] = useState<LineaPlanilla[]>([]);
  const [originalLineas, setOriginalLineas] = useState<Record<number, LineaPlanilla>>({});
  const [catalogos, setCatalogos] = useState<CatalogoBundle | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState('');

  // Paginación
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(150);

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
      const data = await apiRequest(`/api/planillas/versiones/${p.version_id}`);
      setVersionData(data.version);
      setLineas(data.lineas);
      const map: Record<number, LineaPlanilla> = {};
      data.lineas.forEach((l: LineaPlanilla) => { map[l.id] = { ...l }; });
      setOriginalLineas(map);
    } catch (err: any) {
      setErrorMsg(err.message || 'Error al cargar líneas de planilla.');
    }
  };

  useEffect(() => {
    if (selectedPlanillaId) {
      loadVersionDetalle(selectedPlanillaId);
    }
  }, [selectedPlanillaId, planillas]);

  useEffect(() => {
    setCurrentPage(1);
  }, [selectedPlanillaId, tipoFiltro, search]);

  // Manejo de edición reactiva en la grilla
  const handleCellChange = (id: number, field: string, value: string) => {
    setLineas((prev) =>
      prev.map((line) => {
        if (line.id !== id) return line;
        const updated = { ...line, [field]: value === '' ? 0 : parseFloat(value) || 0 };

        // Recálculo dinámico de Licencia y Neto
        const imp = Number(updated.importe || 0);
        const dias = Number(updated.dias_licencia || 0);
        const lic = dias > 0 ? (imp / 30) * dias : 0;
        updated.monto_licencia = Math.round(lic * 100) / 100;

        const totDesc =
          updated.monto_licencia +
          Number(updated.pichincha || 0) +
          Number(updated.sullana || 0) +
          Number(updated.subcafae || 0) +
          Number(updated.brenta || 0) +
          Number(updated.sitrase || 0) +
          Number(updated.fentase || 0) +
          Number(updated.otros || 0);

        updated.total_descuentos = Math.round(totDesc * 100) / 100;
        updated.neto = Math.round((imp - updated.total_descuentos) * 100) / 100;

        return updated;
      })
    );
  };

  // Detectar filas modificadas
  const getModifiedRows = () => {
    const changes: any[] = [];
    lineas.forEach((l) => {
      const orig = originalLineas[l.id];
      if (!orig) return;
      if (
        l.importe !== orig.importe ||
        l.dias_licencia !== orig.dias_licencia ||
        l.pichincha !== orig.pichincha ||
        l.sullana !== orig.sullana ||
        l.subcafae !== orig.subcafae ||
        l.brenta !== orig.brenta ||
        l.sitrase !== orig.sitrase ||
        l.fentase !== orig.fentase ||
        l.otros !== orig.otros
      ) {
        changes.push({
          detalle_id: l.id,
          importe: l.importe,
          dias_licencia: l.dias_licencia,
          PICHINCHA: l.pichincha,
          SULLANA: l.sullana,
          SUBCAFAE: l.subcafae,
          BRENTA: l.brenta,
          SITRASE: l.sitrase,
          FENTASE: l.fentase,
          OTROS: l.otros,
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
    } catch (err: any) {
      setErrorMsg(err.message || 'Error al guardar cambios de planilla.');
    } finally {
      setSaving(false);
    }
  };

  // Crear Nueva Planilla
  const handleCreatePlanilla = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    try {
      const res = await apiRequest('/api/planillas', {
        method: 'POST',
        body: JSON.stringify(createForm),
      });
      setIsCreateOpen(false);
      await loadPlanillas();
      if (res.planilla?.planilla_id) {
        setSelectedPlanillaId(res.planilla.planilla_id);
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Error al crear planilla.');
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
    } catch (err: any) {
      alert(err.message || 'Error al limpiar descuentos.');
    }
  };

  // Cierre Formal
  const handleOpenCloseModal = () => {
    if (!versionData || !catalogos) return;
    const reqSignatures = versionData.tipo === 'IIEE' ? 4 : 3;
    const available = catalogos.firmas.filter((f) => f.ambito === versionData.tipo);
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
    } catch (err: any) {
      alert(err.message || 'Error al cerrar planilla.');
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
    } catch (err: any) {
      alert(err.message || 'Error al reabrir planilla.');
    }
  };

  const filteredLineas = lineas.filter(
    (l) =>
      !search ||
      l.dni.includes(search) ||
      l.apellidos.toLowerCase().includes(search.toLowerCase()) ||
      l.nombres.toLowerCase().includes(search.toLowerCase())
  );

  const isClosed = versionData?.estado === 'CERRADA';
  const hasNegativeNet = lineas.some((l) => l.neto < 0);

  return (
    <div className="page-container">
      {/* Selector de Planillas y Acciones Principales */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          {/* Selector de Ámbito: IIEE vs SEDE */}
          <div style={{ display: 'inline-flex', background: '#F1F5F9', padding: '0.25rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', gap: '0.25rem' }}>
            <button
              type="button"
              onClick={() => setTipoFiltro('IIEE')}
              className={`btn ${tipoFiltro === 'IIEE' ? 'btn-primary' : 'btn-ghost'}`}
              style={{ padding: '0.4rem 0.9rem', fontSize: '0.825rem', fontWeight: 600, borderRadius: 'var(--radius-sm)' }}
            >
              🏫 II.EE.
            </button>
            <button
              type="button"
              onClick={() => setTipoFiltro('SEDE')}
              className={`btn ${tipoFiltro === 'SEDE' ? 'btn-primary' : 'btn-ghost'}`}
              style={{ padding: '0.4rem 0.9rem', fontSize: '0.825rem', fontWeight: 600, borderRadius: 'var(--radius-sm)' }}
            >
              🏢 SEDE UGEL
            </button>
          </div>

          {/* Filtro por Año */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Año:</span>
            <select
              className="form-select"
              style={{ width: 'auto', minWidth: '95px', fontWeight: 600 }}
              value={selectedAnio}
              onChange={(e) => setSelectedAnio(Number(e.target.value))}
            >
              {aniosDisponibles.map((a) => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
          </div>

          {/* Filtro por Mes */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Mes:</span>
            <select
              className="form-select"
              style={{ width: 'auto', minWidth: '150px', fontWeight: 600 }}
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

          {/* Versión y Estado Badge */}
          {versionData && (
            <span className={`badge ${isClosed ? 'badge-emerald' : 'badge-amber'}`} style={{ fontWeight: 600 }}>
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
              className="btn btn-secondary"
            >
              <Plus size={16} />
              <span>Nueva Planilla</span>
            </button>
          )}
        </div>

        {/* Acciones de Edición y Cierre */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {hasChanges && (
            <button onClick={handleSaveBatch} disabled={saving} className="btn btn-primary">
              <Save size={16} />
              <span>{saving ? 'Guardando...' : `Guardar Cambios (${modifiedChanges.length})`}</span>
            </button>
          )}

          {!isClosed && canEdit && (
            <button onClick={() => setIsClearOpen(true)} className="btn btn-ghost" title="Limpiar descuentos">
              <Trash2 size={16} />
              <span>Limpiar</span>
            </button>
          )}

          {isAdmin && !isClosed && (
            <button onClick={handleOpenCloseModal} className="btn btn-success" disabled={hasNegativeNet}>
              <Lock size={16} />
              <span>Cerrar Planilla</span>
            </button>
          )}

          {isAdmin && isClosed && (
            <button onClick={() => setIsReopenOpen(true)} className="btn btn-secondary">
              <Unlock size={16} />
              <span>Reabrir Planilla</span>
            </button>
          )}
        </div>
      </div>

      {errorMsg && (
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid var(--crimson-500)', padding: '0.85rem 1.25rem', borderRadius: 'var(--radius-md)', color: '#F87171', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AlertTriangle size={18} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Contenido condicional: si no hay planilla para el año/mes vs si hay planilla */}
      {!selectedPlanillaId ? (
        <div className="card" style={{ textAlign: 'center', padding: '3.5rem 2rem', marginTop: '1rem', border: '1px dashed var(--border-subtle)' }}>
          <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'rgba(20, 184, 166, 0.1)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: 'var(--teal-500)', marginBottom: '1.25rem' }}>
            <Calendar size={32} />
          </div>
          <h3 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>
            No existe planilla de {tipoFiltro === 'IIEE' ? 'Instituciones Educativas' : 'Sede UGEL'} para {MESES.find(m => m.num === selectedMes)?.nombre} {selectedAnio}
          </h3>
          <p style={{ color: 'var(--text-muted)', maxWidth: '520px', margin: '0 auto 1.5rem', fontSize: '0.9rem' }}>
            Seleccione otro año o mes en los filtros superiores, o genere una nueva planilla para este periodo.
          </p>
          {canEdit && (
            <button
              onClick={() => {
                setCreateForm({ anio: selectedAnio, mes: selectedMes, tipo: tipoFiltro, origen: 'MAESTRO' });
                setIsCreateOpen(true);
              }}
              className="btn btn-primary"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}
            >
              <Plus size={16} />
              <span>Crear Planilla {MESES.find(m => m.num === selectedMes)?.nombre} {selectedAnio}</span>
            </button>
          )}
        </div>
      ) : (
        <>
          {/* Banner Resumen de la Versión */}
          {versionData && (
        <div className="card" style={{ marginBottom: '1.5rem', padding: '1.25rem 1.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div>
                <span className={`badge ${versionData.tipo === 'IIEE' ? 'badge-indigo' : 'badge-teal'}`}>
                  {versionData.tipo === 'IIEE' ? 'Instituciones Educativas' : 'Sede UGEL'}
                </span>
                <h2 style={{ fontSize: '1.2rem', marginTop: '0.35rem', marginBottom: '0.1rem' }}>
                  Periodo {versionData.anio}-{String(versionData.mes).padStart(2, '0')} · Versión {versionData.numero}
                </h2>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Origen: {versionData.origen} • Creada por: {versionData.creada_por_nombre || 'Sistema'}
                </span>
              </div>
              <span className={`badge ${isClosed ? 'badge-emerald' : 'badge-amber'}`} style={{ marginLeft: '1rem' }}>
                {isClosed ? <CheckCircle2 size={13} /> : <Clock size={13} />}
                {versionData.estado}
              </span>
            </div>

            {/* Totales */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Trabajadores</span>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>{lineas.length}</div>
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Importe Total</span>
                <div className="mono-amount" style={{ fontSize: '1.1rem', color: 'var(--text-primary)' }}>
                  S/ {lineas.reduce((acc, l) => acc + Number(l.importe || 0), 0).toFixed(2)}
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Descuentos</span>
                <div className="mono-amount" style={{ fontSize: '1.1rem', color: '#DC2626' }}>
                  -S/ {lineas.reduce((acc, l) => acc + Number(l.total_descuentos || 0), 0).toFixed(2)}
                </div>
              </div>
              <div>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Líquido Neto</span>
                <div className="mono-amount" style={{ fontSize: '1.25rem', color: '#1D4ED8', fontWeight: 800 }}>
                  S/ {lineas.reduce((acc, l) => acc + Number(l.neto || 0), 0).toFixed(2)}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Barra de Filtro y Métricas de la Grilla */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.85rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', width: '320px' }}>
            <input
              type="text"
              className="form-input"
              placeholder="Buscar por DNI o apellidos/nombres..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: '2.5rem' }}
            />
            <Search size={16} style={{ position: 'absolute', left: '0.9rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          </div>
          <span style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
            Mostrando <strong>{filteredLineas.length}</strong> de {lineas.length} servidores
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {isClosed ? (
            <span style={{ fontSize: '0.825rem', color: '#166534', background: '#DCFCE7', border: '1px solid #BBF7D0', padding: '0.35rem 0.75rem', borderRadius: 'var(--radius-sm)', display: 'inline-flex', alignItems: 'center', gap: '0.35rem', fontWeight: 600 }}>
              <Lock size={14} /> Planilla Cerrada Oficial e Inmutable
            </span>
          ) : (
            <span style={{ fontSize: '0.825rem', color: '#92400E', background: '#FEF3C7', border: '1px solid #FDE68A', padding: '0.35rem 0.75rem', borderRadius: 'var(--radius-sm)', display: 'inline-flex', alignItems: 'center', gap: '0.35rem', fontWeight: 600 }}>
              <Clock size={14} /> Modo Edición de Planilla
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
              <th colSpan={7} className="th-group-descuentos">
                DESCUENTOS POR PLANILLA (CAFAE / JUDICIALES / SINDICALES)
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
              <th style={{ textAlign: 'right', width: 105 }}>Importe Base</th>
              <th style={{ textAlign: 'center', width: 65 }}>Días</th>
              <th style={{ textAlign: 'right', width: 90 }}>Monto S/G</th>
              <th style={{ textAlign: 'right', width: 90 }}>Pichincha</th>
              <th style={{ textAlign: 'right', width: 90 }}>Sullana</th>
              <th style={{ textAlign: 'right', width: 90 }}>Sub-CAFAE</th>
              <th style={{ textAlign: 'right', width: 90 }}>Brenta</th>
              <th style={{ textAlign: 'right', width: 90 }}>Sitrase</th>
              <th style={{ textAlign: 'right', width: 90 }}>Fentase</th>
              <th style={{ textAlign: 'right', width: 90 }}>Otros</th>
              <th style={{ textAlign: 'right', width: 110 }} className="col-highlight-desc">Total Desc.</th>
              <th style={{ textAlign: 'right', width: 120 }} className="col-highlight-neto">Líquido Neto</th>
            </tr>
          </thead>
          <tbody>
            {filteredLineas
              .slice((currentPage - 1) * pageSize, currentPage * pageSize)
              .map((l, index) => {
                const rowIndex = (currentPage - 1) * pageSize + index + 1;
                const isModified =
                originalLineas[l.id] &&
                (l.importe !== originalLineas[l.id].importe ||
                  l.dias_licencia !== originalLineas[l.id].dias_licencia ||
                  l.pichincha !== originalLineas[l.id].pichincha ||
                  l.sullana !== originalLineas[l.id].sullana ||
                  l.subcafae !== originalLineas[l.id].subcafae ||
                  l.brenta !== originalLineas[l.id].brenta ||
                  l.sitrase !== originalLineas[l.id].sitrase ||
                  l.fentase !== originalLineas[l.id].fentase ||
                  l.otros !== originalLineas[l.id].otros);

              const isNeg = l.neto < 0;

              return (
                <tr key={l.id} style={{ background: isNeg ? '#FEE2E2' : isModified ? '#ECFDF5' : undefined }}>
                  <td style={{ color: 'var(--text-muted)', textAlign: 'center', fontWeight: 600 }}>{rowIndex}</td>
                  <td className="mono-amount" style={{ fontWeight: 600 }}>
                    <span style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', padding: '0.15rem 0.45rem', borderRadius: 'var(--radius-sm)' }}>
                      {l.dni}
                    </span>
                  </td>
                  <td style={{ fontWeight: 700, color: '#0F172A', whiteSpace: 'nowrap' }}>{l.apellidos}, {l.nombres}</td>
                  <td style={{ fontSize: '0.775rem', color: '#475569' }}>{l.institucion_nombre || l.area_nombre || '—'}</td>

                  {/* Importe Base */}
                  <td style={{ textAlign: 'right' }}>
                    {isClosed ? (
                      <span className="mono-amount" style={{ fontWeight: 700, color: '#0F172A' }}>S/ {Number(l.importe).toFixed(2)}</span>
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

                  {/* Los 7 Descuentos */}
                  {(['pichincha', 'sullana', 'subcafae', 'brenta', 'sitrase', 'fentase', 'otros'] as const).map((conc) => {
                    const val = Number(l[conc] || 0);
                    return (
                      <td key={conc} style={{ textAlign: 'right' }}>
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
                            value={l[conc]}
                            onChange={(e) => handleCellChange(l.id, conc, e.target.value)}
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
            currentPage={currentPage}
            totalItems={filteredLineas.length}
            pageSize={pageSize}
            onPageChange={setCurrentPage}
            onPageSizeChange={setPageSize}
            pageSizeOptions={[25, 50, 100, 150, 200]}
            itemLabel="servidores"
          />
        )}
      </div>
      </>
      )}

      {/* Modal Crear Planilla */}
      <Modal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Crear Nueva Planilla Mensual">
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
                {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                  <option key={m} value={m}>
                    {m} - {['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre'][m - 1]}
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
              <option value="MAESTRO">Crear desde Maestro de Personal (descuentos en cero)</option>
              <option value="COPIA">Copiar del Mes Anterior (mantiene importes y descuentos históricos)</option>
            </select>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.5rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
            <button type="button" onClick={() => setIsCreateOpen(false)} className="btn btn-secondary">Cancelar</button>
            <button type="submit" className="btn btn-primary">Crear Planilla</button>
          </div>
        </form>
      </Modal>

      {/* Modal Cierre Formal */}
      <Modal isOpen={isCloseOpen} onClose={() => setIsCloseOpen(false)} title="Cierre Formal de Planilla">
        <p style={{ fontSize: '0.875rem', marginBottom: '1.25rem' }}>
          El cierre formal congela la planilla y le otorga valor oficial inmutable. Requiere la asignación de las firmas institucionales ({versionData?.tipo === 'IIEE' ? '4 firmas' : '3 firmas'}).
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.5rem' }}>
          {catalogos?.firmas?.filter((f) => f.ambito === versionData?.tipo).map((firma, idx) => (
            <div key={firma.id} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', background: 'var(--bg-input)', padding: '0.75rem', borderRadius: 'var(--radius-md)' }}>
              <span className="badge badge-teal">Firma {idx + 1}</span>
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{firma.nombre_firmante}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{firma.cargo_firmante}</div>
              </div>
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
          <button onClick={() => setIsCloseOpen(false)} className="btn btn-secondary">Cancelar</button>
          <button onClick={handleConfirmClose} className="btn btn-success">Confirmar Cierre Oficial</button>
        </div>
      </Modal>

      {/* Modal Reabrir Planilla */}
      <Modal isOpen={isReopenOpen} onClose={() => setIsReopenOpen(false)} title="Reapertura Versionada de Planilla">
        <p style={{ fontSize: '0.875rem', marginBottom: '1rem' }}>
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
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
          <button onClick={() => setIsReopenOpen(false)} className="btn btn-secondary">Cancelar</button>
          <button onClick={handleConfirmReopen} className="btn btn-primary" disabled={reopenMotivo.trim().length < 5}>
            Confirmar Reapertura
          </button>
        </div>
      </Modal>

      {/* Modal Limpiar Descuentos */}
      <Modal isOpen={isClearOpen} onClose={() => setIsClearOpen(false)} title="Limpiar Descuentos">
        <p style={{ fontSize: '0.875rem', marginBottom: '1.25rem' }}>
          Seleccione si desea poner en cero todos los descuentos o un concepto en particular:
        </p>
        <div className="form-group">
          <label className="form-label">Concepto a Limpiar</label>
          <select className="form-select" value={clearConcepto} onChange={(e) => setClearConcepto(e.target.value)}>
            <option value="">-- Todos los 8 Descuentos --</option>
            <option value="PICHINCHA">Pichincha</option>
            <option value="SULLANA">Caja Sullana</option>
            <option value="SUBCAFAE">Sub-CAFAE</option>
            <option value="BRENTA">BRENTA</option>
            <option value="SITRASE">SITRASE</option>
            <option value="FENTASE">SITASE / FENTASE</option>
            <option value="OTROS">Otros Descuentos</option>
          </select>
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
          <button onClick={() => setIsClearOpen(false)} className="btn btn-secondary">Cancelar</button>
          <button onClick={handleClearDescuentos} className="btn btn-danger">Limpiar Valores</button>
        </div>
      </Modal>
    </div>
  );
};
