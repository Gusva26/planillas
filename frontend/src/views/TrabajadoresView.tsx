import React, { useEffect, useState } from 'react';
import { apiRequest } from '../api/client';
import { mensajeDeError } from '../api/errors';
import { usePaginacion } from '../hooks/usePaginacion';
import { useAuth } from '../context/AuthContext';
import { Trabajador, TrabajadorPayload, CatalogoBundle } from '../types';
import { Modal } from '../components/Modal';
import { Pagination } from '../components/Pagination';
import { 
  Users, 
  Search, 
  Plus, 
  Edit3, 
  CheckCircle2, 
  XCircle, 
  Building2, 
  Landmark,
  Briefcase,
  Calendar,
  CreditCard,
  UserCheck,
  UserX,
  X
} from 'lucide-react';

export const TrabajadoresView: React.FC = () => {
  const { user } = useAuth();
  const [trabajadores, setTrabajadores] = useState<Trabajador[]>([]);
  const [catalogos, setCatalogos] = useState<CatalogoBundle | null>(null);
  const [loading, setLoading] = useState(true);

  // Filtros
  const [search, setSearch] = useState('');
  const [tipoFiltro, setTipoFiltro] = useState<string>('TODOS');
  const [soloActivos, setSoloActivos] = useState(false);

  // Paginación
  const paginacion = usePaginacion(trabajadores, { tamanoInicial: 15 });

  // Modales
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTrabajador, setEditingTrabajador] = useState<Trabajador | null>(null);
  const [modalActiveTab, setModalActiveTab] = useState<'personal' | 'laboral' | 'remuneracion'>('personal');
  const [formData, setFormData] = useState({
    dni: '',
    apellidos: '',
    nombres: '',
    tipo: 'IIEE',
    institucion_id: '',
    area_id: '',
    nivel_id: '',
    cargo_id: '',
    situacion_id: '',
    categoria_id: '',
    fecha_nacimiento: '',
    regimen_laboral: '276',
    jornada_laboral: '40',
    regimen_pensionario: '',
    tiempo_servicio_texto: '',
    fecha_ingreso: '',
    fecha_termino: '',
    leyenda_permanente: '',
    tipo_pago: 'CUENTA',
    numero_cheque: '',
    cuenta_multired: '',
    importe: '0.00',
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const canEdit = user && ['ADMINISTRADOR', 'PLANILLAS'].includes(user.rol);

  const loadData = async () => {
    setLoading(true);
    try {
      const [trabs, cats] = await Promise.all([
        apiRequest<Trabajador[]>(`/api/trabajadores?solo_activos=${soloActivos}${tipoFiltro !== 'TODOS' ? `&tipo=${tipoFiltro}` : ''}${search ? `&q=${encodeURIComponent(search)}` : ''}`),
        apiRequest<CatalogoBundle>('/api/catalogos/bundle'),
      ]);
      setTrabajadores(trabs);
      setCatalogos(cats);
    } catch (err) {
      setTrabajadores([]);
      alert(mensajeDeError(err, 'Error al cargar el personal.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    paginacion.irAPagina(1);
    loadData();
  }, [tipoFiltro, soloActivos]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    paginacion.irAPagina(1);
    loadData();
  };

  const handleClearSearch = () => {
    setSearch('');
    paginacion.irAPagina(1);
    setTimeout(() => {
      loadData();
    }, 0);
  };

  const handleOpenCreate = () => {
    setEditingTrabajador(null);
    setModalActiveTab('personal');
    setFormData({
      dni: '',
      apellidos: '',
      nombres: '',
      tipo: 'IIEE',
      institucion_id: '',
      area_id: '',
      nivel_id: '',
      cargo_id: '',
      situacion_id: '',
      categoria_id: '',
      fecha_nacimiento: '',
      regimen_laboral: '276',
      jornada_laboral: '40',
      regimen_pensionario: '',
      tiempo_servicio_texto: '',
      fecha_ingreso: '',
      fecha_termino: '',
      leyenda_permanente: '',
      tipo_pago: 'CUENTA',
      numero_cheque: '',
      cuenta_multired: '',
      importe: '0.00',
    });
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleOpenEdit = (t: Trabajador) => {
    setEditingTrabajador(t);
    setModalActiveTab('personal');
    setFormData({
      dni: t.dni,
      apellidos: t.apellidos,
      nombres: t.nombres,
      tipo: t.tipo,
      institucion_id: t.institucion_id ? String(t.institucion_id) : '',
      area_id: t.area_id ? String(t.area_id) : '',
      nivel_id: t.nivel_id ? String(t.nivel_id) : '',
      cargo_id: t.cargo_id ? String(t.cargo_id) : '',
      situacion_id: t.situacion_id ? String(t.situacion_id) : '',
      categoria_id: t.categoria_id ? String(t.categoria_id) : '',
      fecha_nacimiento: t.fecha_nacimiento ? String(t.fecha_nacimiento).substring(0, 10) : '',
      regimen_laboral: t.regimen_laboral || '276',
      jornada_laboral: t.jornada_laboral || '40',
      regimen_pensionario: t.regimen_pensionario || '',
      tiempo_servicio_texto: t.tiempo_servicio_texto || '',
      fecha_ingreso: t.fecha_ingreso ? String(t.fecha_ingreso).substring(0, 10) : '',
      fecha_termino: t.fecha_termino ? String(t.fecha_termino).substring(0, 10) : '',
      leyenda_permanente: t.leyenda_permanente || '',
      tipo_pago: t.tipo_pago || 'CUENTA',
      numero_cheque: t.numero_cheque || '',
      cuenta_multired: t.cuenta_multired || '',
      importe: String(t.importe || '0.00'),
    });
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleSaveTrabajador = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    // Validaciones
    if (!/^\d{8}$/.test(formData.dni.trim())) {
      setFormError('El DNI debe tener exactamente 8 dígitos numéricos.');
      return;
    }
    if (!formData.apellidos.trim() || !formData.nombres.trim()) {
      setFormError('Apellidos y Nombres son campos obligatorios.');
      return;
    }
    if (formData.tipo === 'IIEE' && !formData.institucion_id) {
      setFormError('Para personal de II.EE. la Institución Educativa es obligatoria.');
      return;
    }
    if (formData.tipo === 'SEDE' && !formData.area_id) {
      setFormError('Para personal de Sede el Área es obligatoria.');
      return;
    }

    setSaving(true);
    try {
      const payload: TrabajadorPayload = {
        dni: formData.dni.trim(),
        apellidos: formData.apellidos.trim(),
        nombres: formData.nombres.trim(),
        tipo: formData.tipo === 'SEDE' ? 'SEDE' : 'IIEE',
        institucion_id: formData.tipo === 'IIEE' && formData.institucion_id ? Number(formData.institucion_id) : null,
        area_id: formData.tipo === 'SEDE' && formData.area_id ? Number(formData.area_id) : null,
        nivel_id: formData.nivel_id ? Number(formData.nivel_id) : null,
        cargo_id: formData.cargo_id ? Number(formData.cargo_id) : null,
        situacion_id: formData.situacion_id ? Number(formData.situacion_id) : null,
        categoria_id: formData.categoria_id ? Number(formData.categoria_id) : null,
        fecha_nacimiento: formData.fecha_nacimiento || null,
        regimen_laboral: formData.regimen_laboral || '276',
        jornada_laboral: formData.jornada_laboral || '40',
        regimen_pensionario: formData.regimen_pensionario.trim() || null,
        tiempo_servicio_texto: formData.tiempo_servicio_texto.trim() || null,
        fecha_ingreso: formData.fecha_ingreso || null,
        fecha_termino: formData.fecha_termino || null,
        leyenda_permanente: formData.leyenda_permanente.trim() || null,
        tipo_pago: formData.tipo_pago || 'CUENTA',
        numero_cheque: formData.numero_cheque.trim() || null,
        cuenta_multired: formData.cuenta_multired.trim() || null,
        importe: parseFloat(formData.importe) || 0,
      };

      if (editingTrabajador) {
        payload.revision = editingTrabajador.revision || 1;
        await apiRequest(`/api/trabajadores/${editingTrabajador.id}`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        });
      } else {
        await apiRequest('/api/trabajadores', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
      }

      setIsModalOpen(false);
      loadData();
    } catch (err) {
      setFormError(mensajeDeError(err, 'Error al guardar trabajador.'));
    } finally {
      setSaving(false);
    }
  };

  const handleToggleEstado = async (t: Trabajador) => {
    if (!confirm(`¿Confirma que desea ${t.activo ? 'desactivar' : 'activar'} a ${t.nombres} ${t.apellidos}?`)) return;
    try {
      await apiRequest(`/api/trabajadores/${t.id}/estado`, {
        method: 'PATCH',
        body: JSON.stringify({ activo: !t.activo, revision: t.revision || 1 }),
      });
      loadData();
    } catch (err) {
      alert(mensajeDeError(err, 'Error al cambiar estado.'));
    }
  };

  return (
    <div className="page-container">
      {/* Barra Superior con Resumen y Acción Principal */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
        marginBottom: '1.5rem'
      }}>
        <div>
          <h2 style={{ fontSize: '1.35rem', color: '#0F172A', fontWeight: 800, margin: 0, letterSpacing: '-0.02em' }}>
            Maestro Unificado de Personal
          </h2>
          <p style={{ fontSize: '0.85rem', color: '#64748B', margin: '0.2rem 0 0' }}>
            Directorio oficial de servidores de Instituciones Educativas y Sede Central UGEL Chepén.
          </p>
        </div>

        {canEdit && (
          <button 
            onClick={handleOpenCreate} 
            className="btn btn-primary"
            style={{ fontWeight: 700, gap: '0.5rem', boxShadow: '0 2px 6px rgba(29, 78, 216, 0.2)' }}
          >
            <Plus size={17} />
            <span>Registrar Nuevo Personal</span>
          </button>
        )}
      </div>

      {/* Toolbar de Filtros y Búsqueda */}
      <div className="filter-toolbar">
        {/* Selector de Ámbito con Controles Segmentados */}
        <div className="segmented-control">
          <button
            onClick={() => setTipoFiltro('TODOS')}
            className={`segmented-item ${tipoFiltro === 'TODOS' ? 'active' : ''}`}
          >
            <Users size={15} />
            <span>Todos ({trabajadores.length})</span>
          </button>
          <button
            onClick={() => setTipoFiltro('IIEE')}
            className={`segmented-item ${tipoFiltro === 'IIEE' ? 'active' : ''}`}
          >
            <Building2 size={15} />
            <span>Solo II.EE.</span>
          </button>
          <button
            onClick={() => setTipoFiltro('SEDE')}
            className={`segmented-item ${tipoFiltro === 'SEDE' ? 'active' : ''}`}
          >
            <Landmark size={15} />
            <span>Solo Sede UGEL</span>
          </button>
        </div>

        {/* Búsqueda en Tiempo Real / Enter */}
        <form onSubmit={handleSearchSubmit} className="search-input-wrap">
          <input
            type="text"
            className="form-input"
            placeholder="Buscar por DNI o apellidos..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <Search size={16} />
          {search && (
            <button
              type="button"
              onClick={handleClearSearch}
              className="btn btn-ghost"
              style={{
                position: 'absolute',
                right: '0.5rem',
                top: '50%',
                transform: 'translateY(-50%)',
                padding: '0.25rem',
                color: '#94A3B8'
              }}
              title="Limpiar búsqueda"
            >
              <X size={14} />
            </button>
          )}
        </form>

        {/* Toggle Solo Activos */}
        <label style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          fontSize: '0.825rem',
          cursor: 'pointer',
          color: '#334155',
          userSelect: 'none',
          fontWeight: 600,
        }}>
          <input
            type="checkbox"
            checked={soloActivos}
            onChange={(e) => setSoloActivos(e.target.checked)}
            style={{ width: 16, height: 16, cursor: 'pointer', accentColor: '#1D4ED8' }}
          />
          <span>Solo activos en planilla</span>
        </label>
      </div>

      {/* Tabla Maestro Institucional */}
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th style={{ width: '90px' }}>DNI</th>
              <th>Apellidos y Nombres</th>
              <th style={{ width: '90px' }}>Ámbito</th>
              <th>Adscripción (I.E. / Área Sede)</th>
              <th>Cargo Institucional</th>
              <th style={{ width: '130px' }}>Cta. Multired</th>
              <th style={{ textAlign: 'right', width: '120px' }}>Haber Base</th>
              <th style={{ width: '90px', textAlign: 'center' }}>Estado</th>
              {canEdit && <th style={{ textAlign: 'center', width: '130px' }}>Acciones</th>}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: '4rem' }}>
                  <div style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{
                      width: 32,
                      height: 32,
                      border: '3px solid #E2E8F0',
                      borderTopColor: '#2563EB',
                      borderRadius: '50%',
                      animation: 'spin 1s linear infinite'
                    }} />
                    <span style={{ fontSize: '0.85rem', color: '#64748B' }}>Cargando directorio de servidores...</span>
                  </div>
                </td>
              </tr>
            ) : trabajadores.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: '4rem' }}>
                  <div className="empty-state" style={{ margin: '0 auto', maxWidth: '420px', border: 'none' }}>
                    <div className="empty-state-icon">
                      <Users size={26} />
                    </div>
                    <div className="empty-state-title">No se encontraron trabajadores</div>
                    <p className="empty-state-desc">
                      Intenta con otros términos de búsqueda o modifica los filtros de ámbito.
                    </p>
                    {canEdit && (
                      <button onClick={handleOpenCreate} className="btn btn-secondary btn-sm">
                        <Plus size={14} />
                        <span>Registrar Nuevo Personal</span>
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ) : (
              paginacion.items.map((t) => (
                <tr key={t.id}>
                  <td className="mono-amount" style={{ color: '#1D4ED8', fontWeight: 700 }}>
                    {t.dni}
                  </td>
                  <td>
                    <div style={{ fontWeight: 700, color: '#0F172A', fontSize: '0.85rem' }}>
                      {t.apellidos}, {t.nombres}
                    </div>
                    <div style={{ fontSize: '0.725rem', color: '#64748B', display: 'flex', alignItems: 'center', gap: '0.35rem', marginTop: '1px' }}>
                      <Calendar size={11} style={{ color: '#94A3B8' }} />
                      <span>Nac: {t.fecha_nacimiento ? String(t.fecha_nacimiento).substring(0, 10) : '—'}</span>
                      {t.regimen_pensionario && (
                        <>
                          <span style={{ color: '#CBD5E1' }}>•</span>
                          <span style={{ color: '#475569', fontWeight: 500 }}>{t.regimen_pensionario}</span>
                        </>
                      )}
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${t.tipo === 'IIEE' ? 'badge-indigo' : 'badge-teal'}`}>
                      {t.tipo === 'IIEE' ? 'II.EE.' : 'SEDE'}
                    </span>
                  </td>
                  <td style={{ color: '#334155', fontWeight: 500 }}>
                    {t.institucion_nombre || t.area_nombre || '—'}
                  </td>
                  <td style={{ color: '#475569' }}>
                    {t.cargo_nombre || '—'}
                  </td>
                  <td className="mono-amount" style={{ fontSize: '0.8rem', color: t.cuenta_multired ? '#0F172A' : '#94A3B8' }}>
                    {t.cuenta_multired || (t.tipo_pago === 'CHEQUE' ? 'Cheque' : 'Sin Cta')}
                  </td>
                  <td className="mono-amount" style={{ textAlign: 'right', fontWeight: 700, color: '#0F172A' }}>
                    S/ {Number(t.importe || 0).toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <span className={`badge ${t.activo ? 'badge-emerald' : 'badge-crimson'}`}>
                      {t.activo ? 'Activo' : 'Cesado'}
                    </span>
                  </td>
                  {canEdit && (
                    <td style={{ textAlign: 'center' }}>
                      <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
                        <button
                          onClick={() => handleOpenEdit(t)}
                          className="btn btn-secondary btn-sm"
                          style={{ padding: '0.3rem 0.55rem' }}
                          title="Editar ficha del servidor"
                          aria-label={`Editar ficha de ${t.nombres} ${t.apellidos}`}
                        >
                          <Edit3 size={13} />
                          <span>Editar</span>
                        </button>
                        <button
                          onClick={() => handleToggleEstado(t)}
                          className={`btn ${t.activo ? 'btn-ghost' : 'btn-success'} btn-sm`}
                          style={{ padding: '0.3rem 0.45rem' }}
                          title={t.activo ? 'Desactivar de planilla' : 'Activar en planilla'}
                          aria-label={t.activo ? 'Desactivar de planilla' : 'Activar en planilla'}
                        >
                          {t.activo ? (
                            <UserX size={15} style={{ color: '#DC2626' }} />
                          ) : (
                            <UserCheck size={15} style={{ color: '#FFFFFF' }} />
                          )}
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>

        {trabajadores.length > 0 && (
          <Pagination
            currentPage={paginacion.pagina}
            totalItems={paginacion.total}
            pageSize={paginacion.tamano}
            onPageChange={paginacion.irAPagina}
            onPageSizeChange={paginacion.cambiarTamano}
            pageSizeOptions={[15, 30, 50, 100]}
            itemLabel="servidores registrados"
          />
        )}
      </div>

      {/* Modal Crear / Editar Ficha Integral */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingTrabajador ? `Ficha de Personal · DNI ${editingTrabajador.dni}` : 'Registrar Nuevo Servidor en Maestro'}
        maxWidth="820px"
      >
        {formError && (
          <div style={{
            background: '#FEF2F2',
            border: '1px solid #FECACA',
            padding: '0.85rem 1rem',
            borderRadius: 'var(--radius-md)',
            color: '#991B1B',
            marginBottom: '1.25rem',
            fontSize: '0.85rem',
          }}>
            {formError}
          </div>
        )}

        <form onSubmit={handleSaveTrabajador}>
          {/* Tabs Internas del Modal para Máxima Claridad */}
          <div style={{
            display: 'flex',
            borderBottom: '1px solid var(--border-subtle)',
            marginBottom: '1.25rem',
            gap: '0.5rem'
          }}>
            <button
              type="button"
              onClick={() => setModalActiveTab('personal')}
              className="btn btn-ghost"
              style={{
                borderRadius: '0',
                borderBottom: modalActiveTab === 'personal' ? '2.5px solid #1D4ED8' : '2.5px solid transparent',
                color: modalActiveTab === 'personal' ? '#1D4ED8' : '#64748B',
                fontWeight: modalActiveTab === 'personal' ? 700 : 500,
                padding: '0.6rem 0.85rem'
              }}
            >
              1. Identificación y Datos Personales
            </button>
            <button
              type="button"
              onClick={() => setModalActiveTab('laboral')}
              className="btn btn-ghost"
              style={{
                borderRadius: '0',
                borderBottom: modalActiveTab === 'laboral' ? '2.5px solid #1D4ED8' : '2.5px solid transparent',
                color: modalActiveTab === 'laboral' ? '#1D4ED8' : '#64748B',
                fontWeight: modalActiveTab === 'laboral' ? 700 : 500,
                padding: '0.6rem 0.85rem'
              }}
            >
              2. Ubicación Laboral y Cargo
            </button>
            <button
              type="button"
              onClick={() => setModalActiveTab('remuneracion')}
              className="btn btn-ghost"
              style={{
                borderRadius: '0',
                borderBottom: modalActiveTab === 'remuneracion' ? '2.5px solid #1D4ED8' : '2.5px solid transparent',
                color: modalActiveTab === 'remuneracion' ? '#1D4ED8' : '#64748B',
                fontWeight: modalActiveTab === 'remuneracion' ? 700 : 500,
                padding: '0.6rem 0.85rem'
              }}
            >
              3. Régimen y Pago Multired
            </button>
          </div>

          {/* TAB 1: IDENTIFICACIÓN */}
          {modalActiveTab === 'personal' && (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">DNI (8 dígitos) *</label>
                  <input
                    type="text"
                    maxLength={8}
                    className="form-input mono-amount"
                    placeholder="12345678"
                    value={formData.dni}
                    onChange={(e) => setFormData({ ...formData, dni: e.target.value.replace(/\D/g, '') })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Fecha de Nacimiento</label>
                  <input
                    type="date"
                    className="form-input"
                    value={formData.fecha_nacimiento}
                    onChange={(e) => setFormData({ ...formData, fecha_nacimiento: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Ámbito Institucional *</label>
                  <select
                    className="form-select"
                    value={formData.tipo}
                    onChange={(e) => setFormData({ ...formData, tipo: e.target.value })}
                  >
                    <option value="IIEE">Institución Educativa (II.EE.)</option>
                    <option value="SEDE">Sede Central UGEL Chepén</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Apellidos Paterno y Materno *</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Ej. SILVA SUAREZ"
                    value={formData.apellidos}
                    onChange={(e) => setFormData({ ...formData, apellidos: e.target.value.toUpperCase() })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Nombres Completos *</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Ej. LUIS GUSTABO"
                    value={formData.nombres}
                    onChange={(e) => setFormData({ ...formData, nombres: e.target.value.toUpperCase() })}
                    required
                  />
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: UBICACIÓN LABORAL */}
          {modalActiveTab === 'laboral' && (
            <div>
              {formData.tipo === 'IIEE' ? (
                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                  <div className="form-group">
                    <label className="form-label">Institución Educativa *</label>
                    <select
                      className="form-select"
                      value={formData.institucion_id}
                      onChange={(e) => setFormData({ ...formData, institucion_id: e.target.value })}
                      required
                    >
                      <option value="">-- Seleccionar Institución Educativa --</option>
                      {catalogos?.instituciones?.map((i) => (
                        <option key={i.id} value={i.id}>{i.nombre} ({i.codigo_modular || 'S/C'})</option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Nivel Educativo</label>
                    <select
                      className="form-select"
                      value={formData.nivel_id}
                      onChange={(e) => setFormData({ ...formData, nivel_id: e.target.value })}
                    >
                      <option value="">-- Seleccionar Nivel --</option>
                      {catalogos?.niveles?.map((n) => (
                        <option key={n.id} value={n.id}>{n.nombre}</option>
                      ))}
                    </select>
                  </div>
                </div>
              ) : (
                <div className="form-group" style={{ marginBottom: '1rem' }}>
                  <label className="form-label">Área de Sede Central UGEL *</label>
                  <select
                    className="form-select"
                    value={formData.area_id}
                    onChange={(e) => setFormData({ ...formData, area_id: e.target.value })}
                    required
                  >
                    <option value="">-- Seleccionar Área de Sede --</option>
                    {catalogos?.areas?.map((a) => (
                      <option key={a.id} value={a.id}>{a.nombre}</option>
                    ))}
                  </select>
                </div>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Cargo Institucional</label>
                  <select
                    className="form-select"
                    value={formData.cargo_id}
                    onChange={(e) => setFormData({ ...formData, cargo_id: e.target.value })}
                  >
                    <option value="">-- Cargo --</option>
                    {catalogos?.cargos?.map((c) => (
                      <option key={c.id} value={c.id}>{c.nombre}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Categoría / Grupo</label>
                  <select
                    className="form-select"
                    value={formData.categoria_id}
                    onChange={(e) => setFormData({ ...formData, categoria_id: e.target.value })}
                  >
                    <option value="">-- Categoría --</option>
                    {catalogos?.categorias?.map((cat) => (
                      <option key={cat.id} value={cat.id}>{cat.codigo} - {cat.descripcion}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Situación Laboral</label>
                  <select
                    className="form-select"
                    value={formData.situacion_id}
                    onChange={(e) => setFormData({ ...formData, situacion_id: e.target.value })}
                  >
                    <option value="">-- Situación --</option>
                    {catalogos?.situaciones?.map((s) => (
                      <option key={s.id} value={s.id}>{s.nombre}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: RÉGIMEN Y PAGO */}
          {modalActiveTab === 'remuneracion' && (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Régimen Laboral</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="276"
                    value={formData.regimen_laboral}
                    onChange={(e) => setFormData({ ...formData, regimen_laboral: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Jornada Laboral (Hrs)</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="40"
                    value={formData.jornada_laboral}
                    onChange={(e) => setFormData({ ...formData, jornada_laboral: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Régimen Pensionario</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="ONP / AFP Integra / etc."
                    value={formData.regimen_pensionario}
                    onChange={(e) => setFormData({ ...formData, regimen_pensionario: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Tiempo de Servicio (AA-MM-DD)</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Ej. 15-08-20"
                    value={formData.tiempo_servicio_texto}
                    onChange={(e) => setFormData({ ...formData, tiempo_servicio_texto: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Fecha de Ingreso</label>
                  <input
                    type="date"
                    className="form-input"
                    value={formData.fecha_ingreso}
                    onChange={(e) => setFormData({ ...formData, fecha_ingreso: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Fecha de Término</label>
                  <input
                    type="date"
                    className="form-input"
                    value={formData.fecha_termino}
                    onChange={(e) => setFormData({ ...formData, fecha_termino: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div className="form-group">
                  <label className="form-label">Importe Base Mensual (S/) *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    className="form-input mono-amount"
                    value={formData.importe}
                    onChange={(e) => setFormData({ ...formData, importe: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Modalidad de Pago</label>
                  <select
                    className="form-select"
                    value={formData.tipo_pago}
                    onChange={(e) => setFormData({ ...formData, tipo_pago: e.target.value })}
                  >
                    <option value="CUENTA">Cuenta Ahorros / TeleAhorro BN</option>
                    <option value="CHEQUE">Cheque de Gerencia</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">
                    {formData.tipo_pago === 'CHEQUE' ? 'N° de Cheque' : 'Cta. TeleAhorro / Multired'}
                  </label>
                  <input
                    type="text"
                    className="form-input mono-amount"
                    placeholder={formData.tipo_pago === 'CHEQUE' ? 'CHQ-00123' : '4832411958'}
                    value={formData.tipo_pago === 'CHEQUE' ? formData.numero_cheque : formData.cuenta_multired}
                    onChange={(e) => {
                      if (formData.tipo_pago === 'CHEQUE') {
                        setFormData({ ...formData, numero_cheque: e.target.value });
                      } else {
                        setFormData({ ...formData, cuenta_multired: e.target.value });
                      }
                    }}
                  />
                </div>
              </div>

              <div className="form-group" style={{ marginBottom: '1.25rem' }}>
                <label className="form-label">Leyenda Permanente en Boleta</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Ej. MANDATO JUDICIAL RES. N° 45-2018"
                  value={formData.leyenda_permanente}
                  onChange={(e) => setFormData({ ...formData, leyenda_permanente: e.target.value })}
                />
              </div>
            </div>
          )}

          {/* Botones de Acción */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderTop: '1px solid var(--border-subtle)',
            paddingTop: '1.25rem',
            marginTop: '1.25rem'
          }}>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {modalActiveTab !== 'personal' && (
                <button
                  type="button"
                  onClick={() => setModalActiveTab(modalActiveTab === 'remuneracion' ? 'laboral' : 'personal')}
                  className="btn btn-secondary btn-sm"
                >
                  Paso Anterior
                </button>
              )}
              {modalActiveTab !== 'remuneracion' && (
                <button
                  type="button"
                  onClick={() => setModalActiveTab(modalActiveTab === 'personal' ? 'laboral' : 'remuneracion')}
                  className="btn btn-secondary btn-sm"
                >
                  Siguiente Paso
                </button>
              )}
            </div>

            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <button type="button" onClick={() => setIsModalOpen(false)} className="btn btn-secondary">
                Cancelar
              </button>
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? 'Guardando...' : editingTrabajador ? 'Actualizar Ficha Integral' : 'Guardar Servidor'}
              </button>
            </div>
          </div>
        </form>
      </Modal>
    </div>
  );
};
