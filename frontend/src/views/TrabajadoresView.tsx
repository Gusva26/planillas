import React, { useEffect, useState } from 'react';
import { apiRequest } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Trabajador, CatalogoBundle } from '../types';
import { Modal } from '../components/Modal';
import { Pagination } from '../components/Pagination';
import { 
  Users, 
  Search, 
  Plus, 
  Edit3, 
  CheckCircle, 
  XCircle, 
  Filter, 
  Building2, 
  Briefcase,
  Calendar
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
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(15);

  // Modales
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTrabajador, setEditingTrabajador] = useState<Trabajador | null>(null);
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
    } catch (err: any) {
      console.error('Error al cargar personal:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setCurrentPage(1);
    loadData();
  }, [tipoFiltro, soloActivos]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    loadData();
  };

  const handleOpenCreate = () => {
    setEditingTrabajador(null);
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
      setFormError('Para trabajadores de II.EE. la Institución Educativa es obligatoria.');
      return;
    }
    if (formData.tipo === 'SEDE' && !formData.area_id) {
      setFormError('Para trabajadores de Sede el Área es obligatoria.');
      return;
    }

    setSaving(true);
    try {
      const payload: any = {
        dni: formData.dni.trim(),
        apellidos: formData.apellidos.trim(),
        nombres: formData.nombres.trim(),
        tipo: formData.tipo,
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
    } catch (err: any) {
      setFormError(err.message || 'Error al guardar trabajador.');
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
    } catch (err: any) {
      alert(err.message || 'Error al cambiar estado.');
    }
  };

  return (
    <div className="page-container">
      {/* Header y Filtros */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
        <div>
          <h2 style={{ fontSize: '1.35rem', margin: 0 }}>Maestro de Personal CAFAE</h2>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Trabajadores de Instituciones Educativas (II.EE.) y Sede Central UGEL Chepén
          </span>
        </div>

        {/* Buscador */}
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '0.5rem' }}>
          <div style={{ position: 'relative', width: '280px' }}>
            <input
              type="text"
              className="form-input"
              placeholder="Buscar por DNI o nombres..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: '2.5rem' }}
            />
            <Search size={16} style={{ position: 'absolute', left: '0.9rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          </div>
          <button type="submit" className="btn btn-secondary">
            Buscar
          </button>
        </form>
      </div>

      {/* Barra de Filtros Tipo y Nuevo */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
          {/* Tabs Ámbito */}
          <div style={{ display: 'inline-flex', background: '#F1F5F9', padding: '0.25rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', gap: '0.25rem' }}>
            {['TODOS', 'IIEE', 'SEDE'].map((t) => (
              <button
                key={t}
                onClick={() => setTipoFiltro(t)}
                className={`btn ${tipoFiltro === t ? 'btn-primary' : 'btn-ghost'}`}
                style={{ padding: '0.35rem 0.85rem', fontSize: '0.8rem' }}
              >
                {t === 'TODOS' ? 'Todos los Ámbitos' : t === 'IIEE' ? '🏫 Solo II.EE.' : '🏢 Solo Sede UGEL'}
              </button>
            ))}
          </div>

          {/* Toggle Activos */}
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.825rem', cursor: 'pointer', color: 'var(--text-secondary)' }}>
            <input
              type="checkbox"
              checked={soloActivos}
              onChange={(e) => setSoloActivos(e.target.checked)}
            />
            <span>Solo activos</span>
          </label>

          {/* Botón Nuevo */}
          {canEdit && (
            <button onClick={handleOpenCreate} className="btn btn-primary">
              <Plus size={16} />
              <span>Nuevo Trabajador</span>
            </button>
          )}
        </div>
      </div>

      {/* Tabla Maestro */}
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>DNI</th>
              <th>Apellidos y Nombres / F. Nacimiento</th>
              <th>Ámbito</th>
              <th>Adscripción (I.E. / Área)</th>
              <th>Cargo</th>
              <th>Cta. Multired</th>
              <th style={{ textAlign: 'right' }}>Importe Base</th>
              <th>Estado</th>
              {canEdit && <th style={{ textAlign: 'center' }}>Acciones</th>}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: '3rem' }}>Cargando personal...</td>
              </tr>
            ) : trabajadores.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                  No se encontraron trabajadores con los filtros aplicados.
                </td>
              </tr>
            ) : (
              trabajadores
                .slice((currentPage - 1) * pageSize, currentPage * pageSize)
                .map((t) => (
                <tr key={t.id}>
                  <td className="mono-amount" style={{ color: 'var(--teal-500)', fontWeight: 700 }}>{t.dni}</td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{t.apellidos}, {t.nombres}</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <Calendar size={11} />
                      <span>F. Nac: {t.fecha_nacimiento ? String(t.fecha_nacimiento).substring(0, 10) : 'No registrada'}</span>
                      {t.regimen_pensionario && <span>• {t.regimen_pensionario}</span>}
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${t.tipo === 'IIEE' ? 'badge-indigo' : 'badge-teal'}`}>
                      {t.tipo}
                    </span>
                  </td>
                  <td>{t.institucion_nombre || t.area_nombre || '—'}</td>
                  <td>{t.cargo_nombre || '—'}</td>
                  <td className="mono-amount" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    {t.cuenta_multired || 'Cheque / S/C'}
                  </td>
                  <td className="mono-amount" style={{ textAlign: 'right', fontWeight: 600, color: 'var(--text-primary)' }}>
                    S/ {Number(t.importe || 0).toFixed(2)}
                  </td>
                  <td>
                    <span className={`badge ${t.activo ? 'badge-emerald' : 'badge-crimson'}`}>
                      {t.activo ? 'Activo' : 'Cesado'}
                    </span>
                  </td>
                  {canEdit && (
                    <td style={{ textAlign: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                        <button
                          onClick={() => handleOpenEdit(t)}
                          className="btn btn-secondary"
                          style={{ padding: '0.35rem 0.6rem', fontSize: '0.75rem' }}
                          title="Editar ficha completa"
                        >
                          <Edit3 size={13} />
                          <span>Editar</span>
                        </button>
                        <button
                          onClick={() => handleToggleEstado(t)}
                          className={`btn ${t.activo ? 'btn-ghost' : 'btn-success'}`}
                          style={{ padding: '0.35rem 0.5rem', fontSize: '0.75rem' }}
                          title={t.activo ? 'Desactivar trabajador' : 'Activar trabajador'}
                        >
                          {t.activo ? <XCircle size={14} style={{ color: '#F87171' }} /> : <CheckCircle size={14} />}
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
            currentPage={currentPage}
            totalItems={trabajadores.length}
            pageSize={pageSize}
            onPageChange={setCurrentPage}
            onPageSizeChange={setPageSize}
            pageSizeOptions={[10, 15, 25, 50, 100]}
            itemLabel="trabajadores"
          />
        )}
      </div>

      {/* Modal Crear / Editar */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingTrabajador ? `Editar Ficha de Personal · DNI ${editingTrabajador.dni}` : 'Registrar Nuevo Trabajador'}
        maxWidth="800px"
      >
        {formError && (
          <div style={{ background: '#FEE2E2', border: '1px solid #FECACA', padding: '0.75rem', borderRadius: 'var(--radius-md)', color: '#B91C1C', marginBottom: '1rem', fontSize: '0.85rem' }}>
            {formError}
          </div>
        )}

        <form onSubmit={handleSaveTrabajador}>
          {/* SECCIÓN 1: DATOS PERSONALES */}
          <h4 style={{ fontSize: '0.9rem', color: 'var(--teal-500)', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '0.35rem', marginBottom: '0.85rem' }}>
            1. Datos Personales
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.85rem', marginBottom: '0.85rem' }}>
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
              <label className="form-label">Ámbito *</label>
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

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem', marginBottom: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Apellidos Completos *</label>
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

          {/* SECCIÓN 2: ADSCRIPCIÓN Y CARGO */}
          <h4 style={{ fontSize: '0.9rem', color: 'var(--teal-500)', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '0.35rem', marginBottom: '0.85rem' }}>
            2. Adscripción Institucional y Cargo
          </h4>
          {formData.tipo === 'IIEE' ? (
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '0.85rem', marginBottom: '0.85rem' }}>
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
            <div className="form-group" style={{ marginBottom: '0.85rem' }}>
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

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.85rem', marginBottom: '1rem' }}>
            <div className="form-group">
              <label className="form-label">Cargo</label>
              <select
                className="form-select"
                value={formData.cargo_id}
                onChange={(e) => setFormData({ ...formData, cargo_id: e.target.value })}
              >
                <option value="">-- Seleccionar Cargo --</option>
                {catalogos?.cargos?.map((c) => (
                  <option key={c.id} value={c.id}>{c.nombre}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Categoría / Grupo Ocupacional</label>
              <select
                className="form-select"
                value={formData.categoria_id}
                onChange={(e) => setFormData({ ...formData, categoria_id: e.target.value })}
              >
                <option value="">-- Seleccionar Categoría --</option>
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

          {/* SECCIÓN 3: RÉGIMEN LABORAL Y PENSIONARIO */}
          <h4 style={{ fontSize: '0.9rem', color: 'var(--teal-500)', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '0.35rem', marginBottom: '0.85rem' }}>
            3. Régimen Laboral y Datos de Boleta
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.85rem', marginBottom: '0.85rem' }}>
            <div className="form-group">
              <label className="form-label">Régimen Laboral Nº</label>
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

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.85rem', marginBottom: '1rem' }}>
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

          {/* SECCIÓN 4: PAGO Y LEYENDAS */}
          <h4 style={{ fontSize: '0.9rem', color: 'var(--teal-500)', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '0.35rem', marginBottom: '0.85rem' }}>
            4. Remuneración Base y Pago
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.85rem', marginBottom: '0.85rem' }}>
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
                <option value="CUENTA">Cuenta Ahorros / TeleAhorro</option>
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
            <label className="form-label">Leyenda Permanente</label>
            <input
              type="text"
              className="form-input"
              placeholder="Ej. MANDATO JUDICIAL RES. N° 45-2018"
              value={formData.leyenda_permanente}
              onChange={(e) => setFormData({ ...formData, leyenda_permanente: e.target.value })}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
            <button type="button" onClick={() => setIsModalOpen(false)} className="btn btn-secondary">
              Cancelar
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? 'Guardando...' : editingTrabajador ? 'Actualizar Ficha Completa' : 'Registrar Trabajador'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
